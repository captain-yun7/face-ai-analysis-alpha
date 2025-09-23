#!/bin/bash

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로깅 함수
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 스크립트 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 설정
TERRAFORM_DIR="$PROJECT_DIR/terraform"
ANSIBLE_DIR="$PROJECT_DIR/ansible"

log_info "🚀 Face API Oracle Cloud 배포 시작..."

# 사전 조건 확인
check_prerequisites() {
    log_info "📋 사전 조건 확인 중..."
    
    # 필수 도구 확인
    local tools=("terraform" "ansible" "oci")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool이 설치되어 있지 않습니다."
            exit 1
        fi
    done
    
    # Terraform 설정 파일 확인
    if [[ ! -f "$TERRAFORM_DIR/terraform.tfvars" ]]; then
        log_error "terraform.tfvars 파일이 없습니다."
        log_info "terraform.tfvars.example을 참조하여 생성하세요."
        exit 1
    fi
    
    # SSH 키 확인
    if [[ ! -f "$HOME/.ssh/oracle_key" ]]; then
        log_warning "Oracle SSH 키가 없습니다. 새로 생성합니다..."
        ssh-keygen -t rsa -b 4096 -f ~/.ssh/oracle_key -N ""
        log_success "SSH 키 생성 완료: ~/.ssh/oracle_key"
    fi
    
    log_success "사전 조건 확인 완료"
}

# Terraform 인프라 배포
deploy_infrastructure() {
    log_info "📦 Terraform 인프라 배포 중..."
    
    cd "$TERRAFORM_DIR"
    
    # Terraform 초기화
    log_info "Terraform 초기화 중..."
    terraform init
    
    # 계획 확인
    log_info "배포 계획 확인 중..."
    terraform plan -out=tfplan
    
    # 사용자 확인
    echo
    read -p "배포를 계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "배포가 취소되었습니다."
        exit 0
    fi
    
    # 인프라 생성
    log_info "인프라 생성 중... (시간이 오래 걸릴 수 있습니다)"
    terraform apply tfplan
    
    # 출력값 저장
    INSTANCE_IP=$(terraform output -raw instance_public_ip)
    log_success "인프라 배포 완료. 인스턴스 IP: $INSTANCE_IP"
    
    cd "$PROJECT_DIR"
}

# Ansible 인벤토리 업데이트
update_inventory() {
    log_info "📝 Ansible 인벤토리 업데이트 중..."
    
    local inventory_file="$ANSIBLE_DIR/inventory/hosts.yml"
    
    # IP 주소 업데이트
    sed -i.backup "s/REPLACE_WITH_PUBLIC_IP/$INSTANCE_IP/g" "$inventory_file"
    
    log_success "인벤토리 업데이트 완료"
}

# 인스턴스 준비 대기
wait_for_instance() {
    log_info "⏳ 인스턴스 준비 대기 중..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        log_info "연결 시도 $attempt/$max_attempts..."
        
        if ssh -i ~/.ssh/oracle_key -o ConnectTimeout=10 -o StrictHostKeyChecking=no ubuntu@"$INSTANCE_IP" "echo 'connected'" &>/dev/null; then
            log_success "인스턴스 연결 성공"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "인스턴스 연결 실패"
            exit 1
        fi
        
        sleep 30
        ((attempt++))
    done
}

# Ansible 플레이북 실행
run_ansible() {
    log_info "⚙️ Ansible 서버 설정 중..."
    
    cd "$ANSIBLE_DIR"
    
    # 연결 테스트
    log_info "Ansible 연결 테스트..."
    ansible all -m ping
    
    # 전체 플레이북 실행
    log_info "서버 설정 플레이북 실행 중..."
    ansible-playbook playbooks/site.yml -v
    
    log_success "Ansible 설정 완료"
    
    cd "$PROJECT_DIR"
}

# 배포 후 검증
verify_deployment() {
    log_info "🔍 배포 검증 중..."
    
    # 애플리케이션 헬스체크
    log_info "애플리케이션 헬스체크..."
    local max_attempts=10
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "http://$INSTANCE_IP:8000/health" > /dev/null; then
            log_success "애플리케이션이 정상적으로 실행 중입니다"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_warning "애플리케이션 헬스체크 실패 (HTTP)"
            break
        fi
        
        sleep 10
        ((attempt++))
    done
    
    # SSL 인증서 확인 (도메인이 설정된 경우)
    local domain=$(grep -o 'your-domain\.com' "$ANSIBLE_DIR/inventory/hosts.yml" | head -1)
    if [[ "$domain" != "your-domain.com" ]]; then
        log_info "HTTPS 연결 테스트..."
        if curl -f -s "https://$domain/health" > /dev/null; then
            log_success "HTTPS 연결 성공"
        else
            log_warning "HTTPS 연결 실패"
        fi
    fi
}

# 배포 정보 출력
print_deployment_info() {
    log_success "🎉 배포 완료!"
    echo
    echo "==================== 배포 정보 ===================="
    echo "인스턴스 IP: $INSTANCE_IP"
    echo "SSH 연결: ssh -i ~/.ssh/oracle_key ubuntu@$INSTANCE_IP"
    echo "HTTP URL: http://$INSTANCE_IP:8000"
    echo "헬스체크: http://$INSTANCE_IP:8000/health"
    
    local domain=$(grep -o 'domain_name:.*' "$ANSIBLE_DIR/inventory/hosts.yml" | cut -d' ' -f2)
    if [[ "$domain" != "your-domain.com" ]]; then
        echo "HTTPS URL: https://$domain"
        echo "HTTPS 헬스체크: https://$domain/health"
    fi
    
    echo "=================================================="
    echo
    echo "📋 다음 단계:"
    echo "1. 도메인 DNS를 $INSTANCE_IP로 설정"
    echo "2. SSL 인증서 발급 (도메인 설정 후)"
    echo "3. 애플리케이션 테스트"
    echo
}

# 에러 처리
cleanup_on_error() {
    log_error "배포 중 오류가 발생했습니다."
    
    read -p "인프라를 정리하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "인프라 정리 중..."
        cd "$TERRAFORM_DIR"
        terraform destroy -auto-approve
        log_success "인프라 정리 완료"
    fi
    
    exit 1
}

# 메인 실행 함수
main() {
    trap cleanup_on_error ERR
    
    check_prerequisites
    deploy_infrastructure
    update_inventory
    wait_for_instance
    run_ansible
    verify_deployment
    print_deployment_info
}

# 도움말
show_help() {
    echo "Face API Oracle Cloud 배포 스크립트"
    echo
    echo "사용법: $0 [옵션]"
    echo
    echo "옵션:"
    echo "  -h, --help     이 도움말 표시"
    echo "  --skip-infra   인프라 배포 건너뛰기"
    echo "  --skip-ansible Ansible 실행 건너뛰기"
    echo "  --verify-only  검증만 실행"
    echo
    echo "예제:"
    echo "  $0                 # 전체 배포"
    echo "  $0 --skip-infra    # 인프라 건너뛰고 애플리케이션만 배포"
    echo "  $0 --verify-only   # 배포 검증만 실행"
    echo
}

# 옵션 처리
SKIP_INFRA=false
SKIP_ANSIBLE=false
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --skip-infra)
            SKIP_INFRA=true
            shift
            ;;
        --skip-ansible)
            SKIP_ANSIBLE=true
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
done

# 옵션에 따른 실행
if [[ "$VERIFY_ONLY" == "true" ]]; then
    # IP 주소 가져오기
    if [[ -f "$TERRAFORM_DIR/terraform.tfstate" ]]; then
        INSTANCE_IP=$(cd "$TERRAFORM_DIR" && terraform output -raw instance_public_ip)
        verify_deployment
    else
        log_error "Terraform 상태 파일을 찾을 수 없습니다."
        exit 1
    fi
else
    # 조건부 실행
    check_prerequisites
    
    if [[ "$SKIP_INFRA" == "false" ]]; then
        deploy_infrastructure
        update_inventory
        wait_for_instance
    else
        # 기존 인프라에서 IP 가져오기
        INSTANCE_IP=$(cd "$TERRAFORM_DIR" && terraform output -raw instance_public_ip)
    fi
    
    if [[ "$SKIP_ANSIBLE" == "false" ]]; then
        run_ansible
    fi
    
    verify_deployment
    print_deployment_info
fi
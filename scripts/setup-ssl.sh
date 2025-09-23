#!/bin/bash

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 로깅 함수
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 기본값 설정
DOMAIN=${1:-""}
EMAIL=${2:-""}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 도움말 표시
show_help() {
    echo "SSL 인증서 설정 스크립트"
    echo
    echo "사용법: $0 <domain> [email]"
    echo
    echo "인자:"
    echo "  domain    도메인 이름 (예: api.example.com)"
    echo "  email     Let's Encrypt 알림 이메일 (선택사항)"
    echo
    echo "예제:"
    echo "  $0 api.example.com admin@example.com"
    echo "  $0 myapi.com"
    echo
}

# 인자 검증
validate_args() {
    if [[ -z "$DOMAIN" ]]; then
        log_error "도메인이 지정되지 않았습니다."
        show_help
        exit 1
    fi
    
    if [[ -z "$EMAIL" ]]; then
        EMAIL="admin@$DOMAIN"
        log_info "이메일이 지정되지 않아 기본값을 사용합니다: $EMAIL"
    fi
    
    # 도메인 유효성 검사
    if ! [[ "$DOMAIN" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$ ]]; then
        log_error "유효하지 않은 도메인 형식입니다: $DOMAIN"
        exit 1
    fi
}

# DNS 확인
check_dns() {
    log_info "DNS 설정 확인 중..."
    
    # 도메인이 현재 서버를 가리키는지 확인
    local domain_ip
    domain_ip=$(dig +short "$DOMAIN" | tail -n1)
    
    if [[ -z "$domain_ip" ]]; then
        log_error "도메인 $DOMAIN의 DNS 레코드를 찾을 수 없습니다."
        log_warning "도메인의 A 레코드가 이 서버의 IP를 가리키도록 설정하세요."
        
        read -p "DNS 설정을 완료했다면 계속하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_warning "SSL 설정이 취소되었습니다."
            exit 0
        fi
    else
        log_success "DNS 레코드 확인됨: $DOMAIN -> $domain_ip"
    fi
}

# 기존 인증서 확인
check_existing_cert() {
    local cert_path="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    
    if [[ -f "$cert_path" ]]; then
        log_info "기존 SSL 인증서를 발견했습니다."
        
        # 인증서 만료일 확인
        local expiry_date
        expiry_date=$(openssl x509 -enddate -noout -in "$cert_path" | cut -d= -f2)
        
        log_info "현재 인증서 만료일: $expiry_date"
        
        read -p "기존 인증서를 갱신하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "인증서 갱신을 건너뜁니다."
            return 0
        fi
    fi
    
    return 1
}

# 웹 서버 중지
stop_webserver() {
    log_info "SSL 인증서 발급을 위해 웹 서버를 일시 중지합니다..."
    
    # Docker 컨테이너 중지
    if docker ps --format "table {{.Names}}" | grep -q nginx-proxy; then
        docker stop nginx-proxy || true
        NGINX_WAS_RUNNING=true
    fi
    
    # Nginx 서비스 중지 (시스템에 직접 설치된 경우)
    if systemctl is-active --quiet nginx 2>/dev/null; then
        sudo systemctl stop nginx
        SYSTEM_NGINX_WAS_RUNNING=true
    fi
}

# 웹 서버 시작
start_webserver() {
    log_info "웹 서버를 다시 시작합니다..."
    
    # Docker 컨테이너 시작
    if [[ "$NGINX_WAS_RUNNING" == "true" ]]; then
        cd "$PROJECT_DIR"
        docker-compose -f docker/docker-compose.prod.yml start nginx
    fi
    
    # Nginx 서비스 시작
    if [[ "$SYSTEM_NGINX_WAS_RUNNING" == "true" ]]; then
        sudo systemctl start nginx
    fi
}

# SSL 인증서 발급
obtain_certificate() {
    log_info "Let's Encrypt SSL 인증서 발급 중..."
    
    # Certbot 설치 확인
    if ! command -v certbot &> /dev/null; then
        log_info "Certbot을 설치합니다..."
        sudo apt update
        sudo apt install -y certbot
    fi
    
    # 인증서 발급
    sudo certbot certonly \
        --standalone \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains "$DOMAIN" \
        --non-interactive
    
    if [[ $? -eq 0 ]]; then
        log_success "SSL 인증서 발급 완료"
    else
        log_error "SSL 인증서 발급 실패"
        start_webserver
        exit 1
    fi
}

# Nginx 설정 업데이트
update_nginx_config() {
    log_info "Nginx 설정을 업데이트합니다..."
    
    local nginx_config="$PROJECT_DIR/docker/nginx/nginx.conf"
    local ansible_template="$PROJECT_DIR/ansible/playbooks/templates/nginx.conf.j2"
    
    # Ansible 인벤토리에서 도메인 업데이트
    local inventory_file="$PROJECT_DIR/ansible/inventory/hosts.yml"
    if [[ -f "$inventory_file" ]]; then
        sed -i.backup "s/domain_name: .*/domain_name: $DOMAIN/" "$inventory_file"
        sed -i.backup "s/ssl_email: .*/ssl_email: $EMAIL/" "$inventory_file"
        log_success "Ansible 인벤토리 업데이트 완료"
    fi
    
    # Nginx 설정에서 도메인 업데이트 (템플릿이 있는 경우)
    if [[ -f "$nginx_config" ]]; then
        sed -i.backup "s/your-domain\.com/$DOMAIN/g" "$nginx_config"
        log_success "Nginx 설정 업데이트 완료"
    fi
}

# 자동 갱신 설정
setup_renewal() {
    log_info "SSL 인증서 자동 갱신 설정 중..."
    
    # 갱신 스크립트 생성
    local renewal_script="/opt/ssl-renewal.sh"
    sudo tee "$renewal_script" > /dev/null <<EOF
#!/bin/bash

# SSL 인증서 갱신 스크립트
LOG_FILE="/var/log/ssl-renewal.log"
DATE=\$(date '+%Y-%m-%d %H:%M:%S')

echo "[\$DATE] SSL 인증서 갱신 시작" >> \$LOG_FILE

# 인증서 갱신
if certbot renew --quiet --no-self-upgrade; then
    echo "[\$DATE] SSL 인증서 갱신 성공" >> \$LOG_FILE
    
    # Docker 컨테이너가 실행 중인 경우 Nginx 재시작
    if docker ps --format "table {{.Names}}" | grep -q nginx-proxy; then
        docker exec nginx-proxy nginx -s reload
        echo "[\$DATE] Nginx 설정 재로드 완료" >> \$LOG_FILE
    fi
else
    echo "[\$DATE] SSL 인증서 갱신 실패" >> \$LOG_FILE
fi
EOF
    
    sudo chmod +x "$renewal_script"
    
    # Cron 작업 설정
    local cron_job="0 2 * * * $renewal_script"
    
    # 기존 cron 작업 제거
    sudo crontab -l 2>/dev/null | grep -v ssl-renewal.sh | sudo crontab - || true
    
    # 새 cron 작업 추가
    (sudo crontab -l 2>/dev/null; echo "$cron_job") | sudo crontab -
    
    log_success "자동 갱신 설정 완료 (매일 02:00)"
}

# SSL 인증서 테스트
test_certificate() {
    log_info "SSL 인증서 테스트 중..."
    
    # HTTPS 연결 테스트
    if curl -f -s "https://$DOMAIN" > /dev/null; then
        log_success "HTTPS 연결 성공"
    else
        log_warning "HTTPS 연결 테스트 실패"
    fi
    
    # SSL 등급 확인 (선택사항)
    log_info "SSL Labs에서 SSL 등급을 확인할 수 있습니다:"
    log_info "https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
}

# 배포 정보 출력
print_ssl_info() {
    log_success "🔒 SSL 설정 완료!"
    echo
    echo "==================== SSL 정보 ===================="
    echo "도메인: $DOMAIN"
    echo "이메일: $EMAIL"
    echo "인증서 위치: /etc/letsencrypt/live/$DOMAIN/"
    echo "HTTPS URL: https://$DOMAIN"
    echo "헬스체크: https://$DOMAIN/health"
    echo "=================================================="
    echo
    echo "📋 참고사항:"
    echo "• SSL 인증서는 90일마다 자동 갱신됩니다"
    echo "• 갱신 로그: /var/log/ssl-renewal.log"
    echo "• 수동 갱신: sudo certbot renew"
    echo
}

# 에러 처리
cleanup_on_error() {
    log_error "SSL 설정 중 오류가 발생했습니다."
    start_webserver
    exit 1
}

# 메인 실행
main() {
    trap cleanup_on_error ERR
    
    validate_args
    check_dns
    
    if ! check_existing_cert; then
        stop_webserver
        obtain_certificate
        start_webserver
    fi
    
    update_nginx_config
    setup_renewal
    test_certificate
    print_ssl_info
}

# 옵션 처리
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    "")
        log_error "도메인이 지정되지 않았습니다."
        show_help
        exit 1
        ;;
    *)
        main
        ;;
esac
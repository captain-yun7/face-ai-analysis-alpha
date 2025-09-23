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

# 스크립트 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 설정
BACKUP_DIR="$PROJECT_DIR/backups"
COMPOSE_FILE="$PROJECT_DIR/docker/docker-compose.prod.yml"

log_info "🔙 Face API 애플리케이션 롤백 시작..."

# 사용 가능한 백업 목록 표시
list_backups() {
    log_info "사용 가능한 백업 목록:"
    echo
    
    # Docker 이미지 백업 목록
    echo "📦 Docker 이미지 백업:"
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}" | grep "face-api:backup-" || echo "  백업 이미지 없음"
    
    echo
    
    # 파일 백업 목록
    echo "📁 파일 백업:"
    if [[ -d "$BACKUP_DIR" ]]; then
        find "$BACKUP_DIR" -name "backup-*.tar.gz" -printf "%f\t%TY-%Tm-%Td %TH:%TM\t%s bytes\n" | sort -r || echo "  백업 파일 없음"
    else
        echo "  백업 디렉토리 없음"
    fi
    
    echo
}

# 백업 선택
select_backup() {
    local backup_images
    backup_images=($(docker images --format "{{.Repository}}:{{.Tag}}" | grep "face-api:backup-" | sort -r))
    
    if [[ ${#backup_images[@]} -eq 0 ]]; then
        log_error "사용 가능한 백업 이미지가 없습니다."
        exit 1
    fi
    
    echo "롤백할 백업을 선택하세요:"
    for i in "${!backup_images[@]}"; do
        echo "$((i+1)). ${backup_images[i]}"
    done
    
    read -p "번호를 입력하세요 (1-${#backup_images[@]}): " -r choice
    
    if [[ "$choice" -ge 1 && "$choice" -le ${#backup_images[@]} ]]; then
        SELECTED_BACKUP="${backup_images[$((choice-1))]}"
        log_info "선택된 백업: $SELECTED_BACKUP"
    else
        log_error "잘못된 선택입니다."
        exit 1
    fi
}

# 현재 상태 확인
check_current_state() {
    log_info "현재 애플리케이션 상태 확인..."
    
    # 컨테이너 상태 확인
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_info "애플리케이션이 실행 중입니다."
        CURRENT_RUNNING=true
        
        # 헬스체크
        if curl -f -s "http://localhost:8000/health" > /dev/null; then
            log_info "현재 애플리케이션 헬스체크 통과"
        else
            log_warning "현재 애플리케이션 헬스체크 실패"
        fi
    else
        log_warning "애플리케이션이 실행되지 않고 있습니다."
        CURRENT_RUNNING=false
    fi
}

# 롤백 실행 전 확인
confirm_rollback() {
    echo
    log_warning "⚠️  롤백 주의사항:"
    echo "• 현재 버전의 데이터나 설정이 손실될 수 있습니다"
    echo "• 롤백 후에는 이전 상태로 되돌리기 어려울 수 있습니다"
    echo "• 현재 실행 중인 세션이 중단됩니다"
    echo
    
    read -p "정말 롤백을 진행하시겠습니까? (yes/no): " -r confirm
    
    if [[ "$confirm" != "yes" ]]; then
        log_info "롤백이 취소되었습니다."
        exit 0
    fi
}

# 현재 버전 백업
backup_current() {
    log_info "현재 버전을 백업합니다..."
    
    # 현재 이미지 백업
    if docker images -q face-api:latest > /dev/null; then
        local backup_tag="rollback-backup-$(date +%Y%m%d-%H%M%S)"
        docker tag face-api:latest "face-api:$backup_tag"
        log_success "현재 이미지 백업 완료: face-api:$backup_tag"
    fi
    
    # 현재 설정 백업
    if [[ -d "$PROJECT_DIR" ]]; then
        local backup_name="rollback-backup-$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        tar -czf "$BACKUP_DIR/$backup_name.tar.gz" \
            -C "$PROJECT_DIR" \
            docker/ \
            .env \
            logs/ \
            2>/dev/null || true
            
        log_success "현재 설정 백업 완료: $backup_name.tar.gz"
    fi
}

# Docker 이미지 롤백
rollback_docker_image() {
    log_info "Docker 이미지 롤백 중..."
    
    # 백업 이미지를 latest로 태그
    docker tag "$SELECTED_BACKUP" face-api:latest
    
    log_success "Docker 이미지 롤백 완료"
}

# 애플리케이션 재시작
restart_application() {
    log_info "애플리케이션 재시작 중..."
    
    cd "$PROJECT_DIR"
    
    # 기존 컨테이너 중지
    if [[ "$CURRENT_RUNNING" == "true" ]]; then
        docker-compose -f "$COMPOSE_FILE" down
    fi
    
    # 새 컨테이너 시작
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "애플리케이션 재시작 완료"
}

# 롤백 검증
verify_rollback() {
    log_info "롤백 검증 중..."
    
    # 애플리케이션 시작 대기
    local max_attempts=30
    local attempt=1
    
    log_info "애플리케이션 시작 대기..."
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "http://localhost:8000/health" > /dev/null; then
            log_success "애플리케이션이 정상적으로 시작되었습니다."
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "애플리케이션 시작 실패"
            return 1
        fi
        
        log_info "시작 대기 $attempt/$max_attempts..."
        sleep 10
        ((attempt++))
    done
    
    # 컨테이너 상태 확인
    local unhealthy_containers
    unhealthy_containers=$(docker-compose -f "$COMPOSE_FILE" ps | grep -v "Up" | wc -l)
    
    if [[ "$unhealthy_containers" -gt 1 ]]; then  # 헤더 라인 제외
        log_warning "일부 컨테이너가 비정상 상태입니다."
        docker-compose -f "$COMPOSE_FILE" ps
    else
        log_success "모든 컨테이너가 정상 상태입니다."
    fi
    
    # 메모리 및 CPU 사용량 확인
    local memory_usage
    memory_usage=$(docker stats --no-stream --format "{{.MemPerc}}" face-api | sed 's/%//')
    log_info "메모리 사용량: ${memory_usage}%"
    
    # 최근 로그 확인
    local error_count
    error_count=$(docker logs face-api --since="2m" 2>&1 | grep -c "ERROR" || echo "0")
    
    if [[ "$error_count" -gt 0 ]]; then
        log_warning "최근 2분간 에러 $error_count 건 발생"
        echo "최근 에러 로그:"
        docker logs face-api --since="2m" 2>&1 | grep "ERROR" | tail -5
    else
        log_success "최근 에러 없음"
    fi
}

# 롤백 정보 출력
print_rollback_info() {
    log_success "🎉 롤백 완료!"
    echo
    echo "==================== 롤백 정보 ===================="
    echo "롤백된 백업: $SELECTED_BACKUP"
    echo "롤백 시간: $(date)"
    echo "현재 컨테이너 상태:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo "=================================================="
    echo
    echo "📋 참고사항:"
    echo "• 현재 버전은 rollback-backup-* 태그로 백업되었습니다"
    echo "• 문제가 계속되면 다른 백업으로 다시 롤백할 수 있습니다"
    echo "• 애플리케이션 URL: http://localhost:8000"
    echo
}

# 롤백 실패 처리
handle_rollback_failure() {
    log_error "롤백에 실패했습니다."
    
    # 다른 백업으로 재시도 제안
    echo
    log_info "사용 가능한 다른 백업들:"
    docker images --format "{{.Repository}}:{{.Tag}}" | grep "face-api:backup-"
    
    read -p "다른 백업으로 재시도하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        select_backup
        rollback_docker_image
        restart_application
        verify_rollback
    else
        log_warning "롤백을 중단합니다. 수동으로 복구해주세요."
        exit 1
    fi
}

# 도움말
show_help() {
    echo "Face API 롤백 스크립트"
    echo
    echo "사용법: $0 [옵션]"
    echo
    echo "옵션:"
    echo "  -h, --help        이 도움말 표시"
    echo "  --list            사용 가능한 백업 목록만 표시"
    echo "  --auto            가장 최근 백업으로 자동 롤백"
    echo "  --backup <tag>    특정 백업으로 롤백"
    echo
    echo "예제:"
    echo "  $0                        # 대화형 롤백"
    echo "  $0 --list                 # 백업 목록 표시"
    echo "  $0 --auto                 # 자동 롤백"
    echo "  $0 --backup backup-20240101-120000  # 특정 백업으로 롤백"
    echo
}

# 메인 함수
main() {
    trap handle_rollback_failure ERR
    
    list_backups
    select_backup
    check_current_state
    confirm_rollback
    backup_current
    rollback_docker_image
    restart_application
    verify_rollback
    print_rollback_info
}

# 옵션 처리
LIST_ONLY=false
AUTO_ROLLBACK=false
SPECIFIC_BACKUP=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --list)
            LIST_ONLY=true
            shift
            ;;
        --auto)
            AUTO_ROLLBACK=true
            shift
            ;;
        --backup)
            SPECIFIC_BACKUP=$2
            shift 2
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
done

# 실행 모드에 따른 분기
if [[ "$LIST_ONLY" == "true" ]]; then
    list_backups
elif [[ "$AUTO_ROLLBACK" == "true" ]]; then
    # 가장 최근 백업 자동 선택
    SELECTED_BACKUP=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "face-api:backup-" | head -1)
    if [[ -z "$SELECTED_BACKUP" ]]; then
        log_error "사용 가능한 백업이 없습니다."
        exit 1
    fi
    log_info "자동 선택된 백업: $SELECTED_BACKUP"
    
    check_current_state
    backup_current
    rollback_docker_image
    restart_application
    verify_rollback
    print_rollback_info
elif [[ -n "$SPECIFIC_BACKUP" ]]; then
    # 특정 백업으로 롤백
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "face-api:$SPECIFIC_BACKUP"; then
        SELECTED_BACKUP="face-api:$SPECIFIC_BACKUP"
        log_info "지정된 백업: $SELECTED_BACKUP"
        
        check_current_state
        confirm_rollback
        backup_current
        rollback_docker_image
        restart_application
        verify_rollback
        print_rollback_info
    else
        log_error "지정된 백업을 찾을 수 없습니다: $SPECIFIC_BACKUP"
        list_backups
        exit 1
    fi
else
    # 대화형 롤백
    main
fi
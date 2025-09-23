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
BRANCH=${1:-main}

log_info "🔄 Face API 애플리케이션 업데이트 시작..."

# 백업 생성
create_backup() {
    log_info "📦 현재 상태 백업 생성 중..."
    
    mkdir -p "$BACKUP_DIR"
    local backup_name="backup-$(date +%Y%m%d-%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    # 현재 Docker 이미지 백업
    if docker images -q face-api:latest > /dev/null; then
        log_info "Docker 이미지 백업 중..."
        docker tag face-api:latest face-api:backup-$(date +%Y%m%d-%H%M%S)
    fi
    
    # 설정 파일 백업
    tar -czf "$backup_path.tar.gz" \
        -C "$PROJECT_DIR" \
        docker/ \
        .env \
        logs/ \
        2>/dev/null || true
    
    log_success "백업 생성 완료: $backup_path.tar.gz"
    
    # 오래된 백업 정리 (7일 이상)
    find "$BACKUP_DIR" -name "backup-*.tar.gz" -mtime +7 -delete 2>/dev/null || true
}

# 소스 코드 업데이트
update_source() {
    log_info "📥 소스 코드 업데이트 중..."
    
    cd "$PROJECT_DIR"
    
    # Git 상태 확인
    if [[ ! -d ".git" ]]; then
        log_warning "Git 저장소가 아닙니다. 소스 업데이트를 건너뜁니다."
        return 0
    fi
    
    # 변경사항 스태시
    if ! git diff-index --quiet HEAD --; then
        log_info "로컬 변경사항을 임시 저장합니다..."
        git stash push -m "Auto-stash before update $(date)"
    fi
    
    # 원격 저장소에서 최신 코드 가져오기
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
    
    log_success "소스 코드 업데이트 완료"
}

# 애플리케이션 상태 확인
check_app_status() {
    log_info "🔍 현재 애플리케이션 상태 확인..."
    
    # Docker Compose 서비스 상태
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_info "애플리케이션이 실행 중입니다."
        return 0
    else
        log_warning "애플리케이션이 실행되지 않고 있습니다."
        return 1
    fi
}

# 새 이미지 빌드
build_new_image() {
    log_info "🔨 새 Docker 이미지 빌드 중..."
    
    cd "$PROJECT_DIR"
    
    # 이미지 빌드
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    log_success "Docker 이미지 빌드 완료"
}

# 무중단 업데이트
rolling_update() {
    log_info "🚀 무중단 업데이트 수행 중..."
    
    cd "$PROJECT_DIR"
    
    # 헬스체크 함수
    check_health() {
        local url="http://localhost:8000/health"
        if curl -f -s "$url" > /dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    }
    
    # 새 컨테이너 시작 전 헬스체크
    if check_app_status; then
        log_info "기존 애플리케이션의 헬스체크..."
        if ! check_health; then
            log_warning "기존 애플리케이션이 비정상 상태입니다."
        fi
    fi
    
    # 새 컨테이너 시작
    log_info "새 버전의 컨테이너 시작 중..."
    docker-compose -f "$COMPOSE_FILE" up -d --force-recreate
    
    # 새 컨테이너 헬스체크 대기
    log_info "새 애플리케이션 시작 대기 중..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if check_health; then
            log_success "새 애플리케이션이 정상적으로 시작되었습니다."
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "새 애플리케이션 시작 실패"
            return 1
        fi
        
        log_info "헬스체크 시도 $attempt/$max_attempts..."
        sleep 10
        ((attempt++))
    done
}

# 롤백 함수
rollback() {
    log_warning "🔙 이전 버전으로 롤백 중..."
    
    # 가장 최근 백업 이미지 찾기
    local backup_image
    backup_image=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep "face-api:backup-" | head -1)
    
    if [[ -n "$backup_image" ]]; then
        log_info "백업 이미지로 롤백: $backup_image"
        docker tag "$backup_image" face-api:latest
        docker-compose -f "$COMPOSE_FILE" up -d --force-recreate
        
        # 롤백 후 헬스체크
        sleep 30
        if curl -f -s "http://localhost:8000/health" > /dev/null; then
            log_success "롤백 완료 - 애플리케이션이 정상 작동합니다."
        else
            log_error "롤백 후에도 애플리케이션이 정상 작동하지 않습니다."
        fi
    else
        log_error "롤백할 백업 이미지를 찾을 수 없습니다."
    fi
}

# 후속 작업
post_update_tasks() {
    log_info "🧹 후속 작업 수행 중..."
    
    # 미사용 Docker 이미지 정리
    docker image prune -f
    
    # 로그 로테이션
    if [[ -d "$PROJECT_DIR/logs" ]]; then
        find "$PROJECT_DIR/logs" -name "*.log" -size +100M -exec truncate -s 50M {} \;
    fi
    
    # 시스템 정보 로깅
    {
        echo "=== 업데이트 완료 $(date) ==="
        echo "Git commit: $(git rev-parse HEAD 2>/dev/null || echo 'N/A')"
        echo "Docker images:"
        docker images | grep face-api
        echo "Container status:"
        docker-compose -f "$COMPOSE_FILE" ps
        echo "==========================="
    } >> "$PROJECT_DIR/logs/update.log"
    
    log_success "후속 작업 완료"
}

# 업데이트 검증
verify_update() {
    log_info "✅ 업데이트 검증 중..."
    
    # 애플리케이션 헬스체크
    if curl -f -s "http://localhost:8000/health" > /dev/null; then
        log_success "애플리케이션 헬스체크 통과"
    else
        log_error "애플리케이션 헬스체크 실패"
        return 1
    fi
    
    # 메모리 사용량 확인
    local memory_usage
    memory_usage=$(docker stats --no-stream --format "{{.MemPerc}}" face-api | sed 's/%//')
    
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        log_warning "메모리 사용량이 높습니다: ${memory_usage}%"
    else
        log_success "메모리 사용량 정상: ${memory_usage}%"
    fi
    
    # 로그 확인
    local error_count
    error_count=$(docker logs face-api --since="5m" 2>&1 | grep -c "ERROR" || echo "0")
    
    if [[ "$error_count" -gt 0 ]]; then
        log_warning "최근 5분간 에러 $error_count 건 발생"
    else
        log_success "최근 에러 없음"
    fi
}

# 업데이트 정보 출력
print_update_info() {
    log_success "🎉 업데이트 완료!"
    echo
    echo "==================== 업데이트 정보 ===================="
    echo "브랜치: $BRANCH"
    echo "커밋: $(git rev-parse HEAD 2>/dev/null || echo 'N/A')"
    echo "업데이트 시간: $(date)"
    
    # 컨테이너 상태
    echo "컨테이너 상태:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo "======================================================"
    echo
}

# 도움말
show_help() {
    echo "Face API 업데이트 스크립트"
    echo
    echo "사용법: $0 [branch] [옵션]"
    echo
    echo "인자:"
    echo "  branch     업데이트할 Git 브랜치 (기본값: main)"
    echo
    echo "옵션:"
    echo "  -h, --help        이 도움말 표시"
    echo "  --no-backup       백업 생성 건너뛰기"
    echo "  --force-rebuild   캐시 무시하고 강제 리빌드"
    echo "  --rollback        이전 버전으로 롤백"
    echo "  --verify-only     업데이트 검증만 실행"
    echo
    echo "예제:"
    echo "  $0                    # main 브랜치로 업데이트"
    echo "  $0 develop            # develop 브랜치로 업데이트"
    echo "  $0 --rollback         # 이전 버전으로 롤백"
    echo "  $0 --verify-only      # 현재 상태 검증만 실행"
    echo
}

# 에러 핸들링
handle_error() {
    log_error "업데이트 중 오류가 발생했습니다."
    
    read -p "이전 버전으로 롤백하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rollback
    fi
    
    exit 1
}

# 메인 함수
main() {
    trap handle_error ERR
    
    create_backup
    update_source
    build_new_image
    rolling_update
    post_update_tasks
    verify_update
    print_update_info
}

# 옵션 처리
NO_BACKUP=false
FORCE_REBUILD=false
ROLLBACK_ONLY=false
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        --rollback)
            ROLLBACK_ONLY=true
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        -*)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
        *)
            BRANCH=$1
            shift
            ;;
    esac
done

# 실행 모드에 따른 분기
if [[ "$ROLLBACK_ONLY" == "true" ]]; then
    rollback
elif [[ "$VERIFY_ONLY" == "true" ]]; then
    verify_update
else
    if [[ "$NO_BACKUP" == "false" ]]; then
        main
    else
        update_source
        build_new_image
        rolling_update
        post_update_tasks
        verify_update
        print_update_info
    fi
fi
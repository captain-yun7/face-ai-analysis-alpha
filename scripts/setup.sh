#!/bin/bash
# Face Analysis API 설치 스크립트

set -e

echo "🚀 Face Analysis API 설치 시작..."

# 컬러 출력을 위한 함수
print_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# 시스템 요구사항 확인
check_requirements() {
    print_info "시스템 요구사항 확인 중..."
    
    # Python 3.8+ 확인
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3가 설치되지 않았습니다."
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    required_version="3.8"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        print_error "Python 3.8 이상이 필요합니다. 현재 버전: $python_version"
        exit 1
    fi
    
    print_success "Python $python_version 확인됨"
}

# 가상환경 생성 및 활성화
setup_venv() {
    print_info "Python 가상환경 설정 중..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "가상환경 생성 완료"
    else
        print_info "기존 가상환경 사용"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    print_success "가상환경 활성화 완료"
}

# 의존성 설치
install_dependencies() {
    print_info "의존성 설치 중..."
    
    # 시스템 의존성 (Ubuntu/Debian)
    if command -v apt-get &> /dev/null; then
        print_info "시스템 의존성 설치 (관리자 권한 필요)..."
        sudo apt-get update
        sudo apt-get install -y \
            build-essential \
            cmake \
            libopencv-dev \
            libgl1-mesa-glx \
            libglib2.0-0 \
            libsm6 \
            libxext6 \
            libxrender-dev \
            libgomp1
        print_success "시스템 의존성 설치 완료"
    fi
    
    # Python 기본 의존성 설치
    print_info "Python 기본 패키지 설치 중..."
    pip install fastapi uvicorn python-multipart pydantic pydantic-settings python-dotenv loguru psutil
    pip install numpy pillow opencv-python onnxruntime
    print_success "Python 기본 의존성 설치 완료"
    
    # InsightFace 설치 시도 (선택적)
    print_info "InsightFace 설치 시도 중..."
    if pip install insightface 2>/dev/null; then
        print_success "InsightFace 설치 성공!"
    else
        print_warning "InsightFace 설치 실패 - 더미 모드로 실행됩니다"
        print_info "Python 3.9-3.11을 사용하면 InsightFace 설치가 더 안정적입니다"
    fi
    
    print_success "의존성 설치 완료"
}

# 환경 설정
setup_config() {
    print_info "환경 설정 중..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success ".env 파일 생성 완료"
        print_warning "필요에 따라 .env 파일을 수정하세요"
    else
        print_info "기존 .env 파일 사용"
    fi
    
    # 로그 디렉토리 생성
    mkdir -p logs
    print_success "로그 디렉토리 생성 완료"
}

# InsightFace 모델 다운로드
download_models() {
    print_info "InsightFace 모델 다운로드 시도 중..."
    
    python3 -c "
try:
    import insightface
    app = insightface.app.FaceAnalysis(providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=-1)
    print('✅ InsightFace 모델 다운로드 완료!')
except ImportError:
    print('⚠️ InsightFace가 설치되지 않음 - 더미 모드로 실행됩니다')
except Exception as e:
    print(f'⚠️ 모델 다운로드 실패: {e} - 더미 모드로 실행됩니다')
"
    
    # 모델 다운로드가 실패해도 계속 진행
    print_info "모델 초기화 완료 (실패 시 더미 모드로 동작)"
}

# 서버 테스트
test_server() {
    print_info "서버 테스트 중..."
    
    # 백그라운드에서 서버 시작
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    SERVER_PID=$!
    
    # 서버 시작 대기
    sleep 10
    
    # 헬스체크 테스트
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "서버 테스트 통과!"
        print_info "🌐 API 문서: http://localhost:8000/docs"
        print_info "🔍 헬스체크: http://localhost:8000/health"
        
        # 헬스체크 결과 표시
        health_result=$(curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "JSON 파싱 실패")
        print_info "헬스체크 응답: $health_result"
    else
        print_error "서버 테스트 실패"
        print_info "로그를 확인하세요: tail -f logs/app.log"
    fi
    
    # 서버 종료
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
}

# Docker 설치 확인 및 안내
check_docker() {
    print_info "Docker 설치 확인..."
    
    if command -v docker &> /dev/null; then
        print_success "Docker 설치됨"
        print_info "Docker로 실행하려면: docker-compose up -d"
    else
        print_warning "Docker가 설치되지 않았습니다"
        print_info "Docker 설치 가이드: https://docs.docker.com/get-docker/"
    fi
}

# 사용법 출력
print_usage() {
    print_success "설치 완료! 🎉"
    echo ""
    echo "📋 사용법:"
    echo "  개발 서버 실행:  python -m uvicorn app.main:app --reload"
    echo "  프로덕션 실행:    gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker"
    echo "  Docker 실행:     docker-compose up -d"
    echo ""
    echo "🔗 유용한 링크:"
    echo "  API 문서:        http://localhost:8000/docs"
    echo "  헬스체크:        http://localhost:8000/health"
    echo "  로그 확인:       tail -f logs/app.log"
    echo ""
}

# 메인 실행
main() {
    check_requirements
    setup_venv
    install_dependencies
    setup_config
    download_models
    test_server
    check_docker
    print_usage
}

# 옵션 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-test)
            SKIP_TEST=true
            shift
            ;;
        --docker-only)
            DOCKER_ONLY=true
            shift
            ;;
        --help|-h)
            echo "사용법: $0 [옵션]"
            echo "옵션:"
            echo "  --skip-test    서버 테스트 생략"
            echo "  --docker-only  Docker 설정만 확인"
            echo "  --help, -h     도움말 출력"
            exit 0
            ;;
        *)
            print_error "알 수 없는 옵션: $1"
            exit 1
            ;;
    esac
done

# Docker만 확인하는 경우
if [ "$DOCKER_ONLY" = true ]; then
    check_docker
    print_info "Docker Compose로 실행: docker-compose up -d"
    exit 0
fi

# 메인 실행
main

print_success "Face Analysis API 설치 완료! 🏁"
#!/bin/bash
# Face Analysis API ARM64 환경 설치 스크립트

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

echo "🚀 Face Analysis API ARM64 설치 시작..."

# 아키텍처 확인
ARCH=$(uname -m)
OS=$(uname -s)

log_info "시스템 정보:"
log_info "  아키텍처: $ARCH"
log_info "  운영체제: $OS"

if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" ]]; then
    log_warning "ARM64 아키텍처가 아닙니다. 호환성 문제가 발생할 수 있습니다."
fi

# 시스템 패키지 업데이트 및 필수 도구 설치
install_system_dependencies() {
    log_info "시스템 의존성 설치 중..."
    
    sudo apt-get update
    sudo apt-get install -y \
        build-essential \
        cmake \
        pkg-config \
        wget \
        curl \
        git \
        libopencv-dev \
        libgl1-mesa-dev \
        libglib2.0-dev \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        libfontconfig1-dev \
        libfreetype6-dev \
        python3-dev \
        python3-pip \
        python3-venv
    
    log_success "시스템 의존성 설치 완료"
}

# Miniconda ARM64 버전 설치
install_miniconda_arm64() {
    if [[ -d "$HOME/miniconda3" ]]; then
        log_info "Miniconda가 이미 설치되어 있습니다."
        return 0
    fi
    
    log_info "Miniconda ARM64 설치 중..."
    
    # ARM64용 Miniconda 다운로드
    local miniconda_url
    if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
        miniconda_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"
    else
        miniconda_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    fi
    
    wget "$miniconda_url" -O /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p "$HOME/miniconda3"
    rm /tmp/miniconda.sh
    
    # PATH 업데이트
    export PATH="$HOME/miniconda3/bin:$PATH"
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    
    log_success "Miniconda ARM64 설치 완료"
}

# Conda 환경 설정
setup_conda_environment() {
    log_info "Conda 환경 설정 중..."
    
    # Conda 초기화
    conda init bash
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    
    # Conda 설정 최적화
    conda config --set solver libmamba
    conda config --set channel_priority flexible
    conda config --remove channels defaults 2>/dev/null || true
    conda config --add channels conda-forge
    conda config --add channels pytorch
    
    # ARM64 환경에 최적화된 채널 추가
    if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
        conda config --add channels https://conda.anaconda.org/conda-forge/linux-aarch64
    fi
    
    log_success "Conda 환경 설정 완료"
}

# Python 환경 생성
create_python_environment() {
    log_info "Python 환경 생성 중..."
    
    # 기존 환경 제거
    if conda env list | grep -q "face-api"; then
        log_info "기존 환경 제거 중..."
        conda env remove -n face-api -y 2>/dev/null || true
    fi
    
    # 새 환경 생성
    conda create -n face-api python=3.11 -c conda-forge -y
    conda activate face-api
    
    log_success "Python 환경 생성 완료"
}

# ARM64 최적화 패키지 설치
install_arm64_packages() {
    log_info "ARM64 최적화 패키지 설치 중..."
    
    conda activate face-api
    
    # 핵심 패키지 설치 (Conda)
    log_info "핵심 패키지 설치 (conda)..."
    conda install -c conda-forge --override-channels \
        numpy \
        opencv \
        pillow \
        scipy \
        scikit-image \
        matplotlib \
        -y
    
    # PyTorch ARM64 버전
    log_info "PyTorch ARM64 설치..."
    if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
        # ARM64용 PyTorch
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    else
        conda install pytorch torchvision torchaudio cpuonly -c pytorch -y
    fi
    
    # ONNX Runtime ARM64
    log_info "ONNX Runtime ARM64 설치..."
    pip install onnxruntime
    
    log_success "ARM64 최적화 패키지 설치 완료"
}

# InsightFace ARM64 설치
install_insightface_arm64() {
    log_info "InsightFace ARM64 설치 중..."
    
    conda activate face-api
    
    # InsightFace 의존성 설치
    pip install \
        easydict \
        scikit-learn \
        Cython \
        albumentations
    
    # InsightFace 설치 (ARM64 호환 버전)
    pip install insightface
    
    # 모델 디렉토리 생성
    mkdir -p "$HOME/.insightface/models"
    
    log_success "InsightFace ARM64 설치 완료"
}

# FastAPI 및 웹 서버 패키지 설치
install_web_packages() {
    log_info "웹 서버 패키지 설치 중..."
    
    conda activate face-api
    
    # requirements.txt에서 패키지 설치
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    else
        # 기본 웹 패키지 설치
        pip install \
            fastapi \
            uvicorn \
            gunicorn \
            python-multipart \
            pydantic \
            pydantic-settings \
            psutil \
            loguru
    fi
    
    log_success "웹 서버 패키지 설치 완료"
}

# 환경 설정
setup_environment() {
    log_info "환경 설정 중..."
    
    # 디렉토리 생성
    mkdir -p logs temp
    
    # 환경변수 파일 생성
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_info ".env 파일을 .env.example에서 복사했습니다."
        else
            cat > .env << EOF
# Face API ARM64 환경 설정
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
HOST=0.0.0.0
PORT=8000
USE_GPU=false
MODEL_NAME=buffalo_l
CACHE_ENABLED=false
EOF
            log_info "기본 .env 파일을 생성했습니다."
        fi
    fi
    
    log_success "환경 설정 완료"
}

# 설치 검증
verify_installation() {
    log_info "설치 검증 중..."
    
    conda activate face-api
    
    # Python 패키지 임포트 테스트
    local packages=(
        "import numpy; print('✅ NumPy:', numpy.__version__)"
        "import cv2; print('✅ OpenCV:', cv2.__version__)"
        "import torch; print('✅ PyTorch:', torch.__version__)"
        "import onnxruntime; print('✅ ONNX Runtime:', onnxruntime.__version__)"
        "import insightface; print('✅ InsightFace 임포트 성공')"
        "import fastapi; print('✅ FastAPI:', fastapi.__version__)"
        "import uvicorn; print('✅ Uvicorn 임포트 성공')"
    )
    
    local success_count=0
    local total_count=${#packages[@]}
    
    for package_test in "${packages[@]}"; do
        if python -c "$package_test" 2>/dev/null; then
            ((success_count++))
        else
            log_warning "패키지 테스트 실패: $package_test"
        fi
    done
    
    log_info "검증 결과: $success_count/$total_count 패키지 성공"
    
    if [[ $success_count -eq $total_count ]]; then
        log_success "모든 패키지 검증 통과!"
    else
        log_warning "일부 패키지 검증 실패"
    fi
    
    # 모델 다운로드 테스트 (선택사항)
    log_info "InsightFace 모델 테스트..."
    python -c "
import insightface
try:
    app = insightface.app.FaceAnalysis(providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    print('✅ InsightFace 모델 로드 성공')
except Exception as e:
    print(f'⚠️  InsightFace 모델 로드 실패: {e}')
    print('   모델은 첫 실행 시 자동 다운로드됩니다.')
" || true
}

# 서비스 스크립트 생성
create_service_scripts() {
    log_info "서비스 스크립트 생성 중..."
    
    # 개발 서버 시작 스크립트
    cat > start-dev.sh << 'EOF'
#!/bin/bash
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate face-api
export PYTHONPATH="$PWD"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EOF
    chmod +x start-dev.sh
    
    # 프로덕션 서버 시작 스크립트
    cat > start-prod.sh << 'EOF'
#!/bin/bash
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate face-api
export PYTHONPATH="$PWD"
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
EOF
    chmod +x start-prod.sh
    
    # 테스트 스크립트
    cat > test.sh << 'EOF'
#!/bin/bash
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate face-api
export PYTHONPATH="$PWD"
python -m pytest tests/ -v
EOF
    chmod +x test.sh
    
    log_success "서비스 스크립트 생성 완료"
}

# 정보 출력
print_installation_info() {
    log_success "🎉 ARM64 환경 설치 완료!"
    echo
    echo "==================== 설치 정보 ===================="
    echo "아키텍처: $ARCH"
    echo "Python 환경: face-api"
    echo "Conda 경로: $HOME/miniconda3"
    echo "=================================================="
    echo
    echo "🔧 환경 활성화:"
    echo "  source \$HOME/miniconda3/etc/profile.d/conda.sh"
    echo "  conda activate face-api"
    echo
    echo "🚀 서버 실행:"
    echo "  개발 서버: ./start-dev.sh"
    echo "  프로덕션: ./start-prod.sh"
    echo
    echo "🧪 테스트:"
    echo "  ./test.sh"
    echo "  curl http://localhost:8000/health"
    echo
    echo "📁 중요 파일:"
    echo "  환경 설정: .env"
    echo "  로그: logs/"
    echo "  임시 파일: temp/"
    echo
}

# 에러 처리
handle_error() {
    log_error "설치 중 오류가 발생했습니다."
    log_info "문제 해결을 위한 정보:"
    echo "  - 시스템: $OS $ARCH"
    echo "  - Python: $(python3 --version 2>/dev/null || echo 'Not installed')"
    echo "  - Conda: $(conda --version 2>/dev/null || echo 'Not installed')"
    echo
    echo "로그 파일을 확인하거나 이슈를 보고해주세요."
    exit 1
}

# 메인 실행 함수
main() {
    trap handle_error ERR
    
    install_system_dependencies
    install_miniconda_arm64
    setup_conda_environment
    create_python_environment
    install_arm64_packages
    install_insightface_arm64
    install_web_packages
    setup_environment
    verify_installation
    create_service_scripts
    print_installation_info
}

# 도움말
show_help() {
    echo "Face Analysis API ARM64 설치 스크립트"
    echo
    echo "사용법: $0 [옵션]"
    echo
    echo "옵션:"
    echo "  -h, --help        이 도움말 표시"
    echo "  --system-only     시스템 의존성만 설치"
    echo "  --python-only     Python 환경만 설치"
    echo "  --verify-only     설치 검증만 실행"
    echo "  --clean           기존 환경 정리 후 재설치"
    echo
    echo "예제:"
    echo "  $0                # 전체 설치"
    echo "  $0 --clean        # 정리 후 재설치"
    echo "  $0 --verify-only  # 검증만 실행"
    echo
}

# 정리 함수
clean_environment() {
    log_info "기존 환경 정리 중..."
    
    # Conda 환경 제거
    if command -v conda &> /dev/null; then
        conda env remove -n face-api -y 2>/dev/null || true
    fi
    
    # 임시 파일 정리
    rm -rf /tmp/miniconda.sh
    rm -rf logs/* temp/* 2>/dev/null || true
    
    log_success "환경 정리 완료"
}

# 옵션 처리
SYSTEM_ONLY=false
PYTHON_ONLY=false
VERIFY_ONLY=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --system-only)
            SYSTEM_ONLY=true
            shift
            ;;
        --python-only)
            PYTHON_ONLY=true
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
done

# 실행 모드에 따른 분기
if [[ "$CLEAN" == "true" ]]; then
    clean_environment
fi

if [[ "$VERIFY_ONLY" == "true" ]]; then
    verify_installation
elif [[ "$SYSTEM_ONLY" == "true" ]]; then
    install_system_dependencies
elif [[ "$PYTHON_ONLY" == "true" ]]; then
    install_miniconda_arm64
    setup_conda_environment
    create_python_environment
    install_arm64_packages
    install_insightface_arm64
    install_web_packages
    verify_installation
else
    main
fi
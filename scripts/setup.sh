#!/bin/bash
# Face Analysis API 간단 설치 스크립트 (conda 전용)

set -e

echo "🚀 Face Analysis API 설치 시작..."

# 컬러 출력 함수
print_info() { echo -e "\033[1;34m[INFO]\033[0m $1"; }
print_success() { echo -e "\033[1;32m[SUCCESS]\033[0m $1"; }
print_error() { echo -e "\033[1;31m[ERROR]\033[0m $1"; }

# 1. Miniconda 설치 확인/설치
if [ ! -d "$HOME/miniconda" ]; then
    print_info "Miniconda 설치 중..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p $HOME/miniconda
    print_success "Miniconda 설치 완료"
fi

# 2. conda 환경 설정
export PATH="$HOME/miniconda/bin:$PATH"
source $HOME/miniconda/etc/profile.d/conda.sh

# 3. conda 설정 (conda-forge 채널만 사용)
print_info "Conda 채널 설정 중..."
conda config --set solver libmamba
conda config --remove channels defaults 2>/dev/null || true
conda config --add channels conda-forge

# 4. 기존 환경 삭제 (있는 경우)
if conda env list | grep -q "insightface"; then
    print_info "기존 환경 삭제 중..."
    conda env remove -n insightface -y 2>/dev/null || true
fi

# 5. insightface 환경 생성
print_info "conda 환경 생성 중..."
conda create -n insightface python=3.11 -c conda-forge --override-channels -y

# 6. 환경 활성화
print_info "환경 활성화 중..."
conda activate insightface

# 7. 핵심 패키지 설치 (conda)
print_info "핵심 패키지 설치 중 (conda)..."
conda install -c conda-forge --override-channels \
    opencv \
    numpy \
    insightface \
    onnxruntime \
    pydantic-settings \
    loguru \
    -y

# 8. 추가 패키지 설치 (pip)
print_info "추가 패키지 설치 중 (pip)..."
pip install -r requirements.txt

# 9. 환경 설정
print_info "환경 설정 중..."
mkdir -p logs

# 10. 설치 검증
print_info "설치 검증 중..."
python -c "import insightface; print('✅ insightface 임포트 성공')" || print_error "insightface 임포트 실패"
python -c "import cv2; print('✅ OpenCV 임포트 성공')" || print_error "OpenCV 임포트 실패"
python -c "import fastapi; print('✅ FastAPI 임포트 성공')" || print_error "FastAPI 임포트 실패"
python -c "import loguru; print('✅ Loguru 임포트 성공')" || print_error "Loguru 임포트 실패"
python -c "import pydantic_settings; print('✅ Pydantic Settings 임포트 성공')" || print_error "Pydantic Settings 임포트 실패"

print_success "설치 완료! 🎉"
echo ""
echo "✅ 서버 실행 방법:"
echo "  source $HOME/miniconda/etc/profile.d/conda.sh"
echo "  conda activate insightface"
echo "  python -m app.main"
echo ""
echo "🔗 테스트:"
echo "  curl http://localhost:8000/health"
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

# 3. insightface 환경 생성/활성화
if ! conda env list | grep -q "insightface"; then
    print_info "conda 환경 생성 중..."
    conda create -n insightface python=3.11 -y
fi
conda activate insightface

# 4. 패키지 설치
print_info "패키지 설치 중..."
conda install -c conda-forge insightface opencv numpy -y
pip install -r requirements.txt

# 5. 환경 설정
mkdir -p logs

print_success "설치 완료! 🎉"
echo ""
echo "✅ 서버 실행 방법:"
echo "  conda activate insightface"
echo "  python -m app.main"
echo ""
echo "🔗 테스트:"
echo "  curl http://localhost:8000/health"
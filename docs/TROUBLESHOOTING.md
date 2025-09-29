# 문제 해결 가이드

> 자주 발생하는 문제와 해결 방법을 정리한 가이드입니다.

## 🔧 설치 관련 문제

### InsightFace 설치 실패

#### 문제: "No module named 'insightface'" 
**원인:** InsightFace 패키지가 설치되지 않았거나 설치 실패
**해결:**
```bash
# 1. 시스템 의존성 먼저 설치
sudo apt-get install build-essential cmake

# 2. pip 업그레이드 후 재시도
pip install --upgrade pip setuptools wheel
pip install insightface
```

#### 문제: InsightFace 빌드 실패 (컴파일 에러)
**원인:** 시스템 의존성 부족 또는 Python 버전 호환성
**해결:**
```bash
# Ubuntu/Debian
sudo apt-get install -y \
    build-essential \
    cmake \
    libopencv-dev \
    libgl1-mesa-glx \
    libglib2.0-0

# Python 3.12 호환성 문제 시
# 다음 중 하나 시도:

# 방법 1: 최신 cmake 사용
pip install cmake --upgrade
pip install insightface

# 방법 2: 소스에서 설치
pip install --no-binary insightface insightface

# 방법 3: Python 3.11 사용 (권장)
pyenv install 3.11.0
pyenv local 3.11.0
```

#### 문제: Python 3.12 호환성 이슈 (가장 흔한 문제)
**원인:** InsightFace가 Python 3.12에서 C++ 컴파일 에러 발생
**해결 (성공률 100%):**
```bash
# ✅ 추천 해결법: conda 환경 사용
# 1. Miniconda 설치
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
bash /tmp/miniconda.sh -b -p $HOME/miniconda

# 2. conda 환경 설정
export PATH="$HOME/miniconda/bin:$PATH"
source $HOME/miniconda/etc/profile.d/conda.sh

# 3. Python 3.11 환경 생성
conda create -n insightface python=3.11 -y
conda activate insightface

# 4. conda-forge로 설치 (컴파일 없이)
conda install -c conda-forge insightface opencv numpy -y
pip install fastapi uvicorn psutil

# 5. 설치 확인
python -c "import insightface; print('✅ InsightFace 설치 성공')"
```

**대안 방법들:**
```bash
# 옵션 1: pyenv로 Python 3.11 사용
pyenv install 3.11.0
pyenv local 3.11.0

# 옵션 2: Docker 사용
docker run -it python:3.11-slim bash

# 옵션 3: 빌드 시간 늘리기 (비추천, 30분+ 소요)
pip install insightface --timeout 3600
```

### conda 환경 관련 문제

#### 문제: "conda: command not found"
**원인:** conda가 PATH에 없거나 설치되지 않음
**해결:**
```bash
# 1. conda 설치 확인
ls -la $HOME/miniconda/bin/conda

# 2. PATH 설정
export PATH="$HOME/miniconda/bin:$PATH"
source $HOME/miniconda/etc/profile.d/conda.sh

# 3. 영구 설정 (선택사항)
echo 'export PATH="$HOME/miniconda/bin:$PATH"' >> ~/.bashrc
echo 'source $HOME/miniconda/etc/profile.d/conda.sh' >> ~/.bashrc
```

#### 문제: "conda activate insightface" 실패
**원인:** conda init이 실행되지 않음
**해결:**
```bash
# conda 초기화
conda init bash
source ~/.bashrc

# 또는 수동으로 활성화
source $HOME/miniconda/etc/profile.d/conda.sh
conda activate insightface
```

#### 문제: "PackagesNotFoundError" conda-forge에서 패키지 없음
**원인:** 채널 설정 문제
**해결:**
```bash
# conda-forge 채널 추가
conda config --add channels conda-forge
conda config --set channel_priority strict

# 강제로 conda-forge에서 설치
conda install -c conda-forge insightface --force-reinstall
```

#### 문제: conda 환경에서 "ModuleNotFoundError"
**원인:** 잘못된 환경에서 실행 중
**해결:**
```bash
# 1. 현재 환경 확인
conda env list
echo $CONDA_DEFAULT_ENV

# 2. 올바른 환경 활성화
conda activate insightface

# 3. 패키지 설치 확인
conda list | grep insightface
pip list | grep fastapi
```

### conda vs pip 혼용 관련 문제

#### 문제: pip와 conda 패키지 충돌
**원인:** 동일한 패키지를 pip와 conda로 중복 설치
**해결:**
```bash
# 1. 충돌 패키지 확인
conda list | grep "<pip>"

# 2. conda로 통일 (권장)
pip uninstall numpy opencv-python
conda install -c conda-forge numpy opencv

# 3. 또는 pip로 통일 (비권장)
conda remove numpy opencv
pip install numpy opencv-python
```

#### 문제: "어떤 패키지를 conda로, 어떤 것을 pip로?"
**가이드라인:**
```bash
# ✅ conda로 설치할 것들 (ML/CV 라이브러리)
conda install -c conda-forge insightface opencv numpy scipy matplotlib pytorch

# ✅ pip로 설치할 것들 (순수 Python 패키지)
pip install fastapi uvicorn pydantic requests sqlalchemy psutil

# ❌ 혼용 금지 (같은 패키지를 둘 다로 설치하지 말 것)
# conda install numpy && pip install numpy  # 절대 금지
```

### 시스템 의존성 설치 실패

#### 문제: "E: Unable to locate package build-essential"
**원인:** 패키지 저장소 업데이트 필요
**해결:**
```bash
sudo apt-get update
sudo apt-get install build-essential cmake
```

#### 문제: macOS에서 cmake 설치 실패
**원인:** Xcode Command Line Tools 부족
**해결:**
```bash
# Xcode Command Line Tools 설치
xcode-select --install

# Homebrew 설치 후
brew install cmake opencv
```

#### 문제: Windows에서 빌드 도구 부족
**원인:** Visual Studio Build Tools 없음
**해결:**
```bash
# Visual Studio Build Tools 설치
# 또는 Visual Studio Community with C++ workload
# Microsoft C++ Build Tools 다운로드 및 설치
```

## 🚀 실행 관련 문제

### 서버 시작 실패

#### 문제: "Port 8000 already in use"
**원인:** 포트 8000이 이미 사용 중
**해결:**
```bash
# 다른 포트 사용
uvicorn app.main:app --port 8001

# 또는 기존 프로세스 종료
lsof -ti:8000 | xargs kill -9
# 또는
pkill -f uvicorn
```

#### 문제: "ModuleNotFoundError: No module named 'app'"
**원인:** Python 경로 설정 또는 가상환경 문제
**해결:**
```bash
# 1. 가상환경 활성화 확인
source venv/bin/activate

# 2. 올바른 디렉토리에서 실행
cd /path/to/face-ai-analysis-alpha
uvicorn app.main:app --reload

# 3. PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 문제: "ImportError: cannot import name 'model_manager'"
**원인:** app/models/__init__.py 파일 누락
**해결:**
```bash
# __init__.py 파일 생성
touch app/models/__init__.py
echo '"""AI 모델 관련 모듈"""' > app/models/__init__.py
```

### 모델 로딩 실패

#### 문제: "model_loaded: false" in health check
**원인:** InsightFace 모델 다운로드 실패 또는 로딩 에러
**해결:**
```bash
# 1. 수동으로 모델 다운로드 시도
python3 -c "
import insightface
app = insightface.app.FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=-1)
print('모델 다운로드 완료')
"

# 2. 모델 캐시 디렉토리 확인
ls -la ~/.insightface/

# 3. 권한 문제 해결
chmod -R 755 ~/.insightface/

# 4. 네트워크 문제 시 수동 다운로드
wget https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip
```

#### 문제: GPU 관련 에러
**원인:** CUDA 설정 문제
**해결:**
```bash
# CPU만 사용하도록 설정
export CUDA_VISIBLE_DEVICES=""

# 또는 코드에서 CPU 강제 사용
# providers=['CPUExecutionProvider']
```

### 메모리 관련 문제

#### 문제: "Out of memory" 에러
**원인:** 시스템 메모리 부족
**해결:**
```bash
# 1. 메모리 사용량 확인
free -h
htop

# 2. 스왑 추가 (임시)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 3. 배치 크기 줄이기 (코드 수정 필요)
# 또는 이미지 크기 제한
```

## 🔄 API 관련 문제

### 응답 관련 문제

#### 문제: 500 Internal Server Error
**원인:** 다양한 서버 내부 오류
**해결:**
```bash
# 1. 로그 확인
tail -f logs/app.log

# 2. 디버그 모드로 실행
uvicorn app.main:app --reload --log-level debug

# 3. 특정 에러 확인
grep ERROR logs/app.log
```

#### 문제: 422 Unprocessable Entity
**원인:** 요청 데이터 형식 오류
**해결:**
```bash
# 올바른 요청 형식 확인
curl -X POST http://localhost:8000/compare-faces \
  -H "Content-Type: application/json" \
  -d '{
    "source_image": "data:image/jpeg;base64,/9j/4AAQ...",
    "target_image": "data:image/jpeg;base64,/9j/4AAQ...",
    "similarity_threshold": 0.01
  }'
```

#### 문제: 타임아웃 에러
**원인:** 처리 시간 초과
**해결:**
```bash
# 1. 이미지 크기 줄이기
# 2. 타임아웃 시간 늘리기
uvicorn app.main:app --timeout-graceful-shutdown 60

# 3. 비동기 처리 확인
```

### 이미지 처리 문제

#### 문제: "Invalid image format"
**원인:** 잘못된 이미지 형식 또는 base64 인코딩 오류
**해결:**
```python
# 올바른 base64 형식 확인
import base64
import io
from PIL import Image

# 이미지를 base64로 변환
with open("image.jpg", "rb") as img_file:
    img_base64 = base64.b64encode(img_file.read()).decode()
    img_data = f"data:image/jpeg;base64,{img_base64}"
```

#### 문제: "No faces detected"
**원인:** 이미지에서 얼굴을 찾을 수 없음
**해결:**
```bash
# 1. 이미지 품질 확인
# - 해상도가 너무 낮지 않은지
# - 얼굴이 명확히 보이는지
# - 조명이 적절한지

# 2. 다른 이미지로 테스트
# 3. 얼굴 감지 임계값 조정 (코드 수정 필요)
```

## 💾 데이터베이스/저장소 문제

### 로그 파일 문제

#### 문제: "Permission denied" 로그 파일 접근 불가
**원인:** 로그 디렉토리 권한 문제
**해결:**
```bash
# 로그 디렉토리 생성 및 권한 설정
mkdir -p logs
chmod 755 logs
chown $USER:$USER logs
```

#### 문제: 로그 파일이 너무 큼
**원인:** 로그 로테이션 설정 없음
**해결:**
```bash
# 수동으로 로그 정리
truncate -s 0 logs/app.log

# logrotate 설정 (영구 해결)
sudo vim /etc/logrotate.d/face-api
```

## 🌐 네트워크 관련 문제

### 외부 접근 문제

#### 문제: "Connection refused" 외부에서 접근 불가
**원인:** 방화벽 또는 호스트 설정 문제
**해결:**
```bash
# 1. 방화벽 확인
sudo ufw status
sudo ufw allow 8000

# 2. 호스트 설정 확인
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. 바인드 주소 확인
netstat -tulpn | grep 8000
```

#### 문제: Docker 네트워크 문제
**원인:** Docker 컨테이너 네트워크 설정
**해결:**
```bash
# 포트 매핑 확인
docker run -p 8000:8000 face-api:latest

# 네트워크 상태 확인
docker network ls
docker inspect <container_id>
```

## 🐛 환경별 특이사항

### Python 3.12 환경
```bash
# ❌ 문제: InsightFace pip 설치 실패 (C++ 컴파일 에러)
# ✅ 해결: conda 환경으로 Python 3.11 사용
conda create -n insightface python=3.11 -y
conda activate insightface
conda install -c conda-forge insightface -y
```

### Ubuntu 22.04
```bash
# 기본적으로 대부분 문제없이 동작
# OpenCV 의존성 주의
sudo apt-get install libgl1-mesa-glx
```

### macOS
```bash
# Xcode Command Line Tools 필수
# Homebrew 통한 의존성 설치 권장
brew install cmake opencv
```

### Windows
```bash
# Visual Studio Build Tools 필수
# Windows Subsystem for Linux (WSL) 사용 권장
```

## 📊 성능 관련 문제

### 메모리 사용량 과다

#### 문제: 메모리 사용량이 계속 증가
**원인:** 메모리 누수 또는 캐시 설정 문제
**해결:**
```bash
# 1. 메모리 모니터링
pip install memory_profiler
mprof run python app/main.py

# 2. 가비지 컬렉션 강제 실행
import gc
gc.collect()

# 3. 캐시 크기 제한 (코드 수정)
```

### 처리 속도 저하

#### 문제: API 응답이 느림
**원인:** 모델 로딩 지연 또는 이미지 처리 비효율
**해결:**
```bash
# 1. 모델 사전 로딩 확인
# 2. 이미지 크기 최적화
# 3. GPU 사용 여부 확인
nvidia-smi

# 4. 프로파일링
python -m cProfile -o profile.stats app/main.py
```

## 🔍 로그 분석

### 유용한 로그 명령어
```bash
# 실시간 로그 모니터링
tail -f logs/app.log

# 에러만 필터링
grep ERROR logs/app.log

# 특정 시간대 로그
grep "2025-09-19 14:" logs/app.log

# 로그 통계
grep -c "ERROR" logs/app.log
grep -c "INFO" logs/app.log

# 최근 100줄만 보기
tail -n 100 logs/app.log

# 특정 패턴 검색
grep -i "insightface" logs/app.log
```

## 🆘 추가 도움 요청

문제가 해결되지 않는 경우:

1. **로그 수집**: 전체 에러 로그와 재현 단계 정리
2. **환경 정보**: OS, Python 버전, 설치된 패키지 목록
3. **재현 방법**: 정확한 명령어와 설정
4. **GitHub Issues**: [프로젝트 이슈](../../issues)에 등록

### 환경 정보 수집 명령어
```bash
# 시스템 정보
uname -a
cat /etc/os-release

# Python 정보
python3 --version
pip list

# 패키지 의존성
pip freeze > current_packages.txt

# 디스크 용량
df -h

# 메모리 상태
free -h
```

---

**문제가 해결되면 [WORKFLOW.md](WORKFLOW.md)에 해결 과정을 기록해주세요.**
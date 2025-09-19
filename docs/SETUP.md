# 상세 설치 가이드

> InsightFace 기반 얼굴 분석 백엔드의 상세 설치 방법입니다.

## 📋 시스템 요구사항

### 최소 요구사항
- **OS**: Ubuntu 20.04+ / macOS 10.15+ / Windows 10+
- **Python**: 3.8+
- **RAM**: 4GB+
- **Storage**: 5GB+ (모델 파일 포함)
- **CPU**: 4 cores+

### 권장 요구사항
- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.9+
- **RAM**: 8GB+
- **Storage**: 10GB+
- **CPU**: 8 cores+
- **GPU**: NVIDIA GPU with CUDA 11.0+ (선택사항)

## 🚀 자동 설치 (권장)

### 1분 자동 설치
```bash
# 1. 저장소 클론
git clone <repository-url>
cd whos-your-papa-ai

# 2. 자동 설치 실행
bash scripts/setup.sh
```

자동 설치 스크립트가 다음을 수행합니다:
- ✅ Python 가상환경 생성
- ✅ 모든 의존성 설치
- ✅ InsightFace 모델 다운로드
- ✅ 환경 설정
- ✅ 서버 테스트

## 🐍 conda 환경 설치 (강력 권장)

**Python 3.12 호환성 문제로 conda 설치를 강력히 권장합니다.**

### conda 환경 설치 (5분 설치)
```bash
# 1. Miniconda 설치 (처음만)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
bash /tmp/miniconda.sh -b -p $HOME/miniconda

# 2. conda 환경 설정
export PATH="$HOME/miniconda/bin:$PATH"
source $HOME/miniconda/etc/profile.d/conda.sh

# 3. 전용 환경 생성 및 활성화
conda create -n insightface python=3.11 -y
conda activate insightface

# 4. 패키지 설치 (conda + pip 혼용)
conda install -c conda-forge insightface opencv numpy -y  # ML/CV 라이브러리
pip install fastapi uvicorn psutil                        # Python 웹 패키지

# 5. 서버 실행
python -m app.main
```

### conda vs pip 사용 가이드라인

**conda로 설치할 것들 (시스템 의존성 포함)**:
```bash
# ML/CV 라이브러리 - 컴파일된 바이너리 + C++ 의존성
conda install -c conda-forge insightface    # ✅ pip 실패, conda 성공
conda install -c conda-forge opencv         # OpenCV C++ 라이브러리
conda install -c conda-forge numpy          # BLAS/LAPACK 최적화
conda install -c conda-forge pytorch       # CUDA 지원 등
```

**pip로 설치해도 되는 것들 (순수 Python)**:
```bash
# 웹 프레임워크 및 Python 전용 패키지
pip install fastapi uvicorn                 # 순수 Python
pip install psutil requests                 # 가벼운 유틸리티
pip install pydantic sqlalchemy            # ORM, 스키마
```

### conda 환경 장점
- ✅ **설치 성공률 100%**: Python 3.12 호환성 문제 해결
- ✅ **빠른 설치**: 컴파일 없이 미리 빌드된 바이너리 사용 (2-3분 vs 30분+)
- ✅ **안정성**: C++ 라이브러리 의존성 자동 해결
- ✅ **환경 격리**: 기존 Python 환경과 독립적

## 🔧 수동 설치 (venv)

자동 설치가 실패할 경우 수동으로 설치하세요:

### 1단계: 환경 준비

```bash
# Python 버전 확인
python3 --version  # 3.8+ 필요

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# pip 업그레이드
pip install --upgrade pip
```

### 2단계: 시스템 의존성 설치

#### Ubuntu/Debian
```bash
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
```

**⚠️ 중요:** `build-essential cmake`는 InsightFace 설치에 필수입니다!

#### macOS
```bash
# Homebrew 설치 후
brew install cmake opencv

# Xcode Command Line Tools
xcode-select --install
```

#### Windows
```bash
# Visual Studio Build Tools 설치 필요
# 또는 Visual Studio Community with C++ workload
```

### 3단계: Python 의존성 설치

```bash
# 기본 패키지 설치
pip install fastapi uvicorn python-multipart pydantic pydantic-settings python-dotenv loguru psutil
pip install numpy pillow opencv-python onnxruntime

# InsightFace 설치 (시스템 의존성 필요)
# ⚠️ 경고: Python 3.12에서 컴파일 에러 발생 가능 - conda 사용 권장
pip install insightface
```

**패키지 설명:**
- `fastapi`: 웹 API 프레임워크
- `uvicorn`: ASGI 서버
- `pydantic-settings`: 설정 관리
- `psutil`: 시스템 리소스 모니터링
- `insightface`: 얼굴 인식 AI 모델

### 4단계: 환경 설정

```bash
# 환경변수 파일 생성
cp .env.example .env

# 로그 디렉토리 생성
mkdir -p logs
```

### 5단계: InsightFace 모델 다운로드

```bash
python3 -c "
import insightface
app = insightface.app.FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=-1)
print('✅ 모델 다운로드 완료!')
"
```

## 🧪 설치 검증

### 서버 시작

#### conda 환경에서 서버 시작 (권장)
```bash
# conda 환경 활성화
export PATH="$HOME/miniconda/bin:$PATH"
source $HOME/miniconda/etc/profile.d/conda.sh
conda activate insightface

# 서버 시작
python -m app.main
```

#### venv 환경에서 서버 시작
```bash
# 가상환경 활성화
source venv/bin/activate

# 개발 서버 시작
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 헬스체크 테스트
```bash
curl http://localhost:8000/health
```

**예상 응답:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": false,
  "memory_usage": {
    "used_mb": 4151,
    "total_mb": 13869,
    "percent": 29.9
  },
  "version": "1.0.0",
  "uptime_seconds": 5.97
}
```

### 기타 엔드포인트 테스트
```bash
# 간단한 핑 테스트
curl http://localhost:8000/ping

# 루트 엔드포인트
curl http://localhost:8000/

# API 문서 확인 (브라우저)
open http://localhost:8000/docs
```

## ✅ 성공적인 설치 확인

다음 명령어로 설치가 성공적인지 확인하세요:

```bash
# 1. 서버 시작
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. 다른 터미널에서 테스트
curl http://localhost:8000/health
curl http://localhost:8000/ping
curl http://localhost:8000/docs  # 브라우저에서 열리면 API 문서 확인
```

**예상 결과:**
- ✅ 서버가 오류 없이 시작
- ✅ `/health` 엔드포인트가 200 상태 코드 반환
- ✅ `/docs`에서 Swagger UI 표시
- ✅ `model_loaded: true` (InsightFace 정상 로드)

**만약 `model_loaded: false`라면:**
- InsightFace 설치가 완료되지 않았거나 실패
- [문제 해결 가이드](TROUBLESHOOTING.md)를 참조하세요

## 🚀 다음 단계

설치가 완료되면:

1. **개발 환경 구성**: [DEVELOPMENT.md](DEVELOPMENT.md) 참조
2. **실제 기능 테스트**: 얼굴 분석 API 테스트
3. **배포 준비**: [DEPLOYMENT.md](DEPLOYMENT.md) 참조

## 📚 관련 문서

- [개발 환경 가이드](DEVELOPMENT.md)
- [문제 해결 가이드](TROUBLESHOOTING.md)  
- [API 설계 문서](API_DESIGN.md)
- [아키텍처 문서](ARCHITECTURE.md)
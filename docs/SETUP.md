# 설치 가이드

> InsightFace 기반 얼굴 분석 백엔드의 간단한 설치 방법입니다.

## 📋 시스템 요구사항

- **OS**: Ubuntu 20.04+ / macOS 10.15+ / Windows 10+
- **Python**: 3.11 (자동 설치됨)
- **RAM**: 4GB+
- **Storage**: 3GB+

## 🚀 1분 자동 설치

```bash
# 1. 저장소 클론
git clone <repository-url>
cd whos-your-papa-ai

# 2. 자동 설치 실행
bash scripts/setup.sh
```

**자동 설치가 수행하는 작업:**
- ✅ Miniconda 설치 (처음만)
- ✅ Python 3.11 환경 생성
- ✅ InsightFace + 모든 의존성 설치
- ✅ 환경 설정

## 🔧 수동 설치

자동 설치 실패 시에만 사용하세요:

```bash
# 1. Miniconda 설치 (처음만)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
bash /tmp/miniconda.sh -b -p $HOME/miniconda

# 2. conda 환경 설정
export PATH="$HOME/miniconda/bin:$PATH"
source $HOME/miniconda/etc/profile.d/conda.sh

# 3. 환경 생성 및 활성화
conda create -n insightface python=3.11 -y
conda activate insightface

# 4. 패키지 설치
conda install -c conda-forge insightface opencv numpy -y
pip install -r requirements.txt

# 5. 환경 설정
mkdir -p logs
```

## 🏃‍♂️ 서버 실행

```bash
# 환경 활성화
conda activate insightface

# 서버 시작
python -m app.main
```

## 🧪 테스트

```bash
# 헬스체크
curl http://localhost:8000/health

# 예상 응답
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": false,
  "memory_usage": {...},
  "version": "1.0.0"
}
```

## ✅ 성공 확인

다음이 모두 확인되면 설치 성공:
- ✅ 서버가 오류 없이 시작
- ✅ `model_loaded: true` 응답
- ✅ API 문서 확인: http://localhost:8000/docs

## 🐛 문제 해결

**설치 실패 시:**
1. Python 버전이 3.8+ 인지 확인
2. 인터넷 연결 확인
3. 디스크 공간 3GB+ 확인

**서버 실행 실패 시:**
1. conda 환경 활성화 확인: `conda activate insightface`
2. 로그 확인: `tail -f logs/app.log`

## 📚 다음 단계

- [개발 가이드](DEVELOPMENT.md)
- [API 문서](API_DESIGN.md)
- [Next.js 연동](NEXTJS_INTEGRATION.md)
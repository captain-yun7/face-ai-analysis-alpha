# 🚀 빠른 시작 가이드

InsightFace 기반 얼굴 분석 AI 백엔드를 빠르게 시작하는 방법입니다.

## 📋 시스템 요구사항

- **Python**: 3.8 이상
- **메모리**: 4GB 이상 (권장 8GB)
- **저장공간**: 5GB 이상
- **OS**: Ubuntu 20.04+, macOS 10.15+, Windows 10+

## ⚡ 1분 설치 (자동)

```bash
# 1. 저장소 클론
git clone <your-repo-url>
cd whos-your-papa-ai

# 2. 자동 설치 실행
bash setup.sh
```

설치 스크립트가 다음을 자동으로 수행합니다:
- ✅ Python 가상환경 생성
- ✅ 모든 의존성 설치  
- ✅ InsightFace 모델 다운로드
- ✅ 환경 설정
- ✅ 서버 테스트

## 🔧 수동 설치

### 1단계: 환경 준비

```bash
# Python 버전 확인
python3 --version  # 3.8+ 필요

# 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# pip 업그레이드
pip install --upgrade pip
```

### 2단계: 의존성 설치

```bash
# Python 패키지 설치
pip install -r requirements.txt

# 시스템 의존성 (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y libopencv-dev libgl1-mesa-glx libglib2.0-0
```

### 3단계: 모델 다운로드

```bash
# InsightFace 모델 자동 다운로드
python3 -c "
import insightface
app = insightface.app.FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=-1)
print('모델 다운로드 완료!')
"
```

### 4단계: 환경 설정

```bash
# 환경변수 파일 생성
cp .env.example .env

# 로그 디렉토리 생성  
mkdir -p logs
```

## 🏃‍♂️ 서버 실행

### 개발 모드

```bash
# 개발 서버 시작 (자동 재로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 프로덕션 모드

```bash
# Gunicorn으로 프로덕션 실행
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Docker 실행

```bash
# Docker Compose로 실행
docker-compose up -d

# 개별 컨테이너 실행
docker build -t face-api .
docker run -p 8000:8000 face-api
```

## 🧪 서버 테스트

### 헬스체크

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
    "used_mb": 1024,
    "total_mb": 8192
  },
  "version": "1.0.0"
}
```

### API 문서 확인

브라우저에서 다음 URL 접속:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 얼굴 비교 테스트

```bash
# 간단한 얼굴 비교 테스트
curl -X POST http://localhost:8000/compare-faces \
  -H "Content-Type: application/json" \
  -d '{
    "source_image": "data:image/jpeg;base64,/9j/4AAQ...",
    "target_image": "data:image/jpeg;base64,/9j/4AAQ...",
    "similarity_threshold": 0.6
  }'
```

## 🔗 Next.js 연동

### 1. Next.js 환경변수 설정

```env
# Next.js .env.local 파일에 추가
USE_INSIGHT_FACE=true
INSIGHT_FACE_API_URL=http://localhost:8000
INSIGHT_FACE_API_KEY=your-api-key  # 선택사항
FALLBACK_TO_AWS=true
```

### 2. 기존 코드는 변경 없음

Next.js의 기존 얼굴 비교 코드는 수정 없이 자동으로 InsightFace를 사용합니다.

## 📊 성능 확인

### 메모리 사용량

```bash
# 시스템 메모리 확인
free -h

# 프로세스별 메모리 확인
ps aux | grep uvicorn
```

### API 성능 테스트

```bash
# Apache Bench로 부하 테스트
ab -n 100 -c 10 http://localhost:8000/health

# 응답 시간 측정
time curl http://localhost:8000/health
```

## 🐛 문제 해결

### 일반적인 오류

#### 1. "No module named 'insightface'"
```bash
pip install insightface
```

#### 2. "CUDA out of memory"
```bash
# .env 파일에서 CPU 모드로 변경
USE_GPU=false
```

#### 3. "Port 8000 already in use"
```bash
# 다른 포트 사용
uvicorn app.main:app --port 8001
```

#### 4. 모델 다운로드 실패
```bash
# 수동 다운로드
mkdir -p ~/.insightface/models
# 모델 파일을 직접 다운로드 후 배치
```

### 로그 확인

```bash
# 애플리케이션 로그
tail -f logs/app.log

# 에러만 확인
grep ERROR logs/app.log

# 실시간 에러 모니터링
tail -f logs/app.log | grep -E "(ERROR|CRITICAL)"
```

## 📈 모니터링

### 시스템 리소스

```bash
# CPU, 메모리 실시간 모니터링
htop

# GPU 사용량 (NVIDIA)
watch -n 1 nvidia-smi

# 디스크 사용량
df -h
```

### API 메트릭

```bash
# 실시간 메트릭 확인
curl http://localhost:8000/metrics

# 상세 헬스체크
curl http://localhost:8000/health/detailed
```

## 🔒 보안 설정

### API 키 활성화

```bash
# .env 파일 수정
API_KEY_ENABLED=true
API_KEY=your-secure-api-key-here

# 서버 재시작 후 헤더에 키 포함하여 요청
curl -H "X-API-Key: your-secure-api-key-here" \
     http://localhost:8000/compare-faces
```

### Rate Limiting 설정

```bash
# .env 파일에서 제한 설정
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

## 📞 지원

### 문제 발생 시

1. **로그 확인**: `tail -f logs/app.log`
2. **설정 검증**: `.env` 파일 확인
3. **의존성 재설치**: `pip install -r requirements.txt --force-reinstall`
4. **포트 변경**: 다른 포트로 실행 시도

### 성능 문제

- 메모리 부족 → `MAX_BATCH_SIZE` 축소
- CPU 과부하 → `WORKERS` 수 조정  
- GPU 메모리 부족 → `USE_GPU=false`로 설정

---

## 🎉 완료!

축하합니다! InsightFace 기반 얼굴 분석 API가 성공적으로 실행되고 있습니다.

### 다음 단계
- [API 문서](http://localhost:8000/docs)에서 엔드포인트 확인
- [성능 최적화 가이드](docs/SETUP_GUIDE.md) 참조
- [Next.js 연동 가이드](docs/INTEGRATION_PLAN.md) 확인

### 유용한 링크
- **API 문서**: http://localhost:8000/docs  
- **헬스체크**: http://localhost:8000/health
- **메트릭**: http://localhost:8000/metrics
- **GitHub Issues**: [여기에 이슈 링크]

**Happy Coding! 🚀**
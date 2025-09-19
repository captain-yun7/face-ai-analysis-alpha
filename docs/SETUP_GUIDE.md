# 🚀 설치 및 설정 가이드 (Setup Guide)

## 📌 개요

InsightFace 기반 얼굴 분석 백엔드의 설치, 설정, 실행을 위한 단계별 가이드입니다.

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

## 🛠️ 설치 방법

### Method 1: 로컬 개발 환경 (추천)

#### 1. Python 환경 설정

```bash
# Python 버전 확인
python3 --version  # 3.8+ 확인

# 가상환경 생성
cd /home/k8s-admin/whos-your-papa-ai
python3 -m venv venv

# 가상환경 활성화
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# pip 업그레이드
pip install --upgrade pip
```

#### 2. 의존성 설치

```bash
# 기본 의존성 설치
pip install fastapi uvicorn python-multipart
pip install pillow opencv-python numpy
pip install insightface onnxruntime

# 개발 도구 (선택사항)
pip install pytest black flake8 pre-commit
```

#### 3. InsightFace 모델 다운로드

```bash
# Python에서 실행
python3 -c "
import insightface
app = insightface.app.FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0)
print('모델 다운로드 완료!')
"
```

### Method 2: Docker 환경

#### 1. Docker 설치
```bash
# Ubuntu
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
# 로그아웃 후 재로그인

# Docker 버전 확인
docker --version
```

#### 2. Dockerfile 기반 빌드
```bash
# 프로젝트 루트에서
docker build -t face-api:latest .

# 컨테이너 실행
docker run -p 8000:8000 face-api:latest
```

### Method 3: GPU 지원 환경

#### 1. CUDA 설치 (Ubuntu)
```bash
# NVIDIA 드라이버 설치
sudo apt update
sudo apt install nvidia-driver-470

# CUDA Toolkit 설치
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sudo sh cuda_11.8.0_520.61.05_linux.run

# 환경변수 설정
echo 'export PATH=/usr/local/cuda-11.8/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

#### 2. GPU 지원 패키지 설치
```bash
# ONNX Runtime GPU
pip uninstall onnxruntime
pip install onnxruntime-gpu

# CUDA 지원 확인
python3 -c "
import onnxruntime as ort
print('CUDA Providers:', ort.get_available_providers())
"
```

## ⚙️ 환경 설정

### 1. 환경 변수 설정

```bash
# .env 파일 생성
cat > .env << EOF
# 애플리케이션 설정
APP_NAME=Face Analysis API
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=info

# 서버 설정
HOST=0.0.0.0
PORT=8000
WORKERS=1

# 모델 설정
MODEL_NAME=buffalo_l
MODEL_ROOT=~/.insightface/models
USE_GPU=false

# 보안 설정
API_KEY_ENABLED=false
API_KEY=your-secret-api-key

# 캐시 설정
CACHE_ENABLED=true
CACHE_TTL=3600
REDIS_URL=redis://localhost:6379

# 로깅 설정
LOG_FILE=logs/app.log
LOG_ROTATION=1d
LOG_RETENTION=30d

# 성능 설정
MAX_IMAGE_SIZE=10485760  # 10MB
MAX_BATCH_SIZE=10
PROCESSING_TIMEOUT=30
EOF
```

### 2. 설정 파일 구조

```python
# app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # 애플리케이션
    app_name: str = "Face Analysis API"
    debug: bool = False
    
    # 서버
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # 모델
    model_name: str = "buffalo_l"
    model_root: str = "~/.insightface/models"
    use_gpu: bool = False
    
    # 성능
    max_image_size: int = 10 * 1024 * 1024  # 10MB
    max_batch_size: int = 10
    processing_timeout: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## 🏃‍♂️ 실행 방법

### 1. 개발 서버 실행

```bash
# 기본 실행
cd /home/k8s-admin/whos-your-papa-ai
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 간단히
uvicorn app.main:app --reload

# 로그 확인
tail -f logs/app.log
```

### 2. 프로덕션 실행

```bash
# Gunicorn 설치
pip install gunicorn

# 프로덕션 실행
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# 백그라운드 실행
nohup gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 > server.log 2>&1 &
```

### 3. Docker 실행

```bash
# 단일 컨테이너
docker run -d -p 8000:8000 --name face-api face-api:latest

# Docker Compose
docker-compose up -d

# 로그 확인
docker logs -f face-api
```

## 🔧 초기 설정 및 테스트

### 1. 서버 헬스체크

```bash
# 서버 상태 확인
curl http://localhost:8000/health

# 예상 응답
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

### 2. API 테스트

```bash
# 간단한 테스트 이미지 생성
python3 -c "
import base64
import requests
from PIL import Image
import io

# 테스트 이미지 생성 (간단한 패턴)
img = Image.new('RGB', (200, 200), color='red')
buffer = io.BytesIO()
img.save(buffer, format='JPEG')
img_str = base64.b64encode(buffer.getvalue()).decode()

# API 호출 테스트
response = requests.post('http://localhost:8000/detect-faces', 
                        json={'image': f'data:image/jpeg;base64,{img_str}'})
print('Status:', response.status_code)
print('Response:', response.json())
"
```

### 3. 성능 테스트

```bash
# Apache Bench로 부하 테스트
apt install apache2-utils
ab -n 100 -c 10 http://localhost:8000/health

# Python으로 동시성 테스트
python3 -c "
import asyncio
import aiohttp
import time

async def test_concurrent():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(50):
            task = session.get('http://localhost:8000/health')
            tasks.append(task)
        
        start = time.time()
        responses = await asyncio.gather(*tasks)
        end = time.time()
        
        print(f'50 requests in {end-start:.2f}s')
        print(f'Average: {(end-start)/50*1000:.2f}ms per request')

asyncio.run(test_concurrent())
"
```

## 🐛 문제 해결 (Troubleshooting)

### 1. 일반적인 문제

#### InsightFace 설치 실패
```bash
# 문제: 모델 다운로드 실패
# 해결: 수동 다운로드
mkdir -p ~/.insightface/models
cd ~/.insightface/models
wget https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip
unzip buffalo_l.zip
```

#### 메모리 부족 오류
```bash
# 문제: OOM (Out of Memory)
# 해결: 설정 조정
export INSIGHTFACE_MAX_MEMORY=2048  # MB
export OMP_NUM_THREADS=2
```

#### CUDA 관련 오류
```bash
# 문제: CUDA out of memory
# 해결: CPU 모드로 전환
echo "USE_GPU=false" >> .env

# 또는 배치 크기 줄이기
echo "MAX_BATCH_SIZE=1" >> .env
```

### 2. 로그 분석

```bash
# 에러 로그 확인
grep -i error logs/app.log

# 성능 로그 확인
grep -i "slow\|timeout\|failed" logs/app.log

# 실시간 모니터링
tail -f logs/app.log | grep -E "(ERROR|WARNING|CRITICAL)"
```

### 3. 모니터링 설정

```bash
# 시스템 리소스 모니터링
sudo apt install htop iotop
htop  # CPU, 메모리 사용량

# GPU 모니터링 (NVIDIA)
watch -n 1 nvidia-smi

# Python 메모리 프로파일링
pip install memory-profiler
python -m memory_profiler app/main.py
```

## 🔒 보안 설정

### 1. API 키 설정

```bash
# 강력한 API 키 생성
python3 -c "
import secrets
api_key = secrets.token_urlsafe(32)
print(f'API_KEY={api_key}')
"

# .env 파일에 추가
echo "API_KEY_ENABLED=true" >> .env
echo "API_KEY=your-generated-key" >> .env
```

### 2. Rate Limiting 설정

```python
# app/core/config.py에 추가
class Settings(BaseSettings):
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
```

### 3. 방화벽 설정

```bash
# UFW 방화벽 설정 (Ubuntu)
sudo ufw enable
sudo ufw allow 8000/tcp  # API 포트만 열기
sudo ufw deny 22/tcp     # SSH 포트 제한 (필요시)
```

## 📊 모니터링 설정

### 1. 로그 수집

```bash
# Logrotate 설정
sudo cat > /etc/logrotate.d/face-api << EOF
/home/k8s-admin/whos-your-papa-ai/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 644 k8s-admin k8s-admin
}
EOF
```

### 2. 메트릭 수집 (선택사항)

```bash
# Prometheus 메트릭 설정
pip install prometheus-client

# Grafana 대시보드 설정
# (별도 설치 필요)
```

## 🚀 배포 준비

### 1. 프로덕션 체크리스트

```bash
# [ ] 환경변수 설정 완료
# [ ] 로그 디렉토리 생성
# [ ] 모델 파일 다운로드 완료
# [ ] 성능 테스트 통과
# [ ] 보안 설정 완료
# [ ] 모니터링 설정 완료
# [ ] 백업 전략 수립

# 체크 스크립트
bash scripts/production-check.sh
```

### 2. 자동 시작 설정

```bash
# Systemd 서비스 생성
sudo cat > /etc/systemd/system/face-api.service << EOF
[Unit]
Description=Face Analysis API
After=network.target

[Service]
Type=exec
User=k8s-admin
WorkingDirectory=/home/k8s-admin/whos-your-papa-ai
Environment=PATH=/home/k8s-admin/whos-your-papa-ai/venv/bin
ExecStart=/home/k8s-admin/whos-your-papa-ai/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화
sudo systemctl enable face-api
sudo systemctl start face-api
sudo systemctl status face-api
```

## 📝 빠른 시작 스크립트

```bash
#!/bin/bash
# setup.sh - 원클릭 설치 스크립트

set -e

echo "🚀 Face Analysis API 설치 시작..."

# 1. Python 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 2. 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# 3. 환경 설정
cp .env.example .env

# 4. 로그 디렉토리 생성
mkdir -p logs

# 5. 모델 다운로드
python3 -c "
import insightface
app = insightface.app.FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0)
print('✅ 모델 다운로드 완료!')
"

# 6. 테스트 실행
echo "🧪 서버 테스트 중..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
sleep 5

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 설치 완료! 서버가 정상 동작합니다."
    echo "🌐 http://localhost:8000/docs 에서 API 문서를 확인하세요."
else
    echo "❌ 설치 실패! 로그를 확인하세요."
    exit 1
fi

kill $SERVER_PID
echo "🏁 설치 스크립트 완료!"
```

---

**작성일**: 2025-09-19  
**버전**: 1.0.0  
**작성자**: AI Backend Team
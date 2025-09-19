# 배포 가이드

> 프로덕션 환경으로 배포하기 위한 가이드입니다.

## 📋 배포 준비

### 배포 전 체크리스트
- [ ] 모든 테스트 통과 확인
- [ ] 성능 벤치마크 측정
- [ ] 보안 검토 완료
- [ ] 환경변수 설정 완료
- [ ] 로그 및 모니터링 설정
- [ ] 백업 및 롤백 계획 수립

## 🐳 Docker 배포

### 1. Dockerfile 최적화
```dockerfile
# Multi-stage build로 이미지 크기 최적화
FROM python:3.11-slim as builder

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopencv-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim as runtime

# 런타임 의존성만 설치
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 패키지 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 복사
COPY app/ ./app/
COPY .env.example .env

# 디렉토리 생성
RUN mkdir -p logs

# 비특권 사용자 생성
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Gunicorn으로 실행
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### 2. Docker Compose 설정
```yaml
# docker-compose.yml
version: '3.8'

services:
  face-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - face-api
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### 3. 프로덕션 빌드 및 실행
```bash
# 이미지 빌드
docker build -t face-api:latest .

# 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f face-api

# 상태 확인
docker-compose ps
```

## ⚙️ Nginx 리버스 프록시

### nginx.conf 설정
```nginx
events {
    worker_connections 1024;
}

http {
    upstream face_api {
        server face-api:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        listen 80;
        server_name your-domain.com;
        
        # HTTP to HTTPS redirect
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        # SSL 설정
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # 보안 헤더
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # 파일 업로드 크기 제한
        client_max_body_size 10M;

        location / {
            # Rate limiting
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://face_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 타임아웃 설정
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        location /health {
            # 헬스체크는 rate limiting 제외
            proxy_pass http://face_api;
            access_log off;
        }
    }
}
```

## ☸️ Kubernetes 배포

### 1. Deployment 설정
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: face-api
  labels:
    app: face-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: face-api
  template:
    metadata:
      labels:
        app: face-api
    spec:
      containers:
      - name: face-api
        image: face-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        emptyDir: {}
```

### 2. Service 설정
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: face-api-service
spec:
  selector:
    app: face-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. ConfigMap 설정
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: face-api-config
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  MAX_WORKERS: "4"
```

### 4. Secret 설정
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: face-api-secret
type: Opaque
data:
  API_KEY: <base64-encoded-api-key>
  DATABASE_URL: <base64-encoded-db-url>
```

### 5. 배포 실행
```bash
# ConfigMap 및 Secret 적용
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 애플리케이션 배포
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 상태 확인
kubectl get pods
kubectl get services
kubectl logs -f deployment/face-api
```

## 🖥️ VM/서버 직접 배포

### 1. 시스템 준비
```bash
# Ubuntu 20.04+ 서버에서
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git nginx

# 방화벽 설정
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. 애플리케이션 설치
```bash
# 사용자 생성
sudo adduser --system --group --home /opt/face-api face-api

# 소스 코드 배포
sudo git clone <repository-url> /opt/face-api/app
sudo chown -R face-api:face-api /opt/face-api

# 가상환경 설정
sudo -u face-api python3 -m venv /opt/face-api/venv
sudo -u face-api /opt/face-api/venv/bin/pip install -r /opt/face-api/app/requirements.txt
```

### 3. Systemd 서비스 설정
```ini
# /etc/systemd/system/face-api.service
[Unit]
Description=Face API Service
After=network.target

[Service]
Type=exec
User=face-api
Group=face-api
WorkingDirectory=/opt/face-api/app
Environment=PATH=/opt/face-api/venv/bin
ExecStart=/opt/face-api/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 4. 서비스 시작
```bash
# 서비스 등록 및 시작
sudo systemctl daemon-reload
sudo systemctl enable face-api
sudo systemctl start face-api

# 상태 확인
sudo systemctl status face-api
sudo journalctl -u face-api -f
```

## 📊 모니터링 설정

### 1. Prometheus 메트릭
```python
# app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

REQUEST_COUNT = Counter('face_api_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('face_api_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('face_api_active_connections', 'Active connections')

# FastAPI에서 메트릭 엔드포인트 추가
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 2. Grafana 대시보드
```json
{
  "dashboard": {
    "title": "Face API Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(face_api_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, face_api_request_duration_seconds_bucket)"
          }
        ]
      }
    ]
  }
}
```

### 3. 로그 수집 (ELK Stack)
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:7.14.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"

  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

## 🔒 보안 강화

### 1. API 키 인증
```python
# app/core/security.py
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials
```

### 2. Rate Limiting
```python
# app/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/compare-faces")
@limiter.limit("10/minute")
async def compare_faces(request: Request, ...):
    pass
```

### 3. SSL/TLS 설정
```bash
# Let's Encrypt 인증서 발급
sudo certbot --nginx -d your-domain.com

# 자동 갱신 설정
sudo crontab -e
0 12 * * * /usr/bin/certbot renew --quiet
```

## 📈 성능 최적화

### 1. 애플리케이션 설정
```python
# app/core/config.py
class ProductionConfig:
    # Worker 프로세스 수
    WORKERS = multiprocessing.cpu_count() * 2 + 1
    
    # 커넥션 풀 설정
    MAX_CONNECTIONS = 100
    
    # 캐시 설정
    CACHE_TTL = 3600  # 1시간
    
    # 로그 레벨
    LOG_LEVEL = "INFO"
```

### 2. 데이터베이스 최적화
```bash
# Redis 설정 최적화
echo "maxmemory 2gb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
```

### 3. 시스템 튜닝
```bash
# 파일 디스크립터 제한 증가
echo "* soft nofile 65535" >> /etc/security/limits.conf
echo "* hard nofile 65535" >> /etc/security/limits.conf

# 커널 파라미터 조정
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.ip_local_port_range = 1024 65535" >> /etc/sysctl.conf
```

## 🔄 배포 자동화

### 1. GitHub Actions CI/CD
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build Docker image
      run: docker build -t face-api:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push face-api:${{ github.sha }}
    
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/face-api face-api=face-api:${{ github.sha }}
```

### 2. 롤링 업데이트
```bash
# Kubernetes 롤링 업데이트
kubectl set image deployment/face-api face-api=face-api:new-version

# 롤백
kubectl rollout undo deployment/face-api
```

## 📋 배포 후 검증

### 체크리스트
```bash
# 1. 서비스 상태 확인
curl https://your-domain.com/health

# 2. 부하 테스트
ab -n 1000 -c 10 https://your-domain.com/health

# 3. 로그 확인
tail -f /var/log/face-api/app.log

# 4. 메트릭 확인
curl https://your-domain.com/metrics

# 5. 보안 스캔
nmap -p 80,443 your-domain.com
```

---

**배포 완료 후 [WORKFLOW.md](WORKFLOW.md)에 배포 과정을 기록하세요.**
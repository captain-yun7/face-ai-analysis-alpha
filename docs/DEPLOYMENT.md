# Oracle Cloud 프리티어 배포 가이드

> Oracle Cloud ARM A1 인스턴스와 Terraform + Ansible을 활용한 완전 무료 배포 전략

## 🎯 프리티어 활용 최대화 전략

### Oracle Cloud Free Tier 리소스
- **Compute**: ARM A1 4vCPU + 24GB RAM (Always Free)
- **Storage**: 200GB Block Volume (Always Free)  
- **Network**: 10TB/월 아웃바운드 트래픽
- **Load Balancer**: 1개 (Always Free)
- **Container Registry**: 500MB (Always Free)

### 인프라 아키텍처
```
인터넷:443 → Oracle Load Balancer → ARM A1 인스턴스 (Nginx:443 → FastAPI:8000)
```

## 📂 프로젝트 구조

```
whos-your-papa-ai/
├── terraform/              # 인프라 코드
│   ├── provider.tf         # Oracle Cloud Provider
│   ├── network.tf          # VCN, Subnet, Security
│   ├── compute.tf          # ARM A1 인스턴스
│   ├── variables.tf        # 변수 정의
│   ├── outputs.tf          # 출력값
│   └── terraform.tfvars.example
├── ansible/                # 서버 설정 자동화
│   ├── inventory/
│   │   └── hosts.yml
│   ├── playbooks/
│   │   ├── 01-system-setup.yml
│   │   ├── 02-docker-install.yml
│   │   ├── 03-app-deploy.yml
│   │   ├── 04-nginx-ssl.yml
│   │   └── 05-monitoring.yml
│   ├── roles/
│   └── ansible.cfg
├── docker/                 # 컨테이너 설정
│   ├── Dockerfile.arm64    # ARM64 최적화
│   ├── docker-compose.prod.yml
│   └── nginx/
│       ├── nginx.conf
│       └── ssl/
├── scripts/                # 배포 스크립트
│   ├── deploy.sh           # 원클릭 배포
│   ├── setup-arm64.sh      # ARM64 환경 설정
│   ├── update.sh           # 무중단 업데이트
│   └── rollback.sh         # 롤백
└── .github/
    └── workflows/
        └── deploy.yml      # CI/CD 파이프라인
```

## 🚀 단계별 배포 가이드

### Phase 1: Terraform 인프라 구성

#### 1. Oracle Cloud 설정
```bash
# OCI CLI 설치 및 설정
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
oci setup config

# Terraform 설치
wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_arm64.zip
unzip terraform_1.5.0_linux_arm64.zip
sudo mv terraform /usr/local/bin/
```

#### 2. Terraform 구성 파일 작성

**terraform/provider.tf**
```hcl
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

provider "oci" {
  tenancy_ocid         = var.tenancy_ocid
  user_ocid           = var.user_ocid
  fingerprint         = var.fingerprint
  private_key_path    = var.private_key_path
  region              = var.region
}
```

**terraform/variables.tf**
```hcl
variable "tenancy_ocid" {
  description = "OCID of the tenancy"
  type        = string
}

variable "user_ocid" {
  description = "OCID of the user"
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint of the public key"
  type        = string
}

variable "private_key_path" {
  description = "Path to the private key"
  type        = string
}

variable "region" {
  description = "Oracle Cloud region"
  type        = string
  default     = "ap-seoul-1"
}

variable "compartment_ocid" {
  description = "OCID of the compartment"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}
```

**terraform/network.tf**
```hcl
# VCN 생성
resource "oci_core_vcn" "face_api_vcn" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "face-api-vcn"
  dns_label      = "faceapi"
}

# 인터넷 게이트웨이
resource "oci_core_internet_gateway" "face_api_igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.face_api_vcn.id
  display_name   = "face-api-igw"
}

# 라우트 테이블
resource "oci_core_route_table" "face_api_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.face_api_vcn.id
  display_name   = "face-api-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.face_api_igw.id
  }
}

# 서브넷
resource "oci_core_subnet" "face_api_subnet" {
  compartment_id    = var.compartment_ocid
  vcn_id           = oci_core_vcn.face_api_vcn.id
  cidr_block       = "10.0.1.0/24"
  display_name     = "face-api-subnet"
  dns_label        = "faceapisub"
  route_table_id   = oci_core_route_table.face_api_rt.id
}

# 보안 그룹
resource "oci_core_security_list" "face_api_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.face_api_vcn.id
  display_name   = "face-api-sl"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"
    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"
    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"
    tcp_options {
      min = 443
      max = 443
    }
  }
}
```

**terraform/compute.tf**
```hcl
# ARM A1 인스턴스
resource "oci_core_instance" "face_api_instance" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_ocid
  display_name        = "face-api-arm"
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 4
    memory_in_gbs = 24
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.face_api_subnet.id
    display_name     = "face-api-vnic"
    assign_public_ip = true
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu_images.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
      ssh_public_key = var.ssh_public_key
    }))
  }
}

# 데이터 소스
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

data "oci_core_images" "ubuntu_images" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}
```

#### 3. 인프라 배포
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Phase 2: Ansible 서버 설정

#### 1. Ansible 설치
```bash
sudo apt update
sudo apt install -y ansible
```

#### 2. 플레이북 작성

**ansible/playbooks/01-system-setup.yml**
```yaml
---
- name: System Setup
  hosts: face_api_servers
  become: yes
  tasks:
    - name: Update system
      apt:
        update_cache: yes
        upgrade: dist

    - name: Install essential packages
      apt:
        name:
          - curl
          - wget
          - git
          - htop
          - ufw
          - fail2ban
        state: present

    - name: Configure firewall
      ufw:
        rule: allow
        port: "{{ item }}"
      loop:
        - 22
        - 80
        - 443

    - name: Enable firewall
      ufw:
        state: enabled
```

**ansible/playbooks/02-docker-install.yml**
```yaml
---
- name: Install Docker
  hosts: face_api_servers
  become: yes
  tasks:
    - name: Install Docker dependencies
      apt:
        name:
          - apt-transport-https
          - ca-certificates
          - curl
          - gnupg
          - lsb-release
        state: present

    - name: Add Docker GPG key
      apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        state: present

    - name: Add Docker repository
      apt_repository:
        repo: "deb [arch=arm64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
        state: present

    - name: Install Docker
      apt:
        name:
          - docker-ce
          - docker-ce-cli
          - containerd.io
          - docker-compose-plugin
        state: present

    - name: Start Docker service
      systemd:
        name: docker
        state: started
        enabled: yes

    - name: Add user to docker group
      user:
        name: ubuntu
        groups: docker
        append: yes
```

#### 3. 배포 실행
```bash
cd ansible
ansible-playbook -i inventory/hosts.yml playbooks/01-system-setup.yml
ansible-playbook -i inventory/hosts.yml playbooks/02-docker-install.yml
```

### Phase 3: Docker 컨테이너화

#### 1. ARM64 최적화 Dockerfile

**docker/Dockerfile.arm64**
```dockerfile
# ARM64 최적화된 Multi-stage build
FROM --platform=linux/arm64 python:3.11-slim as builder

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
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# ARM64 최적화된 패키지 설치
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Runtime stage
FROM --platform=linux/arm64 python:3.11-slim as runtime

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

#### 2. 프로덕션 Docker Compose

**docker/docker-compose.prod.yml**
```yaml
version: '3.8'

services:
  face-api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.arm64
    container_name: face-api
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - USE_GPU=false
    volumes:
      - ../logs:/app/logs
      - /etc/localtime:/etc/localtime:ro
    networks:
      - face-api-network
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '3.0'
        reservations:
          memory: 4G
          cpus: '2.0'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - face-api
    networks:
      - face-api-network

networks:
  face-api-network:
    driver: bridge
```

#### 3. Nginx 설정

**docker/nginx/nginx.conf**
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
    
    # 로그 포맷
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    server {
        listen 80;
        server_name _;
        
        # HTTP to HTTPS redirect
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        # SSL 설정
        ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # 보안 헤더
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

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

### Phase 4: 자동화 스크립트

#### 1. 원클릭 배포 스크립트

**scripts/deploy.sh**
```bash
#!/bin/bash
set -e

echo "🚀 Face API 배포 시작..."

# 환경 확인
if [ ! -f "terraform.tfvars" ]; then
    echo "❌ terraform.tfvars 파일이 필요합니다"
    exit 1
fi

# 1. Terraform 인프라 배포
echo "📦 인프라 배포 중..."
cd terraform
terraform init
terraform apply -auto-approve
cd ..

# 2. Ansible 서버 설정
echo "⚙️ 서버 설정 중..."
cd ansible
ansible-playbook -i inventory/hosts.yml playbooks/site.yml
cd ..

# 3. Docker 이미지 빌드 및 배포
echo "🐳 애플리케이션 배포 중..."
cd docker
docker-compose -f docker-compose.prod.yml up -d --build
cd ..

# 4. SSL 인증서 발급
echo "🔒 SSL 인증서 설정 중..."
./scripts/setup-ssl.sh

echo "✅ 배포 완료!"
echo "🌐 https://your-domain.com 에서 확인하세요"
```

#### 2. SSL 자동화 스크립트

**scripts/setup-ssl.sh**
```bash
#!/bin/bash
set -e

DOMAIN=${1:-your-domain.com}
EMAIL=${2:-admin@$DOMAIN}

echo "🔒 SSL 인증서 설정 시작..."

# Certbot 설치
sudo apt update
sudo apt install -y certbot

# Let's Encrypt 인증서 발급
sudo certbot certonly --standalone \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# 자동 갱신 설정
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# Nginx 재시작
docker-compose -f docker/docker-compose.prod.yml restart nginx

echo "✅ SSL 설정 완료!"
```

### Phase 5: CI/CD 파이프라인

**.github/workflows/deploy.yml**
```yaml
name: Deploy to Oracle Cloud

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Setup OCI CLI
      uses: oracle-actions/configure-oci-cli@v1.0
      with:
        user: ${{ secrets.OCI_USER_OCID }}
        fingerprint: ${{ secrets.OCI_FINGERPRINT }}
        tenancy: ${{ secrets.OCI_TENANCY_OCID }}
        region: ${{ secrets.OCI_REGION }}
        private-key: ${{ secrets.OCI_PRIVATE_KEY }}

    - name: Build ARM64 image
      run: |
        docker buildx create --use
        docker buildx build --platform linux/arm64 \
          -f docker/Dockerfile.arm64 \
          -t face-api:${{ github.sha }} .

    - name: Deploy to instance
      run: |
        # SSH 배포 스크립트 실행
        ssh -i ~/.ssh/oracle_key ubuntu@${{ secrets.INSTANCE_IP }} \
          "cd whos-your-papa-ai && git pull && ./scripts/update.sh"
```

## 📊 모니터링 및 로깅

### 1. 시스템 모니터링
```bash
# 시스템 리소스 모니터링
htop

# Docker 컨테이너 상태
docker stats

# 로그 확인
docker-compose -f docker/docker-compose.prod.yml logs -f
```

### 2. 애플리케이션 로그
```bash
# 애플리케이션 로그
tail -f logs/app.log

# Nginx 로그
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 💰 비용 최적화

### 프리티어 리소스 활용
- **ARM A1 인스턴스**: 4vCPU, 24GB RAM (무료)
- **블록 스토리지**: 200GB (무료)
- **네트워크**: 10TB 아웃바운드 (무료)
- **Load Balancer**: 1개 (무료)

### 예상 비용: $0/월

## 🔧 유지보수

### 1. 정기 업데이트
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 이미지 업데이트
./scripts/update.sh
```

### 2. 백업
```bash
# 애플리케이션 백업
tar -czf backup-$(date +%Y%m%d).tar.gz app/ logs/ docker/

# 데이터베이스 백업 (필요시)
# mysqldump 또는 pg_dump 사용
```

### 3. 롤백
```bash
# 이전 버전으로 롤백
./scripts/rollback.sh
```

## 📋 배포 후 검증

### 체크리스트
```bash
# 1. 서비스 상태 확인
curl https://your-domain.com/health

# 2. SSL 인증서 확인
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# 3. 부하 테스트
ab -n 100 -c 10 https://your-domain.com/health

# 4. 로그 확인
docker-compose -f docker/docker-compose.prod.yml logs --tail=100

# 5. 리소스 사용량 확인
docker stats
```

---

**배포 완료 후 [WORKFLOW.md](WORKFLOW.md)에 배포 과정을 기록하세요.**
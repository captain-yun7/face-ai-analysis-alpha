# Oracle Cloud 프리티어 배포 가이드

> Oracle Cloud ARM A1 인스턴스와 Terraform + Ansible을 활용한 완전 무료 배포 전략

## 🎯 프리티어 활용 최대화 전략

### Oracle Cloud Free Tier 리소스
- **Compute**: ARM A1 1vCPU + 6GB RAM (Always Free)
- **Storage**: 200GB Block Volume (Always Free)  
- **Network**: 10TB/월 아웃바운드 트래픽
- **Load Balancer**: 1개 (Always Free)
- **Container Registry**: 500MB (Always Free)

### 인프라 아키텍처
```
인터넷:8000 → ARM A1 인스턴스 (Face API:8000 + systemd 관리)
선택사항: 인터넷:443 → Oracle Load Balancer → ARM A1 인스턴스 (Nginx:443 → FastAPI:8000)
```

## 📂 프로젝트 구조

```
face-ai-analysis-alpha/
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
│   │   ├── site.yml               # 전체 배포 오케스트레이션
│   │   ├── 01-system-setup.yml     # 시스템 패키지 + UFW 8000 포트
│   │   ├── 02-ai-dependencies.yml  # InsightFace + OpenGL 설치
│   │   ├── 03-app-deploy.yml       # Python venv 기반 배포
│   │   ├── 04-nginx-ssl.yml        # 웹서버 + SSL (선택사항)
│   │   ├── 05-monitoring.yml       # 모니터링 (선택사항)
│   │   └── templates/
│   │       └── face-api.service.j2 # systemd 서비스
│   ├── roles/
│   └── ansible.cfg
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
    ocpus         = 1
    memory_in_gbs = 6
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

#### 3. 완전 자동화 배포 실행 (한 번에!)
```bash
cd ansible
# 모든 단계를 한 번에 실행 (시스템 설정 → AI 의존성 → 앱 배포)
ansible-playbook -i inventory/hosts.yml playbooks/site.yml
```

**또는 단계별 실행:**
```bash
cd ansible
ansible-playbook -i inventory/hosts.yml playbooks/01-system-setup.yml     # 시스템 + 방화벽
ansible-playbook -i inventory/hosts.yml playbooks/02-ai-dependencies.yml  # InsightFace + OpenGL  
ansible-playbook -i inventory/hosts.yml playbooks/03-app-deploy.yml       # Python venv 배포
ansible-playbook -i inventory/hosts.yml playbooks/04-nginx-ssl.yml        # 웹서버 (선택)
```

### Phase 3: AI 의존성 및 Python 환경 구성

#### 1. AI 의존성 자동 설치 (02-ai-dependencies.yml)

**핵심 구성요소:**
- **OpenGL 시스템 라이브러리**: ARM64 환경에서 InsightFace 실행 필수
- **Python 가상환경**: 시스템과 분리된 안전한 패키지 관리  
- **InsightFace + ONNX Runtime**: 얼굴 분석 AI 모델
- **자동 검증**: 설치 후 AI 모델 로딩 테스트

```yaml
# 02-ai-dependencies.yml 주요 작업들
- name: Install OpenGL and graphics system libraries
  apt:
    name:
      - libgl1-mesa-glx      # OpenGL Mesa library  
      - libglib2.0-0         # GLib library
      - libsm6               # X11 Session Management
      - libxext6             # X11 extensions
      - libxrender-dev       # X Rendering Extension
      - libgomp1             # GNU OpenMP runtime
      - build-essential      # 컴파일 도구
      
- name: Create Python virtual environment
  command: python3.10 -m venv /home/ubuntu/venv
  
- name: Install InsightFace and dependencies  
  pip:
    name:
      - insightface>=0.7.3
      - onnxruntime>=1.16.0
      - opencv-python-headless>=4.8.0
    virtualenv: /home/ubuntu/venv
```

#### 2. Python 가상환경 배포 (03-app-deploy.yml)

**핵심 배포 과정:**
- **애플리케이션 코드 배치**: `/home/ubuntu/face-ai-analysis-alpha/`
- **환경 설정**: `.env` 파일 자동 생성
- **systemd 서비스**: 자동 시작 및 관리
- **검증**: Face API 모듈 임포트 테스트

```yaml  
# 03-app-deploy.yml 주요 작업들
- name: Create environment file for Face API
  copy:
    dest: "{{ app_dir }}/.env"
    content: |
      ENVIRONMENT=production
      LOG_LEVEL=INFO
      USE_GPU=false
      MODEL_NAME=buffalo_l
      API_HOST=0.0.0.0
      API_PORT=8000

- name: Test Face API module import
  command: "{{ venv_path }}/bin/python -c 'from app.main import app; print(\"✅ Face API imports successfully\")'"
  
- name: Create systemd service for Face API
  template:
    src: templates/face-api.service.j2
    dest: /etc/systemd/system/face-api.service
```

#### 3. systemd 서비스 관리

**face-api.service.j2 템플릿:**
```ini
[Unit]
Description=Face API Application (InsightFace)
After=network-online.target

[Service]
Type=exec
WorkingDirectory=/home/ubuntu/face-ai-analysis-alpha
ExecStart=/home/ubuntu/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
User=ubuntu
Restart=on-failure

# Environment variables
Environment=MODEL_NAME=buffalo_l
Environment=USE_GPU=false
Environment=LOG_LEVEL=INFO

[Install]
WantedBy=multi-user.target
```

**서비스 관리 명령어:**
```bash
# 서비스 시작
sudo systemctl start face-api

# 서비스 상태 확인  
sudo systemctl status face-api

# 서비스 재시작
sudo systemctl restart face-api

# 로그 확인
journalctl -u face-api -f
```

### Phase 4: 배포 검증 및 테스트

#### 1. AI 모델 로딩 확인
```bash
# 헬스체크 (AI 모델 상태 포함)
curl http://144.24.82.25:8000/health

# 예상 응답:
{
  "status": "healthy",
  "model_loaded": true,  # ✅ 핵심!
  "gpu_available": false,
  "memory_usage": {"percent": 23.0},
  "version": "1.0.0"
}
```

#### 2. 얼굴 분석 API 테스트
```bash
# 얼굴 감지 테스트
curl -X POST http://144.24.82.25:8000/detect-faces \
  -H "Content-Type: application/json" \
  -d @test_image.json

#### 3. InsightFace 모델 상태 확인
```bash
# SSH로 서버 접속 후 확인
ssh -i ~/.ssh/oracle_key ubuntu@144.24.82.25

# 가상환경 활성화 스크립트 실행
./activate_venv.sh

# 출력 예시:
# ✅ Face API virtual environment activated  
# Python: Python 3.10.x
# InsightFace: 0.7.3
# ONNX Runtime: 1.22.1

# AI 모델 디렉토리 확인
ls -la ~/.insightface/models/buffalo_l/
# buffalo_l 모델 파일들 확인 (약 280MB)
```

#### 4. 성능 및 리소스 모니터링
```bash
# 메모리 사용량 확인
free -h

# Face API 프로세스 확인  
ps aux | grep python

# CPU 사용률 확인
htop
```

### Phase 5: 웹서버 및 SSL 설정 (선택사항)

**04-nginx-ssl.yml 플레이북으로 설치:**
```bash
# Nginx 프록시 및 SSL 설정 (선택사항)
ansible-playbook -i inventory/hosts.yml playbooks/04-nginx-ssl.yml
```

**Nginx 구성 예시:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    # SSL 설정
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;  # Face API systemd 서비스
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
}
```

### Phase 6: 자동화 스크립트

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

# 2. Ansible 전체 배포 (시스템 + AI + 앱)
echo "⚙️ 서버 및 애플리케이션 배포 중..."
cd ansible
ansible-playbook -i inventory/hosts.yml playbooks/site.yml
cd ..

# 3. 배포 검증
echo "🔍 배포 검증 중..."
PUBLIC_IP=$(cd terraform && terraform output -raw public_ip)
curl -f http://$PUBLIC_IP:8000/health || {
    echo "❌ Face API 헬스체크 실패"
    exit 1
}

echo "✅ 배포 완료!"
echo "🌐 http://$PUBLIC_IP:8000 에서 확인하세요"
echo "📊 헬스체크: http://$PUBLIC_IP:8000/health"
```

#### 2. SSL 자동화 스크립트 (선택사항)

**scripts/setup-ssl.sh**
```bash
#!/bin/bash
set -e

DOMAIN=${1:-your-domain.com}
EMAIL=${2:-admin@$DOMAIN}

echo "🔒 SSL 인증서 설정 시작..."

# Certbot 설치
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Let's Encrypt 인증서 발급
sudo certbot certonly --standalone \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# 자동 갱신 설정
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# Nginx 재시작
sudo systemctl restart nginx

echo "✅ SSL 설정 완료!"
```

### Phase 7: CI/CD 파이프라인

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

    - name: Deploy to instance
      run: |
        # SSH로 코드 업데이트 및 서비스 재시작
        ssh -i ~/.ssh/oracle_key ubuntu@${{ secrets.INSTANCE_IP }} \
          "cd face-ai-analysis-alpha && \
           git pull && \
           sudo systemctl restart face-api && \
           sleep 10 && \
           curl -f http://localhost:8000/health"
```

## 📊 모니터링 및 로깅

### 1. systemd 서비스 모니터링
```bash
# Face API 서비스 상태 확인
sudo systemctl status face-api

# 실시간 로그 확인
journalctl -u face-api -f

# 시스템 리소스 모니터링
htop

# Face API 프로세스 확인
ps aux | grep python | grep uvicorn
```

### 2. 애플리케이션 로그 및 성능
```bash
# Face API 로그 (최근 100줄)
journalctl -u face-api --lines=100

# 메모리 사용량 확인
free -h

# 디스크 사용량 확인
df -h

# AI 모델 로딩 상태 확인
curl http://localhost:8000/health
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

# Face API 애플리케이션 업데이트
cd /home/ubuntu/face-ai-analysis-alpha
git pull
sudo systemctl restart face-api

# AI 모델 캐시 정리 (필요시)
rm -rf ~/.insightface/models/*
```

### 2. 백업
```bash
# 애플리케이션 백업
tar -czf backup-$(date +%Y%m%d).tar.gz \
    /home/ubuntu/face-ai-analysis-alpha \
    /home/ubuntu/venv \
    ~/.insightface/models

# systemd 서비스 백업
sudo cp /etc/systemd/system/face-api.service /home/ubuntu/
```

### 3. 롤백
```bash
# Git을 통한 이전 버전으로 롤백
cd /home/ubuntu/face-ai-analysis-alpha
git log --oneline  # 커밋 히스토리 확인
git reset --hard <이전-커밋-해시>
sudo systemctl restart face-api
```

## 📋 배포 후 검증

### 체크리스트
```bash
# 1. Face API 서비스 상태 확인
curl http://PUBLIC_IP:8000/health
# 예상 응답: {"status":"healthy","model_loaded":true}

# 2. systemd 서비스 상태 확인
sudo systemctl status face-api

# 3. AI 모델 로딩 확인
ls -la ~/.insightface/models/buffalo_l/

# 4. 부하 테스트
ab -n 100 -c 10 http://PUBLIC_IP:8000/health

# 5. 로그 확인
journalctl -u face-api --lines=100

# 6. 리소스 사용량 확인
free -h && ps aux | grep python

# 7. 포트 8000 접근 가능 확인
sudo ufw status | grep 8000
sudo netstat -tlnp | grep :8000
```

---

**배포 완료 후 [WORKFLOW.md](WORKFLOW.md)에 배포 과정을 기록하세요.**
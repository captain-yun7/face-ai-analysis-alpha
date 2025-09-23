# Terraform Oracle Cloud Infrastructure

Oracle Cloud에 Face API용 ARM A1 인스턴스를 배포하는 Terraform 구성입니다.

## 사전 준비사항

1. **Oracle Cloud 계정 및 API 키 설정**
   ```bash
   # OCI CLI 설치
   bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
   
   # OCI 설정
   oci setup config
   ```

2. **Terraform 설치**
   ```bash
   # ARM64용 Terraform 다운로드 및 설치
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_arm64.zip
   unzip terraform_1.6.0_linux_arm64.zip
   sudo mv terraform /usr/local/bin/
   ```

3. **SSH 키 생성**
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/oracle_key
   ```

## 배포 방법

1. **설정 파일 준비**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # terraform.tfvars 파일을 편집하여 실제 값 입력
   ```

2. **Terraform 초기화 및 배포**
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

3. **인스턴스 접속**
   ```bash
   # 출력된 SSH 명령어 사용
   ssh -i ~/.ssh/oracle_key ubuntu@<PUBLIC_IP>
   ```

## 리소스 구성

- **Compute**: ARM A1.Flex (4 OCPU, 24GB RAM)
- **Network**: VCN, Public Subnet, Internet Gateway
- **Storage**: 50GB Boot Volume + 50GB Block Volume
- **Security**: Security List (SSH, HTTP, HTTPS 허용)

## 정리

```bash
terraform destroy
```

## 주의사항

- 프리티어 한도 내에서 리소스 생성
- SSH 키와 API 키는 안전하게 보관
- terraform.tfvars 파일은 Git에 커밋하지 않음
# 개발 환경 구성 가이드

> 로컬 개발 환경 설정 및 개발 워크플로우 가이드입니다.

## 🛠️ 개발 환경 설정

### 필수 도구

```bash
# 1. Git 설정
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 2. Python 개발 도구 설치
pip install -r requirements-dev.txt
```

### requirements-dev.txt 내용
```txt
# 개발 도구
black==23.9.1           # 코드 포맷터
isort==5.12.0          # import 정리
flake8==6.1.0          # 린터
mypy==1.6.1            # 타입 체커
pytest==7.4.3         # 테스트 프레임워크
pytest-cov==4.1.0     # 커버리지
pytest-asyncio==0.21.1 # 비동기 테스트

# API 개발 도구
httpie==3.2.2          # API 테스트 클라이언트
jupyter==1.0.0         # 노트북 개발

# 개발 서버
watchdog==3.0.0        # 파일 변경 감지
```

## 🏗️ 프로젝트 구조

```
whos-your-papa-ai/
├── app/                    # FastAPI 애플리케이션
│   ├── api/               # API 라우터
│   │   ├── routes/
│   │   │   ├── faces.py   # 얼굴 관련 API
│   │   │   └── health.py  # 헬스체크
│   │   └── dependencies.py
│   ├── core/              # 핵심 설정
│   │   ├── config.py      # 환경 설정
│   │   ├── security.py    # 보안 관련
│   │   └── logging.py     # 로깅 설정
│   ├── models/            # AI 모델 관련
│   │   ├── model_manager.py
│   │   └── face_analyzer.py
│   ├── services/          # 비즈니스 로직
│   │   ├── face_service.py
│   │   └── comparison_service.py
│   ├── schemas/           # Pydantic 스키마
│   │   ├── requests.py
│   │   └── responses.py
│   ├── utils/             # 유틸리티
│   │   ├── image_utils.py
│   │   └── validation.py
│   └── main.py           # 앱 엔트리포인트
├── docs/                  # 문서
├── tests/                 # 테스트
├── logs/                  # 로그 파일
└── requirements.txt       # 의존성
```

## 🚀 개발 서버 실행

### 기본 개발 서버
```bash
# 가상환경 활성화
source venv/bin/activate

# 개발 서버 시작 (자동 재로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 더 상세한 로깅
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### 환경변수 설정
```bash
# .env 파일 설정
cp .env.example .env

# 개발용 환경변수
echo "ENVIRONMENT=development" >> .env
echo "LOG_LEVEL=DEBUG" >> .env
echo "RELOAD=true" >> .env
```

### 개발용 스크립트
```bash
# scripts/dev.sh 생성
#!/bin/bash
source venv/bin/activate
export ENVIRONMENT=development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# 실행 권한 부여
chmod +x scripts/dev.sh

# 개발 서버 시작
./scripts/dev.sh
```

## 🧪 테스트

### 테스트 실행
```bash
# 전체 테스트
pytest

# 특정 테스트 파일
pytest tests/test_basic.py

# 커버리지 포함
pytest --cov=app tests/

# 상세 출력
pytest -v tests/

# 실패한 테스트만 재실행
pytest --lf
```

### 테스트 작성 가이드
```python
# tests/test_example.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """헬스체크 엔드포인트 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_async_function():
    """비동기 함수 테스트"""
    result = await some_async_function()
    assert result is not None
```

## 🎨 코드 품질

### 코드 포맷팅
```bash
# Black 포맷터 실행
black app/ tests/

# isort로 import 정리
isort app/ tests/

# 둘 다 한번에
black app/ tests/ && isort app/ tests/
```

### 린팅
```bash
# flake8 린터 실행
flake8 app/ tests/

# mypy 타입 체크
mypy app/
```

### pre-commit 훅 설정
```bash
# .pre-commit-config.yaml 생성
pip install pre-commit
pre-commit install

# 수동 실행
pre-commit run --all-files
```

### .pre-commit-config.yaml 예시
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
```

## 📝 개발 워크플로우

### 1. 새 기능 개발
```bash
# 1. 브랜치 생성
git checkout -b feature/new-feature

# 2. 코드 작성
# ... 개발 작업 ...

# 3. 테스트 작성 및 실행
pytest tests/test_new_feature.py

# 4. 코드 품질 체크
black app/ tests/
flake8 app/ tests/
mypy app/

# 5. 커밋
git add .
git commit -m "feat: add new feature"

# 6. 푸시
git push origin feature/new-feature
```

### 2. 버그 수정
```bash
# 1. 버그 재현 테스트 작성
# 2. 최소한의 변경으로 수정
# 3. 테스트 통과 확인
# 4. 회귀 테스트 추가
```

### 3. 리팩토링
```bash
# 1. 기존 테스트 모두 통과 확인
# 2. 리팩토링 수행
# 3. 테스트 재실행
# 4. 성능 측정 및 비교
```

## 🔧 유용한 개발 도구

### API 테스트
```bash
# HTTPie로 API 테스트
http GET localhost:8000/health
http POST localhost:8000/compare-faces source_image=@image1.jpg target_image=@image2.jpg

# curl로 API 테스트
curl -X GET http://localhost:8000/health
curl -X POST http://localhost:8000/compare-faces \
  -H "Content-Type: application/json" \
  -d '{"source_image": "base64...", "target_image": "base64..."}'
```

### 로그 모니터링
```bash
# 실시간 로그 확인
tail -f logs/app.log

# 에러 로그만 확인
grep ERROR logs/app.log

# 특정 시간대 로그
grep "2025-09-19 14:" logs/app.log
```

### 성능 프로파일링
```bash
# cProfile로 성능 측정
python -m cProfile -o profile.stats app/main.py

# line_profiler로 라인별 측정
kernprof -l -v slow_function.py

# memory_profiler로 메모리 사용량 측정
mprof run python app/main.py
mprof plot
```

## 🐛 디버깅

### 로컬 디버깅
```python
# 브레이크포인트 설정
import pdb; pdb.set_trace()

# 또는 Python 3.7+
breakpoint()

# 로깅 추가
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug information")
```

### VS Code 디버깅 설정
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/venv/bin/uvicorn",
            "args": ["app.main:app", "--reload"],
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            },
            "console": "integratedTerminal"
        }
    ]
}
```

## 📊 모니터링

### 개발 중 메트릭 확인
```bash
# 시스템 리소스 모니터링
htop
nvidia-smi  # GPU 사용 시

# 애플리케이션 메트릭
curl http://localhost:8000/metrics
curl http://localhost:8000/health
```

### 로그 레벨 설정
```python
# app/core/logging.py에서 개발용 설정
import logging

# 개발 환경에서는 DEBUG 레벨
if os.getenv("ENVIRONMENT") == "development":
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
```

## 🔄 CI/CD 준비

### GitHub Actions 워크플로우
```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest --cov=app tests/
    
    - name: Code quality
      run: |
        black --check app/ tests/
        flake8 app/ tests/
        mypy app/
```

## 📚 참고 자료

### 내부 문서
- [설치 가이드](SETUP.md)
- [문제 해결 가이드](TROUBLESHOOTING.md)
- [API 문서](API_DESIGN.md)

### 외부 자료
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Pytest 가이드](https://docs.pytest.org/)
- [Black 포맷터](https://black.readthedocs.io/)

---

**개발 중 문제가 발생하면 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)를 참조하세요.**
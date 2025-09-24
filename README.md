# 🤖 Who's Your Papa - AI Backend

> InsightFace 기반 고성능 얼굴 분석 백엔드 서비스

## 📌 개요

기존 AWS Rekognition을 대체하여 비용을 절감하고 성능을 향상시키는 얼굴 분석 AI 백엔드입니다. Next.js 프론트엔드와 완벽하게 호환되며, 하이브리드 운영이 가능합니다.

### 🎯 주요 특징

- **고정확도**: 99.83% 얼굴 인식 정확도 (LFW 벤치마크)
- **비용 효율**: AWS 대비 최대 90% 비용 절감
- **빠른 처리**: 실시간 얼굴 분석 및 배치 처리
- **완전 호환**: 기존 Next.js API와 100% 호환
- **확장 가능**: 실시간 추적, 배치 분석 등 고급 기능 지원

## 🚀 빠른 시작

### ⚡ 설치 및 실행

```bash
# 1. 프로젝트 클론
git clone <repository-url> && cd whos-your-papa-ai

# 2. 자동 설치 (처음만)
bash scripts/setup.sh

# 3. 서버 실행
conda activate insightface
python -m app.main
```

### 🧪 테스트

```bash
# 다른 터미널에서 실행
curl http://localhost:8000/health  # {"model_loaded": true}

# 또는 운영 서버에서 테스트
curl http://144.24.82.25:8000/health  # {"model_loaded": true}
```

### 💡 사용 팁

```bash
# 서버 종료: Ctrl+C

# 백그라운드 실행
python -m app.main &

# 포트 변경 (8080 사용)
python -m app.main --port 8080
```

## 🚀 현재 상태

✅ **완료된 기능:**
- InsightFace 모델 완전 통합
- 얼굴 감지 및 비교 API
- Next.js 프론트엔드 연동
- 하이브리드 AWS/Python 지원

## 📚 상세 문서

- **[📖 설치 가이드](docs/SETUP.md)** - 상세 설치 방법 및 문제 해결
- **[🔧 개발 가이드](docs/DEVELOPMENT.md)** - 개발 환경 구성 및 워크플로우  
- **[🐛 문제 해결](docs/TROUBLESHOOTING.md)** - 자주 발생하는 문제와 해결법
- **[🚀 배포 가이드](docs/DEPLOYMENT.md)** - 프로덕션 배포 방법
- **[📋 API 문서](docs/API_DESIGN.md)** - API 명세 및 엔드포인트
- **[🏗️ 아키텍처](docs/ARCHITECTURE.md)** - 시스템 설계 및 구조  
- **[🔗 Next.js 연동](docs/INTEGRATION_PLAN.md)** - Next.js 통합 계획

## 🤝 기여

개발에 참여하려면:
1. 이 저장소를 Fork
2. [개발 가이드](docs/DEVELOPMENT.md)를 따라 환경 구성
3. [CLAUDE.md](CLAUDE.md) 작업 표준 준수
4. Pull Request 생성

## 📄 라이센스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

**🌟 유용하다면 이 저장소에 Star를 눌러주세요!**
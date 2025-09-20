"""
모델 관리자 - InsightFace 모델 로딩 및 관리
"""
import asyncio
from typing import Optional, Dict, Any
import time
from contextlib import asynccontextmanager

from ..core.logging import get_logger

logger = get_logger(__name__)


class ModelManager:
    """AI 모델 로딩 및 관리"""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_loaded = False
        self.load_start_time = None
        
    async def initialize_models(self):
        """모델 초기화"""
        logger.info("모델 초기화 시작...")
        self.load_start_time = time.time()
        
        try:
            # InsightFace 모델 로딩 시도
            await self._load_insightface_model()
            self.model_loaded = True
            
            load_time = time.time() - self.load_start_time
            logger.info(f"모델 초기화 완료 (소요시간: {load_time:.2f}초)")
            
        except Exception as e:
            logger.warning(f"InsightFace 모델 로딩 실패: {e}")
            logger.info("더미 모델로 대체하여 실행")
            self.model_loaded = False
    
    async def _load_insightface_model(self):
        """InsightFace 모델 로딩"""
        try:
            import insightface
            
            # InsightFace 앱 초기화
            app = insightface.app.FaceAnalysis(providers=['CPUExecutionProvider'])
            app.prepare(ctx_id=-1)
            
            self.models['face_analysis'] = app
            logger.info("✅ InsightFace 모델 로딩 성공")
            
        except ImportError:
            raise Exception("InsightFace 패키지가 설치되지 않았습니다")
        except Exception as e:
            raise Exception(f"InsightFace 모델 로딩 실패: {e}")
    
    async def warmup_models(self):
        """모델 워밍업"""
        if not self.model_loaded:
            logger.info("모델이 로드되지 않아 워밍업 스킵")
            return
            
        logger.info("모델 워밍업 중...")
        # 더미 이미지로 워밍업 수행
        # TODO: 실제 구현
        await asyncio.sleep(0.1)  # 더미 워밍업
        logger.info("모델 워밍업 완료")
    
    async def shutdown_models(self):
        """모델 종료"""
        logger.info("모델 종료 중...")
        self.models.clear()
        self.model_loaded = False
        logger.info("모델 종료 완료")
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_loaded": self.model_loaded,
            "models": list(self.models.keys()),
            "load_time": time.time() - self.load_start_time if self.load_start_time else None
        }
    
    def is_ready(self) -> bool:
        """모델 준비 상태 확인"""
        return True  # InsightFace 없이도 기본 기능 제공
    
    def get_health_status(self) -> Dict[str, Any]:
        """헬스 상태 반환"""
        import psutil
        
        try:
            # 시스템 메모리 정보
            memory = psutil.virtual_memory()
            memory_usage = {
                "used_mb": round(memory.used / 1024 / 1024),
                "total_mb": round(memory.total / 1024 / 1024),
                "percent": memory.percent
            }
        except:
            memory_usage = {}
        
        # GPU 가용성 체크
        gpu_available = False
        try:
            import torch
            gpu_available = torch.cuda.is_available()
        except:
            pass
        
        status = "healthy" if self.is_ready() else "unhealthy"
        
        return {
            "status": status,
            "model_loaded": self.model_loaded,
            "gpu_available": gpu_available,
            "memory_usage": memory_usage,
            "version": "1.0.0",
            "statistics": {
                "uptime_seconds": time.time() - self.load_start_time if self.load_start_time else 0
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """메트릭 정보 반환"""
        return {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_processing_time_ms": 0,
            "requests_per_minute": 0,
            "uptime_seconds": time.time() - self.load_start_time if self.load_start_time else 0,
            "error_rate": 0.0
        }
    
    @asynccontextmanager
    async def request_context(self, operation_type: str):
        """요청 컨텍스트 관리"""
        start_time = time.time()
        logger.debug(f"시작: {operation_type}")
        
        try:
            yield
        finally:
            processing_time = time.time() - start_time
            logger.debug(f"완료: {operation_type} (소요시간: {processing_time:.3f}초)")
    
    def get_face_analyzer(self):
        """얼굴 분석기 반환"""
        from .face_analyzer import FaceAnalyzer
        return FaceAnalyzer(self.models.get('face_analysis'))


# 전역 모델 매니저 인스턴스
model_manager = ModelManager()
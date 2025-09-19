"""
헬스체크 및 모니터링 API
"""
import time
from typing import Dict, Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...schemas.responses import HealthResponse, ModelInfoResponse, MetricsResponse
from ...models.model_manager import model_manager
from ...core.config import settings
from ...core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    서비스 헬스체크를 수행합니다.
    
    시스템 상태, 모델 로드 상태, 메모리 사용량 등을 확인합니다.
    """
    try:
        health_status = model_manager.get_health_status()
        
        # 응답 형식에 맞게 조정
        response = HealthResponse(
            status=health_status.get("status", "unknown"),
            model_loaded=health_status.get("model_loaded", False),
            gpu_available=health_status.get("gpu_available", False),
            memory_usage=health_status.get("memory_usage", {}),
            version=health_status.get("version", "unknown"),
            uptime_seconds=health_status.get("statistics", {}).get("uptime_seconds", 0)
        )
        
        # 상태에 따른 HTTP 상태 코드
        if health_status.get("status") == "healthy":
            return response
        else:
            return JSONResponse(
                status_code=503,
                content=response.dict()
            )
            
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "model_loaded": False,
                "gpu_available": False,
                "memory_usage": {},
                "version": settings.app_version,
                "uptime_seconds": 0,
                "error": str(e)
            }
        )


@router.get("/health/detailed")
async def detailed_health():
    """
    상세한 헬스체크 정보를 반환합니다.
    
    모델 상태, 시스템 정보, 통계 등을 포함합니다.
    """
    try:
        return model_manager.get_health_status()
    except Exception as e:
        logger.error(f"상세 헬스체크 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """
    로드된 모델의 정보를 반환합니다.
    
    모델명, 입력 크기, 임베딩 차원, 지원 기능 등을 포함합니다.
    """
    try:
        model_info = model_manager.get_model_info()
        
        if "error" in model_info:
            return JSONResponse(
                status_code=503,
                content=model_info
            )
        
        response = ModelInfoResponse(
            model_name=model_info.get("model_name", "unknown"),
            input_size=model_info.get("input_size", [640, 640]),
            embedding_size=model_info.get("embedding_size", 512),
            supported_features=model_info.get("supported_features", []),
            performance_metrics=model_info.get("performance_metrics", {})
        )
        
        return response
        
    except Exception as e:
        logger.error(f"모델 정보 조회 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    성능 메트릭을 반환합니다.
    
    요청 수, 처리 시간, 에러율 등의 통계를 포함합니다.
    """
    try:
        metrics = model_manager.get_metrics()
        
        response = MetricsResponse(
            current_load=0.0,  # TODO: 실제 부하 계산 로직 추가
            queue_size=0,      # TODO: 큐 크기 추적 로직 추가
            active_requests=0, # TODO: 활성 요청 수 추적 로직 추가
            usage_stats={
                "total_requests": metrics.get("total_requests", 0),
                "successful_requests": metrics.get("successful_requests", 0),
                "failed_requests": metrics.get("failed_requests", 0),
                "avg_processing_time_ms": metrics.get("avg_processing_time_ms", 0),
                "requests_per_minute": metrics.get("requests_per_minute", 0)
            },
            system_info={
                "uptime_seconds": metrics.get("uptime_seconds", 0),
                "error_rate": metrics.get("error_rate", 0)
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"메트릭 조회 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.get("/ping")
async def ping():
    """
    간단한 핑 엔드포인트입니다.
    
    로드밸런서나 모니터링 시스템에서 사용할 수 있습니다.
    """
    return {
        "message": "pong",
        "timestamp": time.time(),
        "version": settings.app_version
    }


@router.get("/ready")
async def readiness_check():
    """
    서비스 준비 상태를 확인합니다.
    
    Kubernetes readiness probe에서 사용할 수 있습니다.
    """
    try:
        health_status = model_manager.get_health_status()
        
        if health_status.get("model_loaded", False):
            return {
                "ready": True,
                "message": "서비스가 준비되었습니다"
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "ready": False,
                    "message": "모델이 로드되지 않았습니다"
                }
            )
            
    except Exception as e:
        logger.error(f"준비 상태 확인 실패: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "message": f"준비 상태 확인 실패: {str(e)}"
            }
        )


@router.get("/live")
async def liveness_check():
    """
    서비스 생존 상태를 확인합니다.
    
    Kubernetes liveness probe에서 사용할 수 있습니다.
    """
    try:
        return {
            "alive": True,
            "message": "서비스가 실행 중입니다",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"생존 상태 확인 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "alive": False,
                "message": f"생존 상태 확인 실패: {str(e)}"
            }
        )
"""
FastAPI 애플리케이션 메인 엔트리포인트
"""
import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .core.config import settings
from .core.logging import get_logger, log_request, log_error
from .models.model_manager import model_manager
from .api.routes import faces, health

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    
    # 시작 시 실행
    logger.info(f"{settings.app_name} v{settings.app_version} 시작 중...")
    
    try:
        # 모델 초기화
        await model_manager.initialize_models()
        
        # 모델 워밍업
        if settings.debug_mode:
            await model_manager.warmup_models()
        
        logger.info("애플리케이션 시작 완료")
        
    except Exception as e:
        log_error(e, {"operation": "application_startup"})
        raise RuntimeError(f"애플리케이션 시작 실패: {str(e)}")
    
    yield
    
    # 종료 시 실행
    logger.info("애플리케이션 종료 중...")
    
    try:
        await model_manager.shutdown_models()
        logger.info("애플리케이션 종료 완료")
        
    except Exception as e:
        log_error(e, {"operation": "application_shutdown"})


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="InsightFace 기반 얼굴 분석 API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.debug else None
)


# 미들웨어 설정
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=settings.get_cors_methods(),
        allow_headers=settings.get_cors_headers(),
    )


# 신뢰할 수 있는 호스트 설정 (프로덕션 환경)
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # 실제 환경에서는 구체적인 호스트 지정
    )


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """요청 처리 미들웨어"""
    start_time = time.time()
    
    # 요청 크기 제한
    if hasattr(request, "headers"):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_image_size * 2:  # 여유분 포함
            return JSONResponse(
                status_code=413,
                content={"error": "요청 크기가 너무 큽니다"}
            )
    
    try:
        response = await call_next(request)
        
        # 요청 로깅
        processing_time = time.time() - start_time
        log_request(
            method=request.method,
            url=str(request.url.path),
            status_code=response.status_code,
            processing_time=processing_time,
            client_ip=request.client.host if request.client else "unknown"
        )
        
        # 응답 헤더에 처리 시간 추가
        response.headers["X-Processing-Time"] = f"{processing_time:.3f}"
        
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        log_error(e, {
            "method": request.method,
            "url": str(request.url.path),
            "processing_time": processing_time,
            "client_ip": request.client.host if request.client else "unknown"
        })
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "내부 서버 오류가 발생했습니다"
                }
            }
        )


# API 키 인증 미들웨어 (선택사항)
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """API 키 인증 미들웨어"""
    
    # API 키가 비활성화된 경우 스킵
    if not settings.api_key_enabled:
        return await call_next(request)
    
    # 헬스체크 엔드포인트는 인증 제외
    if request.url.path in ["/health", "/ping", "/live", "/ready"]:
        return await call_next(request)
    
    # API 키 확인
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != settings.api_key:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "유효하지 않은 API 키입니다"
                }
            }
        )
    
    return await call_next(request)


# 라우터 등록
app.include_router(
    faces.router,
    tags=["faces"],
    responses={
        400: {"description": "잘못된 요청"},
        401: {"description": "인증 실패"},
        413: {"description": "요청 크기 초과"},
        422: {"description": "처리할 수 없는 엔터티"},
        500: {"description": "내부 서버 오류"}
    }
)

app.include_router(
    health.router,
    tags=["monitoring"],
    responses={
        503: {"description": "서비스 사용 불가"}
    }
)


# 글로벌 예외 처리
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 처리"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail
            }
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """값 오류 처리"""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": str(exc)
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    log_error(exc, {
        "method": request.method,
        "url": str(request.url.path),
        "client_ip": request.client.host if request.client else "unknown"
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "내부 서버 오류가 발생했습니다"
            }
        }
    )


# 루트 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "문서는 비활성화되었습니다",
        "health": "/health"
    }


# 개발 서버 실행 (직접 실행 시)
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True
    )
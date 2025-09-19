"""
로깅 설정 및 관리
"""
import sys
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from .config import settings


def setup_logging():
    """로깅 설정 초기화"""
    
    # 기본 로거 제거
    logger.remove()
    
    # 콘솔 로거 추가
    logger.add(
        sys.stdout,
        level=settings.log_level.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True
    )
    
    # 파일 로거 추가
    if settings.log_file:
        logger.add(
            settings.log_file,
            level=settings.log_level.upper(),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression="zip",
            serialize=settings.log_format == "json"
        )
    
    return logger


def get_logger(name: str = None):
    """로거 인스턴스 반환"""
    if name:
        return logger.bind(name=name)
    return logger


def log_request(method: str, url: str, status_code: int, processing_time: float, **kwargs):
    """API 요청 로깅"""
    log_data = {
        "method": method,
        "url": url,
        "status_code": status_code,
        "processing_time_ms": round(processing_time * 1000, 2),
        **kwargs
    }
    
    if status_code >= 400:
        logger.error(f"Request failed: {method} {url}", **log_data)
    elif processing_time > 2.0:  # 2초 이상
        logger.warning(f"Slow request: {method} {url}", **log_data)
    else:
        logger.info(f"Request: {method} {url}", **log_data)


def log_model_performance(
    operation: str, 
    processing_time: float, 
    image_count: int = 1, 
    **kwargs
):
    """모델 성능 로깅"""
    log_data = {
        "operation": operation,
        "processing_time_ms": round(processing_time * 1000, 2),
        "image_count": image_count,
        "avg_time_per_image": round((processing_time / image_count) * 1000, 2),
        **kwargs
    }
    
    if processing_time > 5.0:  # 5초 이상
        logger.warning(f"Slow model operation: {operation}", **log_data)
    else:
        logger.info(f"Model operation: {operation}", **log_data)


def log_error(error: Exception, context: Dict[str, Any] = None):
    """에러 로깅"""
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {}
    }
    
    logger.error(f"Error occurred: {type(error).__name__}: {str(error)}", **log_data)


# 로깅 초기화
setup_logging()
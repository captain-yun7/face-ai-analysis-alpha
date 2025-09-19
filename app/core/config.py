"""
애플리케이션 설정 관리
"""
import os
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 애플리케이션 설정
    app_name: str = "Face Analysis API"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "info"
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    
    # 모델 설정
    model_name: str = "buffalo_l"
    model_root: str = "~/.insightface/models"
    use_gpu: bool = False
    gpu_device_id: int = 0
    
    # 보안 설정
    api_key_enabled: bool = False
    api_key: Optional[str] = None
    secret_key: str = "your-secret-key-for-jwt"
    
    # 캐시 설정
    cache_enabled: bool = True
    cache_ttl: int = 3600
    redis_url: str = "redis://localhost:6379/0"
    
    # 로깅 설정
    log_file: str = "logs/app.log"
    log_rotation: str = "1d"
    log_retention: str = "30d"
    log_format: str = "json"
    
    # 성능 설정
    max_image_size: int = 10 * 1024 * 1024  # 10MB
    max_batch_size: int = 10
    processing_timeout: int = 30
    max_concurrent_requests: int = 100
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_per_day: int = 10000
    
    # 모니터링 설정
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_enabled: bool = True
    
    # CORS 설정
    cors_enabled: bool = True
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    cors_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    cors_headers: str = "*"
    
    # 데이터베이스 설정 (선택사항)
    database_url: str = "sqlite:///./face_analysis.db"
    
    # 스토리지 설정
    temp_storage_path: str = "/tmp/face-api"
    cleanup_temp_files: bool = True
    max_temp_file_age: int = 3600  # 1시간
    
    # 기능 플래그
    enable_face_detection: bool = True
    enable_face_comparison: bool = True
    enable_batch_processing: bool = True
    enable_face_tracking: bool = True
    enable_embedding_extraction: bool = True
    
    # 개발 설정
    reload_on_change: bool = True
    debug_mode: bool = True
    profile_requests: bool = False
    
    @validator("model_root")
    def expand_model_root(cls, v):
        """모델 경로 확장"""
        return str(Path(v).expanduser().resolve())
    
    @validator("temp_storage_path")
    def create_temp_storage(cls, v):
        """임시 저장소 디렉토리 생성"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    def get_cors_origins(self) -> List[str]:
        """CORS origins 목록 반환"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins if self.cors_origins else []
    
    def get_cors_methods(self) -> List[str]:
        """CORS methods 목록 반환"""
        if isinstance(self.cors_methods, str):
            return [method.strip() for method in self.cors_methods.split(",")]
        return self.cors_methods if self.cors_methods else ["GET", "POST"]
    
    def get_cors_headers(self) -> List[str]:
        """CORS headers 목록 반환"""
        if isinstance(self.cors_headers, str):
            return [header.strip() for header in self.cors_headers.split(",")]
        return self.cors_headers if self.cors_headers else ["*"]
    
    def get_providers(self) -> List[str]:
        """ONNX Runtime 프로바이더 목록 반환"""
        if self.use_gpu:
            return ['CUDAExecutionProvider', 'CPUExecutionProvider']
        return ['CPUExecutionProvider']
    
    def ensure_log_directory(self):
        """로그 디렉토리 생성"""
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()

# 로그 디렉토리 생성
settings.ensure_log_directory()
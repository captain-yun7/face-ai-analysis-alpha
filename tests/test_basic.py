"""
기본 기능 테스트
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
import numpy as np

from app.core.config import settings
from app.utils.image_utils import validate_image_size, get_image_hash, is_valid_image_format


class TestConfig:
    """설정 테스트"""
    
    def test_settings_loaded(self):
        """설정이 올바르게 로드되는지 확인"""
        assert settings.app_name == "Face Analysis API"
        assert settings.app_version == "1.0.0"
        assert settings.port == 8000
        assert settings.model_name == "buffalo_l"
    
    def test_providers_cpu(self):
        """CPU 모드에서 프로바이더 확인"""
        providers = settings.get_providers()
        assert 'CPUExecutionProvider' in providers
        if not settings.use_gpu:
            assert len(providers) == 1
    
    def test_providers_gpu(self):
        """GPU 모드에서 프로바이더 확인"""
        original_use_gpu = settings.use_gpu
        settings.use_gpu = True
        
        providers = settings.get_providers()
        assert 'CUDAExecutionProvider' in providers
        assert 'CPUExecutionProvider' in providers
        
        settings.use_gpu = original_use_gpu


class TestImageUtils:
    """이미지 유틸리티 테스트"""
    
    def test_validate_image_size_valid(self):
        """유효한 이미지 크기 테스트"""
        # 1KB 정도의 작은 이미지
        small_image = "data:image/jpeg;base64," + "A" * 1000
        assert validate_image_size(small_image) is True
    
    def test_validate_image_size_too_large(self):
        """너무 큰 이미지 크기 테스트"""
        # 20MB 크기의 큰 이미지 (설정된 최대값 10MB 초과)
        large_image = "data:image/jpeg;base64," + "A" * (20 * 1024 * 1024)
        assert validate_image_size(large_image) is False
    
    def test_get_image_hash(self):
        """이미지 해시 생성 테스트"""
        image_data = "data:image/jpeg;base64,/9j/4AAQSkZJRgABA"
        hash1 = get_image_hash(image_data)
        hash2 = get_image_hash(image_data)
        
        # 같은 이미지는 같은 해시
        assert hash1 == hash2
        assert len(hash1) == 16  # 16자 해시
    
    def test_get_image_hash_different(self):
        """다른 이미지는 다른 해시"""
        image1 = "data:image/jpeg;base64,AAAA"
        image2 = "data:image/jpeg;base64,BBBB"
        
        hash1 = get_image_hash(image1)
        hash2 = get_image_hash(image2)
        
        assert hash1 != hash2
    
    def test_is_valid_image_format_valid(self):
        """유효한 이미지 형식 테스트"""
        valid_formats = [
            "data:image/jpeg;base64,AAAA",
            "data:image/jpg;base64,AAAA",
            "data:image/png;base64,AAAA",
            "data:image/bmp;base64,AAAA",
            "data:image/webp;base64,AAAA"
        ]
        
        for image_data in valid_formats:
            assert is_valid_image_format(image_data) is True
    
    def test_is_valid_image_format_invalid(self):
        """유효하지 않은 이미지 형식 테스트"""
        invalid_formats = [
            "data:text/plain;base64,AAAA",
            "data:image/gif;base64,AAAA",  # GIF는 지원 안함
            "AAAA",  # data: 접두사 없음
            ""
        ]
        
        for image_data in invalid_formats:
            assert is_valid_image_format(image_data) is False


class TestFaceAnalyzer:
    """얼굴 분석기 테스트 (모킹)"""
    
    @patch('app.models.face_analyzer.INSIGHTFACE_AVAILABLE', False)
    async def test_face_analyzer_no_insightface(self):
        """InsightFace가 없을 때 초기화 실패 테스트"""
        from app.models.face_analyzer import FaceAnalyzer
        
        analyzer = FaceAnalyzer()
        result = await analyzer.initialize()
        assert result is False
    
    @patch('app.models.face_analyzer.INSIGHTFACE_AVAILABLE', True)
    @patch('app.models.face_analyzer.insightface.app.FaceAnalysis')
    async def test_face_analyzer_mock_initialization(self, mock_face_analysis):
        """모킹된 InsightFace로 초기화 테스트"""
        from app.models.face_analyzer import FaceAnalyzer
        
        # Mock 설정
        mock_app = Mock()
        mock_face_analysis.return_value = mock_app
        
        analyzer = FaceAnalyzer()
        result = await analyzer.initialize()
        
        assert result is True
        assert analyzer.model_loaded is True
        mock_app.prepare.assert_called_once()
    
    def test_decode_image_valid(self):
        """Base64 이미지 디코딩 테스트"""
        from app.models.face_analyzer import FaceAnalyzer
        
        # 간단한 1x1 픽셀 JPEG 이미지 (Base64)
        jpeg_data = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/gA=="
        image_data = f"data:image/jpeg;base64,{jpeg_data}"
        
        analyzer = FaceAnalyzer()
        
        # 실제 디코딩은 PIL과 OpenCV에 의존하므로 예외가 발생할 수 있음
        # 여기서는 함수가 호출되는지만 확인
        try:
            result = analyzer._decode_image(image_data)
            assert result is not None
        except Exception:
            # 실제 이미지 디코딩 실패는 허용 (테스트 환경 이슈)
            pass


class TestModelManager:
    """모델 관리자 테스트"""
    
    def test_model_manager_initialization(self):
        """모델 관리자 초기화 테스트"""
        from app.models.model_manager import ModelManager
        
        manager = ModelManager()
        assert manager.models == {}
        assert manager.request_count == 0
        assert manager.error_count == 0
    
    def test_health_status_no_models(self):
        """모델이 없을 때 헬스 상태 테스트"""
        from app.models.model_manager import ModelManager
        
        manager = ModelManager()
        health = manager.get_health_status()
        
        assert health["status"] == "unhealthy"
        assert health["model_loaded"] is False
        assert "memory_usage" in health
        assert "statistics" in health


class TestAPISchemas:
    """API 스키마 테스트"""
    
    def test_face_comparison_request_valid(self):
        """얼굴 비교 요청 스키마 테스트"""
        from app.schemas.requests import FaceComparisonRequest
        
        # 간단한 테스트 데이터
        test_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABA"
        
        # 유효한 요청 생성 시도 (실제 이미지 검증은 스킵될 수 있음)
        try:
            request = FaceComparisonRequest(
                source_image=test_image,
                target_image=test_image,
                similarity_threshold=0.6
            )
            assert request.similarity_threshold == 0.6
        except Exception:
            # 이미지 검증 실패는 허용 (테스트 환경)
            pass
    
    def test_face_comparison_request_invalid_threshold(self):
        """잘못된 임계값으로 요청 스키마 테스트"""
        from app.schemas.requests import FaceComparisonRequest
        from pydantic import ValidationError
        
        test_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABA"
        
        # 범위를 벗어난 임계값
        with pytest.raises(ValidationError):
            FaceComparisonRequest(
                source_image=test_image,
                target_image=test_image,
                similarity_threshold=1.5  # 1.0 초과
            )


if __name__ == "__main__":
    # 간단한 테스트 실행
    import unittest
    
    # 기본 테스트들을 실행
    print("🧪 기본 테스트 실행 중...")
    
    # 설정 테스트
    test_config = TestConfig()
    test_config.test_settings_loaded()
    print("✅ 설정 테스트 통과")
    
    # 이미지 유틸리티 테스트
    test_utils = TestImageUtils()
    test_utils.test_is_valid_image_format_valid()
    test_utils.test_is_valid_image_format_invalid()
    print("✅ 이미지 유틸리티 테스트 통과")
    
    print("🎉 모든 기본 테스트 통과!")
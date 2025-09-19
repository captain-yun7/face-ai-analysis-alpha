"""
이미지 처리 유틸리티
"""
import io
import base64
import hashlib
from typing import Tuple, Optional
import numpy as np
from PIL import Image
import cv2

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


def validate_image_size(image_data: str) -> bool:
    """이미지 크기 검증"""
    try:
        # Base64 데이터 크기 확인
        if image_data.startswith('data:image/'):
            _, data = image_data.split(',', 1)
        else:
            data = image_data
        
        # Base64 디코딩된 크기 계산 (대략적)
        data_size = len(data) * 3 / 4  # Base64는 원본의 4/3 크기
        
        return data_size <= settings.max_image_size
        
    except Exception as e:
        logger.error(f"이미지 크기 검증 실패: {e}")
        return False


def get_image_hash(image_data: str) -> str:
    """이미지 해시 생성 (개인정보 보호)"""
    try:
        if image_data.startswith('data:image/'):
            _, data = image_data.split(',', 1)
        else:
            data = image_data
        
        # SHA256 해시 생성
        hash_obj = hashlib.sha256(data.encode('utf-8'))
        return hash_obj.hexdigest()[:16]  # 처음 16자만 사용
        
    except Exception as e:
        logger.error(f"이미지 해시 생성 실패: {e}")
        return "unknown"


def decode_base64_image(image_data: str) -> np.ndarray:
    """Base64 이미지를 OpenCV 형식으로 디코딩"""
    try:
        # data:image/jpeg;base64, 제거
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',')[1]
        
        # Base64 디코딩
        image_bytes = base64.b64decode(image_data)
        
        # PIL로 이미지 로드
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # RGB로 변환 (RGBA인 경우)
        if pil_image.mode == 'RGBA':
            pil_image = pil_image.convert('RGB')
        elif pil_image.mode == 'L':  # 그레이스케일
            pil_image = pil_image.convert('RGB')
        
        # OpenCV 형식으로 변환 (BGR)
        opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        return opencv_image
        
    except Exception as e:
        raise ValueError(f"이미지 디코딩 실패: {str(e)}")


def encode_image_to_base64(image: np.ndarray, format: str = 'JPEG') -> str:
    """OpenCV 이미지를 Base64로 인코딩"""
    try:
        # OpenCV BGR을 RGB로 변환
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # PIL 이미지로 변환
        pil_image = Image.fromarray(rgb_image)
        
        # Base64로 인코딩
        buffer = io.BytesIO()
        pil_image.save(buffer, format=format)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/{format.lower()};base64,{img_str}"
        
    except Exception as e:
        raise ValueError(f"이미지 인코딩 실패: {str(e)}")


def resize_image(image: np.ndarray, max_width: int = 1024, max_height: int = 1024) -> np.ndarray:
    """이미지 리사이징"""
    try:
        height, width = image.shape[:2]
        
        # 리사이징이 필요한지 확인
        if width <= max_width and height <= max_height:
            return image
        
        # 비율 유지하면서 리사이징
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        logger.info(f"이미지 리사이징: {width}x{height} -> {new_width}x{new_height}")
        
        return resized
        
    except Exception as e:
        logger.error(f"이미지 리사이징 실패: {e}")
        return image


def crop_face_region(image: np.ndarray, bbox: dict, padding: float = 0.2) -> np.ndarray:
    """얼굴 영역 크롭"""
    try:
        height, width = image.shape[:2]
        
        x = int(bbox['x'])
        y = int(bbox['y'])
        w = int(bbox['width'])
        h = int(bbox['height'])
        
        # 패딩 추가
        pad_w = int(w * padding)
        pad_h = int(h * padding)
        
        x1 = max(0, x - pad_w)
        y1 = max(0, y - pad_h)
        x2 = min(width, x + w + pad_w)
        y2 = min(height, y + h + pad_h)
        
        cropped = image[y1:y2, x1:x2]
        
        return cropped
        
    except Exception as e:
        logger.error(f"얼굴 크롭 실패: {e}")
        return image


def enhance_image_quality(image: np.ndarray) -> np.ndarray:
    """이미지 품질 향상"""
    try:
        # 히스토그램 평활화
        if len(image.shape) == 3:
            # 컬러 이미지
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l)
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        else:
            # 그레이스케일 이미지
            enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(image)
        
        # 노이즈 제거
        enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        return enhanced
        
    except Exception as e:
        logger.error(f"이미지 품질 향상 실패: {e}")
        return image


def get_image_info(image_data: str) -> dict:
    """이미지 정보 추출"""
    try:
        image = decode_base64_image(image_data)
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) == 3 else 1
        
        # 파일 크기 추정
        if image_data.startswith('data:image/'):
            _, data = image_data.split(',', 1)
        else:
            data = image_data
        
        file_size = len(data) * 3 // 4  # Base64 크기에서 원본 크기 추정
        
        return {
            "width": width,
            "height": height,
            "channels": channels,
            "file_size_bytes": file_size,
            "format": "RGB" if channels == 3 else "GRAY",
            "hash": get_image_hash(image_data)
        }
        
    except Exception as e:
        logger.error(f"이미지 정보 추출 실패: {e}")
        return {
            "error": str(e)
        }


def create_thumbnail(image: np.ndarray, size: Tuple[int, int] = (200, 200)) -> np.ndarray:
    """썸네일 생성"""
    try:
        height, width = image.shape[:2]
        
        # 비율 유지하면서 썸네일 크기 계산
        aspect_ratio = width / height
        
        if aspect_ratio > 1:  # 가로가 더 긴 경우
            new_width = size[0]
            new_height = int(size[0] / aspect_ratio)
        else:  # 세로가 더 긴 경우
            new_height = size[1]
            new_width = int(size[1] * aspect_ratio)
        
        thumbnail = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return thumbnail
        
    except Exception as e:
        logger.error(f"썸네일 생성 실패: {e}")
        return image


def is_valid_image_format(image_data: str) -> bool:
    """지원되는 이미지 형식인지 확인"""
    try:
        if not image_data.startswith('data:image/'):
            return False
        
        # MIME 타입 추출
        mime_type = image_data.split(';')[0].split(':')[1]
        
        supported_formats = [
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'image/bmp',
            'image/webp'
        ]
        
        return mime_type.lower() in supported_formats
        
    except Exception:
        return False
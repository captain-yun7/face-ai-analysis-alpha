"""
API 요청 스키마 정의
"""
from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator
import base64
import io
from PIL import Image


class ImageData(BaseModel):
    """이미지 데이터 스키마"""
    image: str = Field(..., description="Base64 인코딩된 이미지 데이터")
    
    @validator("image")
    def validate_image_format(cls, v):
        """이미지 포맷 검증"""
        if not v.startswith("data:image/"):
            raise ValueError("이미지는 data:image/ 형식이어야 합니다")
        
        try:
            # Base64 데이터 추출
            header, data = v.split(",", 1)
            image_bytes = base64.b64decode(data)
            
            # PIL로 이미지 검증
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()
            
        except Exception as e:
            raise ValueError(f"올바르지 않은 이미지 형식입니다: {str(e)}")
        
        return v


class FaceComparisonRequest(BaseModel):
    """얼굴 비교 요청"""
    source_image: str = Field(..., description="원본 이미지 (Base64)")
    target_image: str = Field(..., description="비교할 이미지 (Base64)")
    similarity_threshold: float = Field(
        default=0.01, 
        ge=0.0, 
        le=1.0, 
        description="유사도 임계값 (0.0-1.0)"
    )
    
    @validator("source_image", "target_image")
    def validate_images(cls, v):
        """이미지 유효성 검사"""
        return ImageData(image=v).image


class FaceDetectionRequest(BaseModel):
    """얼굴 감지 요청"""
    image: str = Field(..., description="분석할 이미지 (Base64)")
    include_landmarks: bool = Field(default=False, description="랜드마크 포함 여부")
    include_attributes: bool = Field(default=True, description="속성 분석 포함 여부")
    max_faces: int = Field(default=10, ge=1, le=50, description="최대 감지할 얼굴 수")
    
    @validator("image")
    def validate_image(cls, v):
        """이미지 유효성 검사"""
        return ImageData(image=v).image


class BatchImage(BaseModel):
    """배치 처리용 이미지"""
    id: str = Field(..., description="이미지 식별자")
    image: str = Field(..., description="이미지 데이터 (Base64)")
    name: Optional[str] = Field(None, description="이미지 이름")
    
    @validator("image")
    def validate_image(cls, v):
        """이미지 유효성 검사"""
        return ImageData(image=v).image


class BatchAnalysisRequest(BaseModel):
    """배치 분석 요청"""
    images: List[BatchImage] = Field(..., min_items=2, max_items=20, description="분석할 이미지들")
    analysis_type: str = Field(
        ..., 
        pattern="^(similarity_matrix|find_best_match|group_similar)$",
        description="분석 유형"
    )
    similarity_threshold: float = Field(
        default=0.6, 
        ge=0.0, 
        le=1.0, 
        description="유사도 임계값"
    )


class FaceTrackingFrame(BaseModel):
    """얼굴 추적용 프레임"""
    timestamp: int = Field(..., ge=0, description="타임스탬프 (ms)")
    image: str = Field(..., description="프레임 이미지 (Base64)")
    
    @validator("image")
    def validate_image(cls, v):
        """이미지 유효성 검사"""
        return ImageData(image=v).image


class FaceTrackingRequest(BaseModel):
    """얼굴 추적 요청"""
    frames: List[FaceTrackingFrame] = Field(
        ..., 
        min_items=2, 
        max_items=100, 
        description="추적할 프레임들"
    )
    track_identity: bool = Field(default=True, description="신원 추적 여부")
    min_track_length: int = Field(default=3, ge=2, description="최소 추적 길이")


class EmbeddingExtractionRequest(BaseModel):
    """임베딩 추출 요청"""
    image: str = Field(..., description="이미지 (Base64)")
    face_id: int = Field(default=0, ge=0, description="얼굴 ID (여러 얼굴 중 선택)")
    normalize: bool = Field(default=True, description="임베딩 정규화 여부")
    
    @validator("image")
    def validate_image(cls, v):
        """이미지 유효성 검사"""
        return ImageData(image=v).image


class FamilySimilarityRequest(BaseModel):
    """가족 유사도 분석 요청"""
    parent_image: str = Field(..., description="부모 이미지 (Base64)")
    child_image: str = Field(..., description="자녀 이미지 (Base64)")
    parent_age: Optional[int] = Field(None, ge=0, le=120, description="부모 나이 (선택사항)")
    child_age: Optional[int] = Field(None, ge=0, le=120, description="자녀 나이 (선택사항)")
    
    @validator("parent_image", "child_image")
    def validate_images(cls, v):
        """이미지 유효성 검사"""
        return ImageData(image=v).image


class FindMostSimilarParentRequest(BaseModel):
    """여러 부모 중 가장 닮은 부모 찾기 요청"""
    child_image: str = Field(..., description="자녀 이미지 (Base64)")
    parent_images: List[str] = Field(..., min_items=2, max_items=10, description="부모 후보 이미지들 (Base64)")
    child_age: Optional[int] = Field(None, ge=0, le=120, description="자녀 나이 (선택사항)")
    use_family_analysis: bool = Field(default=True, description="가족 특화 분석 사용 여부")
    
    @validator("child_image")
    def validate_child_image(cls, v):
        """자녀 이미지 유효성 검사"""
        return ImageData(image=v).image
    
    @validator("parent_images")
    def validate_parent_images(cls, v):
        """부모 이미지들 유효성 검사"""
        validated_images = []
        for i, image in enumerate(v):
            try:
                validated_image = ImageData(image=image).image
                validated_images.append(validated_image)
            except ValueError as e:
                raise ValueError(f"부모 이미지 {i+1}번이 올바르지 않습니다: {str(e)}")
        return validated_images


class ConfigUpdateRequest(BaseModel):
    """설정 업데이트 요청 (관리자용)"""
    use_gpu: Optional[bool] = None
    max_batch_size: Optional[int] = Field(None, ge=1, le=50)
    processing_timeout: Optional[int] = Field(None, ge=1, le=300)
    cache_enabled: Optional[bool] = None
    rate_limit_enabled: Optional[bool] = None
    
    class Config:
        extra = "forbid"  # 추가 필드 금지
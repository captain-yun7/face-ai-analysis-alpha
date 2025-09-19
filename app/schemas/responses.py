"""
API 응답 스키마 정의
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class BoundingBox(BaseModel):
    """바운딩 박스"""
    x: float = Field(..., description="X 좌표")
    y: float = Field(..., description="Y 좌표") 
    width: float = Field(..., description="너비")
    height: float = Field(..., description="높이")


class Landmark(BaseModel):
    """얼굴 랜드마크"""
    x: float = Field(..., description="X 좌표")
    y: float = Field(..., description="Y 좌표")
    type: str = Field(..., description="랜드마크 타입")


class Emotion(BaseModel):
    """감정 분석 결과"""
    emotion: str = Field(..., description="감정명")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")


class Gender(BaseModel):
    """성별 분석 결과"""
    value: str = Field(..., description="성별 (Male/Female)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")


class FaceDetail(BaseModel):
    """얼굴 상세 정보"""
    bounding_box: BoundingBox
    confidence: float = Field(..., ge=0.0, le=1.0, description="얼굴 감지 신뢰도")
    age: Optional[int] = Field(None, ge=0, le=120, description="추정 나이")
    gender: Optional[Gender] = None
    emotions: Optional[List[Emotion]] = None
    landmarks: Optional[List[Landmark]] = None
    embedding: Optional[List[float]] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="이미지 품질 점수")


class FaceMatch(BaseModel):
    """얼굴 매칭 결과"""
    similarity: float = Field(..., ge=0.0, le=1.0, description="유사도 (0.0-1.0)")
    bounding_box: BoundingBox
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
    landmarks: Optional[List[Landmark]] = None


class ResponseMetadata(BaseModel):
    """응답 메타데이터"""
    processing_time_ms: float = Field(..., description="처리 시간 (밀리초)")
    model_version: str = Field(..., description="모델 버전")
    request_id: str = Field(..., description="요청 ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="처리 시간")


class BaseResponse(BaseModel):
    """기본 응답 형식"""
    success: bool = Field(..., description="성공 여부")
    metadata: Optional[ResponseMetadata] = None


class ErrorResponse(BaseResponse):
    """에러 응답"""
    success: bool = Field(default=False)
    error: Dict[str, Any] = Field(..., description="에러 정보")


class FaceComparisonResponse(BaseResponse):
    """얼굴 비교 응답"""
    data: Optional[Dict[str, Any]] = Field(None, description="비교 결과")
    
    class ComparisonData(BaseModel):
        similarity: float = Field(..., ge=0.0, le=1.0, description="전체 유사도")
        confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
        face_matches: List[FaceMatch] = Field(..., description="매칭된 얼굴들")
        source_face: Optional[FaceDetail] = Field(None, description="원본 얼굴")
        target_faces: List[FaceDetail] = Field(..., description="대상 얼굴들")


class FaceDetectionResponse(BaseResponse):
    """얼굴 감지 응답"""
    data: Optional[Dict[str, Any]] = Field(None, description="감지 결과")
    
    class DetectionData(BaseModel):
        faces: List[FaceDetail] = Field(..., description="감지된 얼굴들")
        face_count: int = Field(..., ge=0, description="감지된 얼굴 수")


class SimilarityMatrix(BaseModel):
    """유사도 매트릭스"""
    matrix: List[List[float]] = Field(..., description="N x N 유사도 매트릭스")
    image_ids: List[str] = Field(..., description="이미지 ID 순서")


class BestMatch(BaseModel):
    """최고 매칭 결과"""
    source_id: str = Field(..., description="원본 이미지 ID")
    target_id: str = Field(..., description="매칭된 이미지 ID")
    similarity: float = Field(..., ge=0.0, le=1.0, description="유사도")


class SimilarGroup(BaseModel):
    """유사한 그룹"""
    group_id: int = Field(..., description="그룹 ID")
    members: List[str] = Field(..., description="그룹 멤버 이미지 ID들")
    avg_similarity: float = Field(..., ge=0.0, le=1.0, description="평균 유사도")


class BatchAnalysisResponse(BaseResponse):
    """배치 분석 응답"""
    data: Optional[Dict[str, Any]] = Field(None, description="배치 분석 결과")
    
    class BatchData(BaseModel):
        similarity_matrix: Optional[SimilarityMatrix] = None
        best_matches: Optional[List[BestMatch]] = None
        groups: Optional[List[SimilarGroup]] = None


class TrackFrame(BaseModel):
    """추적 프레임"""
    timestamp: int = Field(..., description="타임스탬프")
    bounding_box: BoundingBox
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")


class FaceTrack(BaseModel):
    """얼굴 추적 결과"""
    track_id: int = Field(..., description="추적 ID")
    frames: List[TrackFrame] = Field(..., description="추적된 프레임들")
    identity_confidence: float = Field(..., ge=0.0, le=1.0, description="신원 신뢰도")


class FaceTrackingResponse(BaseResponse):
    """얼굴 추적 응답"""
    data: Optional[Dict[str, Any]] = Field(None, description="추적 결과")
    
    class TrackingData(BaseModel):
        tracks: List[FaceTrack] = Field(..., description="추적된 얼굴들")


class EmbeddingResponse(BaseResponse):
    """임베딩 추출 응답"""
    data: Optional[Dict[str, Any]] = Field(None, description="임베딩 결과")
    
    class EmbeddingData(BaseModel):
        embedding: List[float] = Field(..., description="512차원 임베딩 벡터")
        bounding_box: BoundingBox
        confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
        landmarks: Optional[List[Landmark]] = None


class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str = Field(..., description="서비스 상태")
    model_loaded: bool = Field(..., description="모델 로드 상태")
    gpu_available: bool = Field(..., description="GPU 사용 가능 여부")
    memory_usage: Dict[str, Union[int, float]] = Field(..., description="메모리 사용량")
    version: str = Field(..., description="서비스 버전")
    uptime_seconds: float = Field(..., description="가동 시간")


class ModelInfoResponse(BaseModel):
    """모델 정보 응답"""
    model_name: str = Field(..., description="모델명")
    input_size: List[int] = Field(..., description="입력 이미지 크기")
    embedding_size: int = Field(..., description="임베딩 차원")
    supported_features: List[str] = Field(..., description="지원 기능 목록")
    performance_metrics: Dict[str, float] = Field(..., description="성능 지표")


class UsageStats(BaseModel):
    """사용량 통계"""
    total_requests: int = Field(..., description="총 요청 수")
    successful_requests: int = Field(..., description="성공한 요청 수")
    failed_requests: int = Field(..., description="실패한 요청 수")
    avg_processing_time_ms: float = Field(..., description="평균 처리 시간")
    requests_per_minute: float = Field(..., description="분당 요청 수")


class MetricsResponse(BaseModel):
    """메트릭 응답"""
    current_load: float = Field(..., description="현재 부하")
    queue_size: int = Field(..., description="대기열 크기")
    active_requests: int = Field(..., description="활성 요청 수")
    usage_stats: UsageStats = Field(..., description="사용량 통계")
    system_info: Dict[str, Any] = Field(..., description="시스템 정보")


class FamilySimilarityResponse(BaseResponse):
    """가족 유사도 분석 응답"""
    data: Optional[Dict[str, Any]] = Field(None, description="가족 유사도 분석 결과")
    
    class FamilyAnalysisData(BaseModel):
        family_similarity: float = Field(..., ge=0.0, le=1.0, description="가족 유사도 점수")
        base_similarity: float = Field(..., ge=0.0, le=1.0, description="기본 얼굴 유사도")
        age_corrected_similarity: float = Field(..., ge=0.0, le=1.0, description="나이 보정 유사도")
        feature_breakdown: Dict[str, float] = Field(..., description="부위별 유사도 분석")
        confidence: float = Field(..., ge=0.0, le=1.0, description="분석 신뢰도")
        explanation: Dict[str, str] = Field(..., description="부위별 설명")
        similarity_level: str = Field(..., description="유사도 수준 분류")
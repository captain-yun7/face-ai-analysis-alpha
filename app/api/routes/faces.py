"""
얼굴 분석 API 엔드포인트
"""
import time
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ...schemas.requests import (
    FaceComparisonRequest,
    FaceDetectionRequest,
    EmbeddingExtractionRequest,
    BatchAnalysisRequest,
    FamilySimilarityRequest,
    FindMostSimilarParentRequest
)
from ...schemas.responses import (
    FaceComparisonResponse,
    FaceDetectionResponse,
    EmbeddingResponse,
    BatchAnalysisResponse,
    FamilySimilarityResponse,
    FindMostSimilarParentResponse,
    ResponseMetadata
)
from ...models.model_manager import model_manager
from ...core.logging import get_logger, log_request
from ...core.config import settings

logger = get_logger(__name__)
router = APIRouter()


def create_response_metadata(processing_time: float) -> ResponseMetadata:
    """응답 메타데이터 생성"""
    return ResponseMetadata(
        processing_time_ms=round(processing_time * 1000, 2),
        model_version=settings.model_name,
        request_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow()
    )


@router.post("/compare-faces", response_model=FaceComparisonResponse)
async def compare_faces(request: FaceComparisonRequest):
    """
    두 이미지의 얼굴을 비교하여 유사도를 계산합니다.
    
    - **source_image**: 원본 이미지 (Base64 인코딩)
    - **target_image**: 비교할 이미지 (Base64 인코딩)
    - **similarity_threshold**: 유사도 임계값 (0.0-1.0)
    """
    start_time = time.time()
    
    try:
        async with model_manager.request_context("face_comparison"):
            # 얼굴 분석기 가져오기
            analyzer = model_manager.get_face_analyzer()
            
            # 얼굴 비교 수행
            result = await analyzer.compare_faces(
                source_image=request.source_image,
                target_image=request.target_image,
                threshold=request.similarity_threshold
            )
            
            processing_time = time.time() - start_time
            
            # 응답 생성
            response_data = FaceComparisonResponse(
                success=True,
                data=result,
                metadata=create_response_metadata(processing_time)
            )
            
            # 로깅
            log_request(
                method="POST",
                url="/compare-faces",
                status_code=200,
                processing_time=processing_time
            )
            
            return response_data
            
    except ValueError as e:
        # 클라이언트 오류 (잘못된 입력)
        processing_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": str(e),
                "details": {}
            }
        }
        
        log_request(
            method="POST",
            url="/compare-faces",
            status_code=400,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=400, detail=error_response)
        
    except Exception as e:
        # 서버 오류
        processing_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": {
                "code": "PROCESSING_ERROR",
                "message": "얼굴 비교 처리 중 오류가 발생했습니다",
                "details": {"original_error": str(e)}
            }
        }
        
        log_request(
            method="POST",
            url="/compare-faces",
            status_code=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=error_response)


@router.post("/detect-faces", response_model=FaceDetectionResponse)
async def detect_faces(request: FaceDetectionRequest):
    """
    이미지에서 얼굴을 감지하고 속성을 분석합니다.
    
    - **image**: 분석할 이미지 (Base64 인코딩)
    - **include_landmarks**: 랜드마크 포함 여부
    - **include_attributes**: 속성 분석 포함 여부
    - **max_faces**: 최대 감지할 얼굴 수
    """
    start_time = time.time()
    
    try:
        async with model_manager.request_context("face_detection"):
            # 얼굴 분석기 가져오기
            analyzer = model_manager.get_face_analyzer()
            
            # 얼굴 감지 수행
            result = await analyzer.detect_faces(
                image=request.image,
                include_landmarks=request.include_landmarks,
                include_attributes=request.include_attributes,
                max_faces=request.max_faces
            )
            
            # 랜드마크 제거 (요청하지 않은 경우)
            if not request.include_landmarks:
                for face in result.get("faces", []):
                    face.pop("landmarks", None)
            
            # 속성 제거 (요청하지 않은 경우)
            if not request.include_attributes:
                for face in result.get("faces", []):
                    face.pop("age", None)
                    face.pop("gender", None)
                    face.pop("emotions", None)
            
            processing_time = time.time() - start_time
            
            response_data = FaceDetectionResponse(
                success=True,
                data=result,
                metadata=create_response_metadata(processing_time)
            )
            
            # 로깅
            log_request(
                method="POST",
                url="/detect-faces",
                status_code=200,
                processing_time=processing_time
            )
            
            return response_data
            
    except ValueError as e:
        processing_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": str(e),
                "details": {}
            }
        }
        
        log_request(
            method="POST",
            url="/detect-faces",
            status_code=400,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=400, detail=error_response)
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": {
                "code": "PROCESSING_ERROR",
                "message": "얼굴 감지 처리 중 오류가 발생했습니다",
                "details": {"original_error": str(e)}
            }
        }
        
        log_request(
            method="POST",
            url="/detect-faces",
            status_code=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=error_response)


@router.post("/extract-embedding", response_model=EmbeddingResponse)
async def extract_embedding(request: EmbeddingExtractionRequest):
    """
    이미지에서 얼굴 임베딩을 추출합니다.
    
    - **image**: 이미지 (Base64 인코딩)
    - **face_id**: 얼굴 ID (여러 얼굴 중 선택)
    - **normalize**: 임베딩 정규화 여부
    """
    start_time = time.time()
    
    try:
        async with model_manager.request_context("embedding_extraction"):
            # 얼굴 분석기 가져오기
            analyzer = model_manager.get_face_analyzer()
            
            # 임베딩 추출 수행
            result = await analyzer.extract_embedding(
                image=request.image,
                face_id=request.face_id,
                normalize=request.normalize if hasattr(request, 'normalize') else True
            )
            
            processing_time = time.time() - start_time
            
            response_data = EmbeddingResponse(
                success=True,
                data=result,
                metadata=create_response_metadata(processing_time)
            )
            
            # 로깅
            log_request(
                method="POST",
                url="/extract-embedding",
                status_code=200,
                processing_time=processing_time
            )
            
            return response_data
            
    except ValueError as e:
        processing_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": str(e),
                "details": {}
            }
        }
        
        log_request(
            method="POST",
            url="/extract-embedding",
            status_code=400,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=400, detail=error_response)
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": {
                "code": "PROCESSING_ERROR",
                "message": "임베딩 추출 처리 중 오류가 발생했습니다",
                "details": {"original_error": str(e)}
            }
        }
        
        log_request(
            method="POST",
            url="/extract-embedding",
            status_code=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=error_response)


@router.post("/batch-analysis", response_model=BatchAnalysisResponse)
async def batch_analysis(request: BatchAnalysisRequest):
    """
    배치 얼굴 분석을 수행합니다.
    
    - **images**: 분석할 이미지들
    - **analysis_type**: 분석 유형 (similarity_matrix, find_best_match, group_similar)
    - **similarity_threshold**: 유사도 임계값
    """
    start_time = time.time()
    
    try:
        async with model_manager.request_context("batch_analysis"):
            # 배치 크기 제한
            if len(request.images) > settings.max_batch_size:
                raise ValueError(f"배치 크기가 최대값을 초과했습니다 (최대 {settings.max_batch_size}개)")
            
            # 얼굴 분석기 가져오기
            analyzer = model_manager.get_face_analyzer()
            
            # 각 이미지에서 임베딩 추출
            embeddings = {}
            face_info = {}
            
            for img in request.images:
                try:
                    result = await analyzer.extract_embedding(img.image, face_id=0)
                    embeddings[img.id] = result["embedding"]
                    face_info[img.id] = {
                        "name": img.name,
                        "bounding_box": result["bounding_box"],
                        "confidence": result["confidence"]
                    }
                except Exception as e:
                    logger.warning(f"이미지 {img.id} 처리 실패: {e}")
                    continue
            
            if len(embeddings) < 2:
                raise ValueError("최소 2개의 유효한 얼굴 이미지가 필요합니다")
            
            # 분석 유형에 따른 처리
            result = {}
            
            if request.analysis_type == "similarity_matrix":
                result = await _create_similarity_matrix(embeddings)
            elif request.analysis_type == "find_best_match":
                result = await _find_best_matches(embeddings, request.similarity_threshold)
            elif request.analysis_type == "group_similar":
                result = await _group_similar_faces(embeddings, request.similarity_threshold)
            
            processing_time = time.time() - start_time
            
            response_data = BatchAnalysisResponse(
                success=True,
                data=result,
                metadata=create_response_metadata(processing_time)
            )
            
            # 로깅
            log_request(
                method="POST",
                url="/batch-analysis",
                status_code=200,
                processing_time=processing_time
            )
            
            return response_data
            
    except ValueError as e:
        processing_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": str(e),
                "details": {}
            }
        }
        
        log_request(
            method="POST",
            url="/batch-analysis",
            status_code=400,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=400, detail=error_response)
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": {
                "code": "PROCESSING_ERROR",
                "message": "배치 분석 처리 중 오류가 발생했습니다",
                "details": {"original_error": str(e)}
            }
        }
        
        log_request(
            method="POST",
            url="/batch-analysis",
            status_code=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=error_response)


@router.post("/compare-family-faces", response_model=FamilySimilarityResponse)
async def compare_family_faces(request: FamilySimilarityRequest):
    """
    부모-자녀 가족 유사도 분석을 수행합니다.
    
    - **parent_image**: 부모 이미지 (Base64 인코딩)
    - **child_image**: 자녀 이미지 (Base64 인코딩)  
    - **parent_age**: 부모 나이 (선택사항, 보정에 사용)
    - **child_age**: 자녀 나이 (선택사항, 보정에 사용)
    """
    start_time = time.time()
    
    try:
        async with model_manager.request_context("family_similarity_analysis"):
            # 얼굴 분석기 가져오기
            analyzer = model_manager.get_face_analyzer()
            
            # 가족 유사도 분석 수행
            result = await analyzer.analyze_family_similarity(
                parent_image=request.parent_image,
                child_image=request.child_image,
                parent_age=request.parent_age,
                child_age=request.child_age
            )
            
            processing_time = time.time() - start_time
            
            # 응답 생성
            response_data = FamilySimilarityResponse(
                success=True,
                data=result,
                metadata=create_response_metadata(processing_time)
            )
            
            # 로깅
            log_request(
                method="POST",
                url="/compare-family-faces",
                status_code=200,
                processing_time=processing_time
            )
            
            return response_data
            
    except ValueError as e:
        # 클라이언트 오류 (잘못된 입력)
        processing_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": str(e),
                "details": {}
            }
        }
        
        log_request(
            method="POST",
            url="/compare-family-faces",
            status_code=400,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=400, detail=error_response)
        
    except Exception as e:
        # 서버 오류
        processing_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": {
                "code": "PROCESSING_ERROR",
                "message": "가족 유사도 분석 처리 중 오류가 발생했습니다",
                "details": {"original_error": str(e)}
            }
        }
        
        log_request(
            method="POST",
            url="/compare-family-faces",
            status_code=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=error_response)


@router.post("/find-most-similar-parent", response_model=FindMostSimilarParentResponse)
async def find_most_similar_parent(request: FindMostSimilarParentRequest):
    """
    여러 부모 중 가장 닮은 부모를 찾습니다.
    
    - **child_image**: 자녀 이미지 (Base64 인코딩)
    - **parent_images**: 부모 후보 이미지들 (Base64 인코딩, 2-10개)
    - **child_age**: 자녀 나이 (선택사항)
    - **use_family_analysis**: 가족 특화 분석 사용 여부
    """
    start_time = time.time()
    
    try:
        async with model_manager.request_context("find_most_similar_parent"):
            # 얼굴 분석기 가져오기
            analyzer = model_manager.get_face_analyzer()
            
            # 부모 찾기 분석 수행
            result = await analyzer.find_most_similar_parent(
                child_image=request.child_image,
                parent_images=request.parent_images,
                child_age=request.child_age,
                use_family_analysis=request.use_family_analysis
            )
            
            processing_time = time.time() - start_time
            
            # 응답 생성
            response_data = FindMostSimilarParentResponse(
                success=True,
                data=result,
                metadata=create_response_metadata(processing_time)
            )
            
            # 로깅
            log_request(
                method="POST",
                url="/find-most-similar-parent",
                status_code=200,
                processing_time=processing_time
            )
            
            return response_data
            
    except ValueError as e:
        # 클라이언트 오류 (잘못된 입력)
        processing_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": str(e),
                "details": {}
            }
        }
        
        log_request(
            method="POST",
            url="/find-most-similar-parent",
            status_code=400,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=400, detail=error_response)
        
    except Exception as e:
        # 서버 오류
        processing_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": {
                "code": "PROCESSING_ERROR",
                "message": "부모 찾기 분석 처리 중 오류가 발생했습니다",
                "details": {"original_error": str(e)}
            }
        }
        
        log_request(
            method="POST",
            url="/find-most-similar-parent",
            status_code=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=error_response)


async def _create_similarity_matrix(embeddings: Dict[str, list]) -> Dict[str, Any]:
    """유사도 매트릭스 생성"""
    import numpy as np
    
    image_ids = list(embeddings.keys())
    n = len(image_ids)
    matrix = [[0.0] * n for _ in range(n)]
    
    for i, id1 in enumerate(image_ids):
        for j, id2 in enumerate(image_ids):
            if i == j:
                matrix[i][j] = 1.0
            else:
                # 코사인 유사도 계산
                emb1 = np.array(embeddings[id1])
                emb2 = np.array(embeddings[id2])
                similarity = float(np.dot(emb1, emb2))
                matrix[i][j] = similarity
    
    return {
        "similarity_matrix": {
            "matrix": matrix,
            "image_ids": image_ids
        }
    }


async def _find_best_matches(embeddings: Dict[str, list], threshold: float) -> Dict[str, Any]:
    """최고 매칭 찾기"""
    import numpy as np
    
    best_matches = []
    image_ids = list(embeddings.keys())
    
    for i, id1 in enumerate(image_ids):
        best_similarity = 0.0
        best_match = None
        
        for j, id2 in enumerate(image_ids):
            if i != j:
                emb1 = np.array(embeddings[id1])
                emb2 = np.array(embeddings[id2])
                similarity = float(np.dot(emb1, emb2))
                
                if similarity > best_similarity and similarity >= threshold:
                    best_similarity = similarity
                    best_match = id2
        
        if best_match:
            best_matches.append({
                "source_id": id1,
                "target_id": best_match,
                "similarity": best_similarity
            })
    
    return {"best_matches": best_matches}


async def _group_similar_faces(embeddings: Dict[str, list], threshold: float) -> Dict[str, Any]:
    """유사한 얼굴 그룹화"""
    import numpy as np
    
    image_ids = list(embeddings.keys())
    groups = []
    visited = set()
    
    for i, id1 in enumerate(image_ids):
        if id1 in visited:
            continue
        
        group = [id1]
        visited.add(id1)
        
        for j, id2 in enumerate(image_ids):
            if i != j and id2 not in visited:
                emb1 = np.array(embeddings[id1])
                emb2 = np.array(embeddings[id2])
                similarity = float(np.dot(emb1, emb2))
                
                if similarity >= threshold:
                    group.append(id2)
                    visited.add(id2)
        
        if len(group) >= 2:
            # 그룹 내 평균 유사도 계산
            similarities = []
            for x in range(len(group)):
                for y in range(x + 1, len(group)):
                    emb_x = np.array(embeddings[group[x]])
                    emb_y = np.array(embeddings[group[y]])
                    sim = float(np.dot(emb_x, emb_y))
                    similarities.append(sim)
            
            avg_similarity = np.mean(similarities) if similarities else 0.0
            
            groups.append({
                "group_id": len(groups),
                "members": group,
                "avg_similarity": float(avg_similarity)
            })
    
    return {"groups": groups}
"""
얼굴 분석 클래스 - InsightFace 기반 얼굴 분석
"""
import base64
import numpy as np
import cv2
from typing import Dict, Any, Optional, List
from io import BytesIO
from PIL import Image

from ..core.logging import get_logger

logger = get_logger(__name__)


class FaceAnalyzer:
    """InsightFace 기반 얼굴 분석기"""
    
    def __init__(self, face_analysis_app):
        self.app = face_analysis_app
        self.is_loaded = face_analysis_app is not None
    
    def _decode_base64_image(self, base64_string: str) -> np.ndarray:
        """Base64 문자열을 이미지로 디코딩"""
        try:
            # data:image/jpeg;base64, 제거
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]
            
            # Base64 디코딩
            image_data = base64.b64decode(base64_string)
            
            # PIL로 이미지 로드
            pil_image = Image.open(BytesIO(image_data))
            
            # RGB로 변환
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # OpenCV 형식으로 변환 (BGR)
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            return opencv_image
            
        except Exception as e:
            raise ValueError(f"이미지 디코딩 실패: {e}")
    
    async def compare_faces(self, source_image: str, target_image: str, threshold: float = 0.01) -> Dict[str, Any]:
        """두 얼굴 이미지 비교"""
        
        if not self.is_loaded:
            return self._dummy_compare_faces(source_image, target_image, threshold)
        
        try:
            # 이미지 디코딩
            source_img = self._decode_base64_image(source_image)
            target_img = self._decode_base64_image(target_image)
            
            # 얼굴 감지 및 임베딩 추출
            source_faces = self.app.get(source_img)
            target_faces = self.app.get(target_img)
            
            if not source_faces:
                raise ValueError("원본 이미지에서 얼굴을 찾을 수 없습니다")
            
            if not target_faces:
                raise ValueError("대상 이미지에서 얼굴을 찾을 수 없습니다")
            
            # 첫 번째 얼굴로 비교 (가장 큰 얼굴)
            source_face = source_faces[0]
            
            # 원본 얼굴 임베딩 정규화 (L2 norm)
            source_embedding = source_face.embedding / np.linalg.norm(source_face.embedding)
            
            # 각 대상 얼굴과 비교
            face_matches = []
            unmatched_faces = []
            max_similarity = 0.0
            
            for target_face in target_faces:
                # 대상 얼굴 임베딩 정규화 (L2 norm)
                target_embedding = target_face.embedding / np.linalg.norm(target_face.embedding)
                
                # 코사인 유사도 계산 (정규화된 벡터의 내적)
                similarity = float(np.dot(source_embedding, target_embedding))
                
                if similarity >= threshold:
                    face_matches.append({
                        "similarity": similarity,
                        "bounding_box": {
                            "x": float(target_face.bbox[0]),
                            "y": float(target_face.bbox[1]),
                            "width": float(target_face.bbox[2] - target_face.bbox[0]),
                            "height": float(target_face.bbox[3] - target_face.bbox[1])
                        },
                        "confidence": float(target_face.det_score),
                        "landmarks": target_face.landmark.tolist() if hasattr(target_face, 'landmark') else []
                    })
                else:
                    # 매칭되지 않은 얼굴로 분류
                    unmatched_faces.append({
                        "bounding_box": {
                            "x": float(target_face.bbox[0]),
                            "y": float(target_face.bbox[1]),
                            "width": float(target_face.bbox[2] - target_face.bbox[0]),
                            "height": float(target_face.bbox[3] - target_face.bbox[1])
                        },
                        "confidence": float(target_face.det_score)
                    })
            
            return {
                "similarity": float(max_similarity),
                "confidence": float(source_face.det_score),
                "face_matches": face_matches,
                "source_face": {
                    "bounding_box": {
                        "x": float(source_face.bbox[0]),
                        "y": float(source_face.bbox[1]),
                        "width": float(source_face.bbox[2] - source_face.bbox[0]),
                        "height": float(source_face.bbox[3] - source_face.bbox[1])
                    },
                    "confidence": float(source_face.det_score),
                    "landmarks": source_face.landmark.tolist() if hasattr(source_face, 'landmark') else []
                },
                "target_faces": [
                    {
                        "bounding_box": {
                            "x": float(face.bbox[0]),
                            "y": float(face.bbox[1]),
                            "width": float(face.bbox[2] - face.bbox[0]),
                            "height": float(face.bbox[3] - face.bbox[1])
                        },
                        "confidence": float(face.det_score)
                    }
                    for face in target_faces
                ],
                "unmatched_faces": unmatched_faces
            }
            
        except Exception as e:
            logger.error(f"얼굴 비교 중 오류: {e}")
            raise RuntimeError(f"얼굴 비교 실패: {e}")
    
    async def detect_faces(self, image: str, include_landmarks: bool = False, include_attributes: bool = True, max_faces: int = 10) -> Dict[str, Any]:
        """얼굴 감지"""
        
        if not self.is_loaded:
            return self._dummy_detect_faces(image, include_landmarks, include_attributes, max_faces)
        
        try:
            # 이미지 디코딩
            img = self._decode_base64_image(image)
            
            # 얼굴 감지
            faces = self.app.get(img)
            
            if not faces:
                return {
                    "faces": [],
                    "face_count": 0
                }
            
            # 최대 얼굴 수 제한
            faces = faces[:max_faces]
            
            detected_faces = []
            for face in faces:
                face_data = {
                    "bounding_box": {
                        "x": float(face.bbox[0]),
                        "y": float(face.bbox[1]),
                        "width": float(face.bbox[2] - face.bbox[0]),
                        "height": float(face.bbox[3] - face.bbox[1])
                    },
                    "confidence": float(face.det_score)
                }
                
                if include_landmarks and hasattr(face, 'landmark') and face.landmark is not None:
                    face_data["landmarks"] = face.landmark.tolist()
                
                if include_attributes:
                    # 나이와 성별 정보 (있다면)
                    if hasattr(face, 'age'):
                        face_data["age"] = int(face.age)
                    if hasattr(face, 'gender'):
                        face_data["gender"] = {
                            "value": "Male" if face.gender == 1 else "Female",
                            "confidence": 0.95  # InsightFace는 confidence를 제공하지 않으므로 기본값
                        }
                
                if hasattr(face, 'embedding') and face.embedding is not None:
                    face_data["embedding"] = face.embedding.tolist()
                    face_data["quality_score"] = float(np.linalg.norm(face.embedding))
                
                detected_faces.append(face_data)
            
            return {
                "faces": detected_faces,
                "face_count": len(detected_faces)
            }
            
        except Exception as e:
            logger.error(f"얼굴 감지 중 오류: {e}")
            raise RuntimeError(f"얼굴 감지 실패: {e}")
    
    async def extract_embedding(self, image: str, face_id: int = 0, normalize: bool = True) -> Dict[str, Any]:
        """얼굴 임베딩 추출"""
        
        if not self.is_loaded:
            return self._dummy_extract_embedding(image, face_id, normalize)
        
        try:
            # 이미지 디코딩
            img = self._decode_base64_image(image)
            
            # 얼굴 감지
            faces = self.app.get(img)
            
            if not faces:
                raise ValueError("이미지에서 얼굴을 찾을 수 없습니다")
            
            if face_id >= len(faces):
                raise ValueError(f"face_id {face_id}가 범위를 벗어났습니다 (감지된 얼굴: {len(faces)}개)")
            
            face = faces[face_id]
            embedding = face.embedding
            
            if normalize:
                embedding = embedding / np.linalg.norm(embedding)
            
            return {
                "embedding": embedding.tolist(),
                "bounding_box": {
                    "x": float(face.bbox[0]),
                    "y": float(face.bbox[1]),
                    "width": float(face.bbox[2] - face.bbox[0]),
                    "height": float(face.bbox[3] - face.bbox[1])
                },
                "confidence": float(face.det_score),
                "landmarks": face.landmark.tolist() if hasattr(face, 'landmark') else []
            }
            
        except Exception as e:
            logger.error(f"임베딩 추출 중 오류: {e}")
            raise RuntimeError(f"임베딩 추출 실패: {e}")
    
    def _dummy_compare_faces(self, source_image: str, target_image: str, threshold: float) -> Dict[str, Any]:
        """더미 얼굴 비교 (InsightFace 없을 때)"""
        import random
        
        # 랜덤한 유사도 생성
        similarity = random.uniform(0.1, 0.9)
        
        return {
            "similarity": similarity,
            "confidence": 0.85,
            "face_matches": [
                {
                    "similarity": similarity,
                    "bounding_box": {"x": 100, "y": 50, "width": 200, "height": 250},
                    "confidence": 0.92,
                    "landmarks": []
                }
            ] if similarity >= threshold else [],
            "source_face": {
                "bounding_box": {"x": 80, "y": 40, "width": 180, "height": 220},
                "confidence": 0.88,
                "landmarks": []
            },
            "target_faces": [
                {
                    "bounding_box": {"x": 100, "y": 50, "width": 200, "height": 250},
                    "confidence": 0.92
                }
            ],
            "unmatched_faces": []
        }
    
    def _dummy_detect_faces(self, image: str, include_landmarks: bool, include_attributes: bool, max_faces: int) -> Dict[str, Any]:
        """더미 얼굴 감지 (InsightFace 없을 때)"""
        return {
            "faces": [
                {
                    "bounding_box": {"x": 100, "y": 50, "width": 200, "height": 250},
                    "confidence": 0.95,
                    "age": 30,
                    "gender": {"value": "Male", "confidence": 0.85},
                    "landmarks": [[120, 80], [180, 80], [150, 120], [130, 160], [170, 160]] if include_landmarks else [],
                    "embedding": [0.1] * 512 if include_attributes else [],
                    "quality_score": 0.85
                }
            ],
            "face_count": 1
        }
    
    def _dummy_extract_embedding(self, image: str, face_id: int, normalize: bool) -> Dict[str, Any]:
        """더미 임베딩 추출 (InsightFace 없을 때)"""
        import random
        
        # 512차원 랜덤 임베딩 생성
        embedding = [random.uniform(-1, 1) for _ in range(512)]
        
        if normalize:
            norm = sum(x**2 for x in embedding) ** 0.5
            embedding = [x / norm for x in embedding]
        
        return {
            "embedding": embedding,
            "bounding_box": {"x": 100, "y": 50, "width": 200, "height": 250},
            "confidence": 0.95,
            "landmarks": [[120, 80], [180, 80], [150, 120], [130, 160], [170, 160]]
        }
    
    async def analyze_family_similarity(self, parent_image: str, child_image: str, parent_age: Optional[int] = None, child_age: Optional[int] = None) -> Dict[str, Any]:
        """가족 유사도 분석"""
        
        if not self.is_loaded:
            return self._dummy_family_similarity(parent_image, child_image, parent_age, child_age)
        
        try:
            # 이미지 디코딩
            parent_img = self._decode_base64_image(parent_image)
            child_img = self._decode_base64_image(child_image)
            
            # 얼굴 감지 및 임베딩 추출
            parent_faces = self.app.get(parent_img)
            child_faces = self.app.get(child_img)
            
            if not parent_faces:
                raise ValueError("부모 이미지에서 얼굴을 찾을 수 없습니다")
            
            if not child_faces:
                raise ValueError("자녀 이미지에서 얼굴을 찾을 수 없습니다")
            
            # 첫 번째 얼굴 사용 (가장 큰 얼굴)
            parent_face = parent_faces[0]
            child_face = child_faces[0]
            
            # InsightFace에서 감지한 연령 정보 추출
            detected_parent_age = int(parent_face.age) if hasattr(parent_face, 'age') else None
            detected_child_age = int(child_face.age) if hasattr(child_face, 'age') else None
            
            # 파라미터로 받은 나이가 없으면 감지된 나이 사용
            final_parent_age = parent_age or detected_parent_age
            final_child_age = child_age or detected_child_age
            
            # 디버그 로그
            logger.info(f"Detected ages - Parent: {detected_parent_age}, Child: {detected_child_age}")
            logger.info(f"Final ages - Parent: {final_parent_age}, Child: {final_child_age}")
            
            # 임베딩 정규화 (L2 norm)
            parent_embedding = parent_face.embedding / np.linalg.norm(parent_face.embedding)
            child_embedding = child_face.embedding / np.linalg.norm(child_face.embedding)
            
            # 코사인 유사도 계산 (정규화된 벡터의 내적)
            similarity = float(np.dot(parent_embedding, child_embedding))
            
            # 디버그 로그
            logger.info(f"Raw similarity score: {similarity}")
            
            # 나이 보정 (선택사항)
            age_adjusted_similarity = similarity
            if final_parent_age and final_child_age:
                # 나이 차이에 따른 보정 (실제로는 더 복잡한 알고리즘 필요)
                age_factor = max(0.5, 1.0 - abs(final_parent_age - final_child_age) * 0.01)  # 단순 보정
                age_adjusted_similarity = similarity * age_factor
            
            return {
                "similarity": float(similarity),
                "confidence": float(parent_face.det_score),
                "parent_face": {
                    "bounding_box": {
                        "x": float(parent_face.bbox[0]),
                        "y": float(parent_face.bbox[1]),
                        "width": float(parent_face.bbox[2] - parent_face.bbox[0]),
                        "height": float(parent_face.bbox[3] - parent_face.bbox[1])
                    },
                    "confidence": float(parent_face.det_score),
                    "age": detected_parent_age  # 실제 감지된 나이 반환
                },
                "child_face": {
                    "bounding_box": {
                        "x": float(child_face.bbox[0]),
                        "y": float(child_face.bbox[1]),
                        "width": float(child_face.bbox[2] - child_face.bbox[0]),
                        "height": float(child_face.bbox[3] - child_face.bbox[1])
                    },
                    "confidence": float(child_face.det_score),
                    "age": detected_child_age  # 실제 감지된 나이 반환
                }
            }
            
        except Exception as e:
            logger.error(f"가족 유사도 분석 중 오류: {e}")
            raise RuntimeError(f"가족 유사도 분석 실패: {e}")
    
    def _dummy_family_similarity(self, parent_image: str, child_image: str, parent_age: Optional[int], child_age: Optional[int]) -> Dict[str, Any]:
        """더미 가족 유사도 분석 (InsightFace 없을 때)"""
        import random
        
        similarity = random.uniform(0.3, 0.8)
        age_adjusted = similarity * random.uniform(0.9, 1.1)
        
        return {
            "similarity_score": similarity,
            "age_adjusted_similarity": age_adjusted,
            "relationship_confidence": "보통",
            "parent_face": {
                "bounding_box": {"x": 80, "y": 40, "width": 180, "height": 220},
                "confidence": 0.88,
                "age": parent_age
            },
            "child_face": {
                "bounding_box": {"x": 100, "y": 50, "width": 160, "height": 200},
                "confidence": 0.92,
                "age": child_age
            },
            "analysis": {
                "facial_features_match": similarity > 0.5,
                "recommended_threshold": 0.4,
                "confidence_level": "보통"
            }
        }
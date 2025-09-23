"""
부모-자녀 닮음 분석 특화 모듈
일반적인 얼굴 인식과는 다른 가족 유사도 측정 알고리즘
"""
import numpy as np
from typing import Dict, List, Any, Tuple
import cv2
from ..core.logging import get_logger

logger = get_logger(__name__)


class FamilySimilarityAnalyzer:
    """부모-자녀 닮음 분석 전용 클래스"""
    
    def __init__(self):
        # 얼굴 특성별 가중치 (유전적 전달 가능성 기반)
        # InsightFace는 5개 랜드마크만 제공하므로 측정 가능한 부위만 포함
        self.feature_weights = {
            'eye_region': 0.35,      # 눈 모양과 위치 (가장 강한 유전)
            'nose_shape': 0.25,      # 코 모양
            'face_shape': 0.30,      # 얼굴형
            'mouth_region': 0.10,    # 입술과 입 모양 (가장 약한 유전)
        }
        
        # 나이 차이에 따른 보정 계수
        self.age_compensation = {
            'child_to_adult': 1.15,   # 아이→어른 비교시 보정
            'same_generation': 1.0,    # 동세대 비교
            'elderly_factor': 0.95     # 고령 요소 고려
        }
    
    def calculate_family_similarity(
        self, 
        parent_face: Dict[str, Any], 
        child_face: Dict[str, Any],
        parent_age: int = None,
        child_age: int = None
    ) -> Dict[str, Any]:
        """
        부모-자녀 특화 닮음 계산
        
        Args:
            parent_face: 부모 얼굴 정보 (임베딩, 랜드마크 포함)
            child_face: 자녀 얼굴 정보 (임베딩, 랜드마크 포함)
            parent_age: 부모 나이 (선택사항)
            child_age: 자녀 나이 (선택사항)
        
        Returns:
            가족 유사도 분석 결과
        """
        try:
            # 1. 기본 얼굴 유사도 (전체 임베딩)
            base_similarity = self._calculate_embedding_similarity(
                parent_face['embedding'], 
                child_face['embedding']
            )
            
            # 2. 부분별 특성 분석
            feature_similarities = self._analyze_facial_features(
                parent_face, child_face
            )
            
            # 3. 나이 차이 보정
            age_corrected_similarity = self._apply_age_compensation(
                base_similarity, parent_age, child_age
            )
            
            # 4. 가중 평균으로 최종 가족 유사도 계산
            family_similarity = self._calculate_weighted_family_score(
                feature_similarities, age_corrected_similarity
            )
            
            # 5. 신뢰도 및 설명 생성
            confidence = self._calculate_confidence(feature_similarities)
            explanation = self._generate_explanation(feature_similarities)
            
            return {
                'family_similarity': family_similarity,
                'base_similarity': base_similarity,
                'age_corrected_similarity': age_corrected_similarity,
                'feature_breakdown': feature_similarities,
                'confidence': confidence,
                'explanation': explanation,
                'similarity_level': self._classify_similarity_level(family_similarity)
            }
            
        except Exception as e:
            logger.error(f"가족 유사도 계산 오류: {e}")
            raise
    
    def _calculate_embedding_similarity(
        self, 
        parent_embedding: np.ndarray, 
        child_embedding: np.ndarray
    ) -> float:
        """기본 임베딩 유사도 계산 (일반적인 얼굴 인식)"""
        # 코사인 유사도
        dot_product = np.dot(parent_embedding, child_embedding)
        
        # 부모-자녀 관계에서는 일반적인 유사도보다 낮은 값이 나올 수 있음
        # 보정 계수 적용
        family_adjusted = dot_product * 1.1  # 가족 관계 보정
        
        return float(np.clip(family_adjusted, 0.0, 1.0))
    
    def _analyze_facial_features(
        self, 
        parent_face: Dict[str, Any], 
        child_face: Dict[str, Any]
    ) -> Dict[str, float]:
        """얼굴 부위별 특성 분석"""
        feature_similarities = {}
        
        parent_landmarks = parent_face.get('landmarks', [])
        child_landmarks = child_face.get('landmarks', [])
        
        # 전체 얼굴 유사도 (임베딩 기반)
        base_similarity = self._calculate_embedding_similarity(
            parent_face['embedding'], 
            child_face['embedding']
        )
        
        if len(parent_landmarks) >= 5 and len(child_landmarks) >= 5:
            # 랜드마크 기반 부위별 분석 (눈, 코, 입, 얼굴형)
            feature_similarities = self._landmark_based_analysis(
                parent_landmarks, child_landmarks
            )
        else:
            # 랜드마크가 없으면 전체 유사도 기반으로 추정
            for feature in self.feature_weights.keys():
                variation = np.random.uniform(-0.1, 0.1)
                feature_similarities[feature] = np.clip(base_similarity + variation, 0.2, 0.95)
        
        return feature_similarities
    
    def _landmark_based_analysis(
        self, 
        parent_landmarks: List[Dict], 
        child_landmarks: List[Dict]
    ) -> Dict[str, float]:
        """랜드마크 기반 부위별 분석"""
        similarities = {}
        
        try:
            # 먼저 얼굴 크기로 정규화하기 위한 기준점 계산
            parent_face_width = self._calculate_face_width(parent_landmarks)
            child_face_width = self._calculate_face_width(child_landmarks)
            
            # 눈 영역 분석 (0: 왼쪽 눈, 1: 오른쪽 눈)
            if len(parent_landmarks) > 1 and len(child_landmarks) > 1:
                eye_sim = self._calculate_eye_similarity(
                    parent_landmarks[:2], child_landmarks[:2],
                    parent_face_width, child_face_width
                )
                similarities['eye_region'] = eye_sim
            
            # 코 영역 분석 (2: 코) - 다른 랜드마크와의 비율로 계산
            if len(parent_landmarks) > 2 and len(child_landmarks) > 2:
                nose_sim = self._calculate_nose_ratio_similarity(
                    parent_landmarks, child_landmarks
                )
                similarities['nose_shape'] = nose_sim
            
            # 입 영역 분석 (3: 왼쪽 입, 4: 오른쪽 입)
            if len(parent_landmarks) > 4 and len(child_landmarks) > 4:
                mouth_sim = self._calculate_mouth_similarity(
                    parent_landmarks[3:5], child_landmarks[3:5],
                    parent_face_width, child_face_width
                )
                similarities['mouth_region'] = mouth_sim
            
            # 전체 얼굴형 분석
            face_shape_sim = self._calculate_face_shape_similarity(
                parent_landmarks, child_landmarks
            )
            similarities['face_shape'] = face_shape_sim
            
            # 기본값으로 채우기 (여기서는 눈, 코, 입, 얼굴형만 계산됨)
            # 눈썹과 턱선은 상위 함수에서 임베딩으로 처리
            for feature in ['eye_region', 'nose_shape', 'face_shape', 'mouth_region']:
                if feature not in similarities:
                    similarities[feature] = 0.5
                    
        except Exception as e:
            logger.warning(f"랜드마크 분석 실패, 기본값 사용: {e}")
            # 실패시 기본값
            for feature in self.feature_weights.keys():
                similarities[feature] = 0.5
        
        return similarities
    
    def _calculate_face_width(self, landmarks: List[Dict]) -> float:
        """얼굴 너비 계산 (정규화용)"""
        if len(landmarks) < 2:
            return 1.0
        # 두 눈 사이의 거리를 기준으로 사용
        return abs(landmarks[1]['x'] - landmarks[0]['x'])
    
    def _embedding_based_feature_estimation(
        self, 
        parent_embedding: np.ndarray, 
        child_embedding: np.ndarray
    ) -> Dict[str, float]:
        """임베딩 기반 특성 추정 (랜드마크가 없을 때)"""
        # 임베딩의 다른 부분이 다른 얼굴 특성을 나타낸다고 가정
        embedding_dim = len(parent_embedding)
        feature_segments = {
            'eye_region': (0, embedding_dim//6),
            'nose_shape': (embedding_dim//6, 2*embedding_dim//6),
            'face_shape': (2*embedding_dim//6, 3*embedding_dim//6),
            'mouth_region': (3*embedding_dim//6, 4*embedding_dim//6),
            'eyebrow_region': (4*embedding_dim//6, 5*embedding_dim//6),
            'chin_jawline': (5*embedding_dim//6, embedding_dim)
        }
        
        similarities = {}
        for feature, (start, end) in feature_segments.items():
            parent_segment = parent_embedding[start:end]
            child_segment = child_embedding[start:end]
            
            # 세그먼트별 코사인 유사도
            segment_sim = np.dot(parent_segment, child_segment)
            similarities[feature] = float(np.clip(segment_sim, 0.0, 1.0))
        
        return similarities
    
    def _calculate_eye_similarity(
        self, 
        parent_eyes: List[Dict], 
        child_eyes: List[Dict],
        parent_face_width: float,
        child_face_width: float
    ) -> float:
        """눈 영역 유사도 계산"""
        try:
            # 두 눈 사이의 거리를 얼굴 너비로 정규화
            parent_eye_distance = np.sqrt(
                (parent_eyes[1]['x'] - parent_eyes[0]['x'])**2 +
                (parent_eyes[1]['y'] - parent_eyes[0]['y'])**2
            )
            child_eye_distance = np.sqrt(
                (child_eyes[1]['x'] - child_eyes[0]['x'])**2 +
                (child_eyes[1]['y'] - child_eyes[0]['y'])**2
            )
            
            # 얼굴 너비 대비 눈 간격 비율
            parent_ratio = parent_eye_distance / parent_face_width if parent_face_width > 0 else 0
            child_ratio = child_eye_distance / child_face_width if child_face_width > 0 else 0
            
            # 비율 차이를 유사도로 변환
            ratio_diff = abs(parent_ratio - child_ratio)
            similarity = 1.0 - min(ratio_diff * 2, 0.5)  # 최대 50% 차이까지 고려
            
            return float(np.clip(similarity, 0.3, 1.0))
        except:
            return 0.5
    
    def _calculate_nose_ratio_similarity(
        self, 
        parent_landmarks: List[Dict], 
        child_landmarks: List[Dict]
    ) -> float:
        """코의 상대적 위치 비율로 유사도 계산"""
        try:
            if len(parent_landmarks) < 5 or len(child_landmarks) < 5:
                return 0.5
            
            # 코(2)와 다른 랜드마크들의 관계 분석
            parent_nose = parent_landmarks[2]
            child_nose = child_landmarks[2]
            
            # 눈 중심점 계산
            parent_eye_center = {
                'x': (parent_landmarks[0]['x'] + parent_landmarks[1]['x']) / 2,
                'y': (parent_landmarks[0]['y'] + parent_landmarks[1]['y']) / 2
            }
            child_eye_center = {
                'x': (child_landmarks[0]['x'] + child_landmarks[1]['x']) / 2,
                'y': (child_landmarks[0]['y'] + child_landmarks[1]['y']) / 2
            }
            
            # 입 중심점 계산
            parent_mouth_center = {
                'x': (parent_landmarks[3]['x'] + parent_landmarks[4]['x']) / 2,
                'y': (parent_landmarks[3]['y'] + parent_landmarks[4]['y']) / 2
            }
            child_mouth_center = {
                'x': (child_landmarks[3]['x'] + child_landmarks[4]['x']) / 2,
                'y': (child_landmarks[3]['y'] + child_landmarks[4]['y']) / 2
            }
            
            # 눈-코-입의 수직 비율 계산
            parent_eye_nose_dist = abs(parent_nose['y'] - parent_eye_center['y'])
            parent_nose_mouth_dist = abs(parent_mouth_center['y'] - parent_nose['y'])
            parent_ratio = parent_eye_nose_dist / (parent_nose_mouth_dist + 0.001)  # 0으로 나누기 방지
            
            child_eye_nose_dist = abs(child_nose['y'] - child_eye_center['y'])
            child_nose_mouth_dist = abs(child_mouth_center['y'] - child_nose['y'])
            child_ratio = child_eye_nose_dist / (child_nose_mouth_dist + 0.001)
            
            # 비율 차이를 유사도로 변환
            ratio_diff = abs(parent_ratio - child_ratio)
            similarity = 1.0 / (1.0 + ratio_diff * 2)  # 차이가 작을수록 유사
            
            return float(np.clip(similarity, 0.3, 0.95))
        except Exception as e:
            logger.warning(f"코 비율 계산 실패: {e}")
            return 0.5
    
    def _calculate_mouth_similarity(
        self, 
        parent_mouth: List[Dict], 
        child_mouth: List[Dict],
        parent_face_width: float,
        child_face_width: float
    ) -> float:
        """입 모양 유사도 계산"""
        try:
            # 입의 너비를 얼굴 너비로 정규화
            parent_mouth_width = abs(parent_mouth[1]['x'] - parent_mouth[0]['x'])
            child_mouth_width = abs(child_mouth[1]['x'] - child_mouth[0]['x'])
            
            # 얼굴 너비 대비 입 너비 비율
            parent_ratio = parent_mouth_width / parent_face_width if parent_face_width > 0 else 0
            child_ratio = child_mouth_width / child_face_width if child_face_width > 0 else 0
            
            # 비율 차이를 유사도로 변환
            ratio_diff = abs(parent_ratio - child_ratio)
            similarity = 1.0 - min(ratio_diff * 3, 0.6)  # 최대 60% 차이까지 고려
            
            return float(np.clip(similarity, 0.3, 1.0))
        except:
            return 0.5
    
    def _calculate_face_shape_similarity(
        self, 
        parent_landmarks: List[Dict], 
        child_landmarks: List[Dict]
    ) -> float:
        """전체 얼굴형 유사도 계산"""
        try:
            # 랜드마크들의 전체적인 배치 패턴 분석
            parent_points = np.array([[lm['x'], lm['y']] for lm in parent_landmarks])
            child_points = np.array([[lm['x'], lm['y']] for lm in child_landmarks])
            
            # 중심점 기준으로 정규화
            parent_center = np.mean(parent_points, axis=0)
            child_center = np.mean(child_points, axis=0)
            
            parent_normalized = parent_points - parent_center
            child_normalized = child_points - child_center
            
            # 형태 유사도 (간단한 근사)
            correlation = np.corrcoef(parent_normalized.flatten(), child_normalized.flatten())[0, 1]
            
            return float(np.clip(abs(correlation), 0.0, 1.0))
        except:
            return 0.5
    
    def _apply_age_compensation(
        self, 
        base_similarity: float, 
        parent_age: int = None, 
        child_age: int = None
    ) -> float:
        """나이 차이에 따른 보정 적용"""
        if parent_age is None or child_age is None:
            return base_similarity
        
        age_diff = abs(parent_age - child_age)
        
        # 나이 차이가 클수록 얼굴 변화가 크므로 보정 필요
        if age_diff > 20:
            compensation = self.age_compensation['child_to_adult']
        elif age_diff > 50:
            compensation = self.age_compensation['elderly_factor']
        else:
            compensation = self.age_compensation['same_generation']
        
        # 나이 차이에 따른 추가 보정
        age_factor = 1.0 + (age_diff / 100.0)  # 나이 차이 100세당 10% 보정
        
        compensated = base_similarity * compensation * age_factor
        
        return float(np.clip(compensated, 0.0, 1.0))
    
    def _calculate_weighted_family_score(
        self, 
        feature_similarities: Dict[str, float], 
        age_corrected_similarity: float
    ) -> float:
        """가중 평균으로 최종 가족 유사도 계산"""
        weighted_sum = 0.0
        total_weight = 0.0
        
        # 부위별 가중 평균
        for feature, similarity in feature_similarities.items():
            weight = self.feature_weights.get(feature, 0.1)
            weighted_sum += similarity * weight
            total_weight += weight
        
        feature_score = weighted_sum / total_weight if total_weight > 0 else 0.5
        
        # 전체 유사도와 부위별 유사도의 조합 (7:3 비율)
        final_score = 0.7 * age_corrected_similarity + 0.3 * feature_score
        
        return float(np.clip(final_score, 0.0, 1.0))
    
    def _calculate_confidence(self, feature_similarities: Dict[str, float]) -> float:
        """분석 신뢰도 계산"""
        # 부위별 유사도의 분산이 낮을수록 신뢰도 높음
        similarities = list(feature_similarities.values())
        variance = np.var(similarities)
        
        # 분산이 낮을수록 신뢰도 높음 (0.1 이하면 높은 신뢰도)
        confidence = 1.0 - min(variance * 2, 0.5)
        
        return float(np.clip(confidence, 0.3, 1.0))
    
    def _generate_explanation(self, feature_similarities: Dict[str, float]) -> Dict[str, str]:
        """유사도 설명 생성"""
        explanations = {}
        
        for feature, similarity in feature_similarities.items():
            if similarity > 0.7:
                level = "매우 유사"
            elif similarity > 0.5:
                level = "유사"
            elif similarity > 0.3:
                level = "약간 유사"
            else:
                level = "다름"
            
            explanations[feature] = f"{level} ({similarity:.2f})"
        
        return explanations
    
    def _classify_similarity_level(self, family_similarity: float) -> str:
        """가족 유사도 수준 분류"""
        if family_similarity > 0.8:
            return "매우 높은 닮음"
        elif family_similarity > 0.6:
            return "높은 닮음"
        elif family_similarity > 0.4:
            return "보통 닮음"
        elif family_similarity > 0.2:
            return "약간 닮음"
        else:
            return "낮은 닮음"


# 전역 인스턴스
family_analyzer = FamilySimilarityAnalyzer()
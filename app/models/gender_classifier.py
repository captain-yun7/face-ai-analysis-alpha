"""
얼굴 기하학 기반 성별 분류기 - InsightFace landmarks를 사용한 masculinity/femininity 점수 추정
"""
import numpy as np
from typing import Dict, List, Tuple
import logging
import math

logger = logging.getLogger(__name__)


class GeometricGenderClassifier:
    """얼굴 기하학 특징 기반 성별 분류기"""
    
    def __init__(self):
        self.is_trained = True  # 기하학적 계산은 별도 학습 불필요
        self._setup_feature_weights()
        logger.info("얼굴 기하학 기반 성별 분류기 초기화 완료")
    
    def _setup_feature_weights(self):
        """얼굴 특징별 가중치 설정 (연구 논문 기반)"""
        # 각 특징이 masculinity에 기여하는 정도
        self.feature_weights = {
            'jaw_masculinity': 0.30,      # 턱선 각도 (가장 중요)
            'face_width_ratio': 0.25,     # 얼굴 폭/높이 비율
            'brow_prominence': 0.20,      # 눈썹-눈 거리
            'nose_width_ratio': 0.15,     # 코 폭 비율
            'cheek_definition': 0.10      # 광대뼈 정의
        }
        
        # 각 특징의 정규화 범위 (연구 데이터 기반 추정값)
        self.feature_ranges = {
            'jaw_masculinity': (0.3, 1.2),    # 턱선 각도 범위
            'face_width_ratio': (0.7, 1.1),   # 얼굴 비율 범위
            'brow_prominence': (0.05, 0.25),  # 눈썹 거리 범위
            'nose_width_ratio': (0.2, 0.5),   # 코 폭 범위
            'cheek_definition': (0.1, 0.4)    # 광대 정의 범위
        }
    
    def calculate_masculinity_from_landmarks(self, landmarks: List[List[float]]) -> Dict[str, float]:
        """facial landmarks에서 masculinity 점수 계산"""
        
        try:
            # landmarks를 numpy 배열로 변환
            landmarks_array = np.array(landmarks)
            
            # 각 얼굴 특징 계산
            features = self._extract_facial_features(landmarks_array)
            
            # 각 특징을 0-1 범위로 정규화
            normalized_features = self._normalize_features(features)
            
            # 가중 평균으로 전체 masculinity 점수 계산
            masculinity_score = sum(
                normalized_features[feature] * weight 
                for feature, weight in self.feature_weights.items()
            )
            
            # 0.0-1.0 범위로 클램핑
            masculinity_score = max(0.0, min(1.0, masculinity_score))
            femininity_score = 1.0 - masculinity_score
            
            return {
                "masculinity_score": float(masculinity_score),
                "femininity_score": float(femininity_score),
                "features": {
                    feature: float(normalized_features[feature]) 
                    for feature in self.feature_weights.keys()
                },
                "raw_features": features
            }
            
        except Exception as e:
            logger.error(f"Landmarks에서 masculinity 계산 중 오류: {e}")
            return self._default_score()
    
    def _extract_facial_features(self, landmarks: np.ndarray) -> Dict[str, float]:
        """facial landmarks에서 기하학적 특징 추출"""
        
        # InsightFace는 68개 또는 106개 landmarks 제공
        # 여기서는 68개 landmarks 기준으로 구현
        
        features = {}
        
        try:
            # 1. 턱선 masculinity (턱의 각진 정도)
            features['jaw_masculinity'] = self._calculate_jaw_masculinity(landmarks)
            
            # 2. 얼굴 폭/높이 비율
            features['face_width_ratio'] = self._calculate_face_ratio(landmarks)
            
            # 3. 눈썹 prominence (눈썹과 눈 사이 거리)
            features['brow_prominence'] = self._calculate_brow_prominence(landmarks)
            
            # 4. 코 폭 비율
            features['nose_width_ratio'] = self._calculate_nose_width(landmarks)
            
            # 5. 광대뼈 정의
            features['cheek_definition'] = self._calculate_cheek_definition(landmarks)
            
        except Exception as e:
            logger.warning(f"특징 추출 중 일부 오류: {e}")
            # 기본값으로 중성적 특징 설정
            for feature in self.feature_weights.keys():
                if feature not in features:
                    features[feature] = 0.5
        
        return features
    
    def _calculate_jaw_masculinity(self, landmarks: np.ndarray) -> float:
        """턱선의 masculinity 계산 (각진 정도)"""
        try:
            # 턱 라인 포인트들 (대략적인 인덱스, 실제로는 정확한 매핑 필요)
            if len(landmarks) >= 17:  # 68 point 모델 기준
                # 턱 라인: 0-16번 포인트
                jaw_left = landmarks[0]
                jaw_bottom = landmarks[8]  # 턱 끝
                jaw_right = landmarks[16]
                
                # 턱 각도 계산
                left_angle = self._calculate_angle(jaw_left, jaw_bottom, [jaw_bottom[0], jaw_bottom[1] - 10])
                right_angle = self._calculate_angle(jaw_right, jaw_bottom, [jaw_bottom[0], jaw_bottom[1] - 10])
                
                # 평균 각도 (작을수록 각짐 = 남성적)
                avg_angle = (left_angle + right_angle) / 2
                
                # 각도를 masculinity로 변환 (90도=중성, 예각=남성적)
                masculinity = max(0, (90 - avg_angle) / 90)
                return masculinity
            else:
                return 0.5  # 기본값
                
        except Exception as e:
            logger.debug(f"턱 masculinity 계산 오류: {e}")
            return 0.5
    
    def _calculate_face_ratio(self, landmarks: np.ndarray) -> float:
        """얼굴 폭/높이 비율 계산"""
        try:
            if len(landmarks) >= 28:
                # 얼굴 폭 (좌우 끝점)
                face_width = abs(landmarks[16][0] - landmarks[0][0])
                
                # 얼굴 높이 (이마-턱)
                face_height = abs(landmarks[8][1] - landmarks[27][1])  # 코 브리지 상단 추정
                
                if face_height > 0:
                    ratio = face_width / face_height
                    return ratio
                else:
                    return 0.85  # 기본 비율
            else:
                return 0.85
                
        except Exception as e:
            logger.debug(f"얼굴 비율 계산 오류: {e}")
            return 0.85
    
    def _calculate_brow_prominence(self, landmarks: np.ndarray) -> float:
        """눈썹 prominence 계산"""
        try:
            if len(landmarks) >= 48:
                # 눈썹과 눈 사이 거리 (추정)
                # 왼쪽 눈썹-눈 거리
                left_brow_eye_dist = abs(landmarks[19][1] - landmarks[37][1])  # 추정 좌표
                # 오른쪽 눈썹-눈 거리  
                right_brow_eye_dist = abs(landmarks[24][1] - landmarks[44][1])  # 추정 좌표
                
                avg_distance = (left_brow_eye_dist + right_brow_eye_dist) / 2
                
                # 얼굴 크기로 정규화
                face_size = abs(landmarks[8][1] - landmarks[27][1])
                if face_size > 0:
                    normalized_distance = avg_distance / face_size
                    return normalized_distance
                else:
                    return 0.15
            else:
                return 0.15
                
        except Exception as e:
            logger.debug(f"눈썹 prominence 계산 오류: {e}")
            return 0.15
    
    def _calculate_nose_width(self, landmarks: np.ndarray) -> float:
        """코 폭 비율 계산"""
        try:
            if len(landmarks) >= 36:
                # 콧구멍 양쪽 폭
                nose_width = abs(landmarks[35][0] - landmarks[31][0])  # 추정 좌표
                
                # 얼굴 폭으로 정규화
                face_width = abs(landmarks[16][0] - landmarks[0][0])
                if face_width > 0:
                    nose_ratio = nose_width / face_width
                    return nose_ratio
                else:
                    return 0.3
            else:
                return 0.3
                
        except Exception as e:
            logger.debug(f"코 폭 계산 오류: {e}")
            return 0.3
    
    def _calculate_cheek_definition(self, landmarks: np.ndarray) -> float:
        """광대뼈 정의 계산"""
        try:
            if len(landmarks) >= 17:
                # 광대뼈 위치에서의 곡률 계산 (간소화)
                cheek_left = landmarks[1]
                cheek_right = landmarks[15]
                jaw_center = landmarks[8]
                
                # 광대-턱 거리 대비 돌출 정도
                left_prominence = self._point_to_line_distance(cheek_left, landmarks[0], jaw_center)
                right_prominence = self._point_to_line_distance(cheek_right, landmarks[16], jaw_center)
                
                avg_prominence = (left_prominence + right_prominence) / 2
                
                # 얼굴 크기로 정규화
                face_width = abs(landmarks[16][0] - landmarks[0][0])
                if face_width > 0:
                    normalized_prominence = avg_prominence / face_width
                    return normalized_prominence
                else:
                    return 0.2
            else:
                return 0.2
                
        except Exception as e:
            logger.debug(f"광대 정의 계산 오류: {e}")
            return 0.2
    
    def _normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """특징들을 0-1 범위로 정규화"""
        normalized = {}
        
        for feature, value in features.items():
            if feature in self.feature_ranges:
                min_val, max_val = self.feature_ranges[feature]
                # Min-max 정규화
                normalized_value = (value - min_val) / (max_val - min_val)
                # 0-1 범위로 클램핑
                normalized[feature] = max(0.0, min(1.0, normalized_value))
            else:
                normalized[feature] = value
        
        return normalized
    
    def _calculate_angle(self, p1: List[float], p2: List[float], p3: List[float]) -> float:
        """세 점으로 이루어진 각도 계산 (도 단위)"""
        try:
            # 벡터 계산
            v1 = [p1[0] - p2[0], p1[1] - p2[1]]
            v2 = [p3[0] - p2[0], p3[1] - p2[1]]
            
            # 내적과 외적으로 각도 계산
            dot_product = v1[0] * v2[0] + v1[1] * v2[1]
            
            mag_v1 = math.sqrt(v1[0]**2 + v1[1]**2)
            mag_v2 = math.sqrt(v2[0]**2 + v2[1]**2)
            
            if mag_v1 > 0 and mag_v2 > 0:
                cos_angle = dot_product / (mag_v1 * mag_v2)
                cos_angle = max(-1, min(1, cos_angle))  # 클램핑
                angle_rad = math.acos(cos_angle)
                angle_deg = math.degrees(angle_rad)
                return angle_deg
            else:
                return 90.0  # 기본값
                
        except Exception:
            return 90.0
    
    def _point_to_line_distance(self, point: List[float], line_p1: List[float], line_p2: List[float]) -> float:
        """점에서 직선까지의 거리 계산"""
        try:
            # 직선의 방향벡터
            dx = line_p2[0] - line_p1[0]
            dy = line_p2[1] - line_p1[1]
            
            if dx == 0 and dy == 0:
                # 두 점이 같으면 점간 거리
                return math.sqrt((point[0] - line_p1[0])**2 + (point[1] - line_p1[1])**2)
            
            # 점-직선 거리 공식
            distance = abs(dy * point[0] - dx * point[1] + line_p2[0] * line_p1[1] - line_p2[1] * line_p1[0]) / math.sqrt(dx**2 + dy**2)
            return distance
            
        except Exception:
            return 0.0
    
    def _default_score(self) -> Dict[str, float]:
        """기본 중성적 점수 반환"""
        return {
            "masculinity_score": 0.5,
            "femininity_score": 0.5,
            "features": {feature: 0.5 for feature in self.feature_weights.keys()},
            "raw_features": {feature: 0.5 for feature in self.feature_weights.keys()}
        }
    
    def predict_probability(self, embedding: List[float]) -> Dict[str, float]:
        """이전 인터페이스 호환성을 위한 메서드 (더이상 사용하지 않음)"""
        logger.warning("predict_probability는 더이상 사용되지 않습니다. calculate_masculinity_from_landmarks를 사용하세요.")
        return {
            "male": 0.5,
            "female": 0.5
        }


# 전역 분류기 인스턴스
gender_classifier = GeometricGenderClassifier()
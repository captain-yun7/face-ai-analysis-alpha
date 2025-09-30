"""
성별별 상대적 특징 측정기 - InsightFace 기반 masculinity/femininity 강도 측정
"""
import numpy as np
from typing import Dict, List, Tuple
import logging
import math

logger = logging.getLogger(__name__)


class GenderCharacteristicsAnalyzer:
    """성별별 상대적 특징 강도 측정기"""
    
    def __init__(self):
        self.is_trained = True
        self._setup_weights_and_ranges()
        logger.info("성별별 특징 측정기 초기화 완료")
    
    def _setup_weights_and_ranges(self):
        """연구 기반 가중치 및 정규화 범위 설정"""
        
        # 남성성 측정 가중치 (연구 기반)
        self.masculinity_weights = {
            'jaw_features': 0.40,      # 턱 관련 특징 (40%)
            'facial_structure': 0.35,  # 얼굴 구조 (35%)  
            'detail_features': 0.25    # 세부 특징 (25%)
        }
        
        # 여성성 측정 가중치 (연구 기반)
        self.femininity_weights = {
            'mid_face_features': 0.40,   # 중안면 특징 (40%)
            'lips_lower_face': 0.35,     # 입술 및 하안면 (35%)
            'softness_features': 0.25    # 전체적 부드러움 (25%)
        }
        
        # 남성성 특징 정규화 범위
        self.masculinity_ranges = {
            'jaw_angle': (0.3, 1.2),           # 턱 각도 
            'jaw_width_ratio': (0.4, 0.8),     # 턱 폭 비율
            'lower_face_height': (0.4, 0.7),   # 하안면 높이
            'face_width_ratio': (0.7, 1.4),    # 얼굴 폭/높이
            'cheekbone_prominence': (0.0, 0.6), # 광대뼈 돌출
            'inter_ocular_ratio': (0.25, 0.4), # 안간격 비율
            'eyebrow_thickness': (0.05, 0.3),  # 눈썹 두께
            'nose_width_ratio': (0.15, 0.5),   # 코 폭 비율
            'lip_thickness': (0.02, 0.15)      # 입술 두께 (얇을수록 남성적)
        }
        
        # 여성성 특징 정규화 범위
        self.femininity_ranges = {
            'mid_face_ratio': (0.25, 0.4),     # 중안면 비율
            'eye_size_ratio': (0.08, 0.15),    # 눈 크기 비율
            'eye_height_ratio': (0.3, 0.7),    # 눈 높이/폭 비율
            'lip_thickness': (0.05, 0.2),      # 입술 두께 (두꺼울수록 여성적)
            'upper_lower_lip': (0.4, 0.6),     # 상순/하순 비율
            'lower_face_ratio': (0.3, 0.5),    # 하안면/전체 비율
            'jaw_softness': (0.0, 1.0),        # 턱선 부드러움
            'face_curvature': (0.0, 1.0),      # 얼굴 곡률
            'nose_length_ratio': (0.15, 0.25)  # 코 길이 비율
        }
    
    def analyze_gender_characteristics(self, landmarks: List[List[float]], insightface_gender: str) -> Dict[str, float]:
        """성별별 상대적 특징 강도 분석"""
        
        try:
            landmarks_array = np.array(landmarks)
            logger.info(f"🔍 Landmarks 배열 크기: {landmarks_array.shape}, 성별: {insightface_gender}")
            
            if len(landmarks_array) < 68:
                logger.warning(f"Landmarks 부족: {len(landmarks_array)}개 (68개 필요)")
                return self._default_characteristics_score(insightface_gender)
            
            if insightface_gender == "male":
                return self._analyze_masculinity(landmarks_array)
            else:  # female
                return self._analyze_femininity(landmarks_array)
                
        except Exception as e:
            logger.error(f"성별 특징 분석 중 오류: {e}")
            return self._default_characteristics_score(insightface_gender)
    
    def _analyze_masculinity(self, landmarks: np.ndarray) -> Dict[str, float]:
        """남성 내에서의 masculinity 강도 측정"""
        
        # 1. 턱 관련 특징 (40%)
        jaw_features = self._calculate_jaw_features(landmarks)
        jaw_score = self._normalize_and_score(jaw_features, self.masculinity_ranges, 'masculinity_jaw')
        
        # 2. 얼굴 구조 (35%)
        facial_structure = self._calculate_facial_structure(landmarks)
        structure_score = self._normalize_and_score(facial_structure, self.masculinity_ranges, 'masculinity_structure')
        
        # 3. 세부 특징 (25%)
        detail_features = self._calculate_detail_features(landmarks)
        detail_score = self._normalize_and_score(detail_features, self.masculinity_ranges, 'masculinity_detail')
        
        # 가중 평균으로 최종 masculinity 레벨 계산
        masculinity_level = (
            jaw_score * self.masculinity_weights['jaw_features'] +
            structure_score * self.masculinity_weights['facial_structure'] +
            detail_score * self.masculinity_weights['detail_features']
        )
        
        masculinity_level = max(0.0, min(1.0, masculinity_level))
        category = self._get_masculinity_category(masculinity_level)
        
        logger.info(f"🔍 남성성 분석 - 턱: {jaw_score:.3f}, 구조: {structure_score:.3f}, 세부: {detail_score:.3f}")
        logger.info(f"🔍 최종 masculinity: {masculinity_level:.3f} ({category})")
        
        return {
            "type": "masculinity",
            "level": float(masculinity_level),
            "category": category,
            "detailed_analysis": {
                "jaw_features": {"score": float(jaw_score), "components": jaw_features},
                "facial_structure": {"score": float(structure_score), "components": facial_structure},
                "detail_features": {"score": float(detail_score), "components": detail_features}
            }
        }
    
    def _analyze_femininity(self, landmarks: np.ndarray) -> Dict[str, float]:
        """여성 내에서의 femininity 강도 측정"""
        
        # 1. 중안면 특징 (40%)
        mid_face_features = self._calculate_mid_face_features(landmarks)
        mid_face_score = self._normalize_and_score(mid_face_features, self.femininity_ranges, 'femininity_mid_face')
        
        # 2. 입술 및 하안면 (35%)
        lips_lower_face = self._calculate_lips_lower_face(landmarks)
        lips_score = self._normalize_and_score(lips_lower_face, self.femininity_ranges, 'femininity_lips')
        
        # 3. 전체적 부드러움 (25%)
        softness_features = self._calculate_softness_features(landmarks)
        softness_score = self._normalize_and_score(softness_features, self.femininity_ranges, 'femininity_softness')
        
        # 가중 평균으로 최종 femininity 레벨 계산
        femininity_level = (
            mid_face_score * self.femininity_weights['mid_face_features'] +
            lips_score * self.femininity_weights['lips_lower_face'] +
            softness_score * self.femininity_weights['softness_features']
        )
        
        femininity_level = max(0.0, min(1.0, femininity_level))
        category = self._get_femininity_category(femininity_level)
        
        logger.info(f"🔍 여성성 분석 - 중안면: {mid_face_score:.3f}, 입술: {lips_score:.3f}, 부드러움: {softness_score:.3f}")
        logger.info(f"🔍 최종 femininity: {femininity_level:.3f} ({category})")
        
        return {
            "type": "femininity",
            "level": float(femininity_level),
            "category": category,
            "detailed_analysis": {
                "mid_face_features": {"score": float(mid_face_score), "components": mid_face_features},
                "lips_lower_face": {"score": float(lips_score), "components": lips_lower_face},
                "softness_features": {"score": float(softness_score), "components": softness_features}
            }
        }
    
    def _extract_facial_features(self, landmarks: np.ndarray) -> Dict[str, float]:
        """68-point landmarks에서 기하학적 특징 추출"""
        
        features = {}
        
        try:
            # 68-point landmarks 길이 검증
            if len(landmarks) < 68:
                logger.warning(f"Landmarks 부족: {len(landmarks)}개 (68개 필요)")
                return {feature: 0.5 for feature in self.feature_weights.keys()}
            
            # 5가지 핵심 특징 계산
            features['jaw_masculinity'] = self._calculate_jaw_masculinity(landmarks)
            features['face_width_ratio'] = self._calculate_face_ratio(landmarks)
            features['brow_prominence'] = self._calculate_brow_prominence(landmarks)
            features['nose_width_ratio'] = self._calculate_nose_width(landmarks)
            features['cheek_definition'] = self._calculate_cheek_definition(landmarks)
            
        except Exception as e:
            logger.warning(f"특징 추출 오류: {e}")
            # 에러 시 중성 기본값
            features = {feature: 0.5 for feature in self.feature_weights.keys()}
        
        return features
    
    def _calculate_jaw_masculinity(self, landmarks: np.ndarray) -> float:
        """턱선의 masculinity 계산 (각진 정도) - dlib 68-point 표준"""
        try:
            if len(landmarks) >= 17:  # 68 point 모델 기준
                # dlib 표준: 턱라인 0-16번 포인트
                jaw_left = landmarks[0]    # 왼쪽 턱 끝
                jaw_bottom = landmarks[8]  # 턱 아래 중앙 (정확함)
                jaw_right = landmarks[16]  # 오른쪽 턱 끝
                
                # 턱 각도 계산 (턱끝-턱중앙-수직선)
                vertical_ref = [jaw_bottom[0], jaw_bottom[1] - 20]  # 수직 기준점
                left_angle = self._calculate_angle(jaw_left, jaw_bottom, vertical_ref)
                right_angle = self._calculate_angle(jaw_right, jaw_bottom, vertical_ref)
                
                # 평균 각도 (작을수록 각짐 = 남성적)
                avg_angle = (left_angle + right_angle) / 2
                
                # 각도를 masculinity로 변환 (90-130도 범위를 0-1로 매핑)
                # 90도=매우 각진(남성적), 130도=부드러운(여성적)
                masculinity = max(0, min(1, (130 - avg_angle) / 40))
                return masculinity
            else:
                return 0.5  # 기본값
                
        except Exception as e:
            logger.debug(f"턱 masculinity 계산 오류: {e}")
            return 0.5
    
    def _calculate_face_ratio(self, landmarks: np.ndarray) -> float:
        """얼굴 폭/높이 비율 계산 - dlib 68-point 표준"""
        try:
            if len(landmarks) >= 28:
                # dlib 표준: 얼굴 폭 (턱라인 0-16)
                face_width = abs(landmarks[16][0] - landmarks[0][0])
                
                # dlib 표준: 얼굴 높이 (코 브리지 상단 27 - 턱 아래 8)
                face_height = abs(landmarks[8][1] - landmarks[27][1])
                
                if face_height > 0:
                    ratio = face_width / face_height
                    # 남성: 1.0-1.1, 여성: 0.8-0.9 정도
                    return ratio
                else:
                    return 0.85  # 기본 비율
            else:
                return 0.85
                
        except Exception as e:
            logger.debug(f"얼굴 비율 계산 오류: {e}")
            return 0.85
    
    def _calculate_brow_prominence(self, landmarks: np.ndarray) -> float:
        """눈썹 prominence 계산 - dlib 68-point 표준"""
        try:
            if len(landmarks) >= 48:
                # dlib 표준: 눈썹 17-26, 눈 36-47
                # 왼쪽 눈썹 중앙(19) - 왼쪽 눈 위쪽(37)
                left_brow_eye_dist = abs(landmarks[19][1] - landmarks[37][1])
                # 오른쪽 눈썹 중앙(24) - 오른쪽 눈 위쪽(44)  
                right_brow_eye_dist = abs(landmarks[24][1] - landmarks[44][1])
                
                avg_distance = (left_brow_eye_dist + right_brow_eye_dist) / 2
                
                # 얼굴 크기로 정규화 (코브리지-턱)
                face_height = abs(landmarks[8][1] - landmarks[27][1])
                if face_height > 0:
                    normalized_distance = avg_distance / face_height
                    # 남성: 더 돌출된 눈썹 (큰 값), 여성: 평평한 눈썹 (작은 값)
                    return normalized_distance
                else:
                    return 0.15
            else:
                return 0.15
                
        except Exception as e:
            logger.debug(f"눈썹 prominence 계산 오류: {e}")
            return 0.15
    
    def _calculate_nose_width(self, landmarks: np.ndarray) -> float:
        """코 폭 비율 계산 - dlib 68-point 표준"""
        try:
            if len(landmarks) >= 36:
                # dlib 표준: 코 27-35번
                # 콧구멍 양쪽 폭 (31: 왼쪽 콧구멍, 35: 오른쪽 콧구멍)
                left_nostril = landmarks[31]
                right_nostril = landmarks[35]
                nose_width = abs(right_nostril[0] - left_nostril[0])
                
                # 얼굴 폭으로 정규화 (턱라인 0-16)
                jaw_left = landmarks[0]
                jaw_right = landmarks[16]
                face_width = abs(jaw_right[0] - jaw_left[0])
                
                logger.info(f"🔍 코 폭 계산: left_nostril={left_nostril}, right_nostril={right_nostril}")
                logger.info(f"🔍 코 폭: {nose_width:.3f}, 얼굴 폭: {face_width:.3f}")
                
                if face_width > 0:
                    nose_ratio = nose_width / face_width
                    logger.info(f"🔍 코 폭 비율: {nose_ratio:.3f}")
                    return nose_ratio
                else:
                    logger.warning("🔍 얼굴 폭이 0 - 기본값 반환")
                    return 0.3
            else:
                return 0.3
                
        except Exception as e:
            logger.debug(f"코 폭 계산 오류: {e}")
            return 0.3
    
    def _calculate_cheek_definition(self, landmarks: np.ndarray) -> float:
        """광대뼈 정의 계산 - dlib 68-point 표준"""
        try:
            if len(landmarks) >= 17:
                # dlib 표준: 턱라인 0-16에서 광대뼈 추정
                cheek_left = landmarks[1]   # 왼쪽 광대 추정
                cheek_right = landmarks[15] # 오른쪽 광대 추정
                jaw_center = landmarks[8]   # 턱 중앙
                jaw_left = landmarks[0]     # 턱 왼쪽
                jaw_right = landmarks[16]   # 턱 오른쪽
                
                logger.info(f"🔍 광대 계산: cheek_left={cheek_left}, cheek_right={cheek_right}")
                logger.info(f"🔍 턱 점들: jaw_left={jaw_left}, jaw_center={jaw_center}, jaw_right={jaw_right}")
                
                # 광대-턱 거리 대비 돌출 정도
                left_prominence = self._point_to_line_distance(cheek_left, jaw_left, jaw_center)
                right_prominence = self._point_to_line_distance(cheek_right, jaw_right, jaw_center)
                
                logger.info(f"🔍 돌출도: left={left_prominence:.3f}, right={right_prominence:.3f}")
                
                avg_prominence = (left_prominence + right_prominence) / 2
                
                # 얼굴 폭으로 정규화
                face_width = abs(jaw_right[0] - jaw_left[0])
                
                logger.info(f"🔍 평균 돌출도: {avg_prominence:.3f}, 얼굴 폭: {face_width:.3f}")
                
                if face_width > 0:
                    normalized_prominence = avg_prominence / face_width
                    logger.info(f"🔍 정규화된 광대 정의: {normalized_prominence:.3f}")
                    return normalized_prominence
                else:
                    logger.warning("🔍 얼굴 폭이 0 - 기본값 반환")
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
        """구 인터페이스 호환성 (사용 중단)"""
        logger.warning("⚠️ predict_probability 사용 중단. calculate_masculinity_from_landmarks 사용")
        return {"male": 0.5, "female": 0.5}


# 전역 분류기 인스턴스
gender_classifier = GeometricGenderClassifier()
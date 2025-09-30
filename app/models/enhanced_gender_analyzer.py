"""
Enhanced Gender Probability Analyzer - InsightFace genderage 모델의 raw 확률값 활용
"""
import numpy as np
import cv2
from typing import Dict, Any, List, Optional
import logging
from insightface.utils import face_align

logger = logging.getLogger(__name__)


class EnhancedGenderProbabilityAnalyzer:
    """InsightFace genderage 모델의 raw 확률값을 활용한 향상된 성별 분석기"""
    
    def __init__(self, face_analyzer_app):
        """
        Args:
            face_analyzer_app: InsightFace FaceAnalysis 인스턴스
        """
        self.app = face_analyzer_app
        self.genderage_model = None
        
        if hasattr(face_analyzer_app, 'models') and 'genderage' in face_analyzer_app.models:
            self.genderage_model = face_analyzer_app.models['genderage']
            logger.info("✅ genderage 모델 연결 성공")
        else:
            logger.warning("⚠️ genderage 모델을 찾을 수 없음")
    
    def get_gender_probabilities(self, face, img: np.ndarray) -> Dict[str, Any]:
        """
        InsightFace genderage 모델에서 raw 확률값을 추출하여 정확한 성별 확률 반환
        
        Args:
            face: InsightFace face 객체
            img: 원본 이미지 (cv2 형식)
            
        Returns:
            Dict containing gender probabilities and confidence scores
        """
        
        if not self.genderage_model:
            logger.warning("genderage 모델이 없음. 기본값 반환")
            return self._get_default_probabilities(face)
        
        try:
            # genderage 모델에서 raw 출력 얻기
            raw_output = self._get_raw_genderage_output(face, img)
            
            if raw_output is None:
                logger.warning("genderage raw 출력 실패. 기본값 반환")
                return self._get_default_probabilities(face)
            
            # raw 출력 분석: [female_score, male_score, age_normalized]
            female_score = float(raw_output[0])
            male_score = float(raw_output[1])
            age_raw = float(raw_output[2])
            
            logger.info(f"🔍 Raw genderage 출력: female={female_score:.3f}, male={male_score:.3f}, age_raw={age_raw:.3f}")
            
            # Softmax로 확률 정규화
            probabilities = self._softmax([female_score, male_score])
            female_probability = float(probabilities[0])
            male_probability = float(probabilities[1])
            
            # 최종 성별 결정
            predicted_gender = "male" if male_probability > female_probability else "female"
            confidence_score = max(male_probability, female_probability)
            
            # 연령 정보 (0-1 범위를 실제 나이로 변환)
            estimated_age = int(np.round(age_raw * 100))
            
            # Male Score 간단한 카테고리만 추출
            from .male_score_interpreter import male_score_interpreter
            masculinity_level = male_score_interpreter._get_masculinity_category(male_score)
            
            logger.info(f"🎯 최종 결과: {predicted_gender} ({confidence_score:.3f}), 나이: {estimated_age}")
            logger.info(f"🎯 Male Score: {male_score:.3f} ({masculinity_level})")
            
            return {
                "predicted_gender": predicted_gender,
                "male_probability": male_probability,
                "female_probability": female_probability,
                "confidence_score": confidence_score,
                "estimated_age": estimated_age,
                "male_score": male_score,
                "masculinity_level": masculinity_level,
                "raw_scores": {
                    "female_score": female_score,
                    "male_score": male_score
                }
            }
            
        except Exception as e:
            logger.error(f"성별 확률 분석 중 오류: {e}")
            return self._get_default_probabilities(face)
    
    def _get_raw_genderage_output(self, face, img: np.ndarray) -> Optional[np.ndarray]:
        """
        genderage 모델에서 raw 출력을 직접 얻기
        InsightFace의 attribute.py 코드를 참조하여 구현
        """
        
        try:
            # 얼굴 영역 추출 및 정렬
            bbox = face.bbox
            w, h = (bbox[2] - bbox[0]), (bbox[3] - bbox[1])
            center = (bbox[2] + bbox[0]) / 2, (bbox[3] + bbox[1]) / 2
            rotate = 0
            
            # genderage 모델의 입력 크기 (96x96)
            input_size = self.genderage_model.input_size  # (96, 96)
            _scale = input_size[0] / (max(w, h) * 1.5)
            
            # 얼굴 정렬 및 크기 조정
            aimg, M = face_align.transform(img, center, input_size[0], _scale, rotate)
            
            # 모델 입력을 위한 전처리
            input_mean = self.genderage_model.input_mean  # 0.0
            input_std = self.genderage_model.input_std    # 1.0
            
            blob = cv2.dnn.blobFromImage(
                aimg, 
                1.0 / input_std, 
                input_size, 
                (input_mean, input_mean, input_mean), 
                swapRB=True
            )
            
            # 모델 실행
            pred = self.genderage_model.session.run(
                self.genderage_model.output_names, 
                {self.genderage_model.input_name: blob}
            )[0][0]
            
            logger.debug(f"genderage raw prediction: {pred}")
            
            return pred
            
        except Exception as e:
            logger.error(f"Raw genderage 출력 추출 실패: {e}")
            return None
    
    def _softmax(self, x: List[float]) -> np.ndarray:
        """Softmax 함수로 확률 정규화"""
        x = np.array(x)
        exp_x = np.exp(x - np.max(x))  # 수치 안정성을 위한 최대값 빼기
        return exp_x / np.sum(exp_x)
    
    def _get_default_probabilities(self, face) -> Dict[str, Any]:
        """기본 확률값 반환 (fallback)"""
        
        # InsightFace의 기본 성별 분류 사용
        if hasattr(face, 'gender'):
            is_male = face.gender == 1
            # 기본 신뢰도 (높은 값으로 설정)
            high_confidence = 0.85
            low_confidence = 1.0 - high_confidence
            
            if is_male:
                male_prob, female_prob = high_confidence, low_confidence
                predicted_gender = "male"
            else:
                male_prob, female_prob = low_confidence, high_confidence
                predicted_gender = "female"
        else:
            # 성별 정보가 없으면 중성
            male_prob = female_prob = 0.5
            predicted_gender = "unknown"
        
        estimated_age = int(face.age) if hasattr(face, 'age') else 25
        
        return {
            "predicted_gender": predicted_gender,
            "male_probability": male_prob,
            "female_probability": female_prob,
            "confidence_score": max(male_prob, female_prob),
            "estimated_age": estimated_age,
            "raw_scores": {
                "female_score": 0.0,
                "male_score": 0.0,
                "age_raw": 0.0
            }
        }
    


# 전역 인스턴스는 FaceAnalyzer에서 초기화됨
enhanced_gender_analyzer = None
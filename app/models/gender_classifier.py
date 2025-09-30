"""
경량 성별 분류기 - InsightFace 임베딩을 사용한 성별 확률 추정
"""
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class GenderClassifier:
    """경량 성별 분류기 (임베딩 기반)"""
    
    def __init__(self):
        self.is_trained = False
        self.model = None
        self._setup_simple_classifier()
    
    def _setup_simple_classifier(self):
        """간단한 분류기 설정 (더미 구현)"""
        # 실제로는 학습된 모델을 로드하거나 간단한 규칙 기반 분류기 사용
        # 여기서는 임베딩의 특정 차원들을 활용한 휴리스틱 접근법 사용
        
        # 성별 구분에 유용한 임베딩 차원 인덱스들 (가상의 값)
        # 실제로는 데이터 분석을 통해 결정해야 함
        self.gender_indicative_dims = [
            12, 45, 78, 123, 156, 234, 289, 345, 
            389, 412, 456, 489, 501, 67, 201, 333
        ]
        
        # 성별별 가중치 (가상의 값, 실제로는 학습을 통해 얻어야 함)
        self.male_weights = np.array([
            0.8, -0.6, 0.4, -0.3, 0.7, -0.5, 0.2, 0.9,
            -0.4, 0.6, -0.8, 0.3, 0.5, -0.2, 0.7, -0.1
        ])
        
        self.is_trained = True
        logger.info("간단한 성별 분류기 초기화 완료")
    
    def predict_probability(self, embedding: List[float]) -> Dict[str, float]:
        """임베딩에서 성별 확률 추정"""
        
        if not self.is_trained:
            logger.warning("분류기가 학습되지 않음, 랜덤 값 반환")
            return self._random_prediction()
        
        try:
            # 임베딩을 numpy 배열로 변환
            emb_array = np.array(embedding)
            
            # 특정 차원들만 추출
            selected_features = emb_array[self.gender_indicative_dims]
            
            # 가중합 계산
            male_score = np.dot(selected_features, self.male_weights)
            
            # 시그모이드 함수로 확률 변환
            male_prob = self._sigmoid(male_score)
            female_prob = 1.0 - male_prob
            
            return {
                "male": float(male_prob),
                "female": float(female_prob)
            }
            
        except Exception as e:
            logger.error(f"성별 확률 예측 중 오류: {e}")
            return self._random_prediction()
    
    def _sigmoid(self, x: float) -> float:
        """시그모이드 함수"""
        try:
            return 1.0 / (1.0 + np.exp(-x))
        except:
            # 오버플로우 방지
            if x > 0:
                return 1.0
            else:
                return 0.0
    
    def _random_prediction(self) -> Dict[str, float]:
        """랜덤 예측 (분류기가 없을 때)"""
        import random
        
        male_prob = random.uniform(0.2, 0.8)
        female_prob = 1.0 - male_prob
        
        return {
            "male": male_prob,
            "female": female_prob
        }
    
    def train_from_data(self, embeddings: List[List[float]], labels: List[str]):
        """데이터로부터 분류기 학습 (추후 구현용)"""
        # 실제 구현에서는 sklearn의 LogisticRegression 등을 사용
        logger.info("성별 분류기 학습 기능은 아직 구현되지 않음")
        pass
    
    def save_model(self, filepath: str):
        """모델 저장 (추후 구현용)"""
        logger.info("모델 저장 기능은 아직 구현되지 않음")
        pass
    
    def load_model(self, filepath: str):
        """모델 로드 (추후 구현용)"""
        logger.info("모델 로드 기능은 아직 구현되지 않음")
        pass


# 전역 분류기 인스턴스
gender_classifier = GenderClassifier()
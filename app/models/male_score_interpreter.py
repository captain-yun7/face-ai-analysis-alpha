"""
Male Score Interpreter - InsightFace genderage 모델의 Male Score 해석 시스템
"""
import numpy as np
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class MaleScoreInterpreter:
    """InsightFace Male Score 해석 및 분석 시스템"""
    
    def __init__(self):
        """실제 데이터 기반으로 해석 기준 초기화"""
        
        # 실제 관찰된 데이터 (8개 이미지 분석 결과)
        self.observed_data = {
            "male_images": {
                "scores": [3.159, 3.492, 3.824, 3.918, 4.107, 5.166],
                "range": (3.159, 5.166),
                "mean": 3.944,
                "std": 0.627
            },
            "female_images": {
                "scores": [-4.820, -2.392],
                "range": (-4.820, -2.392),
                "mean": -3.606,
                "std": 1.214
            },
            "overall_range": (-5.166, 5.166)
        }
        
        # 남성성 해석 기준 (현재 데이터 기반)
        self.masculinity_levels = {
            "extremely_masculine": (5.0, float('inf')),    # 극도로 남성적
            "very_masculine": (4.0, 5.0),                  # 매우 남성적
            "masculine": (3.0, 4.0),                       # 남성적
            "moderately_masculine": (1.0, 3.0),            # 약간 남성적
            "neutral": (-1.0, 1.0),                        # 중성적
            "moderately_feminine": (-3.0, -1.0),           # 약간 여성적
            "feminine": (-4.0, -3.0),                      # 여성적
            "very_feminine": (-5.0, -4.0),                 # 매우 여성적
            "extremely_feminine": (float('-inf'), -5.0)    # 극도로 여성적
        }
        
        logger.info("Male Score Interpreter 초기화 완료")
    
    def interpret_male_score(self, male_score: float, female_score: float = None) -> Dict[str, Any]:
        """Male Score를 해석하여 상세 정보 반환"""
        
        try:
            # 기본 해석
            category = self._get_masculinity_category(male_score)
            percentile = self._calculate_percentile(male_score)
            
            # Score 차이 계산
            score_difference = None
            if female_score is not None:
                score_difference = male_score - female_score
            
            # 상대적 위치 계산
            relative_position = self._calculate_relative_position(male_score)
            
            # 남성 내 상대적 순위 (남성 이미지들과 비교)
            male_rank = self._calculate_male_rank(male_score)
            
            return {
                "male_score": float(male_score),
                "category": category,
                "description": self._get_category_description(category),
                "percentile": percentile,
                "score_difference": float(score_difference) if score_difference else None,
                "relative_position": relative_position,
                "male_rank": male_rank,
                "interpretation": self._generate_interpretation(male_score, category, percentile),
                "comparison_context": self._get_comparison_context(male_score)
            }
            
        except Exception as e:
            logger.error(f"Male Score 해석 중 오류: {e}")
            return self._get_default_interpretation(male_score)
    
    def _get_masculinity_category(self, score: float) -> str:
        """Score를 카테고리로 분류"""
        for category, (min_val, max_val) in self.masculinity_levels.items():
            if min_val <= score < max_val:
                return category
        return "unknown"
    
    def _calculate_percentile(self, score: float) -> float:
        """전체 관찰 데이터에서의 백분위 계산"""
        all_scores = (self.observed_data["male_images"]["scores"] + 
                     self.observed_data["female_images"]["scores"])
        
        if not all_scores:
            return 50.0
        
        # 현재 score보다 낮은 점수의 비율 계산
        lower_count = sum(1 for s in all_scores if s < score)
        percentile = (lower_count / len(all_scores)) * 100
        
        return round(percentile, 1)
    
    def _calculate_relative_position(self, score: float) -> str:
        """관찰된 범위에서의 상대적 위치"""
        min_score, max_score = self.observed_data["overall_range"]
        
        if score >= max_score:
            return "maximum_observed"
        elif score <= min_score:
            return "minimum_observed"
        else:
            # 0-1 범위로 정규화
            normalized = (score - min_score) / (max_score - min_score)
            if normalized >= 0.8:
                return "very_high"
            elif normalized >= 0.6:
                return "high"
            elif normalized >= 0.4:
                return "moderate"
            elif normalized >= 0.2:
                return "low"
            else:
                return "very_low"
    
    def _calculate_male_rank(self, score: float) -> Dict[str, Any]:
        """남성 이미지들 중에서의 순위 계산"""
        male_scores = self.observed_data["male_images"]["scores"]
        
        if not male_scores:
            return {"rank": None, "total": 0, "description": "데이터 부족"}
        
        # 현재 score보다 낮은 남성 점수의 개수
        lower_count = sum(1 for s in male_scores if s < score)
        rank = lower_count + 1  # 1부터 시작
        
        return {
            "rank": rank,
            "total": len(male_scores),
            "description": f"{len(male_scores)}명 중 {rank}위",
            "percentile_among_males": round((lower_count / len(male_scores)) * 100, 1)
        }
    
    def _get_category_description(self, category: str) -> str:
        """카테고리별 설명"""
        descriptions = {
            "extremely_masculine": "극도로 남성적인 얼굴 특징",
            "very_masculine": "매우 남성적인 얼굴 특징",
            "masculine": "남성적인 얼굴 특징", 
            "moderately_masculine": "약간 남성적인 얼굴 특징",
            "neutral": "중성적인 얼굴 특징",
            "moderately_feminine": "약간 여성적인 얼굴 특징",
            "feminine": "여성적인 얼굴 특징",
            "very_feminine": "매우 여성적인 얼굴 특징",
            "extremely_feminine": "극도로 여성적인 얼굴 특징"
        }
        return descriptions.get(category, "알 수 없는 특징")
    
    def _generate_interpretation(self, score: float, category: str, percentile: float) -> str:
        """종합적인 해석 문구 생성"""
        
        if score >= 4.0:
            strength = "매우 강한"
        elif score >= 3.0:
            strength = "강한"
        elif score >= 1.0:
            strength = "약간의"
        elif score >= -1.0:
            strength = "중성적인"
        else:
            strength = "여성적인"
        
        return f"Male Score {score:.3f}은 {strength} 남성성을 나타내며, 전체 데이터의 상위 {100-percentile:.1f}%에 해당합니다."
    
    def _get_comparison_context(self, score: float) -> Dict[str, str]:
        """비교 컨텍스트 제공"""
        male_avg = self.observed_data["male_images"]["mean"]
        female_avg = self.observed_data["female_images"]["mean"]
        
        context = {}
        
        # 남성 평균과 비교
        if score > male_avg:
            diff = score - male_avg
            context["vs_male_average"] = f"남성 평균({male_avg:.3f})보다 {diff:.3f} 높음"
        else:
            diff = male_avg - score
            context["vs_male_average"] = f"남성 평균({male_avg:.3f})보다 {diff:.3f} 낮음"
        
        # 여성 평균과 비교
        diff_female = score - female_avg
        context["vs_female_average"] = f"여성 평균({female_avg:.3f})보다 {diff_female:.3f} 높음"
        
        return context
    
    def _get_default_interpretation(self, score: float) -> Dict[str, Any]:
        """기본 해석 (오류 시)"""
        return {
            "male_score": float(score),
            "category": "unknown",
            "description": "해석 불가",
            "percentile": 50.0,
            "score_difference": None,
            "relative_position": "unknown",
            "male_rank": {"rank": None, "total": 0, "description": "데이터 부족"},
            "interpretation": f"Male Score {score:.3f} (해석 시스템 오류)",
            "comparison_context": {}
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """현재 수집된 통계 정보 반환"""
        return {
            "total_images_analyzed": (len(self.observed_data["male_images"]["scores"]) + 
                                    len(self.observed_data["female_images"]["scores"])),
            "male_images": len(self.observed_data["male_images"]["scores"]),
            "female_images": len(self.observed_data["female_images"]["scores"]),
            "observed_range": self.observed_data["overall_range"],
            "male_score_stats": self.observed_data["male_images"],
            "female_score_stats": self.observed_data["female_images"],
            "categories": list(self.masculinity_levels.keys())
        }


# 전역 인스턴스
male_score_interpreter = MaleScoreInterpreter()
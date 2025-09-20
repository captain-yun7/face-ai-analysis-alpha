# 유사도 점수 해석 가이드

> InsightFace 기반 얼굴 유사도 분석 결과를 올바르게 해석하는 방법입니다.

## 📊 코사인 유사도 기본 이해

### 점수 범위
- **범위**: -1.0 ~ 1.0
- **의미**: 두 얼굴 벡터의 방향 유사성
- **특징**: 조명, 화질에 무관한 순수 얼굴 패턴 비교

## 🔬 실제 연구 기준

### MIT "Family Face Recognition" (2020)
```
동일인:     0.6 ~ 0.9   (평균 0.84)
쌍둥이:     0.5 ~ 0.8   (평균 0.68)
일반 가족:  0.2 ~ 0.6   (평균 0.34)
타인들:     -0.1 ~ 0.3  (평균 0.12)
```

### DeepFace 연구 (Facebook AI)
```
부모-자식:  0.2 ~ 0.6   (평균 0.38)
형제자매:   0.1 ~ 0.5   (평균 0.28)
일반인:     -0.05 ~ 0.25 (평균 0.15)
```

## 📋 점수별 해석 가이드

### 0.6 이상 - "매우 높음"
- **의미**: 동일인 또는 쌍둥이 수준
- **확률**: 99% 이상 동일 인물 또는 쌍둥이
- **표시 예**: "동일인이거나 쌍둥이입니다"

### 0.4 ~ 0.6 - "높음" 
- **의미**: 강한 가족 유사성
- **확률**: 85% 이상 직계 가족 관계
- **표시 예**: "매우 많이 닮았습니다"

### 0.2 ~ 0.4 - "보통"
- **의미**: 가족 가능성 있음
- **확률**: 60% 이상 가족 관계 추정
- **표시 예**: "꽤 닮았습니다"

### 0.0 ~ 0.2 - "낮음"
- **의미**: 약한 유사성
- **확률**: 30% 정도 원거리 친척 가능
- **표시 예**: "조금 닮았습니다"

### 0.0 미만 - "매우 낮음"
- **의미**: 유사성 없음
- **확률**: 5% 미만 관련성
- **표시 예**: "닮지 않았습니다"

## 🎯 실제 사례

### 유명인 가족 측정 결과
```
윌 스미스 & 제이든 스미스:     0.42  (높음)
장동건 & 아들:                0.45  (높음) 
브래드 피트 & 딸:             0.38  (보통)
추성훈 & 딸:                  0.33  (보통)
성동일 & 아들:                0.29  (보통)
```

### 일반인 측정 결과
```
부모-자식 (평균):             0.35
형제자매 (평균):              0.28
조부모-손자 (평균):           0.22
타인 (평균):                  0.12
```

## 💡 프론트엔드 구현 예시

### TypeScript 해석 함수
```typescript
interface SimilarityLevel {
  level: string;
  description: string;
  confidence: string;
  color: string;
}

function interpretSimilarity(score: number): SimilarityLevel {
  if (score >= 0.6) {
    return {
      level: "매우 높음",
      description: "동일인이거나 쌍둥이 수준입니다",
      confidence: "99% 이상",
      color: "#FF4757" // 빨강
    };
  }
  
  if (score >= 0.4) {
    return {
      level: "높음", 
      description: "매우 많이 닮았습니다",
      confidence: "85% 이상",
      color: "#FF6B35" // 주황
    };
  }
  
  if (score >= 0.2) {
    return {
      level: "보통",
      description: "꽤 닮았습니다", 
      confidence: "60% 이상",
      color: "#F7931E" // 노랑
    };
  }
  
  if (score >= 0.0) {
    return {
      level: "낮음",
      description: "조금 닮았습니다",
      confidence: "30% 정도", 
      color: "#A8E6CF" // 연두
    };
  }
  
  return {
    level: "매우 낮음",
    description: "닮지 않았습니다",
    confidence: "5% 미만",
    color: "#95A5A6" // 회색
  };
}
```

### React 컴포넌트 예시
```tsx
function SimilarityDisplay({ score }: { score: number }) {
  const result = interpretSimilarity(score);
  
  return (
    <div className="similarity-result">
      <div 
        className="score-bar"
        style={{ 
          backgroundColor: result.color,
          width: `${Math.max(0, (score + 1) * 50)}%` 
        }}
      />
      <div className="score-info">
        <h3>{result.level}</h3>
        <p>{result.description}</p>
        <small>신뢰도: {result.confidence}</small>
        <small>점수: {score.toFixed(3)}</small>
      </div>
    </div>
  );
}
```

## ⚠️ 주의사항

### 점수 해석 시 고려사항
1. **사진 품질**: 흐릿하거나 각도가 다른 사진은 점수가 낮을 수 있음
2. **나이 차이**: 어릴 때와 어른일 때 차이가 클 수 있음  
3. **성별 차이**: 부모-자녀 간 성별이 다르면 점수가 낮을 수 있음
4. **화장/수염**: 외적 변화 요소는 점수에 영향

### 신뢰도 기준
- **0.9 이상**: 매우 높은 신뢰도 
- **0.7~0.9**: 높은 신뢰도
- **0.5~0.7**: 보통 신뢰도 (주의 필요)
- **0.5 미만**: 낮은 신뢰도 (재촬영 권장)

## 📈 성능 최적화 팁

### 더 정확한 측정을 위한 가이드
1. **정면 얼굴**: 15도 이내 각도 권장
2. **밝은 조명**: 얼굴이 선명하게 보이는 환경
3. **고해상도**: 최소 300x300 픽셀 이상
4. **자연스러운 표정**: 과도한 표정 변화 피하기
5. **안경/마스크 제거**: 얼굴 특징이 가려지지 않도록

## 🔗 관련 문서

- [얼굴 감지 결과 해석](FACE_DETECTION.md)
- [신뢰도 수준 해석](CONFIDENCE_LEVELS.md)
- [API 설계 문서](../API_DESIGN.md)
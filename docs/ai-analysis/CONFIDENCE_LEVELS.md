# 신뢰도 수준 해석 가이드

> AI 분석 결과의 신뢰도를 올바르게 해석하고 품질을 개선하는 방법입니다.

## 📊 신뢰도 유형별 기준

### 1. 얼굴 감지 신뢰도 (Detection Confidence)

#### 신뢰도 구간
```
0.95 ~ 1.0   🟢 매우 높음  (확실한 얼굴)
0.8 ~ 0.95   🟡 높음      (신뢰할 수 있음) 
0.5 ~ 0.8    🟠 보통      (주의 필요)
0.3 ~ 0.5    🔴 낮음      (재촬영 권장)
0.0 ~ 0.3    ❌ 매우 낮음  (얼굴 아닐 가능성)
```

#### 실제 의미
- **0.98**: 99.8% 확률로 얼굴임
- **0.85**: 85% 확률로 얼굴임 (일반적으로 안전)
- **0.60**: 60% 확률로 얼굴임 (불확실)
- **0.30**: 30% 확률로 얼굴임 (거의 확실하지 않음)

### 2. 유사도 분석 신뢰도

#### 계산 방식
```typescript
// 유사도 분석의 전체적인 신뢰도
function calculateOverallConfidence(
  faceConfidence1: number,
  faceConfidence2: number,
  faceQuality1: number,
  faceQuality2: number
): number {
  // 최소값 기준 (가장 약한 링크)
  const minFaceConfidence = Math.min(faceConfidence1, faceConfidence2);
  const minQuality = Math.min(faceQuality1, faceQuality2);
  
  // 가중 평균
  return (minFaceConfidence * 0.6 + minQuality * 0.4);
}
```

#### 해석 기준
```
0.9 이상    🟢 매우 신뢰함    (결과 그대로 사용 가능)
0.7 ~ 0.9   🟡 신뢰함        (일반적으로 정확)
0.5 ~ 0.7   🟠 보통          (참고용으로 사용)
0.3 ~ 0.5   🔴 신뢰도 낮음    (재시도 권장)
0.3 미만    ❌ 매우 낮음      (결과 신뢰 불가)
```

## 🎯 API별 신뢰도 기준

### detect-faces API
```json
{
  "faces": [{
    "confidence": 0.9876,     // 얼굴 감지 신뢰도
    "quality_score": 0.85     // 이미지 품질 점수
  }]
}
```

**권장 기준:**
- **confidence ≥ 0.8**: 사용 가능
- **quality_score ≥ 0.7**: 좋은 품질
- 둘 다 만족 시 신뢰할 수 있는 결과

### compare-faces API
```json
{
  "similarity": 0.34,
  "confidence": 0.92,        // 원본 얼굴 신뢰도
  "face_matches": [{
    "similarity": 0.34,
    "confidence": 0.88       // 대상 얼굴 신뢰도
  }]
}
```

**권장 기준:**
- **모든 confidence ≥ 0.8**: 유사도 결과 신뢰 가능
- **하나라도 < 0.5**: 재촬영 권장

### analyze-family-similarity API
```json
{
  "similarity": 0.34,
  "confidence": 0.92,        // 부모 얼굴 신뢰도
  "parent_face": {
    "confidence": 0.92
  },
  "child_face": {
    "confidence": 0.88
  }
}
```

## 🚨 신뢰도별 대응 방안

### 높은 신뢰도 (0.8 이상)
```typescript
function handleHighConfidence(result: any) {
  return {
    status: "success",
    message: "분석 결과를 신뢰할 수 있습니다",
    action: "결과 그대로 사용",
    ui: "정상적인 결과 표시"
  };
}
```

### 보통 신뢰도 (0.5 ~ 0.8)
```typescript
function handleMediumConfidence(result: any) {
  return {
    status: "warning", 
    message: "결과 참고용으로 사용하세요",
    action: "추가 검증 권장",
    ui: "주의 표시와 함께 결과 표시"
  };
}
```

### 낮은 신뢰도 (0.5 미만)
```typescript
function handleLowConfidence(result: any) {
  return {
    status: "error",
    message: "더 좋은 품질의 사진으로 재시도하세요", 
    action: "재촬영 요청",
    ui: "오류 메시지와 개선 가이드 표시"
  };
}
```

## 📈 품질 개선 가이드

### 신뢰도 향상 방법

#### 1. 이미지 품질 개선
```typescript
interface QualityRequirements {
  minResolution: { width: number; height: number };
  maxFileSize: number;
  supportedFormats: string[];
  lighting: string;
  angle: string;
}

const optimalRequirements: QualityRequirements = {
  minResolution: { width: 300, height: 300 },
  maxFileSize: 10 * 1024 * 1024, // 10MB
  supportedFormats: ['jpeg', 'jpg', 'png'],
  lighting: "밝고 균등한 조명",
  angle: "정면 ±15도 이내"
};
```

#### 2. 촬영 환경 최적화
- **조명**: 자연광 또는 밝은 실내등
- **배경**: 단순하고 얼굴과 대조되는 색상
- **거리**: 얼굴이 이미지의 30-50% 차지
- **각도**: 정면에서 ±15도 이내
- **표정**: 자연스러운 무표정 또는 미소

#### 3. 기술적 최적화
```typescript
// 이미지 전처리
function preprocessImage(file: File): Promise<string> {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d')!;
    const img = new Image();
    
    img.onload = () => {
      // 적절한 크기로 리사이즈
      const maxSize = 1024;
      let { width, height } = img;
      
      if (width > height && width > maxSize) {
        height = (height * maxSize) / width;
        width = maxSize;
      } else if (height > maxSize) {
        width = (width * maxSize) / height;
        height = maxSize;
      }
      
      canvas.width = width;
      canvas.height = height;
      
      // 이미지 그리기 및 품질 향상
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(img, 0, 0, width, height);
      
      resolve(canvas.toDataURL('image/jpeg', 0.9));
    };
    
    img.src = URL.createObjectURL(file);
  });
}
```

## 🔧 실시간 품질 모니터링

### React 컴포넌트 예시
```tsx
function ConfidenceIndicator({ confidence }: { confidence: number }) {
  const getConfidenceLevel = (conf: number) => {
    if (conf >= 0.9) return { level: '매우 높음', color: '#27AE60', icon: '🟢' };
    if (conf >= 0.7) return { level: '높음', color: '#F39C12', icon: '🟡' };
    if (conf >= 0.5) return { level: '보통', color: '#E67E22', icon: '🟠' };
    if (conf >= 0.3) return { level: '낮음', color: '#E74C3C', icon: '🔴' };
    return { level: '매우 낮음', color: '#95A5A6', icon: '❌' };
  };
  
  const { level, color, icon } = getConfidenceLevel(confidence);
  
  return (
    <div className="confidence-indicator">
      <div className="confidence-bar">
        <div 
          className="confidence-fill"
          style={{ 
            width: `${confidence * 100}%`,
            backgroundColor: color 
          }}
        />
      </div>
      <div className="confidence-info">
        <span className="confidence-icon">{icon}</span>
        <span className="confidence-level">{level}</span>
        <span className="confidence-value">{(confidence * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
}
```

### 실시간 품질 체크
```typescript
function checkRealTimeQuality(videoElement: HTMLVideoElement): QualityCheck {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d')!;
  
  canvas.width = videoElement.videoWidth;
  canvas.height = videoElement.videoHeight;
  ctx.drawImage(videoElement, 0, 0);
  
  // 간단한 품질 지표들
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const brightness = calculateBrightness(imageData);
  const contrast = calculateContrast(imageData);
  const blur = calculateBlur(imageData);
  
  return {
    brightness: brightness > 50 && brightness < 200, // 적절한 밝기
    contrast: contrast > 30,                         // 충분한 대비
    sharpness: blur < 0.5,                          // 선명함
    overall: brightness > 50 && contrast > 30 && blur < 0.5
  };
}
```

## 📋 체크리스트

### 촬영 전 확인사항
- [ ] 충분한 조명 확보
- [ ] 정면 얼굴 각도 확인  
- [ ] 얼굴이 프레임의 30-50% 차지
- [ ] 배경이 단순하고 깔끔
- [ ] 안경, 마스크 등 제거 (필요시)

### 결과 검증 확인사항
- [ ] 얼굴 감지 신뢰도 ≥ 0.8
- [ ] 이미지 품질 점수 ≥ 0.7
- [ ] 바운딩 박스가 얼굴을 정확히 포함
- [ ] 랜드마크가 올바른 위치에 표시
- [ ] 나이/성별 예측이 합리적

## 🔗 관련 문서

- [유사도 점수 해석](SIMILARITY_SCORES.md)
- [얼굴 감지 결과 해석](FACE_DETECTION.md)
- [API 설계 문서](../API_DESIGN.md)
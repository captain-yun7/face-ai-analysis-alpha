# 얼굴 감지 결과 해석 가이드

> InsightFace 얼굴 감지 API 응답 데이터를 올바르게 해석하고 활용하는 방법입니다.

## 📊 API 응답 구조

### detect-faces 응답 예시
```json
{
  "faces": [
    {
      "bounding_box": {
        "x": 150.2,
        "y": 80.5, 
        "width": 200.3,
        "height": 250.1
      },
      "confidence": 0.9876,
      "age": 25,
      "gender": {
        "value": "Male",
        "confidence": 0.95
      },
      "landmarks": [
        [180.1, 120.3], // 왼쪽 눈
        [220.4, 118.7], // 오른쪽 눈
        [200.2, 140.5], // 코
        [185.6, 180.2], // 왼쪽 입꼬리
        [215.8, 178.9]  // 오른쪽 입꼬리
      ],
      "embedding": [0.123, -0.456, ...], // 512차원 벡터
      "quality_score": 0.85
    }
  ],
  "face_count": 1
}
```

## 🎯 Bounding Box 활용

### 좌표 시스템
- **원점**: 이미지 왼쪽 상단 (0, 0)
- **x**: 가로 좌표 (오른쪽으로 증가)
- **y**: 세로 좌표 (아래쪽으로 증가)
- **width/height**: 박스 크기

### 활용 예시
```typescript
interface BoundingBox {
  x: number;
  y: number; 
  width: number;
  height: number;
}

// 얼굴 영역 추출
function extractFaceRegion(imageElement: HTMLImageElement, bbox: BoundingBox) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d')!;
  
  canvas.width = bbox.width;
  canvas.height = bbox.height;
  
  ctx.drawImage(
    imageElement,
    bbox.x, bbox.y, bbox.width, bbox.height, // 소스 영역
    0, 0, bbox.width, bbox.height            // 대상 영역
  );
  
  return canvas.toDataURL();
}

// 얼굴 박스 그리기
function drawFaceBox(ctx: CanvasRenderingContext2D, bbox: BoundingBox, confidence: number) {
  const color = confidence > 0.8 ? '#00FF00' : confidence > 0.5 ? '#FFA500' : '#FF0000';
  
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.strokeRect(bbox.x, bbox.y, bbox.width, bbox.height);
  
  // 신뢰도 표시
  ctx.fillStyle = color;
  ctx.font = '14px Arial';
  ctx.fillText(`${(confidence * 100).toFixed(1)}%`, bbox.x, bbox.y - 5);
}
```

## 📍 Landmarks 해석

### 5점 랜드마크 (기본)
```typescript
interface Landmarks {
  leftEye: [number, number];     // 왼쪽 눈 중심
  rightEye: [number, number];    // 오른쪽 눈 중심  
  nose: [number, number];        // 코끝
  leftMouth: [number, number];   // 왼쪽 입꼬리
  rightMouth: [number, number];  // 오른쪽 입꼬리
}

function parseLandmarks(landmarks: number[][]): Landmarks {
  return {
    leftEye: landmarks[0],
    rightEye: landmarks[1], 
    nose: landmarks[2],
    leftMouth: landmarks[3],
    rightMouth: landmarks[4]
  };
}
```

### 활용 예시
```typescript
// 얼굴 기울기 계산
function calculateFaceAngle(landmarks: Landmarks): number {
  const [leftX, leftY] = landmarks.leftEye;
  const [rightX, rightY] = landmarks.rightEye;
  
  const angle = Math.atan2(rightY - leftY, rightX - leftX) * 180 / Math.PI;
  return angle;
}

// 얼굴 중심점 계산  
function getFaceCenter(landmarks: Landmarks): [number, number] {
  const [leftX, leftY] = landmarks.leftEye;
  const [rightX, rightY] = landmarks.rightEye;
  
  return [(leftX + rightX) / 2, (leftY + rightY) / 2];
}

// 눈 간격 계산
function getEyeDistance(landmarks: Landmarks): number {
  const [leftX, leftY] = landmarks.leftEye;
  const [rightX, rightY] = landmarks.rightEye;
  
  return Math.sqrt((rightX - leftX) ** 2 + (rightY - leftY) ** 2);
}
```

## 🎭 나이/성별 분석

### 나이 예측 해석
```typescript
interface AgeAnalysis {
  estimatedAge: number;
  ageRange: string;
  reliability: string;
}

function analyzeAge(age: number): AgeAnalysis {
  let ageRange: string;
  let reliability: string;
  
  if (age < 18) {
    ageRange = "미성년자";
    reliability = "보통"; // 어린이 나이 예측은 부정확할 수 있음
  } else if (age < 30) {
    ageRange = "청년층";
    reliability = "높음";
  } else if (age < 50) {
    ageRange = "중년층"; 
    reliability = "높음";
  } else {
    ageRange = "장년층";
    reliability = "보통"; // 고령층 구분이 어려울 수 있음
  }
  
  return { estimatedAge: age, ageRange, reliability };
}
```

### 성별 분석 해석
```typescript
interface GenderAnalysis {
  gender: string;
  confidence: number;
  reliability: string;
}

function analyzeGender(gender: {value: string, confidence: number}): GenderAnalysis {
  let reliability: string;
  
  if (gender.confidence > 0.9) {
    reliability = "매우 높음";
  } else if (gender.confidence > 0.7) {
    reliability = "높음"; 
  } else if (gender.confidence > 0.5) {
    reliability = "보통";
  } else {
    reliability = "낮음";
  }
  
  return {
    gender: gender.value,
    confidence: gender.confidence,
    reliability
  };
}
```

## 📊 신뢰도 기준

### 얼굴 감지 Confidence
- **0.95 이상**: 확실한 얼굴 (권장)
- **0.8~0.95**: 높은 신뢰도 
- **0.5~0.8**: 보통 신뢰도 (주의)
- **0.5 미만**: 낮은 신뢰도 (재촬영 권장)

### Quality Score 기준
- **0.9 이상**: 최고 품질
- **0.7~0.9**: 좋은 품질
- **0.5~0.7**: 보통 품질
- **0.5 미만**: 낮은 품질

## ⚠️ 일반적인 문제와 해결

### 낮은 신뢰도 원인
1. **흐릿한 이미지**: 해상도 향상 필요
2. **옆얼굴**: 정면 얼굴로 재촬영
3. **가려진 얼굴**: 마스크, 선글라스 제거
4. **어두운 조명**: 밝은 환경에서 촬영
5. **작은 얼굴**: 더 가까이에서 촬영

### 개선 방법
```typescript
interface QualityCheck {
  isGoodQuality: boolean;
  issues: string[];
  recommendations: string[];
}

function checkFaceQuality(face: any): QualityCheck {
  const issues: string[] = [];
  const recommendations: string[] = [];
  
  // 신뢰도 검사
  if (face.confidence < 0.8) {
    issues.push("얼굴 감지 신뢰도 낮음");
    recommendations.push("더 선명한 사진으로 재시도");
  }
  
  // 품질 점수 검사
  if (face.quality_score < 0.7) {
    issues.push("이미지 품질 낮음");
    recommendations.push("해상도가 높은 이미지 사용");
  }
  
  // 얼굴 크기 검사
  const faceSize = face.bounding_box.width * face.bounding_box.height;
  if (faceSize < 10000) { // 100x100 픽셀 미만
    issues.push("얼굴 크기 너무 작음");
    recommendations.push("더 가까이에서 촬영");
  }
  
  return {
    isGoodQuality: issues.length === 0,
    issues,
    recommendations
  };
}
```

## 🔗 관련 문서

- [유사도 점수 해석](SIMILARITY_SCORES.md)
- [신뢰도 수준 해석](CONFIDENCE_LEVELS.md)
- [API 설계 문서](../API_DESIGN.md)
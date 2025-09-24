# 🔌 API 설계 문서 (API Design Document)

## 📌 개요

InsightFace 기반 얼굴 분석 백엔드 API 설계 문서입니다. 기존 AWS Rekognition API와 호환성을 유지하면서 확장된 기능을 제공합니다.

## 🎯 설계 원칙

1. **호환성**: 기존 Next.js 클라이언트 코드 변경 최소화
2. **확장성**: 새로운 AI 기능 추가 용이
3. **성능**: 배치 처리 및 최적화 지원
4. **표준화**: RESTful API 원칙 준수

## 🔄 기존 AWS Rekognition API 매핑

### 1. 얼굴 비교 API

#### **기존 AWS API**
```typescript
POST /api/rekognition/compare-faces
Request: {
  sourceImage: string (base64),
  targetImage: string (base64),
  similarityThreshold?: number
}

Response: {
  success: boolean,
  data: {
    similarity: number,
    faceMatches: Array<{
      similarity: number,
      face: {
        boundingBox: { width, height, left, top },
        confidence: number
      }
    }>,
    sourceImageFace?: FaceDetail,
    unmatchedFaces: Array<FaceDetail>
  }
}
```

#### **새로운 InsightFace API**
```python
POST /compare-faces
Request: {
  source_image: string (base64),
  target_image: string (base64),
  similarity_threshold?: float = 0.01
}

Response: {
  success: bool,
  data: {
    similarity: float,           # 0.0 ~ 1.0 → 0 ~ 100으로 변환
    confidence: float,
    face_matches: [
      {
        similarity: float,
        bounding_box: { x, y, width, height },
        confidence: float,
        landmarks: Array<{x, y, type}>
      }
    ],
    source_face: FaceDetail,
    target_faces: Array<FaceDetail>,
    processing_time_ms: int
  }
}
```

### 2. 얼굴 감지 API

#### **기존 AWS API**
```typescript
POST /api/rekognition/detect-faces
Request: {
  image: string (base64)
}

Response: {
  success: boolean,
  data: Array<{
    ageRange: { low: number, high: number },
    gender: { value: string, confidence: number },
    emotions: Array<{ type: string, confidence: number }>,
    smile: { value: boolean, confidence: number },
    eyeglasses: { value: boolean, confidence: number },
    boundingBox: { width, height, left, top },
    confidence: number
  }>
}
```

#### **새로운 InsightFace API**
```python
POST /detect-faces
Request: {
  image: string (base64),
  include_landmarks?: bool = false,
  include_attributes?: bool = true
}

Response: {
  success: bool,
  data: {
    faces: [
      {
        bounding_box: { x, y, width, height },
        confidence: float,
        age: int,
        gender: { value: str, confidence: float },
        emotions: [{ emotion: str, confidence: float }],
        landmarks: Array<{x, y, type}>,  # optional
        embedding: Array<float>,         # 512차원 벡터
        quality_score: float
      }
    ],
    face_count: int,
    processing_time_ms: int
  }
}
```

## 🚀 확장 API (새로운 기능)

### 3. 배치 얼굴 분석 API

```python
POST /batch-analysis
Request: {
  images: [
    {
      id: string,
      image: string (base64),
      name?: string
    }
  ],
  analysis_type: "similarity_matrix" | "find_best_match" | "group_similar"
}

Response: {
  success: bool,
  data: {
    similarity_matrix?: Array<Array<float>>,  # N x N 매트릭스
    best_matches?: [
      {
        source_id: str,
        target_id: str,
        similarity: float
      }
    ],
    groups?: [
      {
        group_id: int,
        members: Array<string>,  # image IDs
        avg_similarity: float
      }
    ],
    processing_time_ms: int
  }
}
```

### 4. 실시간 얼굴 추적 API

```python
POST /track-faces
Request: {
  frames: [
    {
      timestamp: int,  # ms
      image: string (base64)
    }
  ],
  track_identity?: bool = true
}

Response: {
  success: bool,
  data: {
    tracks: [
      {
        track_id: int,
        frames: [
          {
            timestamp: int,
            bounding_box: object,
            confidence: float
          }
        ],
        identity_confidence: float
      }
    ]
  }
}
```

### 5. 얼굴 임베딩 추출 API

```python
POST /extract-embedding
Request: {
  image: string (base64),
  face_id?: int = 0  # 여러 얼굴 중 선택
}

Response: {
  success: bool,
  data: {
    embedding: Array<float>,  # 512차원
    bounding_box: object,
    confidence: float,
    landmarks: Array<object>
  }
}
```

## 🔧 유틸리티 API

### 6. 헬스 체크 API

```python
GET /health
Response: {
  status: "healthy" | "unhealthy",
  model_loaded: bool,
  gpu_available: bool,
  memory_usage: {
    used_mb: int,
    total_mb: int
  },
  version: string
}
```

### 7. 모델 정보 API

```python
GET /model-info
Response: {
  model_name: "arcface_r100_v1",
  input_size: [112, 112],
  embedding_size: 512,
  supported_features: Array<string>,
  performance_metrics: {
    accuracy_lfw: 0.9983,
    inference_time_ms: 15
  }
}
```

## 📊 응답 포맷 표준화

### 성공 응답
```python
{
  "success": true,
  "data": { ... },
  "metadata": {
    "processing_time_ms": int,
    "model_version": string,
    "request_id": string
  }
}
```

### 에러 응답
```python
{
  "success": false,
  "error": {
    "code": "INVALID_IMAGE" | "MODEL_ERROR" | "PROCESSING_ERROR",
    "message": string,
    "details": object
  },
  "metadata": {
    "request_id": string,
    "timestamp": string
  }
}
```

## 🔐 인증 및 보안

### API 키 인증 (선택사항)
```http
Headers:
  X-API-Key: your-api-key
  Content-Type: application/json
```

### Rate Limiting
```python
# 기본 제한
- 분당 100회 요청
- 시간당 1000회 요청
- 일일 10000회 요청

# 응답 헤더
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## 🚦 상태 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 성공적인 요청 |
| 400 | Bad Request | 잘못된 요청 파라미터 |
| 401 | Unauthorized | 인증 실패 |
| 413 | Payload Too Large | 이미지 크기 초과 |
| 422 | Unprocessable Entity | 얼굴 감지 실패 |
| 429 | Too Many Requests | Rate limit 초과 |
| 500 | Internal Server Error | 서버 내부 오류 |

## 📝 요청/응답 예시

### 얼굴 비교 요청 예시
```bash
# 로컬 개발 환경
curl -X POST http://localhost:8000/compare-faces \

# 운영 환경 (Oracle Cloud)  
curl -X POST http://144.24.82.25:8000/compare-faces \
  -H "Content-Type: application/json" \
  -d '{
    "source_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA...",
    "target_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA...",
    "similarity_threshold": 0.3
  }'
```

### 응답 예시
```json
{
  "success": true,
  "data": {
    "similarity": 0.875,
    "confidence": 0.92,
    "face_matches": [
      {
        "similarity": 0.875,
        "bounding_box": {
          "x": 100,
          "y": 50,
          "width": 200,
          "height": 250
        },
        "confidence": 0.95
      }
    ],
    "processing_time_ms": 45
  },
  "metadata": {
    "model_version": "arcface_r100_v1",
    "request_id": "req_123456789"
  }
}
```

## 🔄 Next.js 연동 고려사항

### 1. 응답 포맷 변환
```typescript
// 응답 변환 함수
function convertToAWSFormat(insightFaceResponse) {
  return {
    success: insightFaceResponse.success,
    data: {
      similarity: insightFaceResponse.data.similarity * 100, // 0-1 → 0-100
      faceMatches: insightFaceResponse.data.face_matches.map(match => ({
        similarity: match.similarity * 100,
        face: {
          boundingBox: {
            width: match.bounding_box.width / imageWidth,   // 정규화
            height: match.bounding_box.height / imageHeight,
            left: match.bounding_box.x / imageWidth,
            top: match.bounding_box.y / imageHeight
          },
          confidence: match.confidence * 100
        }
      }))
    }
  };
}
```

### 2. 에러 처리 통일
```typescript
// 에러 매핑
const errorCodeMap = {
  'INVALID_IMAGE': 'Invalid image format',
  'MODEL_ERROR': 'Face analysis failed',
  'PROCESSING_ERROR': 'Internal processing error'
};
```

## 📈 성능 목표

| 메트릭 | 목표 값 |
|--------|---------|
| **응답 시간** | < 100ms (단일 비교) |
| **처리량** | > 50 req/sec |
| **정확도** | > 99% (LFW 기준) |
| **메모리 사용** | < 2GB |
| **가용성** | > 99.9% |

---

**작성일**: 2025-09-19  
**버전**: 1.0.0  
**작성자**: AI Backend Team
# Next.js 연동 가이드

> Face Analysis API를 Next.js 프론트엔드와 연동하는 완전 가이드입니다.

## 📋 연동 개요

이 API는 Next.js 애플리케이션과 완벽하게 호환되도록 설계되었습니다:

- ✅ **CORS 설정 완료**: `localhost:3000`, `localhost:3001` 허용
- ✅ **TypeScript 지원**: 타입 정의 포함
- ✅ **Base64 이미지 처리**: 파일 업로드 간편화
- ✅ **성능 최적화**: 평균 응답시간 0.18초

## 🚀 빠른 시작

### 1. API 서버 실행 확인

```bash
# API 서버 상태 확인
curl http://localhost:8000/health

# 예상 응답:
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": false,
  "memory_usage": {...},
  "version": "1.0.0"
}
```

### 2. Next.js 프로젝트 설정

```bash
# Next.js 프로젝트 생성 (없는 경우)
npx create-next-app@latest face-analysis-frontend
cd face-analysis-frontend

# 필요한 패키지 설치
npm install axios
# 또는 fetch API 사용 (추가 설치 불필요)
```

## 📝 TypeScript 타입 정의

```typescript
// types/api.ts
export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  gpu_available: boolean;
  memory_usage: {
    used_mb: number;
    total_mb: number;
    percent: number;
  };
  version: string;
  uptime_seconds: number;
}

export interface FaceDetectionRequest {
  image: string;                    // Base64 이미지 (data:image/jpeg;base64,...)
  include_landmarks?: boolean;      // 기본값: false
  include_attributes?: boolean;     // 기본값: true
  max_faces?: number;              // 기본값: 10
}

export interface FaceDetectionResponse {
  success: boolean;
  metadata: {
    processing_time_ms: number;
    model_version: string;
    request_id: string;
    timestamp: string;
  };
  data: {
    faces: Array<{
      bbox: [number, number, number, number];  // [x1, y1, x2, y2]
      confidence: number;
      landmarks?: Array<[number, number]>;     // 얼굴 특징점
      attributes?: {
        age?: number;
        gender?: string;
        emotion?: string;
      };
    }>;
    face_count: number;
  };
}

export interface FaceComparisonRequest {
  source_image: string;            // Base64 이미지
  target_image: string;            // Base64 이미지  
  similarity_threshold?: number;   // 기본값: 0.01
}

export interface FaceComparisonResponse {
  success: boolean;
  metadata: {
    processing_time_ms: number;
    model_version: string;
    request_id: string;
    timestamp: string;
  };
  data: {
    similarity: number;             // 0.0 ~ 1.0
    is_same_person: boolean;
    confidence: number;
    details: {
      source_face_count: number;
      target_face_count: number;
      comparison_method: string;
    };
  };
}

export interface EmbeddingRequest {
  image: string;                   // Base64 이미지
  face_id?: number;               // 기본값: 0 (첫 번째 얼굴)
  normalize?: boolean;            // 기본값: true
}

export interface EmbeddingResponse {
  success: boolean;
  metadata: {
    processing_time_ms: number;
    model_version: string;
    request_id: string;
    timestamp: string;
  };
  data: {
    embedding: number[];           // 512차원 벡터
    face_id: number;
    confidence: number;
  };
}
```

## 🔧 API 클라이언트 설정

```typescript
// lib/api-client.ts
import axios from 'axios';
import type { 
  HealthResponse, 
  FaceDetectionRequest, 
  FaceDetectionResponse,
  FaceComparisonRequest,
  FaceComparisonResponse,
  EmbeddingRequest,
  EmbeddingResponse
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30초 타임아웃
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 (로깅용)
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

// 응답 인터셉터 (에러 처리)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Error]', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export class FaceAnalysisAPI {
  // 헬스체크
  static async health(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>('/health');
    return response.data;
  }

  // 얼굴 감지
  static async detectFaces(request: FaceDetectionRequest): Promise<FaceDetectionResponse> {
    const response = await apiClient.post<FaceDetectionResponse>('/detect-faces', request);
    return response.data;
  }

  // 얼굴 비교
  static async compareFaces(request: FaceComparisonRequest): Promise<FaceComparisonResponse> {
    const response = await apiClient.post<FaceComparisonResponse>('/compare-faces', request);
    return response.data;
  }

  // 임베딩 추출
  static async extractEmbedding(request: EmbeddingRequest): Promise<EmbeddingResponse> {
    const response = await apiClient.post<EmbeddingResponse>('/extract-embedding', request);
    return response.data;
  }
}

export default FaceAnalysisAPI;
```

## 🖼️ 이미지 처리 유틸리티

```typescript
// lib/image-utils.ts

/**
 * File 객체를 Base64 문자열로 변환
 */
export const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      resolve(result);
    };
    reader.onerror = () => reject(new Error('파일 읽기 실패'));
    reader.readAsDataURL(file);
  });
};

/**
 * 이미지 크기 조정 (성능 최적화용)
 */
export const resizeImage = (file: File, maxWidth: number = 800, maxHeight: number = 600): Promise<string> => {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      // 비율 유지하면서 크기 조정
      const ratio = Math.min(maxWidth / img.width, maxHeight / img.height);
      const width = img.width * ratio;
      const height = img.height * ratio;
      
      canvas.width = width;
      canvas.height = height;
      
      ctx?.drawImage(img, 0, 0, width, height);
      
      canvas.toBlob((blob) => {
        if (blob) {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result as string);
          reader.readAsDataURL(blob);
        } else {
          reject(new Error('이미지 리사이징 실패'));
        }
      }, 'image/jpeg', 0.8);
    };
    
    img.onerror = () => reject(new Error('이미지 로드 실패'));
    img.src = URL.createObjectURL(file);
  });
};

/**
 * 이미지 유효성 검사
 */
export const validateImageFile = (file: File): boolean => {
  // 파일 타입 검사
  if (!file.type.startsWith('image/')) {
    return false;
  }
  
  // 파일 크기 검사 (10MB 제한)
  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    return false;
  }
  
  return true;
};
```

## 🎯 실제 사용 예제

### 1. 얼굴 감지 컴포넌트

```tsx
// components/FaceDetection.tsx
'use client';

import { useState } from 'react';
import { FaceAnalysisAPI } from '@/lib/api-client';
import { fileToBase64, validateImageFile, resizeImage } from '@/lib/image-utils';
import type { FaceDetectionResponse } from '@/types/api';

export default function FaceDetection() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<FaceDetectionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && validateImageFile(file)) {
      setSelectedFile(file);
      setError(null);
    } else {
      setError('올바른 이미지 파일을 선택해주세요 (최대 10MB)');
    }
  };

  const detectFaces = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);

    try {
      // 이미지 크기 조정 후 Base64 변환
      const base64Image = await resizeImage(selectedFile, 800, 600);
      
      // API 호출
      const response = await FaceAnalysisAPI.detectFaces({
        image: base64Image,
        include_landmarks: true,
        include_attributes: true,
        max_faces: 10
      });

      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : '얼굴 감지 실패');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">얼굴 감지</h2>
      
      {/* 파일 선택 */}
      <div className="mb-4">
        <input
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="block w-full text-sm text-gray-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-full file:border-0
            file:text-sm file:font-semibold
            file:bg-blue-50 file:text-blue-700
            hover:file:bg-blue-100"
        />
      </div>

      {/* 분석 버튼 */}
      <button
        onClick={detectFaces}
        disabled={!selectedFile || loading}
        className="px-4 py-2 bg-blue-600 text-white rounded 
          disabled:bg-gray-400 disabled:cursor-not-allowed
          hover:bg-blue-700 transition-colors"
      >
        {loading ? '분석 중...' : '얼굴 감지'}
      </button>

      {/* 에러 표시 */}
      {error && (
        <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* 결과 표시 */}
      {result && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-2">분석 결과</h3>
          <div className="bg-gray-100 p-4 rounded">
            <p><strong>감지된 얼굴 수:</strong> {result.data.face_count}</p>
            <p><strong>처리 시간:</strong> {result.metadata.processing_time_ms}ms</p>
            
            {result.data.faces.map((face, index) => (
              <div key={index} className="mt-3 p-3 bg-white rounded border">
                <h4 className="font-medium">얼굴 {index + 1}</h4>
                <p>신뢰도: {(face.confidence * 100).toFixed(1)}%</p>
                <p>위치: [{face.bbox.map(v => v.toFixed(0)).join(', ')}]</p>
                {face.attributes && (
                  <div className="mt-2">
                    {face.attributes.age && <p>나이: {face.attributes.age}세</p>}
                    {face.attributes.gender && <p>성별: {face.attributes.gender}</p>}
                    {face.attributes.emotion && <p>감정: {face.attributes.emotion}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

### 2. 얼굴 비교 컴포넌트

```tsx
// components/FaceComparison.tsx
'use client';

import { useState } from 'react';
import { FaceAnalysisAPI } from '@/lib/api-client';
import { resizeImage, validateImageFile } from '@/lib/image-utils';
import type { FaceComparisonResponse } from '@/types/api';

export default function FaceComparison() {
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [targetFile, setTargetFile] = useState<File | null>(null);
  const [result, setResult] = useState<FaceComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const compareFaces = async () => {
    if (!sourceFile || !targetFile) return;

    setLoading(true);
    setError(null);

    try {
      const [sourceBase64, targetBase64] = await Promise.all([
        resizeImage(sourceFile, 400, 400),
        resizeImage(targetFile, 400, 400)
      ]);

      const response = await FaceAnalysisAPI.compareFaces({
        source_image: sourceBase64,
        target_image: targetBase64,
        similarity_threshold: 0.6
      });

      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : '얼굴 비교 실패');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">얼굴 비교</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* 원본 이미지 */}
        <div>
          <h3 className="text-lg font-medium mb-2">원본 이미지</h3>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file && validateImageFile(file)) {
                setSourceFile(file);
              }
            }}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4"
          />
          {sourceFile && (
            <img
              src={URL.createObjectURL(sourceFile)}
              alt="원본 이미지"
              className="mt-2 max-w-full h-48 object-cover rounded border"
            />
          )}
        </div>

        {/* 비교 이미지 */}
        <div>
          <h3 className="text-lg font-medium mb-2">비교 이미지</h3>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file && validateImageFile(file)) {
                setTargetFile(file);
              }
            }}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4"
          />
          {targetFile && (
            <img
              src={URL.createObjectURL(targetFile)}
              alt="비교 이미지"
              className="mt-2 max-w-full h-48 object-cover rounded border"
            />
          )}
        </div>
      </div>

      <button
        onClick={compareFaces}
        disabled={!sourceFile || !targetFile || loading}
        className="px-6 py-3 bg-green-600 text-white rounded-lg 
          disabled:bg-gray-400 disabled:cursor-not-allowed
          hover:bg-green-700 transition-colors"
      >
        {loading ? '비교 중...' : '얼굴 비교'}
      </button>

      {error && (
        <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 p-6 bg-gray-50 rounded-lg">
          <h3 className="text-xl font-semibold mb-4">비교 결과</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white p-4 rounded border">
              <h4 className="font-medium text-gray-700">유사도</h4>
              <p className="text-3xl font-bold text-blue-600">
                {(result.data.similarity * 100).toFixed(1)}%
              </p>
            </div>
            
            <div className="bg-white p-4 rounded border">
              <h4 className="font-medium text-gray-700">동일인 여부</h4>
              <p className={`text-2xl font-bold ${
                result.data.is_same_person ? 'text-green-600' : 'text-red-600'
              }`}>
                {result.data.is_same_person ? '동일인' : '다른 사람'}
              </p>
            </div>
          </div>

          <div className="mt-4 text-sm text-gray-600">
            <p>신뢰도: {(result.data.confidence * 100).toFixed(1)}%</p>
            <p>처리 시간: {result.metadata.processing_time_ms}ms</p>
            <p>요청 ID: {result.metadata.request_id}</p>
          </div>
        </div>
      )}
    </div>
  );
}
```

## 🔧 환경 설정

### .env.local 파일

```bash
# API 서버 URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# 개발 환경에서만 사용
NEXT_PUBLIC_DEBUG=true
```

### next.config.js 설정

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // API 프록시 설정 (선택사항)
  async rewrites() {
    return [
      {
        source: '/api/face/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
  
  // 이미지 최적화 설정
  images: {
    domains: ['localhost'],
    formats: ['image/avif', 'image/webp'],
  },
};

module.exports = nextConfig;
```

## 📊 성능 최적화 팁

### 1. 이미지 크기 최적화
```typescript
// 큰 이미지는 리사이징 후 전송
const optimizedImage = await resizeImage(file, 800, 600);
```

### 2. 요청 캐싱
```typescript
// SWR 또는 React Query 사용 예제
import useSWR from 'swr';

const { data: health } = useSWR('/health', FaceAnalysisAPI.health, {
  refreshInterval: 30000, // 30초마다 갱신
});
```

### 3. 에러 핸들링
```typescript
try {
  const result = await FaceAnalysisAPI.detectFaces(request);
} catch (error) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 422) {
      // 잘못된 요청 데이터
    } else if (error.response?.status === 500) {
      // 서버 에러
    }
  }
}
```

## 🚀 배포 시 주의사항

### 1. CORS 설정 업데이트
```bash
# .env 파일에서 프로덕션 도메인 추가
CORS_ORIGINS=https://your-domain.com,http://localhost:3000
```

### 2. API URL 설정
```bash
# 프로덕션 환경에서
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

### 3. 보안 설정
- API 키 인증 활성화
- 요청 속도 제한 확인
- HTTPS 사용 필수

## 🔍 디버깅 가이드

### 1. 네트워크 에러
```bash
# API 서버 상태 확인
curl http://localhost:8000/health

# CORS 헤더 확인
curl -I -H "Origin: http://localhost:3000" http://localhost:8000/health
```

### 2. 이미지 형식 에러
- Base64 형식 확인: `data:image/jpeg;base64,/9j/4AAQ...`
- 파일 크기 제한: 10MB 이하
- 지원 형식: JPEG, PNG, WebP

### 3. 성능 이슈
- 이미지 크기 최적화
- 동시 요청 수 제한 (5개 이하 권장)
- 타임아웃 설정 (30초)

---

## 📚 추가 리소스

- [API 문서](http://localhost:8000/docs) - Swagger UI
- [성능 벤치마크](PERFORMANCE.md)
- [문제 해결 가이드](TROUBLESHOOTING.md)
- [개발 환경 가이드](DEVELOPMENT.md)

**이제 Next.js 애플리케이션에서 강력한 얼굴 분석 기능을 사용할 수 있습니다!** 🎉
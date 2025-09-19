#!/usr/bin/env python3
"""
API 테스트 스크립트
"""
import requests
import base64
from PIL import Image, ImageDraw
import io
import json

# 서버 URL
BASE_URL = "http://localhost:8000"

def create_test_face_image(size=(200, 200), face_color="pink"):
    """간단한 테스트용 얼굴 이미지 생성"""
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)
    
    # 얼굴 원
    face_size = min(size) - 40
    x1 = (size[0] - face_size) // 2
    y1 = (size[1] - face_size) // 2
    x2 = x1 + face_size
    y2 = y1 + face_size
    draw.ellipse([x1, y1, x2, y2], fill=face_color, outline='black')
    
    # 눈
    eye_size = face_size // 8
    left_eye_x = x1 + face_size // 4
    right_eye_x = x2 - face_size // 4
    eye_y = y1 + face_size // 3
    
    draw.ellipse([left_eye_x - eye_size, eye_y - eye_size, 
                  left_eye_x + eye_size, eye_y + eye_size], fill='black')
    draw.ellipse([right_eye_x - eye_size, eye_y - eye_size, 
                  right_eye_x + eye_size, eye_y + eye_size], fill='black')
    
    # 입
    mouth_y = y1 + face_size * 2 // 3
    mouth_width = face_size // 3
    mouth_x = (size[0] - mouth_width) // 2
    draw.arc([mouth_x, mouth_y - 10, mouth_x + mouth_width, mouth_y + 10], 
             start=0, end=180, fill='black', width=3)
    
    return img

def image_to_base64(img):
    """이미지를 base64로 변환"""
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_data = buffer.getvalue()
    return f"data:image/jpeg;base64,{base64.b64encode(img_data).decode()}"

def test_health():
    """헬스체크 테스트"""
    print("=== 헬스체크 테스트 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"서버 상태: {data['status']}")
            print(f"모델 로드됨: {data['model_loaded']}")
            print(f"메모리 사용량: {data['memory_usage']['percent']:.1f}%")
            print("✅ 헬스체크 성공")
        else:
            print(f"❌ 헬스체크 실패: {response.text}")
    except Exception as e:
        print(f"❌ 헬스체크 오류: {e}")

def test_face_detection():
    """얼굴 감지 테스트"""
    print("\n=== 얼굴 감지 테스트 ===")
    try:
        # 테스트 이미지 생성
        test_img = create_test_face_image()
        img_base64 = image_to_base64(test_img)
        
        # API 요청
        payload = {
            "image": img_base64,
            "include_landmarks": False,
            "include_attributes": True,
            "max_faces": 10
        }
        
        response = requests.post(f"{BASE_URL}/detect-faces", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"요청 성공: {data.get('success', False)}")
            if data.get('data'):
                face_count = data['data'].get('face_count', 0)
                print(f"감지된 얼굴 수: {face_count}")
                print("✅ 얼굴 감지 성공")
            else:
                print("⚠️ 얼굴이 감지되지 않음 (정상 - 단순한 그림)")
        else:
            print(f"❌ 얼굴 감지 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 얼굴 감지 오류: {e}")

def test_face_comparison():
    """얼굴 비교 테스트"""
    print("\n=== 얼굴 비교 테스트 ===")
    try:
        # 두 개의 비슷한 테스트 이미지 생성
        img1 = create_test_face_image(face_color="lightblue")
        img2 = create_test_face_image(face_color="lightgreen")
        
        img1_base64 = image_to_base64(img1)
        img2_base64 = image_to_base64(img2)
        
        # API 요청
        payload = {
            "source_image": img1_base64,
            "target_image": img2_base64,
            "similarity_threshold": 0.01
        }
        
        response = requests.post(f"{BASE_URL}/compare-faces", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"요청 성공: {data.get('success', False)}")
            if data.get('data'):
                similarity = data['data'].get('similarity', 0)
                print(f"유사도: {similarity:.3f}")
                print("✅ 얼굴 비교 성공")
            else:
                print("⚠️ 비교할 얼굴이 감지되지 않음 (정상 - 단순한 그림)")
        else:
            print(f"❌ 얼굴 비교 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 얼굴 비교 오류: {e}")

def test_embedding_extraction():
    """임베딩 추출 테스트"""
    print("\n=== 임베딩 추출 테스트 ===")
    try:
        # 테스트 이미지 생성
        test_img = create_test_face_image()
        img_base64 = image_to_base64(test_img)
        
        # API 요청
        payload = {
            "image": img_base64,
            "face_id": 0,
            "normalize": True
        }
        
        response = requests.post(f"{BASE_URL}/extract-embedding", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"요청 성공: {data.get('success', False)}")
            if data.get('data') and data['data'].get('embedding'):
                embedding_len = len(data['data']['embedding'])
                print(f"임베딩 차원: {embedding_len}")
                print("✅ 임베딩 추출 성공")
            else:
                print("⚠️ 임베딩을 추출할 얼굴이 감지되지 않음 (정상 - 단순한 그림)")
        else:
            print(f"❌ 임베딩 추출 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 임베딩 추출 오류: {e}")

def main():
    """메인 테스트 실행"""
    print("🚀 Face Analysis API 테스트 시작\n")
    
    # 순서대로 테스트 실행
    test_health()
    test_face_detection()
    test_face_comparison()
    test_embedding_extraction()
    
    print("\n✨ 모든 테스트 완료!")

if __name__ == "__main__":
    main()
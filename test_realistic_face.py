#!/usr/bin/env python3
"""
실제 얼굴 이미지를 사용한 API 테스트 스크립트
"""
import requests
import base64
import numpy as np
from PIL import Image, ImageDraw
import io
import json

# 서버 URL
BASE_URL = "http://localhost:8001"

def create_realistic_test_face(size=(400, 400)):
    """더 현실적인 테스트용 얼굴 이미지 생성"""
    img = Image.new('RGB', size, color=(255, 220, 177))  # 살색 배경
    draw = ImageDraw.Draw(img)
    
    # 더 큰 얼굴 원
    face_size = int(min(size) * 0.7)
    x1 = (size[0] - face_size) // 2
    y1 = (size[1] - face_size) // 2
    x2 = x1 + face_size
    y2 = y1 + face_size
    
    # 얼굴 타원 (더 현실적인 형태)
    draw.ellipse([x1, y1, x2, y2], fill=(255, 220, 177), outline=(200, 180, 140), width=3)
    
    # 더 큰 눈들
    eye_size = face_size // 12
    left_eye_x = x1 + face_size // 3
    right_eye_x = x2 - face_size // 3
    eye_y = y1 + face_size // 3
    
    # 눈 흰자
    draw.ellipse([left_eye_x - eye_size*2, eye_y - eye_size, 
                  left_eye_x + eye_size*2, eye_y + eye_size], fill='white', outline='black')
    draw.ellipse([right_eye_x - eye_size*2, eye_y - eye_size, 
                  right_eye_x + eye_size*2, eye_y + eye_size], fill='white', outline='black')
    
    # 동공
    draw.ellipse([left_eye_x - eye_size, eye_y - eye_size//2, 
                  left_eye_x + eye_size, eye_y + eye_size//2], fill='black')
    draw.ellipse([right_eye_x - eye_size, eye_y - eye_size//2, 
                  right_eye_x + eye_size, eye_y + eye_size//2], fill='black')
    
    # 코
    nose_x = size[0] // 2
    nose_y = y1 + face_size // 2
    nose_width = face_size // 15
    draw.ellipse([nose_x - nose_width, nose_y - nose_width*2, 
                  nose_x + nose_width, nose_y + nose_width], fill=(200, 180, 140))
    
    # 입
    mouth_y = y1 + face_size * 3 // 4
    mouth_width = face_size // 4
    mouth_x = (size[0] - mouth_width) // 2
    mouth_height = face_size // 20
    draw.ellipse([mouth_x, mouth_y - mouth_height, 
                  mouth_x + mouth_width, mouth_y + mouth_height], fill=(180, 100, 100))
    
    # 머리카락 (상단)
    hair_y = y1 - face_size // 10
    draw.ellipse([x1 - face_size//20, hair_y, x2 + face_size//20, y1 + face_size//3], 
                 fill=(101, 67, 33), outline=(80, 50, 20))
    
    return img

def create_gradient_face(size=(300, 300)):
    """그라디언트 효과가 있는 얼굴"""
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)
    
    # 큰 얼굴 영역
    face_size = int(min(size) * 0.8)
    x1 = (size[0] - face_size) // 2
    y1 = (size[1] - face_size) // 2
    x2 = x1 + face_size
    y2 = y1 + face_size
    
    # 얼굴 기본 형태 (타원)
    draw.ellipse([x1, y1, x2, y2], fill=(240, 200, 160), outline=(200, 160, 120), width=2)
    
    # 상세한 얼굴 특징들
    # 눈썹
    eyebrow_y = y1 + face_size // 4
    left_eyebrow_x = x1 + face_size // 3
    right_eyebrow_x = x2 - face_size // 3
    eyebrow_width = face_size // 8
    eyebrow_height = face_size // 30
    
    draw.ellipse([left_eyebrow_x - eyebrow_width, eyebrow_y - eyebrow_height,
                  left_eyebrow_x + eyebrow_width, eyebrow_y + eyebrow_height], fill=(101, 67, 33))
    draw.ellipse([right_eyebrow_x - eyebrow_width, eyebrow_y - eyebrow_height,
                  right_eyebrow_x + eyebrow_width, eyebrow_y + eyebrow_height], fill=(101, 67, 33))
    
    # 큰 눈들
    eye_y = y1 + face_size // 3
    eye_width = face_size // 10
    eye_height = face_size // 15
    
    # 왼쪽 눈
    draw.ellipse([left_eyebrow_x - eye_width, eye_y - eye_height,
                  left_eyebrow_x + eye_width, eye_y + eye_height], fill='white', outline='black', width=2)
    draw.ellipse([left_eyebrow_x - eye_width//2, eye_y - eye_height//2,
                  left_eyebrow_x + eye_width//2, eye_y + eye_height//2], fill='black')
    
    # 오른쪽 눈
    draw.ellipse([right_eyebrow_x - eye_width, eye_y - eye_height,
                  right_eyebrow_x + eye_width, eye_y + eye_height], fill='white', outline='black', width=2)
    draw.ellipse([right_eyebrow_x - eye_width//2, eye_y - eye_height//2,
                  right_eyebrow_x + eye_width//2, eye_y + eye_height//2], fill='black')
    
    # 코 (더 상세하게)
    nose_x = size[0] // 2
    nose_y = y1 + face_size // 2
    nose_width = face_size // 20
    nose_height = face_size // 8
    
    # 코 다리
    draw.line([nose_x, nose_y - nose_height, nose_x, nose_y + nose_height//2], 
              fill=(200, 160, 120), width=3)
    # 콧구멍
    draw.ellipse([nose_x - nose_width, nose_y + nose_height//3,
                  nose_x + nose_width, nose_y + nose_height], fill=(180, 140, 100))
    
    # 입 (더 현실적으로)
    mouth_y = y1 + face_size * 3 // 4
    mouth_width = face_size // 3
    mouth_height = face_size // 25
    mouth_x = (size[0] - mouth_width) // 2
    
    draw.ellipse([mouth_x, mouth_y - mouth_height,
                  mouth_x + mouth_width, mouth_y + mouth_height*2], fill=(200, 100, 100), outline=(150, 80, 80))
    
    return img

def image_to_base64(img):
    """이미지를 base64로 변환"""
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_data = buffer.getvalue()
    return f"data:image/jpeg;base64,{base64.b64encode(img_data).decode()}"

def test_age_estimation():
    """나이 추정 API 테스트 (여러 이미지)"""
    print("\n=== 나이 추정 API 테스트 ===")
    
    test_images = [
        ("realistic_face", create_realistic_test_face()),
        ("gradient_face", create_gradient_face()),
        ("large_realistic", create_realistic_test_face(size=(600, 600)))
    ]
    
    for name, test_img in test_images:
        try:
            print(f"\n--- {name} 테스트 ---")
            img_base64 = image_to_base64(test_img)
            
            # API 요청
            payload = {"image": img_base64}
            response = requests.post(f"{BASE_URL}/estimate-age", json=payload, timeout=30)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"요청 성공: {data.get('success', False)}")
                if data.get('data'):
                    age_data = data['data']
                    print(f"추정 나이: {age_data.get('age')}세")
                    print(f"연령대: {age_data.get('age_range')}")
                    print(f"신뢰도: {age_data.get('confidence', 0):.3f}")
                    print(f"감지된 얼굴 수: {age_data.get('face_count', 0)}")
                    print(f"✅ {name} 나이 추정 성공")
                else:
                    print(f"⚠️ {name} 데이터가 없습니다")
            else:
                print(f"❌ {name} 나이 추정 실패: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ {name} 나이 추정 오류: {e}")

def test_gender_estimation():
    """성별 확률 추정 API 테스트"""
    print("\n=== 성별 확률 추정 API 테스트 ===")
    
    test_images = [
        ("realistic_face", create_realistic_test_face()),
        ("gradient_face", create_gradient_face()),
        ("large_realistic", create_realistic_test_face(size=(600, 600)))
    ]
    
    for name, test_img in test_images:
        try:
            print(f"\n--- {name} 테스트 ---")
            img_base64 = image_to_base64(test_img)
            
            # API 요청
            payload = {"image": img_base64}
            response = requests.post(f"{BASE_URL}/estimate-gender", json=payload, timeout=30)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"요청 성공: {data.get('success', False)}")
                if data.get('data'):
                    gender_data = data['data']['gender_probability']
                    print(f"남성 확률: {gender_data.get('male_probability', 0):.3f}")
                    print(f"여성 확률: {gender_data.get('female_probability', 0):.3f}")
                    print(f"예측 성별: {gender_data.get('predicted_gender')}")
                    print(f"성별 신뢰도: {gender_data.get('gender_confidence', 0):.3f}")
                    print(f"감지된 얼굴 수: {data['data'].get('face_count', 0)}")
                    print(f"✅ {name} 성별 확률 추정 성공")
                else:
                    print(f"⚠️ {name} 데이터가 없습니다")
            else:
                print(f"❌ {name} 성별 확률 추정 실패: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ {name} 성별 확률 추정 오류: {e}")

def test_direct_detection():
    """직접 얼굴 감지 테스트 (기존 API 사용)"""
    print("\n=== 직접 얼굴 감지 테스트 ===")
    
    test_img = create_realistic_test_face(size=(500, 500))
    img_base64 = image_to_base64(test_img)
    
    try:
        payload = {
            "image": img_base64,
            "include_landmarks": True,
            "include_attributes": True,
            "max_faces": 5
        }
        
        response = requests.post(f"{BASE_URL}/detect-faces", json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"요청 성공: {data.get('success', False)}")
            if data.get('data'):
                face_data = data['data']
                print(f"감지된 얼굴 수: {face_data.get('face_count', 0)}")
                
                for i, face in enumerate(face_data.get('faces', [])):
                    print(f"  얼굴 {i+1}:")
                    print(f"    신뢰도: {face.get('confidence', 0):.3f}")
                    print(f"    나이: {face.get('age', 'N/A')}")
                    print(f"    성별: {face.get('gender', 'N/A')}")
                    bbox = face.get('bounding_box', {})
                    print(f"    위치: ({bbox.get('x', 0):.0f}, {bbox.get('y', 0):.0f}) 크기: {bbox.get('width', 0):.0f}x{bbox.get('height', 0):.0f}")
                
                print("✅ 얼굴 감지 성공")
            else:
                print("⚠️ 얼굴 감지 데이터가 없습니다")
        else:
            print(f"❌ 얼굴 감지 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 얼굴 감지 오류: {e}")

def main():
    """메인 테스트 실행"""
    print("🚀 현실적인 얼굴 이미지를 사용한 API 테스트 시작\n")
    
    # 먼저 기본 얼굴 감지 테스트
    test_direct_detection()
    
    # 새로운 API들 테스트
    test_age_estimation()
    test_gender_estimation()
    
    print("\n✨ 모든 테스트 완료!")

if __name__ == "__main__":
    main()
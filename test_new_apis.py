#!/usr/bin/env python3
"""
새로운 API 엔드포인트 테스트 스크립트
"""
import requests
import base64
from PIL import Image, ImageDraw
import io
import json

# 서버 URL
BASE_URL = "http://localhost:8001"

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

def test_age_estimation():
    """나이 추정 API 테스트"""
    print("\n=== 나이 추정 API 테스트 ===")
    try:
        # 테스트 이미지 생성
        test_img = create_test_face_image(face_color="lightblue")
        img_base64 = image_to_base64(test_img)
        
        # API 요청
        payload = {
            "image": img_base64
        }
        
        response = requests.post(f"{BASE_URL}/estimate-age", json=payload)
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
                print("✅ 나이 추정 API 성공")
            else:
                print("⚠️ 데이터가 없습니다")
        else:
            print(f"❌ 나이 추정 API 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 나이 추정 API 오류: {e}")

def test_gender_estimation():
    """성별 확률 추정 API 테스트"""
    print("\n=== 성별 확률 추정 API 테스트 ===")
    try:
        # 테스트 이미지 생성
        test_img = create_test_face_image(face_color="lightgreen")
        img_base64 = image_to_base64(test_img)
        
        # API 요청
        payload = {
            "image": img_base64
        }
        
        response = requests.post(f"{BASE_URL}/estimate-gender", json=payload)
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
                print("✅ 성별 확률 추정 API 성공")
            else:
                print("⚠️ 데이터가 없습니다")
        else:
            print(f"❌ 성별 확률 추정 API 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 성별 확률 추정 API 오류: {e}")

def test_api_docs():
    """API 문서 접근 테스트"""
    print("\n=== API 문서 접근 테스트 ===")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"문서 접근 Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ API 문서 접근 성공")
        else:
            print(f"⚠️ API 문서 접근 실패 (디버그 모드가 아닐 수 있음)")
            
    except Exception as e:
        print(f"❌ API 문서 접근 오류: {e}")

def main():
    """메인 테스트 실행"""
    print("🚀 새로운 API 엔드포인트 테스트 시작\n")
    
    # 순서대로 테스트 실행
    test_age_estimation()
    test_gender_estimation()
    test_api_docs()
    
    print("\n✨ 모든 테스트 완료!")

if __name__ == "__main__":
    main()
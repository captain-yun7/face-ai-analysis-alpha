#!/usr/bin/env python3
"""
간단한 API 테스트
"""
import requests
import base64
import json

# 작은 단색 이미지 생성 (실제 이미지 형식)
from PIL import Image
import io

def create_simple_test_image():
    """간단한 테스트 이미지 생성"""
    # 단색 이미지
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_data = buffer.getvalue()
    return f"data:image/jpeg;base64,{base64.b64encode(img_data).decode()}"

# 테스트 이미지 생성
test_image = create_simple_test_image()

# 얼굴 비교 테스트
print("=== 얼굴 비교 테스트 (단순 이미지) ===")
try:
    response = requests.post("http://localhost:8000/compare-faces", json={
        "source_image": test_image,
        "target_image": test_image,
        "similarity_threshold": 0.01
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== 임베딩 추출 테스트 (단순 이미지) ===")
try:
    response = requests.post("http://localhost:8000/extract-embedding", json={
        "image": test_image,
        "face_id": 0,
        "normalize": True
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
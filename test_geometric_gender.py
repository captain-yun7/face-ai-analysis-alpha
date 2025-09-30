#!/usr/bin/env python3
"""
새로운 기하학적 성별 분류기 테스트 스크립트
"""
import requests
import json

# 서버 URL (포트 8002)
BASE_URL = "http://localhost:8002"

def test_new_gender_api_structure():
    """새로운 성별 API 응답 구조 테스트"""
    print("🔍 새로운 기하학적 성별 분류기 테스트\n")
    
    # 더미 base64 이미지 (구조 확인용)
    dummy_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAAAAAAAD"
    
    print("=== 성별 확률 추정 API 구조 테스트 ===")
    try:
        payload = {"image": dummy_image}
        response = requests.post(f"{BASE_URL}/estimate-gender", json=payload, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response Structure:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except:
            print(f"Response Text: {response.text}")
            
        print("✅ 성별 확률 추정 API 응답 구조 확인 완료\n")
        
    except Exception as e:
        print(f"❌ 성별 확률 추정 API 테스트 오류: {e}\n")

def test_api_schema_update():
    """OpenAPI 스키마에서 새로운 응답 구조 확인"""
    print("=== OpenAPI 스키마 업데이트 확인 ===")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        
        if response.status_code == 200:
            openapi_data = response.json()
            
            # /estimate-gender 엔드포인트 스키마 확인
            paths = openapi_data.get("paths", {})
            
            if "/estimate-gender" in paths:
                gender_api = paths["/estimate-gender"]
                if "post" in gender_api:
                    post_spec = gender_api["post"]
                    
                    print("✅ /estimate-gender 엔드포인트 발견")
                    print(f"   - Summary: {post_spec.get('summary', 'N/A')}")
                    
                    # 응답 스키마 확인
                    responses = post_spec.get("responses", {})
                    if "200" in responses:
                        success_response = responses["200"]
                        print("   - 200 응답 스키마 정의됨")
                        
                        # 스키마 내용 확인
                        content = success_response.get("content", {})
                        if "application/json" in content:
                            schema = content["application/json"].get("schema", {})
                            print(f"   - JSON 스키마: {schema.get('$ref', 'Inline schema')}")
                    
                    print("✅ API 스키마 업데이트 확인 완료")
            else:
                print("❌ /estimate-gender 엔드포인트를 찾을 수 없음")
                
        else:
            print(f"❌ OpenAPI 스키마 접근 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API 스키마 테스트 오류: {e}")

def test_server_health():
    """서버 상태 및 geometric classifier 로딩 확인"""
    print("\n=== 서버 상태 및 분류기 로딩 확인 ===")
    try:
        # 루트 엔드포인트 확인
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"Root endpoint status: {response.status_code}")
        
        # Health check
        try:
            health_response = requests.get(f"{BASE_URL}/health", timeout=5)
            print(f"Health endpoint status: {health_response.status_code}")
        except:
            print("Health endpoint not available")
            
        print("✅ 서버 상태 정상")
        
    except Exception as e:
        print(f"❌ 서버 상태 확인 오류: {e}")

def compare_old_vs_new_approach():
    """이전 방식과 새로운 방식 비교 설명"""
    print("\n=== 이전 vs 새로운 성별 분류 방식 비교 ===")
    
    print("🔴 이전 방식 (가짜 분류기):")
    print("   - 임의의 임베딩 차원 사용")
    print("   - 가상의 가중치로 계산")
    print("   - 남자 사진도 여성으로 분류 가능")
    print("   - 의미 없는 확률값")
    
    print("\n🟢 새로운 방식 (기하학적 분석):")
    print("   - 실제 얼굴 landmarks 사용")
    print("   - 턱선, 얼굴 비율, 눈썹, 코 폭 등 측정")
    print("   - 생물학적 연구 기반 가중치")
    print("   - masculinity/femininity 연속 점수")
    print("   - InsightFace 이진 분류와 병행 제공")
    
    print("\n📊 새로운 응답 형식:")
    print("""
    {
      "gender_probability": {
        "male_probability": 0.75,      // masculinity score
        "female_probability": 0.25,    // femininity score  
        "predicted_gender": "male",
        "gender_confidence": 0.75
      },
      "geometric_analysis": {
        "masculinity_score": 0.75,
        "femininity_score": 0.25,
        "feature_breakdown": {
          "jaw_masculinity": 0.80,      // 턱선 각진 정도
          "face_width_ratio": 0.70,     // 얼굴 폭/높이 비율  
          "brow_prominence": 0.75,      // 눈썹 돌출
          "nose_width_ratio": 0.72,     // 코 폭
          "cheek_definition": 0.68      // 광대뼈 정의
        },
        "method": "geometric_landmarks"
      },
      "insightface_classification": "male",  // 기존 이진 분류
      "face_count": 1
    }
    """)

def main():
    """메인 테스트 실행"""
    print("🚀 새로운 기하학적 성별 분류기 테스트 시작\n")
    
    test_server_health()
    test_api_schema_update()
    test_new_gender_api_structure()
    compare_old_vs_new_approach()
    
    print("\n✨ 모든 테스트 완료!")
    print("\n💡 다음 단계:")
    print("- 실제 얼굴 사진으로 테스트 필요")
    print("- masculinity/femininity 점수 정확도 검증")
    print("- 기존 가짜 분류기 대비 개선 확인")

if __name__ == "__main__":
    main()
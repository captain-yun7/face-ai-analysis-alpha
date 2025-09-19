"""
의존성 없이 실행할 수 있는 간단한 테스트
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_config_import():
    """설정 모듈 임포트 테스트"""
    try:
        from app.core.config import settings
        print(f"✅ 설정 임포트 성공: {settings.app_name}")
        return True
    except Exception as e:
        print(f"❌ 설정 임포트 실패: {e}")
        return False

def test_image_utils_import():
    """이미지 유틸리티 임포트 테스트"""
    try:
        from app.utils.image_utils import is_valid_image_format
        
        # 간단한 기능 테스트
        valid = is_valid_image_format("data:image/jpeg;base64,AAAA")
        invalid = is_valid_image_format("invalid")
        
        assert valid is True
        assert invalid is False
        
        print("✅ 이미지 유틸리티 테스트 성공")
        return True
    except Exception as e:
        print(f"❌ 이미지 유틸리티 테스트 실패: {e}")
        return False

def test_project_structure():
    """프로젝트 구조 테스트"""
    required_files = [
        'app/main.py',
        'app/core/config.py',
        'app/api/routes/faces.py',
        'app/models/face_analyzer.py',
        'requirements.txt',
        '.env.example'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 누락된 파일들: {missing_files}")
        return False
    else:
        print("✅ 프로젝트 구조 테스트 성공")
        return True

def test_env_example():
    """환경 설정 파일 테스트"""
    try:
        with open('.env.example', 'r') as f:
            content = f.read()
        
        required_vars = ['APP_NAME', 'PORT', 'MODEL_NAME', 'HOST']
        for var in required_vars:
            if var not in content:
                print(f"❌ 환경변수 {var}가 .env.example에 없습니다")
                return False
        
        print("✅ 환경 설정 파일 테스트 성공")
        return True
    except Exception as e:
        print(f"❌ 환경 설정 파일 테스트 실패: {e}")
        return False

def run_all_tests():
    """모든 테스트 실행"""
    print("🧪 간단한 테스트 실행 시작...")
    print("=" * 50)
    
    tests = [
        test_project_structure,
        test_env_example,
        test_config_import,
        test_image_utils_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트 통과!")
        return True
    else:
        print("⚠️ 일부 테스트 실패")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
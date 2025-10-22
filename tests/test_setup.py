#!/usr/bin/env python3
"""
Test script to verify the project setup
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported"""
    try:
        print("🧪 Testing imports...")
        
        from src.core.database import get_db, init_db
        print("✅ Database module imported")
        
        from src.core.models import User, Document, Quiz, Chat
        print("✅ Models imported")
        
        from src.processors.multimedia_processor import MultimediaProcessor
        print("✅ Multimedia processor imported")
        
        from src.services.llm_service import LLMService
        print("✅ LLM service imported")
        
        from src.services.quiz_generator import QuizGenerator
        print("✅ Quiz generator imported")
        
        print("🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_multimedia_processor():
    """Test multimedia processor functionality"""
    try:
        print("\n🧪 Testing multimedia processor...")
        
        from src.processors.multimedia_processor import MultimediaProcessor
        processor = MultimediaProcessor()
        
        print(f"✅ Supported formats: {len(processor.supported_formats)} types")
        for file_type, extensions in processor.supported_formats.items():
            print(f"   {file_type}: {', '.join(extensions)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Multimedia processor error: {e}")
        return False

def test_directories():
    """Test that required directories exist"""
    print("\n🧪 Testing directory structure...")
    
    required_dirs = [
        "src/api",
        "src/core", 
        "src/processors",
        "src/services",
        "static",
        "uploads",
        "data",
        "models"
    ]
    
    all_exist = True
    for directory in required_dirs:
        path = Path(directory)
        if path.exists():
            print(f"✅ {directory}")
        else:
            print(f"❌ {directory} - missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("🚀 AI Multimedia Tutor - Setup Test")
    print("=" * 40)
    
    tests = [
        ("Directory Structure", test_directories),
        ("Module Imports", test_imports),
        ("Multimedia Processor", test_multimedia_processor)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Setup is ready.")
        print("Run 'python run.py' to start the application.")
    else:
        print("\n⚠️  Some tests failed. Check the setup.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
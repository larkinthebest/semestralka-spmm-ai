#!/usr/bin/env python3
"""
Test multimedia dependencies
"""

def test_imports():
    print("🧪 Testing AI Multimedia Tutor Dependencies")
    print("=" * 45)
    
    # Test core dependencies
    try:
        import fastapi
        print("✅ FastAPI")
    except ImportError:
        print("❌ FastAPI")
    
    try:
        import gpt4all
        print("✅ GPT4All")
    except ImportError:
        print("❌ GPT4All")
    
    # Test multimedia dependencies
    try:
        import pytesseract
        from PIL import Image
        print("✅ OCR (pytesseract + PIL)")
    except ImportError as e:
        print(f"❌ OCR: {e}")
    
    try:
        import whisper
        print("✅ Whisper (OpenAI)")
    except ImportError as e:
        print(f"❌ Whisper: {e}")
    
    try:
        import cv2
        print("✅ OpenCV")
    except ImportError as e:
        print(f"❌ OpenCV: {e}")
    
    # Test multimedia processor
    try:
        from src.processors.multimedia_processor import MultimediaProcessor
        processor = MultimediaProcessor()
        print("✅ MultimediaProcessor")
    except ImportError as e:
        print(f"❌ MultimediaProcessor: {e}")
    
    print("\n🎯 Testing complete!")

if __name__ == "__main__":
    test_imports()
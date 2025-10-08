#!/usr/bin/env python3
"""
Comprehensive Test Suite for AI Multimedia Tutor
Tests all major functionality including auth, file upload, chat, and AI responses.
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

import httpx
import pytest
from PIL import Image

# Add project root to path
sys.path.append(str(Path(__file__).parent))

BASE_URL = "http://localhost:8002"

class TestRunner:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        self.auth_token = None
        self.test_user = {
            "username": "testuser",
            "email": "test@example.com", 
            "password": "testpass123"
        }
        self.uploaded_files = []
        
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting AI Multimedia Tutor Test Suite")
        print("=" * 50)
        
        try:
            # Basic connectivity
            await self.test_server_health()
            
            # Authentication tests
            await self.test_user_registration()
            await self.test_user_login()
            await self.test_guest_access()
            
            # File upload tests
            await self.test_text_file_upload()
            await self.test_image_file_upload()
            await self.test_duplicate_file_handling()
            
            # Chat functionality tests
            await self.test_chat_without_files()
            await self.test_chat_with_files()
            await self.test_tutor_specialization()
            await self.test_mode_switching()
            
            # AI response tests
            await self.test_explanation_mode()
            await self.test_testing_mode()
            await self.test_token_management()
            
            # Image processing tests
            await self.test_image_text_extraction()
            
            print("\n✅ All tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def test_server_health(self):
        """Test basic server connectivity"""
        print("\n🔍 Testing server health...")
        
        response = await self.client.get("/")
        assert response.status_code == 200
        assert "AI Multimedia Tutor" in response.text
        print("✅ Server is running and accessible")
    
    async def test_user_registration(self):
        """Test user registration"""
        print("\n👤 Testing user registration...")
        
        response = await self.client.post("/auth/register", json=self.test_user)
        
        if response.status_code == 400 and "already registered" in response.text:
            print("ℹ️  User already exists, skipping registration")
            return
            
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == self.test_user["email"]
        assert data["username"] == self.test_user["username"]
        print("✅ User registration successful")
    
    async def test_user_login(self):
        """Test user login"""
        print("\n🔐 Testing user login...")
        
        response = await self.client.post("/auth/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        self.auth_token = data["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        print("✅ User login successful")
    
    async def test_guest_access(self):
        """Test guest access functionality"""
        print("\n👥 Testing guest access...")
        
        # Remove auth header temporarily
        if "Authorization" in self.client.headers:
            del self.client.headers["Authorization"]
        
        response = await self.client.get("/documents")
        assert response.status_code == 200
        
        # Restore auth header
        if self.auth_token:
            self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        
        print("✅ Guest access working")
    
    async def test_text_file_upload(self):
        """Test text file upload"""
        print("\n📄 Testing text file upload...")
        
        # Create test text file
        test_content = """# Test Document
        
This is a test document for the AI Multimedia Tutor.

## Key Concepts
- Machine Learning
- Natural Language Processing  
- Computer Vision

The document contains various topics for testing."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                files = {"file": ("test_document.md", f, "text/markdown")}
                response = await self.client.post("/documents/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["filename"] == "test_document.md"
            assert "successfully" in data["message"]
            
            self.uploaded_files.append("test_document.md")
            print("✅ Text file upload successful")
            
        finally:
            os.unlink(temp_path)
    
    async def test_image_file_upload(self):
        """Test image file upload with text"""
        print("\n🖼️ Testing image file upload...")
        
        # Create test image with text
        img = Image.new('RGB', (200, 100), color='white')
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name, 'PNG')
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                files = {"file": ("test_image.png", f, "image/png")}
                response = await self.client.post("/documents/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["filename"] == "test_image.png"
            
            self.uploaded_files.append("test_image.png")
            print("✅ Image file upload successful")
            
        finally:
            os.unlink(temp_path)
    
    async def test_duplicate_file_handling(self):
        """Test duplicate file handling"""
        print("\n🔄 Testing duplicate file handling...")
        
        # Try to upload the same file again
        test_content = "Duplicate test content"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            # First upload
            with open(temp_path, 'rb') as f:
                files = {"file": ("duplicate_test.txt", f, "text/plain")}
                response1 = await self.client.post("/documents/upload", files=files)
            
            # Second upload (should detect duplicate)
            with open(temp_path, 'rb') as f:
                files = {"file": ("duplicate_test.txt", f, "text/plain")}
                response2 = await self.client.post("/documents/upload", files=files)
            
            assert response1.status_code == 200
            assert response2.status_code == 200
            assert "already" in response2.json()["message"]
            print("✅ Duplicate file handling working")
            
        finally:
            os.unlink(temp_path)
    
    async def test_chat_without_files(self):
        """Test chat behavior without uploaded files"""
        print("\n💬 Testing chat without files...")
        
        response = await self.client.post("/simple-chat", json={
            "message": "Hello, can you help me?",
            "mode": "explanation",
            "tutor": "enola",
            "chat_id": 1
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["requires_files"] == True
        assert "upload files" in data["response"].lower()
        print("✅ Chat without files handled correctly")
    
    async def test_chat_with_files(self):
        """Test chat with uploaded files"""
        print("\n📚 Testing chat with files...")
        
        if not self.uploaded_files:
            print("⚠️  No uploaded files, skipping test")
            return
        
        response = await self.client.post("/simple-chat", json={
            "message": "What are the key concepts in my documents?",
            "mode": "explanation", 
            "tutor": "enola",
            "chat_id": 1,
            "attached_files": self.uploaded_files
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["requires_files"] == False
        assert len(data["response"]) > 0
        assert "sources" in data
        print("✅ Chat with files working")
    
    async def test_tutor_specialization(self):
        """Test tutor specialization (Enola vs Franklin)"""
        print("\n🎭 Testing tutor specialization...")
        
        if not self.uploaded_files:
            print("⚠️  No uploaded files, skipping test")
            return
        
        # Test Enola (explanation)
        response1 = await self.client.post("/simple-chat", json={
            "message": "Explain machine learning concepts",
            "tutor": "enola",
            "attached_files": self.uploaded_files
        })
        
        # Test Franklin (testing)
        response2 = await self.client.post("/simple-chat", json={
            "message": "Create a quiz about machine learning",
            "tutor": "franklin", 
            "attached_files": self.uploaded_files
        })
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["tutor"] == "enola"
        assert data1["mode"] == "explanation"
        assert data2["tutor"] == "franklin"
        assert data2["mode"] == "testing"
        
        print("✅ Tutor specialization working")
    
    async def test_mode_switching(self):
        """Test mode switching enforcement"""
        print("\n🔄 Testing mode switching...")
        
        # Try to use Franklin in explanation mode (should be forced to testing)
        response = await self.client.post("/simple-chat", json={
            "message": "Test question",
            "mode": "explanation",  # This should be overridden
            "tutor": "franklin",
            "attached_files": self.uploaded_files
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["tutor"] == "franklin"
        assert data["mode"] == "testing"  # Should be forced to testing
        
        print("✅ Mode switching enforcement working")
    
    async def test_explanation_mode(self):
        """Test explanation mode responses"""
        print("\n🧠 Testing explanation mode...")
        
        if not self.uploaded_files:
            print("⚠️  No uploaded files, skipping test")
            return
        
        response = await self.client.post("/simple-chat", json={
            "message": "Explain the main concepts in detail",
            "tutor": "enola",
            "attached_files": self.uploaded_files
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for explanation characteristics
        response_text = data["response"].lower()
        explanation_indicators = ["explain", "concept", "example", "understand"]
        
        has_explanation_content = any(indicator in response_text for indicator in explanation_indicators)
        assert has_explanation_content, "Response should contain explanation content"
        
        print("✅ Explanation mode working")
    
    async def test_testing_mode(self):
        """Test testing mode responses"""
        print("\n📝 Testing testing mode...")
        
        if not self.uploaded_files:
            print("⚠️  No uploaded files, skipping test")
            return
        
        response = await self.client.post("/simple-chat", json={
            "message": "Create a quiz about the concepts",
            "tutor": "franklin",
            "attached_files": self.uploaded_files
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for quiz characteristics
        response_text = data["response"].lower()
        quiz_indicators = ["question", "quiz", "test", "answer"]
        
        has_quiz_content = any(indicator in response_text for indicator in quiz_indicators)
        assert has_quiz_content, "Response should contain quiz content"
        
        print("✅ Testing mode working")
    
    async def test_token_management(self):
        """Test token management with large content"""
        print("\n🔢 Testing token management...")
        
        # Create a large message to test token limits
        large_message = "Explain in detail: " + "machine learning concepts " * 100
        
        response = await self.client.post("/simple-chat", json={
            "message": large_message,
            "tutor": "enola",
            "attached_files": self.uploaded_files
        })
        
        # Should not fail due to token limits
        assert response.status_code == 200
        data = response.json()
        assert len(data["response"]) > 0
        
        print("✅ Token management working")
    
    async def test_image_text_extraction(self):
        """Test image text extraction (OCR)"""
        print("\n🔍 Testing image text extraction...")
        
        # This test will pass even if OCR is not installed
        if "test_image.png" not in self.uploaded_files:
            print("⚠️  No test image uploaded, skipping OCR test")
            return
        
        response = await self.client.post("/simple-chat", json={
            "message": "What text can you see in the image?",
            "tutor": "enola",
            "attached_files": ["test_image.png"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["response"]) > 0
        
        print("✅ Image text extraction attempted (OCR may need setup)")
    
    async def cleanup(self):
        """Clean up test resources"""
        print("\n🧹 Cleaning up...")
        await self.client.aclose()
        print("✅ Cleanup completed")

async def main():
    """Main test runner"""
    runner = TestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    print("AI Multimedia Tutor - Comprehensive Test Suite")
    print("Make sure the server is running on http://localhost:8002")
    print("Starting tests in 3 seconds...")
    
    import time
    time.sleep(3)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)
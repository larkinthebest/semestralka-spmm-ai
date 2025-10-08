#!/usr/bin/env python3
"""
Simple test runner for AI Multimedia Tutor
Run this after starting the server with: python run.py
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def check_server():
    """Check if server is running"""
    try:
        response = requests.get("http://localhost:8002", timeout=5)
        return response.status_code == 200
    except:
        return False

def install_test_dependencies():
    """Install required test dependencies"""
    print("📦 Installing test dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "pytest", "pillow"])
        print("✅ Test dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install test dependencies")
        return False
    return True

def main():
    print("🎓 AI Multimedia Tutor - Test Runner")
    print("=" * 40)
    
    # Check if server is running
    if not check_server():
        print("❌ Server is not running!")
        print("Please start the server first with: python run.py")
        print("Then run this test script in another terminal.")
        sys.exit(1)
    
    print("✅ Server is running on http://localhost:8002")
    
    # Install dependencies
    if not install_test_dependencies():
        sys.exit(1)
    
    # Run tests
    print("\n🚀 Running comprehensive tests...")
    try:
        result = subprocess.run([sys.executable, "test_app.py"], 
                              cwd=Path(__file__).parent,
                              capture_output=False)
        
        if result.returncode == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n❌ Tests failed with code {result.returncode}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted")
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
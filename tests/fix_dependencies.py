#!/usr/bin/env python3
"""
Fix dependency issues for AI Multimedia Tutor
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run command and return success status"""
    try:
        subprocess.check_call(cmd, shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🔧 Fixing AI Multimedia Tutor Dependencies")
    print("=" * 40)
    
    # Fix bcrypt issue
    print("📦 Fixing bcrypt compatibility...")
    if run_command(f"{sys.executable} -m pip uninstall -y bcrypt passlib"):
        print("✅ Uninstalled old versions")
    else:
        print("⚠️  Could not uninstall old versions")
    
    if run_command(f"{sys.executable} -m pip install bcrypt==4.0.1 passlib[bcrypt]==1.7.4"):
        print("✅ Installed compatible bcrypt")
    else:
        print("❌ Failed to install bcrypt")
        return False
    
    # Install other requirements with fallbacks
    print("📦 Installing other requirements...")
    
    # Try to install Pillow separately first
    print("📦 Installing Pillow...")
    if not run_command(f"{sys.executable} -m pip install 'Pillow>=10.2.0'"):
        print("⚠️  Pillow install failed, trying without version constraint...")
        run_command(f"{sys.executable} -m pip install Pillow")
    
    # Install remaining requirements
    if run_command(f"{sys.executable} -m pip install fastapi uvicorn sqlalchemy python-multipart python-jose gpt4all PyPDF2 python-docx google-auth google-auth-oauthlib httpx pytesseract numpy"):
        print("✅ Core requirements installed")
    else:
        print("❌ Failed to install some requirements")
        return False
    
    # Install optional multimedia dependencies
    print("📦 Installing multimedia dependencies...")
    if run_command(f"{sys.executable} -m pip install openai-whisper opencv-python"):
        print("✅ Multimedia dependencies installed")
    else:
        print("⚠️  Some multimedia features may not work (Whisper/OpenCV)")
    
    # Check tesseract installation
    print("📦 Checking tesseract...")
    if os.system("tesseract --version") == 0:
        print("✅ Tesseract found")
    else:
        print("⚠️  Tesseract not found. Install with: brew install tesseract (macOS) or apt-get install tesseract-ocr (Ubuntu)")
    
    print("\n🎉 Dependencies fixed! You can now run:")
    print("python run.py")
    print("\n📝 Note: For full multimedia support, ensure tesseract is installed:")
    print("  macOS: brew install tesseract")
    print("  Ubuntu: sudo apt-get install tesseract-ocr")
    
    return True

if __name__ == "__main__":
    if not main():
        sys.exit(1)
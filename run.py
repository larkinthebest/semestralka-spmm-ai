#!/usr/bin/env python3
"""
AI Multimedia Tutor - Main Entry Point
Run this script to start the application
"""

import sys
import os
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change working directory to project root
os.chdir(project_root)

if __name__ == "__main__":
    # Import after path setup
    from src.api.main import app
    import uvicorn
    
    # Explicitly set SECRET_KEY for consistency during development
    # IMPORTANT: In production, this should be managed securely (e.g., Docker secrets, Kubernetes secrets, cloud environment variables)
    os.environ["SECRET_KEY"] = "super-secret-dev-key-please-change-in-production-environment" 
    
    print("🚀 Starting AI Multimedia Tutor...")
    print("📍 Project root:", project_root)
    print("🌐 Server will be available at: http://localhost:8002")
    print("📚 Upload your files and start learning!")
    print("-" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8002)

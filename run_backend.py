#!/usr/bin/env python3
"""
Simple backend server starter for Promptly
Bypasses some dependency issues for development
"""

import os
import sys
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file first
load_dotenv()

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set environment variables for development (only if not already set)
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017/promptly")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "development-secret-key")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")

if __name__ == "__main__":
    print("🚀 Starting Promptly Backend Server...")
    print("📍 Backend running at: http://localhost:8000")
    print("📖 API Docs available at: http://localhost:8000/docs")
    print("⚡ Environment: development")
    print()
    
    # Start the server
    try:
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0", 
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Make sure MongoDB and Redis are running if you're using those features.")
        sys.exit(1) 
#!/usr/bin/env python3
"""
Development server runner with minimal configuration.
This bypasses external service requirements for basic API testing.
"""
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up development environment
from dev_config import setup_dev_environment
setup_dev_environment()

# Now start the server
if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Promptly API in development mode...")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/ping")
    print("⚠️  Note: External services (MongoDB, Redis, AI) may not work")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
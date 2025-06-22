"""
Development configuration for testing without external services.
Run this before starting the server in development mode.
"""
import os

def setup_dev_environment():
    """Set up minimal environment variables for development testing."""
    # Set required environment variables with minimal values
    if not os.getenv("MONGODB_URL"):
        os.environ["MONGODB_URL"] = "mongodb://localhost:27017/test_db"
    
    if not os.getenv("JWT_SECRET_KEY"):
        os.environ["JWT_SECRET_KEY"] = "dev-secret-key-for-testing-only"
    
    if not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = "fake-api-key-for-testing"
    
    if not os.getenv("REDIS_URL"):
        os.environ["REDIS_URL"] = "redis://localhost:6379"
    
    print("Development environment configured")
    print("WARNING: Using fake/minimal credentials - external services may not work")

if __name__ == "__main__":
    setup_dev_environment()

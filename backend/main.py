"""
Promptly Backend - FastAPI Application
Interactive AI Prompting Platform
"""

import os
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Promptly API",
    description="Backend API for Promptly - Interactive AI Prompting Platform",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
)

# CORS Configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
async def health_check() -> Dict[str, bool]:
    """
    Health check endpoint for container orchestration and monitoring.
    
    Returns:
        Dict containing ok status
    """
    return {"ok": True}


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint with basic API information.
    
    Returns:
        Dict containing API name and version
    """
    return {
        "name": "Promptly API",
        "version": "1.0.0",
        "description": "Interactive AI Prompting Platform"
    }


# Startup event
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize application on startup."""
    print("🚀 Promptly API starting up...")
    print(f"📝 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔧 Debug mode: {os.getenv('DEBUG', 'false')}")
    

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on application shutdown."""
    print("👋 Promptly API shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("RELOAD_ON_CHANGE", "true").lower() == "true",
        workers=int(os.getenv("API_WORKERS", "1"))
    ) 
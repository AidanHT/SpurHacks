"""
Promptly Backend - FastAPI Application
Interactive AI Prompting Platform
"""

import os
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print("🚀 Promptly API starting up...")
    print(f"📝 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔧 Debug mode: {os.getenv('DEBUG', 'false')}")
    yield
    # Shutdown
    print("👋 Promptly API shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Promptly API",
    description="Backend API for Promptly - Interactive AI Prompting Platform",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    lifespan=lifespan,
)

# CORS Configuration
cors_origins: List[str] = [
    origin.strip() 
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()  # Filter out empty strings
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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


# Event handlers moved to lifespan context manager above


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("RELOAD_ON_CHANGE", "true").lower() == "true",
        workers=int(os.getenv("API_WORKERS", "1"))
    ) 
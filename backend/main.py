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
    
    # Initialize database
    from backend.core.database import db_manager
    await db_manager.connect()
    
    yield
    # Shutdown
    print("👋 Promptly API shutting down...")
    await db_manager.disconnect()


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


# Authentication routes
from backend.auth import AuthRoutes, google_oauth_client, github_oauth_client, jwt_authentication

# JWT authentication routes
app.include_router(
    AuthRoutes.get_auth_router(),
    prefix="/auth/jwt",
    tags=["auth"]
)

# User registration routes
app.include_router(
    AuthRoutes.get_register_router(),
    prefix="/auth",
    tags=["auth"]
)

# User management routes
app.include_router(
    AuthRoutes.get_users_router(),
    prefix="/users",
    tags=["users"]
)

# OAuth routes
OAUTH_STATE_SECRET = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")

# Google OAuth
if os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"):
    app.include_router(
        AuthRoutes.get_oauth_router(
            google_oauth_client,
            jwt_authentication,
            OAUTH_STATE_SECRET,
        ),
        prefix="/auth/google",
        tags=["auth"]
    )

# GitHub OAuth
if os.getenv("GITHUB_CLIENT_ID") and os.getenv("GITHUB_CLIENT_SECRET"):
    app.include_router(
        AuthRoutes.get_oauth_router(
            github_oauth_client,
            jwt_authentication,
            OAUTH_STATE_SECRET,
        ),
        prefix="/auth/github",
        tags=["auth"]
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("RELOAD_ON_CHANGE", "true").lower() == "true",
        workers=int(os.getenv("API_WORKERS", "1"))
    ) 
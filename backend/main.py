"""
Promptly Backend - FastAPI Application
Interactive AI Prompting Platform
"""

import os
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import rate limiting components
from backend.core.ratelimit import limiter, DEFAULT_RATE_LIMIT


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print("🚀 Promptly API starting up...")
    print(f"📝 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔧 Debug mode: {os.getenv('DEBUG', 'false')}")
    print(f"⚡ Rate-limiting middleware enabled: {DEFAULT_RATE_LIMIT}")
    
    # Initialize database
    from backend.core.database import db_manager
    await db_manager.connect()
    
    # Initialize models (create indexes)
    from backend.models import init_models
    database = db_manager.database
    if database:
        await init_models(database)
        print("📊 Models initialized with indexes")
    
    yield
    # Shutdown
    print("👋 Promptly API shutting down...")
    await db_manager.disconnect()
    
    # Close Redis connection
    from backend.core.cache import close_redis
    await close_redis()


# Initialize FastAPI app
app = FastAPI(
    title="Promptly API",
    description="Backend API for Promptly - Interactive AI Prompting Platform",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    lifespan=lifespan,
)

# Add rate limiting state
app.state.limiter = limiter

# Add SlowAPI middleware
from slowapi.middleware import SlowAPIMiddleware
app.add_middleware(SlowAPIMiddleware)

# Rate limiting exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom rate limit exceeded handler.
    
    Returns JSON response with 429 status and Retry-After header.
    """
    import logging
    
    logger = logging.getLogger(__name__)
    logger.warning(
        f"Rate limit exceeded for {request.client.host if request.client else 'unknown'} "
        f"on {request.method} {request.url.path}"
    )
    
    response = JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"}
    )
    response.headers["Retry-After"] = str(exc.retry_after or 60)
    return response

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


# AI Services Router (with rate limiting)
from fastapi import APIRouter

ai_router = APIRouter()

@ai_router.get("/ping")
@limiter.limit(DEFAULT_RATE_LIMIT)
async def ai_ping(request: Request) -> Dict[str, str]:
    """
    AI services health check endpoint.
    Rate limited to prevent abuse.
    
    Returns:
        Dict containing AI service status
    """
    return {
        "status": "ok",
        "service": "ai",
        "rate_limit": DEFAULT_RATE_LIMIT
    }

# Include AI router with rate limiting
app.include_router(
    ai_router,
    prefix="/ai",
    tags=["ai"]
)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("RELOAD_ON_CHANGE", "true").lower() == "true",
        workers=int(os.getenv("API_WORKERS", "1"))
    ) 
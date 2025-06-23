"""
Promptly Backend - FastAPI Application
Interactive AI Prompting Platform
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, List

# Add current directory to Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

# Import AI service error for global handling
try:
    from services.ai_internal import GeminiServiceError
except ImportError:
    class GeminiServiceError(Exception):
        def __init__(self, status: int, detail: str):
            self.status = status
            self.detail = detail

# Load environment variables
load_dotenv()


def validate_environment():
    """
    Validate required environment variables at startup.
    
    Raises:
        ValueError: If any required environment variables are missing
    """
    required_vars = ["MONGODB_URL", "JWT_SECRET_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    # GEMINI_API_KEY is optional for core functionality but needed for AI features
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  WARNING: GEMINI_API_KEY not set. AI features will be disabled.")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
    print(f"✅ Environment validation passed")

# Import rate limiting components
from core.ratelimit import limiter, DEFAULT_RATE_LIMIT


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print("🚀 Promptly API starting up...")
    print(f"📝 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔧 Debug mode: {os.getenv('DEBUG', 'false')}")
    print(f"⚡ Rate-limiting middleware enabled: {DEFAULT_RATE_LIMIT}")
    
    # Validate environment variables
    validate_environment()
    
    # Initialize database
    from core.database import db_manager
    await db_manager.connect()
    
    # Initialize models (create indexes)
    from models import init_models
    database = db_manager.database
    if database is not None:
        await init_models(database)
        print("📊 Models initialized with indexes")
    
    yield
    # Shutdown
    print("👋 Promptly API shutting down...")
    await db_manager.disconnect()
    
    # Close Redis connection
    from core.cache import close_redis
    await close_redis()
    
    # Close AI service HTTP client
    try:
        from services.ai_internal import cleanup as ai_cleanup
        await ai_cleanup()
    except ImportError:
        pass


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


# AI service exception handler
@app.exception_handler(GeminiServiceError)
async def gemini_service_error_handler(request: Request, exc: GeminiServiceError):
    """
    Custom Gemini service error handler.
    
    Maps AI service errors to proper HTTP responses.
    """
    import logging
    
    logger = logging.getLogger(__name__)
    logger.error(
        f"Gemini service error {exc.status} for {request.client.host if request.client else 'unknown'} "
        f"on {request.method} {request.url.path}: {exc.detail}"
    )
    
    # Map internal errors to 502 Bad Gateway for external API issues
    status_code = 502 if exc.status >= 500 else exc.status
    
    return JSONResponse(
        status_code=status_code,
        content={"detail": f"AI service error: {exc.detail}"}
    )

# CORS Configuration - Fixed for frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["*"],
)

# Add explicit OPTIONS handler for auth routes
@app.options("/auth/{path:path}")
async def handle_auth_options():
    """Handle CORS preflight requests for auth routes"""
    return {"message": "OK"}

@app.options("/users/{path:path}")
async def handle_users_options():
    """Handle CORS preflight requests for users routes"""
    return {"message": "OK"}


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
print("📥 Importing auth module...")
from auth import AuthRoutes, google_oauth_client, github_oauth_client, jwt_authentication
print("📋 Auth module imported, registering routes...")

# JWT authentication routes
print("🔐 Registering JWT auth routes...")
jwt_router = AuthRoutes.get_auth_router()
app.include_router(
    jwt_router,
    prefix="/auth/jwt",
    tags=["auth"]
)
print(f"✅ JWT auth router loaded with {len(jwt_router.routes)} routes")

# User registration routes
print("📝 Registering user registration routes...")
register_router = AuthRoutes.get_register_router()
app.include_router(
    register_router,
    prefix="/auth",
    tags=["auth"]
)
print(f"✅ Registration router loaded with {len(register_router.routes)} routes")

# User management routes
print("👥 Registering user management routes...")
users_router = AuthRoutes.get_users_router()
app.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)
print(f"✅ Users router loaded with {len(users_router.routes)} routes")

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

# Session management routes
try:
    print("📥 Importing sessions router...")
    from api.sessions import router as sessions_router
    print("📋 Sessions router imported, registering...")
    app.include_router(sessions_router)  # Router already has /sessions prefix
    print("✅ Sessions router loaded successfully")
    print(f"📊 Sessions router has {len(sessions_router.routes)} routes")
except ImportError as e:
    print(f"⚠️ Sessions router import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Error loading sessions router: {e}")
    import traceback
    traceback.print_exc()

# File upload routes
try:
    print("📥 Importing files router...")
    from api.files import router as files_router
    print("📋 Files router imported, registering...")
    app.include_router(files_router)  # Router already has /files prefix
    print("✅ Files router loaded successfully")
    print(f"📊 Files router has {len(files_router.routes)} routes")
except ImportError as e:
    print(f"⚠️ Files router import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Error loading files router: {e}")
    import traceback
    traceback.print_exc()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("RELOAD_ON_CHANGE", "true").lower() == "true",
        workers=int(os.getenv("API_WORKERS", "1"))
    ) 
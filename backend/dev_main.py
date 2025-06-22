"""
Development version of main.py that bypasses external service requirements.
Use this for frontend development when you don't have MongoDB/Redis setup.
"""
import os
import sys
from typing import Dict, Any
from contextlib import asynccontextmanager

# Set up environment before imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dev_config import setup_dev_environment
setup_dev_environment()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional


# Mock models for development
class CreateSessionRequest(BaseModel):
    starter_prompt: str = Field(..., min_length=1, max_length=2000)
    max_questions: int = Field(default=10, ge=1, le=20)
    target_model: str = Field(default="gemini-2.5")
    tone: str = Field(default="friendly")  # friendly or formal
    word_limit: int = Field(default=150, ge=25, le=300)


class SessionResponse(BaseModel):
    id: str
    starter_prompt: str
    max_questions: int
    target_model: str
    tone: str
    word_limit: int
    created_at: str
    status: str = "active"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Simplified lifespan for development."""
    print("🚀 Development API starting up...")
    print("⚠️  External services disabled - for frontend testing only")
    yield
    print("👋 Development API shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Promptly API (Development)",
    description="Development API for frontend testing - external services disabled",
    version="1.0.0-dev",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration for frontend
cors_origins = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
async def health_check() -> Dict[str, bool]:
    """Health check endpoint."""
    return {"ok": True}


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with basic API information."""
    return {
        "name": "Promptly API (Development)",
        "version": "1.0.0-dev",
        "description": "Development API - external services disabled"
    }


# Mock sessions endpoint for frontend testing
@app.post("/sessions", response_model=SessionResponse)
async def create_session(session_data: CreateSessionRequest) -> SessionResponse:
    """
    Mock session creation endpoint for frontend development.
    Returns a fake session ID and echoes back the request data.
    """
    import uuid
    from datetime import datetime
    
    # Validate target model
    valid_models = ["gemini-2.5", "gemini-pro", "gpt-4", "claude-3"]
    if session_data.target_model not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target model. Must be one of: {valid_models}"
        )
    
    # Validate tone
    if session_data.tone not in ["friendly", "formal"]:
        raise HTTPException(
            status_code=400,
            detail="Tone must be either 'friendly' or 'formal'"
        )
    
    # Create mock session response
    session_id = str(uuid.uuid4())
    
    return SessionResponse(
        id=session_id,
        starter_prompt=session_data.starter_prompt,
        max_questions=session_data.max_questions,
        target_model=session_data.target_model,
        tone=session_data.tone,
        word_limit=session_data.word_limit,
        created_at=datetime.utcnow().isoformat(),
        status="active"
    )


@app.get("/sessions/{session_id}")
async def get_session(session_id: str) -> SessionResponse:
    """
    Mock session retrieval endpoint.
    Returns a fake session for any valid UUID.
    """
    import uuid
    from datetime import datetime
    
    try:
        # Validate UUID format
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=session_id,
        starter_prompt="This is a mock session for development testing.",
        max_questions=10,
        target_model="gemini-2.5",
        tone="friendly",
        word_limit=150,
        created_at=datetime.utcnow().isoformat(),
        status="active"
    )


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Promptly Development API...")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/ping")
    print("📋 Test Session Creation: POST http://localhost:8000/sessions")
    print("⚠️  Note: This is a mock API for frontend development only")
    
    uvicorn.run(
        "dev_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
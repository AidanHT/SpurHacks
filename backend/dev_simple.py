"""
Simple development API without Unicode characters for Windows compatibility.
"""
import os
import sys
from typing import Dict
from contextlib import asynccontextmanager

# Set environment variables
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017/test_db")
os.environ.setdefault("JWT_SECRET_KEY", "dev-secret-key-for-testing-only")
os.environ.setdefault("GEMINI_API_KEY", "fake-api-key-for-testing")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Models
class CreateSessionRequest(BaseModel):
    starter_prompt: str = Field(..., min_length=1, max_length=2000)
    max_questions: int = Field(default=10, ge=1, le=20)
    target_model: str = Field(default="gemini-2.5")
    tone: str = Field(default="friendly")
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
    print("Development API starting...")
    print("WARNING: External services disabled - for frontend testing only")
    yield
    print("Development API shutting down...")

# App
app = FastAPI(
    title="Promptly API (Development)",
    description="Development API for frontend testing",
    version="1.0.0-dev",
    docs_url="/docs",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
async def health_check() -> Dict[str, bool]:
    return {"ok": True}

@app.post("/sessions", response_model=SessionResponse)
async def create_session(session_data: CreateSessionRequest) -> SessionResponse:
    import uuid
    from datetime import datetime
    
    # Validate
    valid_models = ["gemini-2.5", "gemini-pro", "gpt-4", "claude-3"]
    if session_data.target_model not in valid_models:
        raise HTTPException(status_code=400, detail=f"Invalid model: {session_data.target_model}")
    
    if session_data.tone not in ["friendly", "formal"]:
        raise HTTPException(status_code=400, detail="Invalid tone")
    
    return SessionResponse(
        id=str(uuid.uuid4()),
        starter_prompt=session_data.starter_prompt,
        max_questions=session_data.max_questions,
        target_model=session_data.target_model,
        tone=session_data.tone,
        word_limit=session_data.word_limit,
        created_at=datetime.utcnow().isoformat(),
        status="active"
    )

if __name__ == "__main__":
    import uvicorn
    print("Starting Development API on http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    uvicorn.run("dev_simple:app", host="0.0.0.0", port=8000, reload=True)

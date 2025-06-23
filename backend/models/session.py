"""
Session model for Promptly
Defines session data structure for AI prompt crafting sessions
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator
from motor.motor_asyncio import AsyncIOMotorDatabase

from .types import PyObjectId


class Session(BaseModel):
    """
    Session model for MongoDB storage
    Represents an AI prompt crafting session
    """
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    title: Optional[str] = Field(None, max_length=200)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Session-specific fields
    starter_prompt: Optional[str] = Field(None, max_length=5000)
    max_questions: int = Field(default=10, ge=1, le=20)
    target_model: str = Field(default="gpt-4", max_length=50)
    settings: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="active", max_length=20)  # active, completed, cancelled
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate session status"""
        valid_statuses = ["active", "completed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class SessionCreate(BaseModel):
    """Schema for creating a new session"""
    title: Optional[str] = Field(None, max_length=200)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    starter_prompt: str = Field(..., min_length=1, max_length=5000)
    max_questions: int = Field(..., ge=1, le=20)
    target_model: str = Field(..., min_length=1, max_length=50)
    settings: Dict[str, Any] = Field(...)
    
    @field_validator('settings')
    @classmethod
    def validate_settings(cls, v):
        """Validate settings structure"""
        if not isinstance(v, dict):
            raise ValueError("Settings must be a dictionary")
        
        # Validate required settings fields
        tone = v.get('tone')
        word_limit = v.get('wordLimit')
        context_sources = v.get('contextSources')
        
        if tone is not None and not isinstance(tone, str):
            raise ValueError("Settings.tone must be a string")
        if word_limit is not None and not isinstance(word_limit, int):
            raise ValueError("Settings.wordLimit must be an integer")
        if context_sources is not None and not isinstance(context_sources, list):
            raise ValueError("Settings.contextSources must be a list")
            
        return v
    
    @field_validator('target_model')
    @classmethod
    def validate_target_model(cls, v):
        """Validate target model is supported"""
        supported_models = [
            'gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo',
            'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku',
            'llama-2-70b', 'llama-2-13b', 'gemini-pro'
        ]
        if v not in supported_models:
            raise ValueError(f"Unsupported target model. Supported models: {', '.join(supported_models)}")
        return v


class SessionUpdate(BaseModel):
    """Schema for updating an existing session"""
    title: Optional[str] = Field(None, max_length=200)
    metadata: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    starter_prompt: Optional[str] = Field(None, max_length=5000)
    max_questions: Optional[int] = Field(None, ge=1, le=20)
    target_model: Optional[str] = Field(None, max_length=50)
    settings: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, max_length=20)
    
    @field_validator('target_model')
    @classmethod
    def validate_target_model(cls, v):
        """Validate target model is supported (if provided)"""
        if v is None:
            return v
        
        supported_models = [
            'gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo',
            'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku',
            'llama-2-70b', 'llama-2-13b', 'gemini-pro'
        ]
        if v not in supported_models:
            raise ValueError(f"Unsupported target model. Supported models: {', '.join(supported_models)}")
        return v
    
    @field_validator('settings')
    @classmethod
    def validate_settings(cls, v):
        """Validate settings structure (if provided)"""
        if v is None:
            return v
            
        if not isinstance(v, dict):
            raise ValueError("Settings must be a dictionary")
        
        # Validate settings fields
        tone = v.get('tone')
        word_limit = v.get('wordLimit')
        context_sources = v.get('contextSources')
        
        if tone is not None and not isinstance(tone, str):
            raise ValueError("Settings.tone must be a string")
        if word_limit is not None and not isinstance(word_limit, int):
            raise ValueError("Settings.wordLimit must be an integer")
        if context_sources is not None and not isinstance(context_sources, list):
            raise ValueError("Settings.contextSources must be a list")
            
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate session status (if provided)"""
        if v is None:
            return v
        
        valid_statuses = ["active", "completed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class SessionRead(BaseModel):
    """Schema for reading session data"""
    id: str = Field(alias="_id")
    user_id: str
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    starter_prompt: Optional[str] = None
    max_questions: int
    target_model: str
    settings: Dict[str, Any]
    status: str
    
    class Config:
        populate_by_name = True


async def ensure_session_indexes(db: AsyncIOMotorDatabase):
    """
    Ensure proper indexes exist for session collection
    
    Indexes:
    - user_id + created_at (descending) for "latest sessions per user"
    - user_id for user session queries
    - created_at for time-based queries
    - status for filtering by session state
    """
    collection = db["sessions"]
    
    # Compound index for user sessions ordered by creation time (latest first)
    await collection.create_index([
        ("user_id", 1),
        ("created_at", -1)
    ], name="user_sessions_by_time")
    
    # Single field indexes
    await collection.create_index("user_id", name="user_id_index")
    await collection.create_index("created_at", name="created_at_index")
    await collection.create_index("updated_at", name="updated_at_index")
    await collection.create_index("status", name="status_index") 
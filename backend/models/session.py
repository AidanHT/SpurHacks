"""
Session model for Promptly
Defines session data structure for AI prompt crafting sessions
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, Annotated

from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator
from motor.motor_asyncio import AsyncIOMotorDatabase


def validate_object_id(v: Any) -> ObjectId:
    """Validate and convert to ObjectId"""
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class Session(BaseModel):
    """
    Session model for MongoDB storage
    Represents an AI prompt crafting session
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    title: Optional[str] = Field(None, max_length=200)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class SessionCreate(BaseModel):
    """Schema for creating a new session"""
    title: Optional[str] = Field(None, max_length=200)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SessionUpdate(BaseModel):
    """Schema for updating an existing session"""
    title: Optional[str] = Field(None, max_length=200)
    metadata: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionRead(BaseModel):
    """Schema for reading session data"""
    id: str = Field(alias="_id")
    user_id: str
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


async def ensure_session_indexes(db: AsyncIOMotorDatabase):
    """
    Ensure proper indexes exist for session collection
    
    Indexes:
    - user_id + created_at (descending) for "latest sessions per user"
    - user_id for user session queries
    - created_at for time-based queries
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
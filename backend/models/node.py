"""
Node model for Promptly
Defines node data structure for prompt decision trees
"""

from datetime import datetime, timezone
from typing import Optional, Annotated, Any

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


class Node(BaseModel):
    """
    Node model for MongoDB storage
    Represents a node in the decision tree for prompt crafting
    """
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    session_id: PyObjectId = Field(...)
    parent_id: Optional[PyObjectId] = Field(None)
    role: str = Field(..., max_length=50)  # e.g., "question", "answer", "prompt"
    content: str = Field(..., max_length=10000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class NodeCreate(BaseModel):
    """Schema for creating a new node"""
    session_id: str = Field(...)
    parent_id: Optional[str] = Field(None)
    role: str = Field(..., max_length=50)
    content: str = Field(..., max_length=10000)


class NodeUpdate(BaseModel):
    """Schema for updating an existing node"""
    role: Optional[str] = Field(None, max_length=50)
    content: Optional[str] = Field(None, max_length=10000)


class NodeRead(BaseModel):
    """Schema for reading node data"""
    id: str = Field(alias="_id")
    session_id: str
    parent_id: Optional[str] = None
    role: str
    content: str
    created_at: datetime
    
    class Config:
        populate_by_name = True


async def ensure_node_indexes(db: AsyncIOMotorDatabase):
    """
    Ensure proper indexes exist for node collection
    
    Indexes:
    - session_id + parent_id for threaded tree queries
    - session_id for session node queries
    - parent_id for child node queries
    - created_at for time-based queries
    """
    collection = db["nodes"]
    
    # Compound index for session nodes with parent relationships
    await collection.create_index([
        ("session_id", 1),
        ("parent_id", 1)
    ], name="session_parent_nodes")
    
    # Compound index for session nodes ordered by creation time
    await collection.create_index([
        ("session_id", 1),
        ("created_at", 1)
    ], name="session_nodes_by_time")
    
    # Single field indexes
    await collection.create_index("session_id", name="session_id_index")
    await collection.create_index("parent_id", name="parent_id_index")
    await collection.create_index("created_at", name="created_at_index") 
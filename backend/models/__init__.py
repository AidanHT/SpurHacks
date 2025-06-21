"""
Models package for Promptly backend
Contains data models and schemas
"""

# Re-export ObjectId for consistency across models
from bson import ObjectId

# User models
from .user import (
    User,
    UserRead,
    UserCreate,
    UserUpdate,
    OAuthAccount,
    PasswordManager,
    password_manager
)

# Session models  
from .session import (
    Session,
    SessionCreate,
    SessionUpdate,
    SessionRead,
    PyObjectId as SessionObjectId,
    ensure_session_indexes
)

# Node models
from .node import (
    Node,
    NodeCreate,
    NodeUpdate,
    NodeRead,
    PyObjectId as NodeObjectId,
    ensure_node_indexes
)

# Shared ObjectId type (use the one from session/node models)
PyObjectId = SessionObjectId

# Model initialization function
async def init_models(db):
    """
    Initialize all models by ensuring proper indexes exist
    
    Args:
        db: AsyncIOMotorDatabase instance
    """
    await ensure_session_indexes(db)
    await ensure_node_indexes(db)

__all__ = [
    # ObjectId types
    "ObjectId",
    "PyObjectId",
    
    # User models
    "User",
    "UserRead", 
    "UserCreate",
    "UserUpdate",
    "OAuthAccount",
    "PasswordManager",
    "password_manager",
    
    # Session models
    "Session",
    "SessionCreate",
    "SessionUpdate", 
    "SessionRead",
    "ensure_session_indexes",
    
    # Node models
    "Node",
    "NodeCreate",
    "NodeUpdate",
    "NodeRead", 
    "ensure_node_indexes",
    
    # Initialization
    "init_models",
] 
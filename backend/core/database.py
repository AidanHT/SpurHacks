"""
Database core module for Promptly
Provides MongoDB async client configuration and dependency injection
"""

import os
from typing import AsyncGenerator, Optional, Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import Depends


class DatabaseManager:
    """Database manager for MongoDB connections"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """Create database connection"""
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            raise ValueError("MONGODB_URL environment variable is required")
        
        try:
            self.client = AsyncIOMotorClient(
                mongodb_url,
                uuidRepresentation="standard"
            )
            
            database_name = os.getenv("MONGODB_DATABASE", "promptly")
            self.database = self.client[database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            print(f"📊 Connected to MongoDB database: {database_name}")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            self.client = None
            self.database = None
            raise
    
    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("🔌 Disconnected from MongoDB")


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_client() -> AsyncIOMotorClient:
    """
    Dependency to get MongoDB client
    
    Returns:
        AsyncIOMotorClient: MongoDB async client
    
    Raises:
        RuntimeError: If database connection fails
    """
    if not db_manager.client:
        await db_manager.connect()
    if not db_manager.client:
        raise RuntimeError("Failed to connect to database")
    return db_manager.client


async def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency to get MongoDB database
    
    Returns:
        AsyncIOMotorDatabase: MongoDB async database
        
    Raises:
        RuntimeError: If database connection fails
    """
    if not db_manager.database:
        try:
            await db_manager.connect()
        except Exception as e:
            print(f"❌ Database connection failed in get_database(): {e}")
            raise RuntimeError(f"Failed to connect to database: {e}") from e
    
    if not db_manager.database:
        raise RuntimeError("Database connection is None after connection attempt")
    
    return db_manager.database


async def get_user_db() -> AsyncGenerator[Any, None]:
    """
    Dependency for FastAPI Users to get user database adapter
    """
    # Import inside function to avoid circular imports
    from fastapi_users.db import MongoDBUserDatabase
    
    database = await get_database()
    collection = database["users"]
    
    # Import User model only when needed to avoid circular imports
    from backend.models.user import User
    yield MongoDBUserDatabase(User, collection) 
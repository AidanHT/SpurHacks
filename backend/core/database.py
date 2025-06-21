"""
Database core module for Promptly
Provides MongoDB async client configuration and dependency injection
"""

import os
from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import Depends


class DatabaseManager:
    """Database manager for MongoDB connections"""
    
    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.database: AsyncIOMotorDatabase | None = None
    
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
        await db_manager.connect()
    if not db_manager.database:
        raise RuntimeError("Failed to connect to database")
    return db_manager.database


async def get_user_db() -> AsyncGenerator:
    """
    Dependency for FastAPI Users to get user database adapter
    """
    try:
        # Try the newer package name first
        from fastapi_users_db_mongodb import MongoDBUserDatabase
        from models.user import User
        
        database = await get_database()
        yield MongoDBUserDatabase(database, User)
    except ImportError:
        try:
            # Fallback to older package name
            from fastapi_users_db_motor import MotorUserDatabase
            from models.user import User
            
            database = await get_database()
            yield MotorUserDatabase(database, User)
        except ImportError:
            # Simple fallback implementation
            from models.user import User
            database = await get_database()
            
            class SimpleUserDatabase:
                def __init__(self, database, user_model):
                    self.database = database
                    self.collection = database.users
                    self.user_model = user_model
                
                async def get(self, id: str):
                    user_dict = await self.collection.find_one({"id": id})
                    return self.user_model(**user_dict) if user_dict else None
                
                async def get_by_email(self, email: str):
                    user_dict = await self.collection.find_one({"email": email})
                    return self.user_model(**user_dict) if user_dict else None
                
                async def create(self, user_dict: dict):
                    result = await self.collection.insert_one(user_dict)
                    user_dict["_id"] = result.inserted_id
                    return self.user_model(**user_dict)
                
                async def update(self, user_dict: dict):
                    await self.collection.replace_one({"id": user_dict["id"]}, user_dict)
                    return self.user_model(**user_dict)
                
                async def delete(self, user):
                    await self.collection.delete_one({"id": user.id})
            
            yield SimpleUserDatabase(database, User) 
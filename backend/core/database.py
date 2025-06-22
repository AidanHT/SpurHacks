"""
Database core module for Promptly
Provides MongoDB async client configuration and dependency injection
"""

import os
import logging
from typing import AsyncGenerator, Optional, Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import Depends

# Setup logging
logger = logging.getLogger(__name__)


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
            logger.info(f"Attempting to connect to MongoDB at: {mongodb_url}")
            self.client = AsyncIOMotorClient(
                mongodb_url,
                uuidRepresentation="standard",
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000
            )
            
            database_name = os.getenv("MONGODB_DATABASE", "promptly")
            self.database = self.client[database_name]
            
            # Test connection with timeout
            await self.client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB database: {database_name}")
            print(f"📊 Connected to MongoDB database: {database_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            print(f"❌ Failed to connect to MongoDB: {e}")
            print(f"   URL: {mongodb_url}")
            print(f"   Make sure MongoDB is running on localhost:27017")
            self.client = None
            self.database = None
            raise
    
    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
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
    if db_manager.database is None:
        try:
            await db_manager.connect()
        except Exception as e:
            logger.error(f"Database connection failed in get_database(): {e}")
            print(f"❌ Database connection failed in get_database(): {e}")
            raise RuntimeError(f"Failed to connect to database: {e}") from e
    
    if db_manager.database is None:
        raise RuntimeError("Database connection is None after connection attempt")
    
    return db_manager.database


async def get_user_db() -> AsyncGenerator[Any, None]:
    """
    Dependency for FastAPI Users to get user database adapter
    """
    # Custom implementation for FastAPI Users 12.x compatibility
    
    # Import logging at the function level to ensure availability
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        database = await get_database()
        collection = database["users"]
        
        # Import User model only when needed to avoid circular imports
        from models.user import User
        from fastapi_users.db import BaseUserDatabase
        from motor.motor_asyncio import AsyncIOMotorCollection
        from typing import Optional
        from fastapi import Request
        
        class CustomMongoDBUserDatabase(BaseUserDatabase[User, str]):
            """Custom MongoDB User Database for FastAPI Users"""
            
            def __init__(self, collection: AsyncIOMotorCollection):
                self.collection = collection
            
            async def get(self, id: str) -> Optional[User]:
                """Get user by ID"""
                try:
                    user_doc = await self.collection.find_one({"_id": id})
                    if user_doc:
                        return User(**user_doc)
                    return None
                except Exception as e:
                    logger.error(f"Error getting user by ID {id}: {e}")
                    return None
            
            async def get_by_email(self, email: str) -> Optional[User]:
                """Get user by email"""
                try:
                    user_doc = await self.collection.find_one({"email": email})
                    if user_doc:
                        return User(**user_doc)
                    return None
                except Exception as e:
                    logger.error(f"Error getting user by email {email}: {e}")
                    return None
            
            async def create(self, create_dict: dict, safe: bool = True, request: Optional[Request] = None) -> User:
                """Create a new user - compatible with FastAPI Users 12.x"""
                try:
                    # Ensure the ID field is set correctly for MongoDB
                    if "id" in create_dict:
                        create_dict["_id"] = create_dict.pop("id")
                    
                    result = await self.collection.insert_one(create_dict)
                    
                    # Retrieve the created user
                    user_doc = await self.collection.find_one({"_id": result.inserted_id})
                    if user_doc:
                        return User(**user_doc)
                    else:
                        raise RuntimeError("Failed to retrieve created user")
                except Exception as e:
                    logger.error(f"Error creating user: {e}")
                    raise RuntimeError(f"Failed to create user: {e}") from e
            
            async def update(self, user: User, update_dict: dict) -> User:
                """Update a user"""
                try:
                    # Remove None values and prepare update
                    update_dict = {k: v for k, v in update_dict.items() if v is not None}
                    
                    if update_dict:
                        await self.collection.update_one(
                            {"_id": user.id}, 
                            {"$set": update_dict}
                        )
                    
                    # Retrieve updated user
                    user_doc = await self.collection.find_one({"_id": user.id})
                    if user_doc:
                        return User(**user_doc)
                    else:
                        raise RuntimeError("Failed to retrieve updated user")
                except Exception as e:
                    logger.error(f"Error updating user {user.id}: {e}")
                    raise RuntimeError(f"Failed to update user: {e}") from e
            
            async def delete(self, user: User) -> None:
                """Delete a user"""
                try:
                    await self.collection.delete_one({"_id": user.id})
                except Exception as e:
                    logger.error(f"Error deleting user {user.id}: {e}")
                    raise RuntimeError(f"Failed to delete user: {e}") from e
        
        yield CustomMongoDBUserDatabase(collection)
        
    except Exception as e:
        logger.error(f"Failed to create user database: {e}")
        raise RuntimeError(f"Failed to create user database: {e}") from e 
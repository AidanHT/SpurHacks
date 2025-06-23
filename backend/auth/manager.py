"""
User manager for Promptly
Handles user operations like registration, password reset, etc.
"""

import os
import uuid
import logging
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager

from models.user import User, UserCreate, password_manager
from core.database import get_user_db

# Setup logging
logger = logging.getLogger(__name__)


class UserManager(BaseUserManager[User, str]):
    """
    User manager for handling user operations
    """
    reset_password_token_secret = os.getenv("RESET_PASSWORD_SECRET", os.getenv("JWT_SECRET_KEY", "change-in-production"))
    verification_token_secret = os.getenv("VERIFICATION_SECRET", os.getenv("JWT_SECRET_KEY", "change-in-production"))

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Called after user registration"""
        logger.info(f"User {user.email} has registered successfully")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after password reset request"""
        logger.info(f"Password reset requested for user {user.email}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after verification request"""
        logger.info(f"Verification requested for user {user.email}")

    async def create(
        self,
        user_create: UserCreate,
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> User:
        """
        Create a new user with additional fields
        """
        logger.info(f"UserManager.create called with: {user_create}")
        
        try:
            await self.validate_password(user_create.password, user_create)

            existing_user = await self.user_db.get_by_email(user_create.email)
            if existing_user is not None:
                raise ValueError("User already exists")

            user_dict = user_create.model_dump()
            logger.info(f"UserCreate.model_dump(): {user_dict}")
            
            password = user_dict.pop("password")
            
            # Hash password using the imported password manager
            user_dict["hashed_password"] = password_manager.hash_password(password)
            user_dict["id"] = str(uuid.uuid4())
            
            # Add timestamps
            from datetime import datetime, timezone
            current_time = datetime.now(timezone.utc).isoformat()
            user_dict["created_at"] = current_time
            user_dict["updated_at"] = current_time

            logger.info(f"Final user_dict before create: {user_dict}")
            
            created_user = await self.user_db.create(user_dict)
            logger.info(f"Created user: {created_user}")
            
            await self.on_after_register(created_user, request)
            
            return created_user
        except ValueError as e:
            logger.error(f"UserManager create validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"UserManager create unexpected error: {e}")
            raise ValueError(f"User creation failed: {str(e)}") 
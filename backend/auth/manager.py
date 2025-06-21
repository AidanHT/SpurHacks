"""
User manager for Promptly
Handles user operations like registration, password reset, etc.
"""

import os
import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, StringIDMixin

from backend.models.user import User, UserCreate
from backend.core.database import get_user_db


class UserManager(StringIDMixin, BaseUserManager[User, str]):
    """
    User manager for handling user operations
    """
    reset_password_token_secret = os.getenv("RESET_PASSWORD_SECRET", "dev-secret-change-in-production")
    verification_token_secret = os.getenv("VERIFICATION_SECRET", "dev-secret-change-in-production")

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Called after user registration"""
        print(f"✅ User {user.email} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after password reset request"""
        print(f"🔑 User {user.email} has requested a password reset. Token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after verification request"""
        print(f"📧 Verification requested for user {user.email}. Token: {token}")

    async def create(
        self,
        user_create: UserCreate,
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> User:
        """
        Create a new user with additional fields
        """
        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            raise ValueError("User already exists")

        user_dict = user_create.model_dump()
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)
        user_dict["id"] = str(uuid.uuid4())
        
        # Add timestamps
        from datetime import datetime
        current_time = datetime.utcnow().isoformat()
        user_dict["created_at"] = current_time
        user_dict["updated_at"] = current_time

        created_user = await self.user_db.create(user_dict)
        
        await self.on_after_register(created_user, request)
        
        return created_user 
"""
User model for Promptly
Defines user data structure and authentication methods
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from fastapi_users import schemas
import argon2


class OAuthAccount(BaseModel):
    """OAuth account model for social login"""
    oauth_name: str
    access_token: str
    expires_at: Optional[int] = None
    refresh_token: Optional[str] = None
    account_id: str
    account_email: str


class User(BaseModel):
    """
    User model for MongoDB storage
    Compatible with FastAPI Users
    """
    id: str = Field(alias="_id")
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    oauth_accounts: List[OAuthAccount] = Field(default_factory=list)
    
    # Additional user profile fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        populate_by_name = True


class UserRead(schemas.BaseUser[str]):
    """User schema for reading user data"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None


class UserCreate(schemas.BaseUserCreate):
    """User schema for creating new users"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    """User schema for updating user data"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None


class PasswordManager:
    """Password hashing and verification using Argon2"""
    
    def __init__(self):
        self.hasher = argon2.PasswordHasher(
            time_cost=2,      # Number of iterations
            memory_cost=102400,  # Memory usage in KiB (100MB)
            parallelism=8,    # Number of parallel threads
            hash_len=32,      # Hash length in bytes
            salt_len=16       # Salt length in bytes
        )
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using Argon2
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return self.hasher.hash(password)
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            self.hasher.verify(hashed_password, password)
            return True
        except argon2.exceptions.VerifyMismatchError:
            return False
        except Exception:
            return False
    
    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Check if password hash needs to be updated
        
        Args:
            hashed_password: Hashed password from database
            
        Returns:
            bool: True if hash needs updating
        """
        return self.hasher.check_needs_rehash(hashed_password)


# Global password manager instance
password_manager = PasswordManager() 
"""
Authentication package for Promptly
FastAPI Users integration with JWT and OAuth support
"""

import os
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
)
from fastapi_users.authentication.strategy import JWTStrategy
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.github import GitHubOAuth2

from backend.core.database import get_user_db
from backend.models.user import User, UserCreate, UserRead, UserUpdate


# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET:
    import secrets
    JWT_SECRET = secrets.token_urlsafe(32)
    print("⚠️  WARNING: JWT_SECRET_KEY not set in environment. Using generated secret for development.")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))


def get_jwt_strategy() -> JWTStrategy:
    """Get JWT strategy configuration"""
    return JWTStrategy(
        secret=JWT_SECRET,
        lifetime_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        algorithm=JWT_ALGORITHM,
    )


# Bearer token transport
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# JWT Authentication backend
jwt_authentication = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# OAuth2 Clients
google_oauth_client = GoogleOAuth2(
    client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
)

github_oauth_client = GitHubOAuth2(
    client_id=os.getenv("GITHUB_CLIENT_ID", ""),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET", ""),
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, str](
    get_user_db,
    [jwt_authentication],
)

# Current user dependencies
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)


async def get_user_manager(user_db=Depends(get_user_db)):
    """Get user manager instance"""
    from backend.auth.manager import UserManager
    
    yield UserManager(user_db)


class AuthRoutes:
    """Authentication routes setup"""
    
    @staticmethod
    def get_auth_router():
        """Get authentication routes"""
        return fastapi_users.get_auth_router(jwt_authentication)
    
    @staticmethod
    def get_register_router():
        """Get user registration routes"""
        return fastapi_users.get_register_router(UserRead, UserCreate)
    
    @staticmethod
    def get_reset_password_router():
        """Get password reset routes"""
        return fastapi_users.get_reset_password_router()
    
    @staticmethod
    def get_verify_router():
        """Get user verification routes"""
        return fastapi_users.get_verify_router(UserRead)
    
    @staticmethod
    def get_users_router():
        """Get user management routes"""
        return fastapi_users.get_users_router(UserRead, UserUpdate)
    
    @staticmethod
    def get_oauth_router(oauth_client, backend, state_secret: str):
        """Get OAuth routes for a specific provider"""
        return fastapi_users.get_oauth_router(
            oauth_client,
            backend,
            state_secret,
            associate_by_email=True,
        )


# Export main components
__all__ = [
    "fastapi_users",
    "current_active_user", 
    "current_superuser",
    "get_user_manager",
    "AuthRoutes",
    "google_oauth_client",
    "github_oauth_client",
    "jwt_authentication",
] 
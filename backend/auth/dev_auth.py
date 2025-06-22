"""
Development authentication bypass for testing.
DO NOT USE IN PRODUCTION!
"""

import os
from backend.models.user import User
from backend.auth import current_active_user
from fastapi import Depends
from bson import ObjectId

# Create a development test user
DEV_USER = User(
    id=str(ObjectId()),
    email="dev@test.com",
    first_name="Dev",
    last_name="User",
    is_active=True,
    is_superuser=False,
    is_verified=True
)

async def get_dev_user_or_authenticated() -> User:
    """
    Return development user in dev environment, otherwise use real auth.
    This allows testing without authentication setup.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "development":
        return DEV_USER
    else:
        # In production, this would still require proper authentication
        return await current_active_user()

def get_auth_dependency():
    """
    Return appropriate auth dependency based on environment.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "development":
        return Depends(get_dev_user_or_authenticated)
    else:
        return Depends(current_active_user) 
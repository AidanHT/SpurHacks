"""
Rate Limiting Configuration using SlowAPI
Implements user-based rate limiting with Redis backend
"""

import os
import logging
from typing import Any
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


def get_rate_limit_key(request: Request) -> str:
    """
    Custom key function for rate limiting.
    
    Priority:
    1. User ID (if authenticated)
    2. Client IP address (fallback for anonymous users)
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Rate limit key identifier
    """
    # Check if user is authenticated
    if hasattr(request.state, "user") and request.state.user:
        user_id = str(request.state.user.id)
        logger.debug(f"Rate limit key: user:{user_id}")
        return f"user:{user_id}"
    
    # Fallback to client IP
    client_ip = get_remote_address(request)
    
    # Handle IPv6 addresses by normalizing them
    if client_ip and ":" in client_ip and not client_ip.startswith("["):
        client_ip = f"[{client_ip}]"  # Normalize IPv6
    
    logger.debug(f"Rate limit key: ip:{client_ip}")
    return f"ip:{client_ip}"


# Initialize rate limiter with Redis backend
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=redis_url,
    default_limits=[]  # No global limits, apply per-route
)

# Default rate limit from environment
DEFAULT_RATE_LIMIT = os.getenv("RATE_LIMIT", "60/minute") 
"""
Redis Cache Configuration and Client Factory
Provides Redis connection for caching and rate limiting
"""

import os
from typing import Optional
from redis.asyncio import Redis

# Global Redis client instance (lazy singleton)
_redis_client: Optional[Redis] = None


def get_redis() -> Redis:
    """
    Get Redis client instance with lazy initialization.
    
    Returns:
        Redis: Configured Redis client instance
        
    Raises:
        ConnectionError: If Redis URL is invalid or connection fails
    """
    global _redis_client
    
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        try:
            _redis_client = Redis.from_url(
                redis_url,
                decode_responses=True,  # Enable JSON string responses
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
        except Exception as e:
            print(f"❌ Failed to create Redis client: {e}")
            raise ConnectionError(f"Invalid Redis URL or connection failed: {redis_url}") from e
    
    return _redis_client


async def close_redis() -> None:
    """
    Close Redis connection gracefully.
    """
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None 
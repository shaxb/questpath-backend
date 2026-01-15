"""
Rate limiting utilities using Redis.

Implements token bucket algorithm via Redis INCR + EXPIRE.
"""
from fastapi import HTTPException, Request
import logging

from .cache import redis_client
from .logger import logger

logger = logging.getLogger(__name__)


async def check_rate_limit(request: Request, key: str, limit: int, window: int):
    """Check and enforce rate limits using Redis.
    
    Args:
        request: FastAPI request object (to get client IP)
        key: Unique identifier for this rate limit (e.g., 'register', 'create_goal')
        limit: Maximum number of requests allowed
        window: Time window in seconds
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    ip = request.client.host
    cache_key = f"rate_limit:{ip}:{key}"
    
    try:
        count = redis_client.get(cache_key)
        if count and int(count) >= limit:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded. Try again in {window} seconds."
            )
        
        # Increment counter and set expiration
        pipe = redis_client.pipeline()
        pipe.incr(cache_key)
        pipe.expire(cache_key, window)
        pipe.execute()
    except HTTPException:
        # Re-raise HTTP exceptions (like rate limit exceeded)
        raise
    except Exception as e:
        # If Redis fails, log but don't block request (graceful degradation)
        logger.error(f"Rate limiting error: {e}")

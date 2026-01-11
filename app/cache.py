import redis
from typing import Optional
from app.config import settings

# Initialize Redis client
redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True
)

def get_cache(key: str) -> Optional[str]:
    """Get value from cache"""
    try:
        return redis_client.get(key)
    except redis.RedisError:
        return None

def set_cache(key: str, value: str, expire: int = 3600) -> bool:
    """Set value in cache with expiration time in seconds"""
    try:
        return redis_client.setex(key, expire, value)
    except redis.RedisError:
        return False

def delete_cache(key: str) -> bool:
    """Delete key from cache"""
    try:
        return redis_client.delete(key) > 0
    except redis.RedisError:
        return False

def clear_cache() -> bool:
    """Clear all cache"""
    try:
        return redis_client.flushdb()
    except redis.RedisError:
        return False
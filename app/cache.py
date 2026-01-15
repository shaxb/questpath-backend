import redis
from typing import Optional


from app.config import settings
from app.logger import logger
# Initialize Redis client
redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True
)

# Cache utility functions
def get_cache(key: str) -> Optional[str]:
    """Get value from cache"""
    try:
        return redis_client.get(key)
    except redis.RedisError:
        logger.warning("Redis error on get_cache, cache may be deleted or expired", exc_info=True, event="cache_miss", key=key)
        return None

def set_cache(key: str, value: str, expire: int = 3600) -> bool:
    """Set value in cache with expiration time in seconds"""
    try:
        return redis_client.setex(key, expire, value)
    except redis.RedisError:
        logger.error("Redis error on set_cache", exc_info=True, event="cache_set_error", key=key, value=value)
        return False

def delete_cache(key: str) -> bool:
    """Delete key from cache"""
    try:
        return redis_client.delete(key) > 0
    except redis.RedisError:
        logger.warning("Redis error on delete_cache or auto deleted by TTL expiration", exc_info=True, event="cache_delete_error", key=key)
        return False

def clear_cache() -> bool:
    """Clear all cache"""
    try:
        return redis_client.flushdb()
    except redis.RedisError:
        logger.error("Redis error on clear_cache", exc_info=True, event="cache_clear_error")
        return False
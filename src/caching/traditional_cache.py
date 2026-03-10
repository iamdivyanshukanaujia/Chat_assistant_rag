"""
Traditional Redis-based key-value caching.
"""
import json
from typing import Optional, Any
import redis

from src.utils.logger import get_logger
from src.utils.exceptions import CacheError
from src.config import settings

logger = get_logger(__name__)


class TraditionalCache:
    """Redis-based traditional caching for common queries."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize traditional cache.
        
        Args:
            redis_client: Redis client instance (optional)
        """
        if redis_client:
            self.redis = redis_client
        else:
            try:
                self.redis = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password if settings.redis_password else None,
                    db=settings.redis_db,
                    decode_responses=True
                )
                # Test connection
                self.redis.ping()
                logger.info("Connected to Redis for traditional caching")
            except Exception as e:
                raise CacheError(f"Failed to connect to Redis: {e}")
        
        self.ttl = settings.cache_ttl_seconds
        self.prefix = f"{settings.memory_redis_prefix}:cache"
    
    def _make_key(self, cache_type: str, key: str) -> str:
        """Generate cache key with prefix."""
        return f"{self.prefix}:{cache_type}:{key}"
    
    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            cache_type: Cache type (RAG, COURSE, FEE, etc.)
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        try:
            redis_key = self._make_key(cache_type, key)
            value = self.redis.get(redis_key)
            
            if value:
                logger.debug(f"Cache hit: {cache_type}:{key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache miss: {cache_type}:{key}")
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        cache_type: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """
        Set value in cache.
        
        Args:
            cache_type: Cache type
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        try:
            redis_key = self._make_key(cache_type, key)
            serialized = json.dumps(value, ensure_ascii=False)
            
            ttl = ttl or self.ttl
            self.redis.setex(redis_key, ttl, serialized)
            
            logger.debug(f"Cache set: {cache_type}:{key} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def delete(self, cache_type: str, key: str):
        """Delete a specific cache entry."""
        try:
            redis_key = self._make_key(cache_type, key)
            self.redis.delete(redis_key)
            logger.debug(f"Cache deleted: {cache_type}:{key}")
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    def invalidate(self, cache_type: Optional[str] = None):
        """
        Invalidate cache entries.
        
        Args:
            cache_type: Specific cache type to invalidate, or None for all
        """
        try:
            if cache_type:
                pattern = f"{self.prefix}:{cache_type}:*"
            else:
                pattern = f"{self.prefix}:*"
            
            # Get all matching keys
            keys = []
            cursor = 0
            while True:
                cursor, batch = self.redis.scan(cursor, match=pattern, count=100)
                keys.extend(batch)
                if cursor == 0:
                    break
            
            # Delete keys
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries")
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        try:
            # Count keys by type
            pattern = f"{self.prefix}:*"
            cursor = 0
            total_keys = 0
            
            while True:
                cursor, batch = self.redis.scan(cursor, match=pattern, count=100)
                total_keys += len(batch)
                if cursor == 0:
                    break
            
            return {
                "total_keys": total_keys,
                "ttl_seconds": self.ttl
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

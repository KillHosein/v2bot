"""
Advanced Redis Caching System for VPN Bot
Provides fast data access and reduces database load
"""
import redis
import json
import pickle
from typing import Any, Optional
from functools import wraps
import time
from .config import logger

class CacheManager:
    """Redis-based caching with fallback to memory"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", use_redis: bool = True):
        self.use_redis = use_redis
        self.memory_cache = {}  # Fallback cache
        
        if use_redis:
            try:
                self.redis = redis.from_url(redis_url, decode_responses=True)
                self.redis.ping()
                logger.info("✅ Redis cache connected")
            except Exception as e:
                logger.warning(f"⚠️ Redis unavailable, using memory cache: {e}")
                self.use_redis = False
                self.redis = None
        else:
            self.redis = None
            logger.info("💾 Using memory cache")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.use_redis and self.redis:
                value = self.redis.get(key)
                if value:
                    return json.loads(value)
            else:
                return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (seconds)"""
        try:
            if self.use_redis and self.redis:
                self.redis.setex(key, ttl, json.dumps(value))
            else:
                self.memory_cache[key] = {
                    'value': value,
                    'expires_at': time.time() + ttl
                }
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def delete(self, key: str):
        """Delete key from cache"""
        try:
            if self.use_redis and self.redis:
                self.redis.delete(key)
            else:
                self.memory_cache.pop(key, None)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        try:
            if self.use_redis and self.redis:
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
            else:
                keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace('*', '') in k]
                for k in keys_to_delete:
                    del self.memory_cache[k]
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            if self.use_redis and self.redis:
                info = self.redis.info('stats')
                return {
                    'type': 'redis',
                    'total_keys': self.redis.dbsize(),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                    'memory_used': self.redis.info('memory').get('used_memory_human', 'N/A')
                }
            else:
                # Clean expired memory cache
                now = time.time()
                active_keys = sum(1 for v in self.memory_cache.values() 
                                if isinstance(v, dict) and v.get('expires_at', 0) > now)
                return {
                    'type': 'memory',
                    'total_keys': active_keys,
                    'hits': 'N/A',
                    'misses': 'N/A',
                    'memory_used': 'N/A'
                }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {'type': 'error', 'message': str(e)}


# Global cache instance
_cache = None

def get_cache() -> CacheManager:
    """Get or create global cache instance"""
    global _cache
    if _cache is None:
        import os
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        use_redis = os.getenv('USE_REDIS', '1') == '1'
        _cache = CacheManager(redis_url, use_redis)
    return _cache


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache()
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

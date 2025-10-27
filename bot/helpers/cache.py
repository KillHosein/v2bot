"""Simple cache system for panel API responses"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import threading

class SimpleCache:
    """Thread-safe simple cache with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str, ttl_seconds: int = 14400) -> Optional[Any]:
        """
        Get value from cache if not expired
        
        Args:
            key: Cache key
            ttl_seconds: Time to live in seconds (default: 4 hours)
        
        Returns:
            Cached value or None if expired/not found
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            created_at = entry.get('created_at')
            value = entry.get('value')
            
            if not created_at:
                return None
            
            # Check if expired
            now = datetime.now()
            if now - created_at > timedelta(seconds=ttl_seconds):
                # Expired - remove it
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            self._cache[key] = {
                'value': value,
                'created_at': datetime.now()
            }
    
    def delete(self, key: str):
        """Delete a key from cache"""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """Clear all cache"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self, ttl_seconds: int = 14400):
        """Remove all expired entries"""
        with self._lock:
            now = datetime.now()
            expired_keys = []
            
            for key, entry in self._cache.items():
                created_at = entry.get('created_at')
                if created_at and now - created_at > timedelta(seconds=ttl_seconds):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)


# Global cache instance
panel_cache = SimpleCache()

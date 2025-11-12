"""
Performance Optimization and Advanced Caching System
Provides query optimization, connection pooling, and intelligent caching
"""
import asyncio
import time
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Callable, Tuple
from datetime import datetime, timedelta
from functools import wraps, lru_cache
from contextlib import asynccontextmanager
import sqlite3
from threading import Lock, local
from .config import logger
from .advanced_logging import get_advanced_logger


class ConnectionPool:
    """Database connection pool for better performance"""
    
    def __init__(self, db_path: str, pool_size: int = 10):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections: List[sqlite3.Connection] = []
        self.available: List[sqlite3.Connection] = []
        self.lock = Lock()
        self.local = local()
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self.connections.append(conn)
            self.available.append(conn)
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create optimized database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # Performance optimizations
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=30000000000")
        
        return conn
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        try:
            with self.lock:
                if self.available:
                    conn = self.available.pop()
                else:
                    # All connections busy, create a temporary one
                    conn = self._create_connection()
            
            yield conn
            
        finally:
            if conn:
                with self.lock:
                    if len(self.available) < self.pool_size:
                        self.available.append(conn)
                    else:
                        conn.close()
    
    def close_all(self):
        """Close all connections in the pool"""
        with self.lock:
            for conn in self.connections:
                try:
                    conn.close()
                except:
                    pass
            self.connections.clear()
            self.available.clear()


class SmartCache:
    """Intelligent caching system with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Tuple[Any, float, int]] = {}  # key -> (value, expiry, hits)
        self.access_times: Dict[str, float] = {}
        self.lock = Lock()
        self.logger = get_advanced_logger()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
    
    def _make_key(self, key: Any) -> str:
        """Convert any key to a string hash"""
        if isinstance(key, str):
            return key
        try:
            key_str = pickle.dumps(key)
            return hashlib.md5(key_str).hexdigest()
        except:
            return str(key)
    
    def get(self, key: Any) -> Optional[Any]:
        """Get value from cache"""
        key_hash = self._make_key(key)
        
        with self.lock:
            if key_hash in self.cache:
                value, expiry, hits = self.cache[key_hash]
                
                # Check expiry
                if time.time() > expiry:
                    del self.cache[key_hash]
                    self.stats['expirations'] += 1
                    self.stats['misses'] += 1
                    return None
                
                # Update access time and hit count
                self.access_times[key_hash] = time.time()
                self.cache[key_hash] = (value, expiry, hits + 1)
                self.stats['hits'] += 1
                return value
            
            self.stats['misses'] += 1
            return None
    
    def set(self, key: Any, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL"""
        key_hash = self._make_key(key)
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        
        with self.lock:
            # Check if we need to evict
            if len(self.cache) >= self.max_size and key_hash not in self.cache:
                self._evict()
            
            self.cache[key_hash] = (value, expiry, 0)
            self.access_times[key_hash] = time.time()
    
    def _evict(self):
        """Evict least recently used item"""
        if not self.access_times:
            return
        
        # Find LRU item
        lru_key = min(self.access_times, key=self.access_times.get)
        
        # Remove it
        del self.cache[lru_key]
        del self.access_times[lru_key]
        self.stats['evictions'] += 1
    
    def delete(self, key: Any) -> bool:
        """Delete key from cache"""
        key_hash = self._make_key(key)
        
        with self.lock:
            if key_hash in self.cache:
                del self.cache[key_hash]
                if key_hash in self.access_times:
                    del self.access_times[key_hash]
                return True
            return False
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.stats['evictions'] += len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'hit_rate': hit_rate,
                'evictions': self.stats['evictions'],
                'expirations': self.stats['expirations']
            }


class QueryOptimizer:
    """Optimize database queries for better performance"""
    
    def __init__(self, cache: SmartCache):
        self.cache = cache
        self.query_stats: Dict[str, Dict] = {}
        self.logger = get_advanced_logger()
    
    def optimize_query(self, query: str) -> str:
        """Apply query optimizations"""
        # Remove unnecessary whitespace
        query = ' '.join(query.split())
        
        # Common optimizations
        optimizations = [
            # Use EXISTS instead of COUNT for existence checks
            (r'SELECT COUNT\(\*\) FROM (.+) WHERE (.+) > 0',
             r'SELECT EXISTS(SELECT 1 FROM \1 WHERE \2)'),
            
            # Add LIMIT 1 for single row queries
            (r'SELECT (.+) FROM (.+) WHERE (.+) ORDER BY (.+)(?! LIMIT)',
             r'SELECT \1 FROM \2 WHERE \3 ORDER BY \4 LIMIT 1'),
        ]
        
        for pattern, replacement in optimizations:
            import re
            query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
        
        return query
    
    def should_cache_query(self, query: str) -> bool:
        """Determine if query result should be cached"""
        # Cache read-only queries
        read_only_keywords = ['SELECT', 'WITH']
        write_keywords = ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        
        query_upper = query.upper().strip()
        
        # Don't cache write operations
        for keyword in write_keywords:
            if query_upper.startswith(keyword):
                return False
        
        # Cache read operations
        for keyword in read_only_keywords:
            if query_upper.startswith(keyword):
                return True
        
        return False
    
    def get_cache_key(self, query: str, params: Optional[Tuple] = None) -> str:
        """Generate cache key for query"""
        key_parts = [query]
        if params:
            key_parts.append(str(params))
        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()
    
    def track_query(self, query: str, duration: float, cached: bool = False):
        """Track query performance statistics"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                'query': query[:100],  # Store first 100 chars
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'cache_hits': 0,
                'last_run': None
            }
        
        stats = self.query_stats[query_hash]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['last_run'] = datetime.now().isoformat()
        
        if cached:
            stats['cache_hits'] += 1
    
    def get_slow_queries(self, threshold: float = 0.1) -> List[Dict]:
        """Get queries slower than threshold"""
        slow_queries = [
            stats for stats in self.query_stats.values()
            if stats['avg_time'] > threshold
        ]
        return sorted(slow_queries, key=lambda x: x['avg_time'], reverse=True)


# Global instances
_connection_pool: Optional[ConnectionPool] = None
_smart_cache: Optional[SmartCache] = None
_query_optimizer: Optional[QueryOptimizer] = None


def initialize_performance_systems(db_path: str):
    """Initialize all performance systems"""
    global _connection_pool, _smart_cache, _query_optimizer
    
    _connection_pool = ConnectionPool(db_path)
    _smart_cache = SmartCache(max_size=2000, default_ttl=600)
    _query_optimizer = QueryOptimizer(_smart_cache)
    
    logger.info("Performance systems initialized")


def get_connection_pool() -> ConnectionPool:
    """Get connection pool instance"""
    global _connection_pool
    if not _connection_pool:
        from .config import DB_NAME
        _connection_pool = ConnectionPool(DB_NAME)
    return _connection_pool


def get_cache() -> SmartCache:
    """Get cache instance"""
    global _smart_cache
    if not _smart_cache:
        _smart_cache = SmartCache()
    return _smart_cache


def get_query_optimizer() -> QueryOptimizer:
    """Get query optimizer instance"""
    global _query_optimizer
    if not _query_optimizer:
        _query_optimizer = QueryOptimizer(get_cache())
    return _query_optimizer


# Decorators for optimization
def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"
            
            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"
            
            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def batch_operation(batch_size: int = 100):
    """Decorator to batch database operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract items from args/kwargs
            items = args[0] if args else kwargs.get('items', [])
            
            if not items:
                return []
            
            results = []
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_result = await func(batch, **kwargs)
                results.extend(batch_result)
            
            return results
        
        return wrapper
    
    return decorator


# Query optimization helper
async def optimized_query(query: str, 
                         params: Optional[Tuple] = None,
                         one: bool = False,
                         cache_ttl: Optional[int] = None):
    """Execute optimized and potentially cached query"""
    optimizer = get_query_optimizer()
    cache = get_cache()
    pool = get_connection_pool()
    
    # Optimize query
    optimized = optimizer.optimize_query(query)
    
    # Check if should cache
    if cache_ttl and optimizer.should_cache_query(optimized):
        cache_key = optimizer.get_cache_key(optimized, params)
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            optimizer.track_query(optimized, 0, cached=True)
            return cached_result
    
    # Execute query
    start = time.time()
    async with pool.get_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(optimized, params)
        else:
            cursor.execute(optimized)
        
        if one:
            result = cursor.fetchone()
            result = dict(result) if result else None
        else:
            result = [dict(row) for row in cursor.fetchall()]
    
    duration = time.time() - start
    optimizer.track_query(optimized, duration)
    
    # Cache if needed
    if cache_ttl and optimizer.should_cache_query(optimized):
        cache.set(cache_key, result, cache_ttl)
    
    return result

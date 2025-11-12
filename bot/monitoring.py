"""
Advanced Monitoring and Health Check System
Tracks bot performance, errors, and system health
"""
import time
import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .db import query_db, execute_db
from .config import logger
import traceback


class PerformanceMonitor:
    """Monitor bot performance and health"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.slow_requests = []
        self._create_tables()
    
    def _create_tables(self):
        """Create monitoring tables"""
        try:
            execute_db("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metadata TEXT
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    user_id INTEGER,
                    handler_name TEXT
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    component TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_time REAL,
                    details TEXT
                )
            """)
            
        except Exception as e:
            logger.error(f"Create monitoring tables error: {e}")
    
    def log_request(self, duration: float, handler_name: str = ""):
        """Log request performance"""
        self.request_count += 1
        
        # Track slow requests (>2 seconds)
        if duration > 2.0:
            self.slow_requests.append({
                'handler': handler_name,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 100 slow requests
            if len(self.slow_requests) > 100:
                self.slow_requests = self.slow_requests[-100:]
        
        # Log to database
        try:
            execute_db(
                """INSERT INTO performance_metrics (timestamp, metric_name, metric_value, metadata)
                   VALUES (?, 'request_duration', ?, ?)""",
                (datetime.now().isoformat(), duration, handler_name)
            )
        except Exception:
            pass
    
    def log_error(self, error: Exception, user_id: Optional[int] = None, handler_name: str = ""):
        """Log error"""
        self.error_count += 1
        
        try:
            execute_db(
                """INSERT INTO error_logs (timestamp, error_type, error_message, stack_trace, user_id, handler_name)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now().isoformat(),
                    type(error).__name__,
                    str(error),
                    traceback.format_exc(),
                    user_id,
                    handler_name
                )
            )
        except Exception as e:
            logger.error(f"Log error failed: {e}")
    
    async def check_database_health(self) -> Dict:
        """Check database connectivity and performance"""
        start = time.time()
        try:
            # Simple query to test DB
            query_db("SELECT 1", one=True)
            duration = time.time() - start
            
            return {
                'status': 'healthy',
                'response_time': duration,
                'message': f'DB responsive in {duration:.3f}s'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time': time.time() - start,
                'message': str(e)
            }
    
    async def check_panel_health(self, panel_id: int) -> Dict:
        """Check VPN panel connectivity"""
        start = time.time()
        try:
            from .panel import VpnPanelAPI
            panel_api = VpnPanelAPI(panel_id=panel_id)
            
            # Try to get panel info
            users, _ = await asyncio.wait_for(
                panel_api.get_all_users(limit=1),
                timeout=5.0
            )
            
            duration = time.time() - start
            
            return {
                'status': 'healthy',
                'response_time': duration,
                'message': f'Panel responsive in {duration:.3f}s'
            }
        except asyncio.TimeoutError:
            return {
                'status': 'timeout',
                'response_time': time.time() - start,
                'message': 'Panel timeout after 5s'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time': time.time() - start,
                'message': str(e)
            }
    
    async def check_cache_health(self) -> Dict:
        """Check cache system health"""
        start = time.time()
        try:
            from .cache_manager import get_cache
            cache = get_cache()
            
            # Test set and get
            test_key = "_health_check_test"
            cache.set(test_key, "test", ttl=10)
            result = cache.get(test_key)
            cache.delete(test_key)
            
            duration = time.time() - start
            
            if result == "test":
                return {
                    'status': 'healthy',
                    'response_time': duration,
                    'message': f'Cache working in {duration:.3f}s'
                }
            else:
                return {
                    'status': 'degraded',
                    'response_time': duration,
                    'message': 'Cache not returning correct values'
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time': time.time() - start,
                'message': str(e)
            }
    
    def get_system_stats(self) -> Dict:
        """Get system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total_gb': memory.total / (1024 ** 3),
                    'used_gb': memory.used / (1024 ** 3),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': disk.total / (1024 ** 3),
                    'used_gb': disk.used / (1024 ** 3),
                    'percent': disk.percent
                },
                'uptime': time.time() - self.start_time
            }
        except Exception as e:
            logger.error(f"System stats error: {e}")
            return {}
    
    def get_performance_stats(self) -> Dict:
        """Get bot performance statistics"""
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'error_rate': (self.error_count / self.request_count * 100) if self.request_count > 0 else 0,
            'requests_per_minute': (self.request_count / (uptime / 60)) if uptime > 0 else 0,
            'slow_requests_count': len(self.slow_requests)
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """Get recent errors"""
        try:
            return query_db(
                """SELECT * FROM error_logs
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (limit,)
            )
        except Exception:
            return []
    
    async def run_full_health_check(self) -> Dict:
        """Run complete health check"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Check database
        db_health = await self.check_database_health()
        results['components']['database'] = db_health
        if db_health['status'] != 'healthy':
            results['overall_status'] = 'degraded'
        
        # Check cache
        cache_health = await self.check_cache_health()
        results['components']['cache'] = cache_health
        if cache_health['status'] != 'healthy':
            results['overall_status'] = 'degraded'
        
        # Check all panels
        try:
            panels = query_db("SELECT id, name FROM panels WHERE enabled = 1")
            for panel in panels:
                panel_health = await self.check_panel_health(panel['id'])
                results['components'][f"panel_{panel['id']}"] = {
                    **panel_health,
                    'name': panel['name']
                }
                if panel_health['status'] != 'healthy':
                    results['overall_status'] = 'degraded'
        except Exception:
            pass
        
        # System resources
        results['system'] = self.get_system_stats()
        results['performance'] = self.get_performance_stats()
        
        # Save health check result
        try:
            execute_db(
                """INSERT INTO health_checks (timestamp, component, status, response_time, details)
                   VALUES (?, 'full_check', ?, ?, ?)""",
                (
                    results['timestamp'],
                    results['overall_status'],
                    0,
                    str(results)
                )
            )
        except Exception:
            pass
        
        return results


# Global monitor instance
_monitor = None

def get_monitor() -> PerformanceMonitor:
    """Get or create global monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


# Decorator for monitoring handler performance
def monitor_handler(handler_name: str = ""):
    """Decorator to monitor handler execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            monitor = get_monitor()
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                monitor.log_request(duration, handler_name or func.__name__)
                return result
            except Exception as e:
                # Try to get user_id from args
                user_id = None
                try:
                    if len(args) > 0 and hasattr(args[0], 'effective_user'):
                        user_id = args[0].effective_user.id
                except Exception:
                    pass
                
                monitor.log_error(e, user_id, handler_name or func.__name__)
                raise
        return wrapper
    return decorator

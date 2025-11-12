"""
Initialize and integrate all advanced features
This module loads all performance enhancements on bot startup
"""
import os
from typing import Optional
from telegram import Bot
from .config import logger, DB_NAME
from .advanced_logging import get_advanced_logger
from .error_handler import get_error_handler
from .advanced_monitoring import get_advanced_monitor
from .performance_optimizer import (
    initialize_performance_systems,
    get_connection_pool,
    get_cache,
    get_query_optimizer
)


def initialize_advanced_systems(bot: Optional[Bot] = None):
    """Initialize all advanced systems on startup"""
    
    logger.info("Initializing advanced systems...")
    
    try:
        # 1. Initialize advanced logging
        adv_logger = get_advanced_logger()
        adv_logger.logger.info("✅ Advanced logging system initialized")
        
        # 2. Initialize error handler
        error_handler = get_error_handler(bot)
        logger.info("✅ Advanced error handling initialized")
        
        # 3. Initialize monitoring
        monitor = get_advanced_monitor()
        logger.info("✅ Advanced monitoring initialized")
        
        # 4. Initialize performance systems
        if os.path.exists(DB_NAME):
            initialize_performance_systems(DB_NAME)
            logger.info("✅ Performance optimization initialized")
            
            # Test cache
            cache = get_cache()
            cache.set('_startup_test', 'ok', ttl=60)
            if cache.get('_startup_test') == 'ok':
                logger.info("✅ Cache system verified")
            
            # Test connection pool
            pool = get_connection_pool()
            logger.info(f"✅ Connection pool initialized with {pool.pool_size} connections")
        else:
            logger.warning(f"Database {DB_NAME} not found, skipping performance init")
        
        # 5. Log system info
        import platform
        import sys
        logger.info(f"System: {platform.system()} {platform.release()}")
        logger.info(f"Python: {sys.version}")
        logger.info(f"Bot started with PID: {os.getpid()}")
        
        # 6. Set up graceful shutdown
        import signal
        import asyncio
        
        def shutdown_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            
            # Close connection pool
            try:
                pool = get_connection_pool()
                pool.close_all()
                logger.info("Connection pool closed")
            except:
                pass
            
            # Clear cache stats
            try:
                cache = get_cache()
                stats = cache.get_stats()
                logger.info(f"Cache stats at shutdown: {stats}")
                cache.clear()
            except:
                pass
            
            # Save monitoring data
            try:
                monitor = get_advanced_monitor()
                metrics = monitor.export_metrics()
                with open('logs/final_metrics.json', 'w') as f:
                    f.write(metrics)
                logger.info("Metrics exported")
            except:
                pass
            
            logger.info("Shutdown complete")
            exit(0)
        
        # Register shutdown handlers
        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)
        
        logger.info("="*50)
        logger.info("🚀 ALL ADVANCED SYSTEMS INITIALIZED SUCCESSFULLY")
        logger.info("="*50)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize advanced systems: {e}")
        return False


async def periodic_maintenance():
    """Run periodic maintenance tasks"""
    import asyncio
    from datetime import datetime
    
    logger = get_advanced_logger()
    monitor = get_advanced_monitor()
    cache = get_cache()
    optimizer = get_query_optimizer()
    
    while True:
        try:
            # Wait for 1 hour
            await asyncio.sleep(3600)
            
            logger.logger.info("Running periodic maintenance...")
            
            # 1. Check system health
            health = await monitor.check_system_health()
            if health['status'] != 'healthy':
                logger.logger.warning(f"System health degraded: {health}")
            
            # 2. Clean old cache entries
            cache_stats = cache.get_stats()
            if cache_stats['hit_rate'] < 20:  # Less than 20% hit rate
                cache.clear()
                logger.logger.info("Cache cleared due to low hit rate")
            
            # 3. Analyze slow queries
            slow_queries = optimizer.get_slow_queries(threshold=0.5)
            if slow_queries:
                logger.logger.warning(f"Found {len(slow_queries)} slow queries")
                for query in slow_queries[:3]:
                    logger.logger.info(f"Slow query: {query['query'][:50]}... avg: {query['avg_time']:.3f}s")
            
            # 4. Check for predictions
            predictions = await monitor.predict_issues()
            for prediction in predictions:
                logger.logger.warning(f"Prediction: {prediction['message']}")
            
            # 5. Compact database (once a day at 3 AM)
            if datetime.now().hour == 3:
                pool = get_connection_pool()
                async with pool.get_connection() as conn:
                    conn.execute("VACUUM")
                    conn.execute("ANALYZE")
                    logger.logger.info("Database maintenance completed")
            
            logger.logger.info("Periodic maintenance completed")
            
        except Exception as e:
            logger.log_error(e, "periodic_maintenance")
            await asyncio.sleep(60)  # Wait 1 minute on error


def get_system_info() -> dict:
    """Get comprehensive system information"""
    import platform
    import psutil
    import sys
    
    try:
        return {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': sys.version,
                'python_implementation': platform.python_implementation()
            },
            'resources': {
                'cpu_count': psutil.cpu_count(),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                'memory': psutil.virtual_memory()._asdict(),
                'disk': psutil.disk_usage('/')._asdict(),
                'boot_time': psutil.boot_time()
            },
            'process': {
                'pid': os.getpid(),
                'cpu_percent': psutil.Process().cpu_percent(),
                'memory_info': psutil.Process().memory_info()._asdict(),
                'num_threads': psutil.Process().num_threads(),
                'create_time': psutil.Process().create_time()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return {}

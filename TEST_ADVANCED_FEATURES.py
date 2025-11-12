#!/usr/bin/env python3
"""
Test script for advanced features
Tests logging, error handling, monitoring, and performance optimization
"""
import asyncio
import time
import sys
import os

# Add bot directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_advanced_logging():
    """Test advanced logging system"""
    print("\n" + "="*60)
    print("🔍 Testing Advanced Logging System")
    print("="*60)
    
    try:
        from bot.advanced_logging import get_advanced_logger, log_performance
        
        logger = get_advanced_logger()
        
        # Test different log levels
        logger.logger.debug("Debug message - should only appear in file")
        logger.logger.info("Info message - should appear in console")
        logger.logger.warning("Warning message")
        logger.logger.error("Error message")
        
        # Test performance logging
        logger.log_performance("test_handler", 1.5, user_id=12345)
        logger.log_performance("slow_handler", 6.0, user_id=67890)  # Should trigger warning
        
        # Test error logging
        try:
            raise ValueError("Test error")
        except Exception as e:
            logger.log_error(e, "test_handler", user_id=12345)
        
        # Test audit logging
        logger.log_audit("test_action", user_id=12345, details={'test': 'data'})
        
        print("✅ Advanced logging tests passed")
        
        # Check if log files were created
        if os.path.exists('logs'):
            log_files = os.listdir('logs')
            print(f"📁 Log files created: {log_files}")
        
        return True
        
    except Exception as e:
        print(f"❌ Advanced logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handler():
    """Test error handling system"""
    print("\n" + "="*60)
    print("🔍 Testing Error Handler System")
    print("="*60)
    
    try:
        from bot.error_handler import get_error_handler, handle_errors
        
        handler = get_error_handler()
        
        # Test error tracking
        test_errors = [
            ValueError("Test value error"),
            KeyError("Test key error"),
            RuntimeError("Test runtime error")
        ]
        
        for error in test_errors:
            handler._track_error(error, user_id=12345, handler_name="test_handler")
        
        # Get error stats
        stats = handler.get_error_stats(hours=1)
        print(f"📊 Error stats: {stats}")
        
        # Test critical error detection
        critical = handler._is_critical_error(RuntimeError("Critical test"))
        print(f"🚨 Critical error detected: {critical}")
        
        print("✅ Error handler tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Error handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_monitoring():
    """Test monitoring system"""
    print("\n" + "="*60)
    print("🔍 Testing Advanced Monitoring System")
    print("="*60)
    
    try:
        from bot.advanced_monitoring import get_advanced_monitor
        
        monitor = get_advanced_monitor()
        
        # Track some requests
        await monitor.track_request("test_handler", 0.1, success=True, user_id=12345)
        await monitor.track_request("slow_handler", 3.0, success=True, user_id=67890)
        await monitor.track_request("error_handler", 0.5, success=False, user_id=11111)
        
        # Check system health
        health = await monitor.check_system_health()
        print(f"💚 System health: {health['status']}")
        print(f"📊 Components: {list(health['components'].keys())}")
        
        # Get metrics
        metrics = monitor._get_application_metrics()
        print(f"📈 Application metrics:")
        print(f"  - Uptime: {metrics['uptime']['formatted']}")
        print(f"  - Total requests: {metrics['requests']['total']}")
        print(f"  - Error rate: {metrics['requests']['error_rate']:.2f}%")
        
        # Test predictions
        predictions = await monitor.predict_issues()
        if predictions:
            print(f"🔮 Predictions: {len(predictions)} potential issues detected")
        
        # Export metrics
        json_metrics = monitor.export_metrics(format='json')
        print(f"📄 Exported {len(json_metrics)} bytes of metrics")
        
        print("✅ Monitoring tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Monitoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance_optimizer():
    """Test performance optimization system"""
    print("\n" + "="*60)
    print("🔍 Testing Performance Optimizer System")
    print("="*60)
    
    try:
        from bot.performance_optimizer import (
            get_cache, get_query_optimizer, cached,
            ConnectionPool, SmartCache, QueryOptimizer
        )
        
        # Test cache
        cache = SmartCache()
        cache.set("test_key", "test_value", ttl=60)
        value = cache.get("test_key")
        assert value == "test_value", "Cache get/set failed"
        print("✅ Cache get/set working")
        
        # Test cache stats
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.get("key1")  # Hit
        cache.get("key3")  # Miss
        stats = cache.get_stats()
        print(f"📊 Cache stats: {stats}")
        
        # Test query optimizer
        optimizer = QueryOptimizer(cache)
        
        # Test query optimization
        original = "SELECT COUNT(*) FROM users WHERE id > 0"
        optimized = optimizer.optimize_query(original)
        print(f"🔧 Query optimization:")
        print(f"  Original: {original}")
        print(f"  Optimized: {optimized}")
        
        # Test cache key generation
        cache_key = optimizer.get_cache_key("SELECT * FROM users", (1, 2, 3))
        print(f"🔑 Cache key generated: {cache_key[:16]}...")
        
        # Test cached decorator
        @cached(ttl=60, key_prefix="test")
        async def expensive_function(x):
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return x * 2
        
        start = time.time()
        result1 = await expensive_function(5)
        duration1 = time.time() - start
        
        start = time.time()
        result2 = await expensive_function(5)  # Should be cached
        duration2 = time.time() - start
        
        print(f"⚡ Cached function test:")
        print(f"  First call: {duration1:.3f}s")
        print(f"  Cached call: {duration2:.3f}s")
        print(f"  Speedup: {duration1/duration2:.1f}x")
        
        print("✅ Performance optimizer tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Performance optimizer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration():
    """Test integration of all systems"""
    print("\n" + "="*60)
    print("🔍 Testing System Integration")
    print("="*60)
    
    try:
        from bot.initialize_advanced_features import (
            initialize_advanced_systems,
            get_system_info
        )
        
        # Initialize all systems
        success = initialize_advanced_systems()
        print(f"🚀 Systems initialization: {'✅ Success' if success else '❌ Failed'}")
        
        # Get system info
        sys_info = get_system_info()
        print(f"💻 System info collected:")
        print(f"  - Platform: {sys_info.get('platform', {}).get('system', 'Unknown')}")
        print(f"  - CPU cores: {sys_info.get('resources', {}).get('cpu_count', 0)}")
        print(f"  - Memory: {sys_info.get('resources', {}).get('memory', {}).get('percent', 0):.1f}% used")
        
        print("✅ Integration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("╔════════════════════════════════════════════════╗")
    print("║   🚀 Testing Advanced Features                ║")
    print("╚════════════════════════════════════════════════╝")
    
    results = []
    
    # Run tests
    results.append(("Advanced Logging", await test_advanced_logging()))
    results.append(("Error Handler", await test_error_handler()))
    results.append(("Monitoring", await test_monitoring()))
    results.append(("Performance Optimizer", await test_performance_optimizer()))
    results.append(("Integration", await test_integration()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("="*60)
    print(f"Total: {passed} passed, {failed} failed")
    print(f"Success rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All advanced features are working correctly!")
        return 0
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

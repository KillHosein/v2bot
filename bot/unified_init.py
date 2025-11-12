"""
Unified Initialization System
Automatically initializes all features on bot startup
"""
import os
import sys
from typing import Optional
from telegram import Bot
from .config import logger


def initialize_all_systems(bot: Optional[Bot] = None) -> bool:
    """
    Initialize all bot systems in correct order
    Returns True if all critical systems initialized successfully
    """
    print("\n" + "="*60)
    print("🚀 WingsBot v5.0 - Unified Initialization")
    print("="*60 + "\n")
    
    critical_errors = []
    optional_errors = []
    
    # 1. Database Setup
    try:
        print("📦 Initializing Database...")
        from .db import db_setup
        db_setup()
        print("  ✅ Database ready")
    except Exception as e:
        critical_errors.append(f"Database: {e}")
        print(f"  ❌ Database failed: {e}")
    
    # 2. Core Systems
    try:
        print("\n🔧 Initializing Core Systems...")
        
        # Wallet System
        try:
            from .wallet_system import WalletSystem
            WalletSystem.setup_tables()
            print("  ✅ Wallet system ready")
        except Exception as e:
            optional_errors.append(f"Wallet: {e}")
            print(f"  ⚠️ Wallet system: {e}")
        
        # Loyalty System
        try:
            from .loyalty_system import LoyaltySystem
            LoyaltySystem.setup_tables()
            print("  ✅ Loyalty system ready")
        except Exception as e:
            optional_errors.append(f"Loyalty: {e}")
            print(f"  ⚠️ Loyalty system: {e}")
        
        # Smart Notifications
        try:
            from .smart_notifications import SmartNotification
            SmartNotification.setup_tables()
            print("  ✅ Smart notifications ready")
        except Exception as e:
            optional_errors.append(f"Notifications: {e}")
            print(f"  ⚠️ Notifications: {e}")
        
        # i18n System
        try:
            from .i18n import setup_i18n_tables
            setup_i18n_tables()
            print("  ✅ Multi-language support ready")
        except Exception as e:
            optional_errors.append(f"i18n: {e}")
            print(f"  ⚠️ i18n: {e}")
            
    except Exception as e:
        critical_errors.append(f"Core Systems: {e}")
        print(f"  ❌ Core systems failed: {e}")
    
    # 3. Advanced Features (v3.0)
    try:
        print("\n🏭 Initializing Advanced Features...")
        
        # Advanced Logging
        try:
            from .advanced_logging import get_advanced_logger
            adv_logger = get_advanced_logger()
            print("  ✅ Advanced logging ready")
        except Exception as e:
            optional_errors.append(f"Advanced Logging: {e}")
            print(f"  ⚠️ Advanced logging: {e}")
        
        # Error Handler
        try:
            from .error_handler import get_error_handler
            error_handler = get_error_handler(bot)
            print("  ✅ Error handler ready")
        except Exception as e:
            optional_errors.append(f"Error Handler: {e}")
            print(f"  ⚠️ Error handler: {e}")
        
        # Advanced Monitoring
        try:
            from .advanced_monitoring import get_advanced_monitor
            monitor = get_advanced_monitor()
            print("  ✅ Advanced monitoring ready")
        except Exception as e:
            optional_errors.append(f"Monitoring: {e}")
            print(f"  ⚠️ Monitoring: {e}")
        
        # Performance Optimizer
        try:
            from .performance_optimizer import (
                get_connection_pool, 
                get_cache, 
                get_query_optimizer
            )
            pool = get_connection_pool()
            cache = get_cache()
            optimizer = get_query_optimizer()
            print("  ✅ Performance optimizer ready")
        except Exception as e:
            optional_errors.append(f"Performance: {e}")
            print(f"  ⚠️ Performance optimizer: {e}")
            
    except Exception as e:
        optional_errors.append(f"Advanced Features: {e}")
        print(f"  ⚠️ Advanced features: {e}")
    
    # 4. Enterprise Plus Features (v4.0)
    try:
        print("\n👑 Initializing Enterprise Plus Features...")
        
        # Rate Limiter
        try:
            from .rate_limiter import get_rate_limiter
            limiter = get_rate_limiter()
            print("  ✅ Rate limiter ready")
        except Exception as e:
            optional_errors.append(f"Rate Limiter: {e}")
            print(f"  ⚠️ Rate limiter: {e}")
        
        # Auto Backup
        try:
            from .auto_backup import get_backup_manager
            backup = get_backup_manager()
            print("  ✅ Auto backup ready")
        except Exception as e:
            optional_errors.append(f"Backup: {e}")
            print(f"  ⚠️ Auto backup: {e}")
        
        # Security Manager
        try:
            from .security_manager import get_security_manager
            security = get_security_manager()
            print("  ✅ Security manager ready")
        except Exception as e:
            optional_errors.append(f"Security: {e}")
            print(f"  ⚠️ Security manager: {e}")
        
        # AI Assistant
        try:
            from .ai_assistant import get_ai_assistant
            ai = get_ai_assistant()
            print("  ✅ AI assistant ready")
        except Exception as e:
            optional_errors.append(f"AI: {e}")
            print(f"  ⚠️ AI assistant: {e}")
            
    except Exception as e:
        optional_errors.append(f"Enterprise Plus: {e}")
        print(f"  ⚠️ Enterprise Plus: {e}")
    
    # 5. UI System (v5.0)
    try:
        print("\n🎨 Initializing UI System...")
        from .ui_manager import get_ui_manager
        ui = get_ui_manager()
        print("  ✅ UI manager ready")
    except Exception as e:
        optional_errors.append(f"UI: {e}")
        print(f"  ⚠️ UI manager: {e}")
    
    # 6. Cache System
    try:
        print("\n💾 Initializing Cache System...")
        from .cache_manager import get_cache as cache_manager
        cache_mgr = cache_manager()
        # Test cache
        cache_mgr.set('_init_test', 'ok', 10)
        if cache_mgr.get('_init_test') == 'ok':
            print("  ✅ Cache system verified")
        else:
            print("  ⚠️ Cache system not optimal")
    except Exception as e:
        optional_errors.append(f"Cache: {e}")
        print(f"  ⚠️ Cache: {e}")
    
    # 7. Background Tasks
    try:
        print("\n⏰ Setting up Background Tasks...")
        import asyncio
        
        # Schedule periodic maintenance
        async def run_maintenance():
            from .advanced_monitoring import get_advanced_monitor
            from .auto_backup import get_backup_manager
            
            monitor = get_advanced_monitor()
            backup = get_backup_manager()
            
            while True:
                try:
                    # Run every hour
                    await asyncio.sleep(3600)
                    
                    # Health check
                    health = await monitor.check_system_health()
                    if health['status'] != 'healthy':
                        logger.warning(f"System health degraded: {health}")
                    
                    # Auto backup (if scheduled)
                    await backup.run_scheduled_backups()
                    
                except Exception as e:
                    logger.error(f"Maintenance error: {e}")
        
        # Schedule the task (don't await, let it run in background)
        asyncio.create_task(run_maintenance())
        print("  ✅ Background tasks scheduled")
        
    except Exception as e:
        optional_errors.append(f"Background Tasks: {e}")
        print(f"  ⚠️ Background tasks: {e}")
    
    # 8. Final Report
    print("\n" + "="*60)
    print("📊 Initialization Summary")
    print("="*60)
    
    if critical_errors:
        print(f"\n❌ Critical Errors ({len(critical_errors)}):")
        for error in critical_errors:
            print(f"  • {error}")
    
    if optional_errors:
        print(f"\n⚠️ Optional Features Failed ({len(optional_errors)}):")
        for error in optional_errors[:5]:  # Show first 5
            print(f"  • {error}")
        if len(optional_errors) > 5:
            print(f"  • ... and {len(optional_errors) - 5} more")
    
    # Determine overall status
    if not critical_errors:
        print("\n✅ Bot initialization successful!")
        print("🚀 All critical systems are operational")
        
        # Log system info
        try:
            import platform
            print(f"\n📱 System Info:")
            print(f"  • Platform: {platform.system()} {platform.release()}")
            print(f"  • Python: {platform.python_version()}")
            print(f"  • Bot Version: 5.0.0 Enterprise Plus")
            print(f"  • Status: Production Ready")
        except:
            pass
        
        return True
    else:
        print("\n❌ Bot initialization failed!")
        print("Critical systems could not be initialized")
        return False


def quick_test() -> bool:
    """Quick test to verify all systems"""
    print("\n🧪 Running Quick System Test...")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test database
    try:
        from .db import query_db
        query_db("SELECT 1", one=True)
        print("  ✅ Database test passed")
        tests_passed += 1
    except:
        print("  ❌ Database test failed")
        tests_failed += 1
    
    # Test cache
    try:
        from .cache_manager import get_cache
        cache = get_cache()
        cache.set('test', 'ok', 10)
        assert cache.get('test') == 'ok'
        print("  ✅ Cache test passed")
        tests_passed += 1
    except:
        print("  ❌ Cache test failed")
        tests_failed += 1
    
    # Test UI
    try:
        from .ui_manager import get_ui_manager
        ui = get_ui_manager()
        ui.format_text('welcome', bot_name='Test', user_name='User')
        print("  ✅ UI test passed")
        tests_passed += 1
    except:
        print("  ❌ UI test failed")
        tests_failed += 1
    
    # Test AI
    try:
        from .ai_assistant import get_ai_assistant
        ai = get_ai_assistant()
        intent, confidence = ai.detect_intent("سلام")
        print("  ✅ AI test passed")
        tests_passed += 1
    except:
        print("  ❌ AI test failed")
        tests_failed += 1
    
    # Test security
    try:
        from .security_manager import get_security_manager
        security = get_security_manager()
        encrypted = security.encrypt_data("test")
        decrypted = security.decrypt_data(encrypted)
        assert decrypted == "test"
        print("  ✅ Security test passed")
        tests_passed += 1
    except:
        print("  ❌ Security test failed")
        tests_failed += 1
    
    print(f"\n📊 Test Results: {tests_passed} passed, {tests_failed} failed")
    
    return tests_failed == 0


# Auto-initialize when imported
if __name__ != "__main__":
    # Only initialize if not being run directly
    import sys
    if 'bot.run' in sys.modules or 'bot.app' in sys.modules:
        # Bot is starting, initialize everything
        if not initialize_all_systems():
            logger.error("Failed to initialize bot systems!")
            # Don't exit, let the bot decide what to do

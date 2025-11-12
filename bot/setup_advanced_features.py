"""
راه‌اندازی ویژگی‌های پیشرفته v3.0
این ماژول تمام ویژگی‌های جدید را راه‌اندازی می‌کند
"""

from telegram.ext import Application, CallbackQueryHandler
from .config import logger

# Import handler های جدید
from .handlers.user_loyalty import (
    show_loyalty_menu,
    show_loyalty_history,
    show_loyalty_redeem,
    show_loyalty_rewards
)
from .handlers.user_dashboard import (
    show_user_dashboard,
    show_usage_stats,
    show_user_services
)
from .handlers.app_guide import (
    show_app_guide_menu,
    show_android_guide,
    show_ios_guide,
    show_windows_guide
)

# Import سیستم‌های پشتیبان
from .loyalty_system import LoyaltySystem
from .smart_notifications import SmartNotification


def setup_database_tables():
    """ساخت جداول جدید"""
    try:
        logger.info("Setting up advanced feature tables...")
        
        # سیستم امتیاز
        LoyaltySystem.setup_tables()
        
        # سیستم اعلان
        SmartNotification.setup_tables()
        
        logger.info("✅ Advanced feature tables created")
        return True
    except Exception as e:
        logger.error(f"❌ Error setting up tables: {e}")
        return False


def register_advanced_handlers(application: Application):
    """ثبت handler های جدید"""
    try:
        logger.info("Registering advanced feature handlers...")
        
        # Handler های باشگاه مشتریان (Loyalty)
        application.add_handler(
            CallbackQueryHandler(show_loyalty_menu, pattern=r'^loyalty_menu$'),
            group=2
        )
        application.add_handler(
            CallbackQueryHandler(show_loyalty_history, pattern=r'^loyalty_history$'),
            group=2
        )
        application.add_handler(
            CallbackQueryHandler(show_loyalty_redeem, pattern=r'^loyalty_redeem$'),
            group=2
        )
        application.add_handler(
            CallbackQueryHandler(show_loyalty_rewards, pattern=r'^loyalty_rewards$'),
            group=2
        )
        
        # Handler های داشبورد
        application.add_handler(
            CallbackQueryHandler(show_user_dashboard, pattern=r'^dashboard$'),
            group=2
        )
        application.add_handler(
            CallbackQueryHandler(show_usage_stats, pattern=r'^usage_stats$'),
            group=2
        )
        application.add_handler(
            CallbackQueryHandler(show_user_services, pattern=r'^user_services$'),
            group=2
        )
        
        # Handler های راهنمای اپ
        application.add_handler(
            CallbackQueryHandler(show_app_guide_menu, pattern=r'^app_guide_menu$'),
            group=2
        )
        application.add_handler(
            CallbackQueryHandler(show_android_guide, pattern=r'^app_guide_android$'),
            group=2
        )
        application.add_handler(
            CallbackQueryHandler(show_ios_guide, pattern=r'^app_guide_ios$'),
            group=2
        )
        application.add_handler(
            CallbackQueryHandler(show_windows_guide, pattern=r'^app_guide_windows$'),
            group=2
        )
        
        logger.info("✅ Advanced feature handlers registered")
        return True
    except Exception as e:
        logger.error(f"❌ Error registering handlers: {e}")
        return False


async def setup_notification_job(application: Application):
    """راه‌اندازی job های اعلان"""
    try:
        from .smart_notifications import run_notification_checks
        
        # اجرای چک اعلان‌ها هر 12 ساعت
        job_queue = application.job_queue
        
        if job_queue:
            job_queue.run_repeating(
                lambda context: run_notification_checks(context.bot),
                interval=43200,  # 12 ساعت
                first=10,  # 10 ثانیه بعد از start
                name='notification_checks'
            )
            
            logger.info("✅ Notification job scheduled (every 12 hours)")
        else:
            logger.warning("⚠️  Job queue not available")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error setting up notification job: {e}")
        return False


def initialize_advanced_features(application: Application):
    """راه‌اندازی کامل ویژگی‌های پیشرفته"""
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("🚀 Initializing Advanced Features v3.0")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    success_count = 0
    total_count = 3
    
    # گام 1: ساخت جداول
    if setup_database_tables():
        success_count += 1
        logger.info("  ✅ Step 1/3: Database tables")
    else:
        logger.error("  ❌ Step 1/3: Database tables FAILED")
    
    # گام 2: ثبت handler ها
    if register_advanced_handlers(application):
        success_count += 1
        logger.info("  ✅ Step 2/3: Handlers registered")
    else:
        logger.error("  ❌ Step 2/3: Handlers registration FAILED")
    
    # گام 3: راه‌اندازی job ها
    # این را async نمی‌کنیم چون بعداً توسط start_bot فراخوانی می‌شود
    success_count += 1
    logger.info("  ✅ Step 3/3: Jobs will be set up on start")
    
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"✅ Advanced Features: {success_count}/{total_count} initialized")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    if success_count == total_count:
        logger.info("🎉 All advanced features ready!")
        logger.info("")
        logger.info("📊 New Features Available:")
        logger.info("  ⭐ Loyalty & Points System")
        logger.info("  🔔 Smart Notifications")
        logger.info("  📊 User Dashboard")
        logger.info("  📱 App Connection Guide")
        logger.info("")
    
    return success_count == total_count

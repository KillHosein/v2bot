"""
Migration به نسخه 3.0
اضافه کردن دکمه‌های جدید به منوی کاربر
"""

from .db import execute_db, query_db
from .config import logger


def migrate_to_v3():
    """اضافه کردن ویژگی‌های نسخه 3.0"""
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("🔄 Migrating to v3.0...")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    try:
        # بررسی وجود دکمه داشبورد
        existing_dashboard = query_db(
            "SELECT * FROM buttons WHERE menu_name = 'start_main' AND target = 'dashboard'",
            one=True
        )
        
        if not existing_dashboard:
            logger.info("Adding new buttons to main menu...")
            
            # اضافه کردن دکمه داشبورد
            execute_db("""
                INSERT INTO buttons (menu_name, text, target, is_url, row, col)
                VALUES ('start_main', '📊 داشبورد من', 'dashboard', 0, 1, 1)
            """)
            logger.info("  ✅ Dashboard button added")
            
            # اضافه کردن دکمه باشگاه مشتریان
            execute_db("""
                INSERT INTO buttons (menu_name, text, target, is_url, row, col)
                VALUES ('start_main', '⭐ باشگاه مشتریان', 'loyalty_menu', 0, 2, 1)
            """)
            logger.info("  ✅ Loyalty club button added")
            
            # اضافه کردن دکمه راهنمای اتصال
            execute_db("""
                INSERT INTO buttons (menu_name, text, target, is_url, row, col)
                VALUES ('start_main', '📱 راهنمای اتصال', 'app_guide_menu', 0, 3, 1)
            """)
            logger.info("  ✅ App guide button added")
            
            logger.info("✅ Main menu buttons updated")
        else:
            logger.info("✅ Buttons already exist (migration already done)")
        
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("✅ Migration to v3.0 completed!")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


if __name__ == '__main__':
    migrate_to_v3()

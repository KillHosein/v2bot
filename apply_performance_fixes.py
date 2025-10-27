#!/usr/bin/env python3
"""
اسکریپت اعمال بهینه‌سازی‌های عملکردی
این اسکریپت ایندکس‌های جدید را به دیتابیس اضافه می‌کند.
"""

import sqlite3
import sys
import os
from datetime import datetime

def get_db_path():
    """Get database path"""
    # Try to import config
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))
        from config import DB_NAME
        return DB_NAME
    except:
        # Fallback to default
        return 'bot.db'

def apply_indexes(db_path):
    """Apply performance indexes to database"""
    
    print(f"🔍 اتصال به دیتابیس: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ خطا: فایل دیتابیس {db_path} یافت نشد!")
        return False
    
    # Backup first
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📦 ایجاد بکاپ در: {backup_path}")
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print("✅ بکاپ با موفقیت ایجاد شد")
    except Exception as e:
        print(f"⚠️ هشدار: خطا در ایجاد بکاپ: {e}")
        response = input("آیا می‌خواهید بدون بکاپ ادامه دهید؟ (y/n): ")
        if response.lower() != 'y':
            return False
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("✅ اتصال به دیتابیس برقرار شد")
    except Exception as e:
        print(f"❌ خطا در اتصال به دیتابیس: {e}")
        return False
    
    # List of indexes to create
    indexes = [
        ("idx_orders_panel_status", "CREATE INDEX IF NOT EXISTS idx_orders_panel_status ON orders(panel_id, status)"),
        ("idx_orders_username", "CREATE INDEX IF NOT EXISTS idx_orders_username ON orders(marzban_username)"),
        ("idx_tickets_status", "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)"),
        ("idx_tickets_user", "CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id)"),
        ("idx_users_banned", "CREATE INDEX IF NOT EXISTS idx_users_banned ON users(banned)"),
        ("idx_referrals_referrer", "CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)"),
    ]
    
    print(f"\n🔨 ایجاد {len(indexes)} ایندکس برای بهینه‌سازی عملکرد...")
    
    created = 0
    errors = 0
    
    for idx_name, idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
            print(f"  ✅ {idx_name}")
            created += 1
        except sqlite3.Error as e:
            print(f"  ⚠️ {idx_name}: {e}")
            errors += 1
    
    # Optimize database
    print("\n⚡ بهینه‌سازی دیتابیس...")
    try:
        cursor.execute("ANALYZE")
        cursor.execute("PRAGMA optimize")
        print("  ✅ بهینه‌سازی انجام شد")
    except Exception as e:
        print(f"  ⚠️ خطا در بهینه‌سازی: {e}")
    
    # Commit and close
    try:
        conn.commit()
        conn.close()
        print("✅ تغییرات ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در ذخیره تغییرات: {e}")
        return False
    
    # Summary
    print("\n" + "="*50)
    print("📊 خلاصه:")
    print(f"  • ایندکس‌های ایجاد شده: {created}")
    print(f"  • خطاها: {errors}")
    print(f"  • بکاپ: {backup_path}")
    print("="*50)
    
    if errors == 0:
        print("\n🎉 تمام بهینه‌سازی‌ها با موفقیت اعمال شد!")
    else:
        print("\n⚠️ برخی بهینه‌سازی‌ها با خطا مواجه شدند (احتمالاً از قبل وجود داشته‌اند)")
    
    return True

def check_indexes(db_path):
    """Check existing indexes"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = cursor.fetchall()
        
        print("\n📋 ایندکس‌های موجود:")
        for idx in indexes:
            print(f"  • {idx[0]}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ خطا در بررسی ایندکس‌ها: {e}")
        return False

def get_db_stats(db_path):
    """Get database statistics"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        stats = {}
        tables = ['users', 'orders', 'plans', 'panels', 'tickets', 'wallet_transactions']
        
        print("\n📊 آمار دیتابیس:")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
                print(f"  • {table}: {count:,} رکورد")
            except:
                pass
        
        # Database size
        db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
        print(f"  • حجم دیتابیس: {db_size:.2f} MB")
        
        conn.close()
        return stats
    except Exception as e:
        print(f"❌ خطا در دریافت آمار: {e}")
        return {}

def main():
    print("="*50)
    print("🚀 اسکریپت بهینه‌سازی عملکرد ربات")
    print("="*50)
    
    db_path = get_db_path()
    
    # Get stats before
    print("\n📈 وضعیت قبل از بهینه‌سازی:")
    get_db_stats(db_path)
    
    # Check existing indexes
    check_indexes(db_path)
    
    # Ask for confirmation
    print("\n⚠️ توجه: این عملیات ممکن است چند دقیقه طول بکشد.")
    print("توصیه می‌شود ربات را در این مدت خاموش کنید.\n")
    
    response = input("آیا می‌خواهید بهینه‌سازی را انجام دهید؟ (y/n): ")
    
    if response.lower() != 'y':
        print("❌ عملیات لغو شد")
        return
    
    # Apply indexes
    if apply_indexes(db_path):
        # Check indexes after
        print("\n✅ بررسی نهایی:")
        check_indexes(db_path)
        
        print("\n" + "="*50)
        print("🎊 بهینه‌سازی با موفقیت انجام شد!")
        print("💡 توصیه: ربات را restart کنید تا تغییرات اعمال شود.")
        print("="*50)
    else:
        print("\n❌ بهینه‌سازی با شکست مواجه شد")
        sys.exit(1)

if __name__ == '__main__':
    main()

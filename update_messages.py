#!/usr/bin/env python3
"""
اسکریپت بروزرسانی متن‌های دیتابیس
این اسکریپت متن‌های جدید قابل تغییر را به جدول messages اضافه می‌کند.
"""

import sqlite3
import sys

DB_NAME = "bot_db.sqlite"

def update_messages():
    """اضافه کردن متن‌های جدید به دیتابیس"""
    new_messages = {
        'admin_messages_menu': 'مدیریت پیام‌ها و صفحات:',
        'admin_users_menu': '👥 مدیریت کاربران',
        'admin_stats_title': '📈 **آمار ربات**',
        'admin_panels_menu': '🖥️ مدیریت پنل‌ها',
        'admin_plans_menu': '📋 مدیریت پلن‌ها',
        'admin_cards_menu': '💳 مدیریت کارت‌های بانکی',
        'admin_settings_menu': '⚙️ **تنظیمات کلی ربات**',
        'trial_panel_select': 'پنل ساخت تست را انتخاب کنید:',
        'trial_inbound_select': (
            'انتخاب اینباند کانفیگ تست\n\n'
            'این گزینه فقط برای پنل‌های XUI/3xUI/Alireza/TX-UI کاربرد دارد.\n'
            'اینباندی را انتخاب کنید تا کانفیگ‌های تست روی همان اینباند ساخته شوند.'
        )
    }
    
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
            # بررسی وجود جدول messages
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
            if not cursor.fetchone():
                print("❌ جدول messages یافت نشد!")
                return False
            
            # اضافه کردن متن‌های جدید
            added = 0
            updated = 0
            for message_name, text in new_messages.items():
                cursor.execute(
                    "SELECT message_name FROM messages WHERE message_name = ?",
                    (message_name,)
                )
                exists = cursor.fetchone()
                
                if exists:
                    # بروزرسانی متن موجود (اختیاری)
                    cursor.execute(
                        "UPDATE messages SET text = ? WHERE message_name = ?",
                        (text, message_name)
                    )
                    updated += 1
                    print(f"✅ متن '{message_name}' بروزرسانی شد")
                else:
                    # اضافه کردن متن جدید
                    cursor.execute(
                        "INSERT INTO messages (message_name, text, file_id, file_type) VALUES (?, ?, NULL, NULL)",
                        (message_name, text)
                    )
                    added += 1
                    print(f"➕ متن '{message_name}' اضافه شد")
            
            conn.commit()
            print(f"\n✅ بروزرسانی کامل شد!")
            print(f"   - {added} متن جدید اضافه شد")
            print(f"   - {updated} متن موجود بروزرسانی شد")
            return True
            
    except sqlite3.Error as e:
        print(f"❌ خطا در بروزرسانی دیتابیس: {e}")
        return False
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        return False


if __name__ == "__main__":
    print("🔄 شروع بروزرسانی متن‌های دیتابیس...")
    print(f"📁 دیتابیس: {DB_NAME}\n")
    
    success = update_messages()
    
    if success:
        print("\n✅ همه چیز با موفقیت انجام شد!")
        print("\n📝 توجه: می‌توانید این متن‌ها را از طریق منوی 'مدیریت پیام‌ها' در پنل ادمین ویرایش کنید.")
        sys.exit(0)
    else:
        print("\n❌ بروزرسانی با خطا مواجه شد!")
        sys.exit(1)

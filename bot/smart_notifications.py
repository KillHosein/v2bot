"""
سیستم اعلان هوشمند
ارسال یادآوری و پیام‌های هوشمند به کاربران
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from telegram import Bot
from telegram.constants import ParseMode

from .db import query_db, execute_db
from .config import logger


class SmartNotification:
    """مدیریت اعلان‌های هوشمند"""
    
    @staticmethod
    def setup_tables():
        """ساخت جداول مورد نیاز"""
        execute_db("""
            CREATE TABLE IF NOT EXISTS notification_settings (
                user_id INTEGER PRIMARY KEY,
                service_expiry BOOLEAN DEFAULT 1,
                traffic_low BOOLEAN DEFAULT 1,
                special_offers BOOLEAN DEFAULT 1,
                new_products BOOLEAN DEFAULT 1,
                birthday BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        execute_db("""
            CREATE TABLE IF NOT EXISTS notification_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                notification_type TEXT,
                message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        logger.info("✅ Smart notification tables created")
    
    @staticmethod
    def get_user_settings(user_id: int) -> Dict:
        """دریافت تنظیمات اعلان کاربر"""
        settings = query_db(
            "SELECT * FROM notification_settings WHERE user_id = ?",
            (user_id,),
            one=True
        )
        
        if not settings:
            # تنظیمات پیش‌فرض
            execute_db(
                "INSERT INTO notification_settings (user_id) VALUES (?)",
                (user_id,)
            )
            settings = {
                'user_id': user_id,
                'service_expiry': 1,
                'traffic_low': 1,
                'special_offers': 1,
                'new_products': 1,
                'birthday': 1
            }
        
        return settings
    
    @staticmethod
    def update_setting(user_id: int, setting_name: str, value: bool):
        """بروزرسانی یک تنظیم"""
        execute_db(f"""
            UPDATE notification_settings 
            SET {setting_name} = ?
            WHERE user_id = ?
        """, (1 if value else 0, user_id))
    
    @staticmethod
    async def send_notification(bot: Bot, user_id: int, notification_type: str, message: str):
        """ارسال اعلان به کاربر"""
        try:
            # بررسی تنظیمات کاربر
            settings = SmartNotification.get_user_settings(user_id)
            
            if not settings.get(notification_type, False):
                logger.info(f"Notification {notification_type} disabled for user {user_id}")
                return False
            
            # ارسال پیام
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            
            # ثبت در لاگ
            execute_db("""
                INSERT INTO notification_log (user_id, notification_type, message)
                VALUES (?, ?, ?)
            """, (user_id, notification_type, message))
            
            logger.info(f"Sent {notification_type} notification to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification to {user_id}: {e}")
            return False
    
    @staticmethod
    async def check_expiring_services(bot: Bot):
        """بررسی سرویس‌های در حال اتمام"""
        # سرویس‌هایی که 1، 3، 7 روز دیگر تمام می‌شوند
        for days in [1, 3, 7]:
            target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            
            services = query_db("""
                SELECT o.user_id, o.id as order_id, u.first_name, 
                       p.name as plan_name, o.expire_date
                FROM orders o
                JOIN users u ON o.user_id = u.user_id
                JOIN plans p ON o.plan_id = p.id
                WHERE DATE(o.expire_date) = ?
                AND o.status = 'active'
            """, (target_date,)) or []
            
            for service in services:
                message = f"""
⚠️ <b>یادآوری اتمام سرویس</b>

سلام {service['first_name']} عزیز! 👋

سرویس <b>{service['plan_name']}</b> شما تا {days} روز دیگر به پایان می‌رسد! ⏰

📅 <b>تاریخ اتمام:</b> {service['expire_date']}

💡 برای تمدید سرویس و جلوگیری از قطعی، همین الان اقدام کنید.

🎁 تخفیف ویژه تمدید: 10% برای شما!
"""
                await SmartNotification.send_notification(
                    bot, 
                    service['user_id'], 
                    'service_expiry', 
                    message
                )
    
    @staticmethod
    async def check_low_traffic(bot: Bot):
        """بررسی سرویس‌های با حجم کم"""
        # سرویس‌هایی که کمتر از 1GB حجم دارند
        services = query_db("""
            SELECT o.user_id, o.id as order_id, u.first_name, 
                   p.name as plan_name, o.remaining_traffic_gb
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            JOIN plans p ON o.plan_id = p.id
            WHERE o.remaining_traffic_gb < 1.0
            AND o.remaining_traffic_gb > 0
            AND o.status = 'active'
        """) or []
        
        for service in services:
            traffic_mb = int(service['remaining_traffic_gb'] * 1024)
            
            message = f"""
📊 <b>هشدار حجم کم</b>

سلام {service['first_name']} عزیز! 👋

حجم سرویس <b>{service['plan_name']}</b> شما رو به اتمام است! ⚠️

📦 <b>حجم باقیمانده:</b> {traffic_mb} مگابایت

💡 برای جلوگیری از قطعی، همین الان اقدام به خرید حجم اضافه یا تمدید کنید.

🎁 پیشنهاد ویژه: 20% تخفیف برای خرید حجم!
"""
            await SmartNotification.send_notification(
                bot, 
                service['user_id'], 
                'traffic_low', 
                message
            )
    
    @staticmethod
    async def send_special_offer(bot: Bot, user_ids: List[int], offer_text: str):
        """ارسال پیشنهاد ویژه"""
        for user_id in user_ids:
            await SmartNotification.send_notification(
                bot,
                user_id,
                'special_offers',
                offer_text
            )
    
    @staticmethod
    async def send_birthday_wish(bot: Bot):
        """ارسال تبریک تولد"""
        today = datetime.now().date()
        
        # کاربرانی که امروز تولدشان است
        users = query_db("""
            SELECT up.user_id, u.first_name
            FROM user_points up
            JOIN users u ON up.user_id = u.user_id
            WHERE strftime('%m-%d', up.birthday) = ?
        """, (today.strftime('%m-%d'),)) or []
        
        for user in users:
            message = f"""
🎂 <b>تولدت مبارک!</b> 🎉

{user['first_name']} عزیز! 🎈

امروز روز خاص توست! 🌟
از طرف تیم ما، تولدت رو تبریک می‌گیم! 🎊

🎁 <b>هدیه تولد:</b>
   • 100 امتیاز هدیه
   • 20% تخفیف ویژه امروز
   • یک ماه سرویس رایگان

برای دریافت هدایا، به باشگاه مشتریان مراجعه کن! 💎
"""
            await SmartNotification.send_notification(
                bot,
                user['user_id'],
                'birthday',
                message
            )


async def run_notification_checks(bot: Bot):
    """اجرای چک‌های دوره‌ای اعلان (توسط Cron)"""
    logger.info("Running notification checks...")
    
    try:
        await SmartNotification.check_expiring_services(bot)
        await SmartNotification.check_low_traffic(bot)
        await SmartNotification.send_birthday_wish(bot)
        
        logger.info("✅ Notification checks completed")
    except Exception as e:
        logger.error(f"Error in notification checks: {e}")

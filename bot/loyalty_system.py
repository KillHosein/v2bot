"""
سیستم امتیاز و وفاداری مشتری
این سیستم به کاربران برای فعالیت‌هایشان امتیاز می‌دهد
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from .db import query_db, execute_db
from .config import logger

# سطوح کاربری
LEVELS = {
    'bronze': {'name': 'برنز', 'min_points': 0, 'discount': 0, 'emoji': '🥉'},
    'silver': {'name': 'نقره', 'min_points': 100, 'discount': 5, 'emoji': '🥈'},
    'gold': {'name': 'طلا', 'min_points': 500, 'discount': 10, 'emoji': '🥇'},
    'platinum': {'name': 'پلاتینیوم', 'min_points': 1000, 'discount': 15, 'emoji': '💎'},
    'diamond': {'name': 'الماس', 'min_points': 2500, 'discount': 20, 'emoji': '💠'}
}

# امتیازات برای فعالیت‌های مختلف
POINT_REWARDS = {
    'signup': 10,           # ثبت نام
    'first_purchase': 50,   # اولین خرید
    'purchase': 10,         # هر 10,000 تومان خرید = 10 امتیاز
    'referral': 100,        # معرفی کاربر جدید
    'review': 20,           # نظر دادن
    'daily_login': 1,       # ورود روزانه
    'birthday': 100,        # تولد
}


class LoyaltySystem:
    """مدیریت سیستم امتیاز و وفاداری"""
    
    @staticmethod
    def setup_tables():
        """ساخت جداول مورد نیاز"""
        # جدول امتیازات کاربر
        execute_db("""
            CREATE TABLE IF NOT EXISTS user_points (
                user_id INTEGER PRIMARY KEY,
                total_points INTEGER DEFAULT 0,
                current_points INTEGER DEFAULT 0,
                level TEXT DEFAULT 'bronze',
                last_daily_login DATE,
                birthday DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # جدول تاریخچه امتیازات
        execute_db("""
            CREATE TABLE IF NOT EXISTS points_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                points INTEGER,
                action TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        logger.info("✅ Loyalty system tables created")
    
    @staticmethod
    def get_user_points(user_id: int) -> Dict:
        """دریافت اطلاعات امتیاز کاربر"""
        points_data = query_db(
            "SELECT * FROM user_points WHERE user_id = ?",
            (user_id,),
            one=True
        )
        
        if not points_data:
            # ساخت رکورد جدید
            execute_db(
                "INSERT INTO user_points (user_id) VALUES (?)",
                (user_id,)
            )
            points_data = {
                'user_id': user_id,
                'total_points': 0,
                'current_points': 0,
                'level': 'bronze'
            }
        
        return points_data
    
    @staticmethod
    def get_level_info(points: int) -> Dict:
        """تعیین سطح کاربر بر اساس امتیاز"""
        level = 'bronze'
        for level_key, level_data in sorted(LEVELS.items(), key=lambda x: x[1]['min_points'], reverse=True):
            if points >= level_data['min_points']:
                level = level_key
                break
        
        return LEVELS[level]
    
    @staticmethod
    def add_points(user_id: int, points: int, action: str, description: str = '') -> bool:
        """اضافه کردن امتیاز به کاربر"""
        try:
            # دریافت امتیاز فعلی
            user_points = LoyaltySystem.get_user_points(user_id)
            
            new_current = user_points['current_points'] + points
            new_total = user_points['total_points'] + points
            
            # تعیین سطح جدید
            new_level_info = LoyaltySystem.get_level_info(new_total)
            new_level = [k for k, v in LEVELS.items() if v == new_level_info][0]
            
            # بروزرسانی امتیاز
            execute_db("""
                UPDATE user_points 
                SET current_points = ?, 
                    total_points = ?,
                    level = ?
                WHERE user_id = ?
            """, (new_current, new_total, new_level, user_id))
            
            # ثبت در تاریخچه
            execute_db("""
                INSERT INTO points_history (user_id, points, action, description)
                VALUES (?, ?, ?, ?)
            """, (user_id, points, action, description))
            
            logger.info(f"Added {points} points to user {user_id} for {action}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding points: {e}")
            return False
    
    @staticmethod
    def use_points(user_id: int, points: int, description: str = '') -> bool:
        """استفاده از امتیاز (تبدیل به تخفیف)"""
        try:
            user_points = LoyaltySystem.get_user_points(user_id)
            
            if user_points['current_points'] < points:
                return False
            
            new_current = user_points['current_points'] - points
            
            execute_db("""
                UPDATE user_points 
                SET current_points = ?
                WHERE user_id = ?
            """, (new_current, user_id))
            
            # ثبت در تاریخچه
            execute_db("""
                INSERT INTO points_history (user_id, points, action, description)
                VALUES (?, ?, 'redeem', ?)
            """, (user_id, -points, description))
            
            logger.info(f"User {user_id} used {points} points")
            return True
            
        except Exception as e:
            logger.error(f"Error using points: {e}")
            return False
    
    @staticmethod
    def check_daily_login(user_id: int) -> int:
        """بررسی و ثبت ورود روزانه"""
        user_points = LoyaltySystem.get_user_points(user_id)
        today = datetime.now().date()
        
        last_login = user_points.get('last_daily_login')
        if last_login:
            last_login = datetime.strptime(str(last_login), '%Y-%m-%d').date()
            if last_login >= today:
                return 0  # امروز قبلا وارد شده
        
        # ثبت ورود امروز
        execute_db("""
            UPDATE user_points 
            SET last_daily_login = ?
            WHERE user_id = ?
        """, (today, user_id))
        
        # اضافه کردن امتیاز
        points = POINT_REWARDS['daily_login']
        LoyaltySystem.add_points(user_id, points, 'daily_login', 'ورود روزانه')
        
        return points
    
    @staticmethod
    def check_birthday(user_id: int) -> int:
        """بررسی تولد و اعطای جایزه"""
        user_points = LoyaltySystem.get_user_points(user_id)
        
        if not user_points.get('birthday'):
            return 0
        
        birthday = datetime.strptime(str(user_points['birthday']), '%Y-%m-%d').date()
        today = datetime.now().date()
        
        # بررسی اینکه امروز تولد است یا نه
        if birthday.month == today.month and birthday.day == today.day:
            # بررسی اینکه امسال جایزه نگرفته
            this_year_birthday = query_db("""
                SELECT * FROM points_history 
                WHERE user_id = ? 
                AND action = 'birthday'
                AND DATE(created_at) >= ?
            """, (user_id, f"{today.year}-01-01"), one=True)
            
            if not this_year_birthday:
                points = POINT_REWARDS['birthday']
                LoyaltySystem.add_points(user_id, points, 'birthday', '🎂 جشن تولد')
                return points
        
        return 0
    
    @staticmethod
    def get_discount_percent(user_id: int) -> int:
        """دریافت درصد تخفیف کاربر بر اساس سطح"""
        user_points = LoyaltySystem.get_user_points(user_id)
        level = user_points.get('level', 'bronze')
        return LEVELS[level]['discount']
    
    @staticmethod
    def calculate_purchase_points(amount: int) -> int:
        """محاسبه امتیاز برای خرید"""
        # هر 10,000 تومان = 10 امتیاز
        return (amount // 10000) * POINT_REWARDS['purchase']
    
    @staticmethod
    def get_points_history(user_id: int, limit: int = 10) -> List[Dict]:
        """دریافت تاریخچه امتیازات"""
        return query_db("""
            SELECT * FROM points_history 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit)) or []
    
    @staticmethod
    def get_user_stats_text(user_id: int) -> str:
        """ساخت متن آمار کاربر"""
        user_points = LoyaltySystem.get_user_points(user_id)
        
        total = user_points['total_points']
        current = user_points['current_points']
        level = user_points.get('level', 'bronze')
        
        level_info = LEVELS[level]
        emoji = level_info['emoji']
        name = level_info['name']
        discount = level_info['discount']
        
        # سطح بعدی
        next_level = None
        for level_key, level_data in sorted(LEVELS.items(), key=lambda x: x[1]['min_points']):
            if level_data['min_points'] > total:
                next_level = level_data
                break
        
        text = f"""
{emoji} <b>باشگاه مشتریان وفادار</b>

━━━━━━━━━━━━━━━━━━━━━━━━

👤 <b>سطح شما:</b> {name} {emoji}
⭐ <b>امتیاز کل:</b> {total:,} امتیاز
💎 <b>امتیاز قابل استفاده:</b> {current:,} امتیاز
🎁 <b>تخفیف ویژه:</b> {discount}%

━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if next_level:
            needed = next_level['min_points'] - total
            text += f"\n🎯 <b>تا سطح {next_level['name']}:</b> {needed:,} امتیاز مانده\n"
        else:
            text += "\n👑 <b>شما در بالاترین سطح هستید!</b>\n"
        
        text += """
━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>روش‌های کسب امتیاز:</b>
   • خرید: هر 10,000 تومان = 10 امتیاز
   • معرفی دوستان: 100 امتیاز
   • ورود روزانه: 1 امتیاز
   • تولد: 100 امتیاز

💰 <b>استفاده از امتیاز:</b>
   • هر 100 امتیاز = 10,000 تومان تخفیف
"""
        
        return text


# نمونه استفاده
def example_usage():
    """مثال استفاده از سیستم"""
    # راه‌اندازی جداول
    LoyaltySystem.setup_tables()
    
    user_id = 123456
    
    # ثبت نام کاربر جدید
    LoyaltySystem.add_points(user_id, POINT_REWARDS['signup'], 'signup', 'ثبت نام در ربات')
    
    # اولین خرید
    LoyaltySystem.add_points(user_id, POINT_REWARDS['first_purchase'], 'first_purchase', 'اولین خرید')
    
    # خرید 50,000 تومانی
    purchase_points = LoyaltySystem.calculate_purchase_points(50000)
    LoyaltySystem.add_points(user_id, purchase_points, 'purchase', 'خرید 50,000 تومانی')
    
    # دریافت آمار
    stats_text = LoyaltySystem.get_user_stats_text(user_id)
    print(stats_text)


if __name__ == '__main__':
    example_usage()

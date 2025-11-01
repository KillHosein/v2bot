"""Admin menu structure and helper functions"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from ..db import query_db

async def get_admin_stats():
    """Get quick stats for admin dashboard"""
    try:
        stats = query_db("""
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM orders WHERE status='active') as active_services,
                (SELECT COALESCE(SUM(amount), 0) FROM wallet_transactions 
                 WHERE direction='credit' AND status='approved' AND date(created_at) = date('now')) as today_income,
                (SELECT COUNT(*) FROM orders WHERE status='pending') as pending_orders,
                (SELECT COUNT(*) FROM tickets WHERE status='open') as open_tickets
        """, one=True)
        
        return {
            'total_users': stats.get('total_users', 0),
            'active_services': stats.get('active_services', 0),
            'today_income': stats.get('today_income', 0),
            'pending_orders': stats.get('pending_orders', 0),
            'open_tickets': stats.get('open_tickets', 0)
        }
    except Exception as e:
        print(f"Error getting admin stats: {e}")
        return {
            'total_users': 0,
            'active_services': 0,
            'today_income': 0,
            'pending_orders': 0,
            'open_tickets': 0
        }

def get_main_menu_keyboard():
    """Generate main admin menu keyboard"""
    # Get bot active status
    try:
        active_val = (query_db("SELECT value FROM settings WHERE key='bot_active'", one=True) or {}).get('value') or '1'
        bot_on = str(active_val) == '1'
    except Exception:
        bot_on = True
    
    toggle_label = "🟢 ربات روشن (خاموش کردن)" if bot_on else "🔴 ربات خاموش (روشن کردن)"
    
    return [
        [
            InlineKeyboardButton(toggle_label, callback_data="admin_toggle_bot_active")
        ],
        [
            InlineKeyboardButton("👥 کاربران", callback_data="admin_user_management"),
            InlineKeyboardButton("📦 سفارشات", callback_data="admin_orders_manage")
        ],
        [
            InlineKeyboardButton("🌐 پنل‌ها", callback_data="admin_panels_menu"),
            InlineKeyboardButton("📝 پلن‌ها", callback_data="admin_plan_manage")
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings_manage"),
            InlineKeyboardButton("📊 آمار", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton("🎯 آمار پیشرفته", callback_data="admin_advanced_stats"),
            InlineKeyboardButton("📡 مانیتورینگ", callback_data="admin_monitoring_menu")
        ],
        [
            InlineKeyboardButton("💳 پرداخت‌ها", callback_data="admin_payments_menu"),
            InlineKeyboardButton("🎁 کد تخفیف", callback_data="admin_discount_menu")
        ],
        [
            InlineKeyboardButton("📝 مدیریت پیام‌ها", callback_data="admin_messages_menu"),
            InlineKeyboardButton("💬 تیکت‌ها", callback_data="admin_tickets_menu")
        ],
        [
            InlineKeyboardButton("📤 ارسال همگانی", callback_data="admin_broadcast_menu"),
            InlineKeyboardButton("📧 پیام به کاربر", callback_data="admin_send_by_id_start")
        ],
        [
            InlineKeyboardButton("🛠️ وضعیت سیستم", callback_data="admin_system_health"),
            InlineKeyboardButton("🔔 ارسال یادآوری‌ها", callback_data="run_alerts_now")
        ],
        [
            InlineKeyboardButton("💾 دریافت سریع بکاپ", callback_data="admin_quick_backup"),
            InlineKeyboardButton("📦 بکاپ پیشرفته", callback_data="backup_start")
        ],
        [
            InlineKeyboardButton("📥 بازیابی از بکاپ", callback_data="backup_restore_start"),
            InlineKeyboardButton("👑 افزودن ادمین", callback_data="admin_admins_menu")
        ],
        [
            InlineKeyboardButton("🕐 کرون جاب‌ها", callback_data="admin_cron_menu"),
            InlineKeyboardButton("📚 آموزش‌ها", callback_data="admin_tutorials_menu")
        ]
    ]

def get_settings_menu():
    """Generate settings menu keyboard"""
    return [
        [InlineKeyboardButton("⚙️ تنظیمات عمومی", callback_data="admin_general_settings")],
        [InlineKeyboardButton("🔔 تنظیمات نوتیفیکیشن‌ها", callback_data="admin_notification_settings")],
        [InlineKeyboardButton("💳 تنظیمات پرداخت", callback_data="admin_payment_settings")],
        [InlineKeyboardButton("🔒 تنظیمات امنیتی", callback_data="admin_security_settings")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main_menu")]
    ]

async def get_admin_dashboard_text():
    """Generate admin dashboard text with stats"""
    stats = await get_admin_stats()
    
    return (
        "👨‍💻 *پنل مدیریت*\n\n"
        "📊 *آمار لحظه‌ای:*\n"
        f"👥 کاربران کل: {stats['total_users']:,}\n"
        f"🔄 سرویس‌های فعال: {stats['active_services']:,}\n"
        f"💰 درآمد امروز: {stats['today_income']:,} تومان\n"
        f"⏳ سفارشات در انتظار: {stats['pending_orders']:,}\n"
        f"📩 تیکت‌های باز: {stats['open_tickets']:,}"
    )

async def get_user_management_keyboard(page=0, limit=10):
    """Generate user management keyboard with pagination"""
    offset = page * limit
    users = query_db(
        """
        SELECT user_id, first_name 
        FROM users 
        ORDER BY user_id DESC 
        LIMIT ? OFFSET ?
        """, 
        (limit, offset)
    )
    
    keyboard = []
    for user in users:
        name = user['first_name'] or "بدون نام"
        btn_text = f"👤 {name} (ID: {user['user_id']})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"admin_view_user_{user['user_id']}")])
    
    # Add pagination
    total_users = query_db("SELECT COUNT(*) as count FROM users", one=True)['count']
    total_pages = (total_users + limit - 1) // limit
    
    pagination = []
    if page > 0:
        pagination.append(InlineKeyboardButton("⏪ قبلی", callback_data=f"admin_users_page_{page-1}"))
    if (page + 1) < total_pages:
        pagination.append(InlineKeyboardButton("بعدی ⏩", callback_data=f"admin_users_page_{page+1}"))
    
    if pagination:
        keyboard.append(pagination)
    
    keyboard.append([
        InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_search_user"),
        InlineKeyboardButton("➕ کاربر جدید", callback_data="admin_add_user")
    ])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main_menu")])
    
    return keyboard, f"صفحه {page + 1} از {max(1, total_pages)} - تعداد کل کاربران: {total_users:,}"

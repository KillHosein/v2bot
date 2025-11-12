"""
داشبورد کاربر - نمایش اطلاعات و آمار
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

from ..db import query_db
from ..loyalty_system import LoyaltySystem
from telegram.ext import ConversationHandler
from ..helpers.back_buttons import BackButtons


async def show_user_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش داشبورد کاربر"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    
    # اطلاعات کاربر
    user_info = query_db(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,),
        one=True
    )
    
    # سرویس‌های فعال
    active_services = query_db("""
        SELECT o.*, p.name as plan_name, p.traffic_gb
        FROM orders o
        JOIN plans p ON o.plan_id = p.id
        WHERE o.user_id = ? AND o.status = 'active'
        ORDER BY o.expire_date ASC
    """, (user_id,)) or []
    
    # کیف پول
    wallet_balance = user_info.get('balance', 0)
    
    # امتیازات
    points_data = LoyaltySystem.get_user_points(user_id)
    level_info = LoyaltySystem.get_level_info(points_data['total_points'])
    
    # آمار خرید
    purchase_stats = query_db("""
        SELECT 
            COUNT(*) as total_purchases,
            SUM(price) as total_spent,
            MAX(created_at) as last_purchase
        FROM orders
        WHERE user_id = ?
    """, (user_id,), one=True)
    
    # ساخت متن داشبورد
    text = f"""
📊 <b>داشبورد من</b>

━━━━━━━━━━━━━━━━━━━━━━━━

👤 <b>نام:</b> {user_info.get('first_name', 'کاربر')}
🆔 <b>شناسه:</b> <code>{user_id}</code>
📅 <b>عضویت:</b> {user_info.get('join_date', '')[:10]}

━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>کیف پول:</b> {wallet_balance:,} تومان
{level_info['emoji']} <b>سطح:</b> {level_info['name']}
⭐ <b>امتیاز:</b> {points_data['current_points']:,}
🎁 <b>تخفیف:</b> {level_info['discount']}%

━━━━━━━━━━━━━━━━━━━━━━━━

📦 <b>سرویس‌های فعال:</b> {len(active_services)}
"""
    
    if active_services:
        for service in active_services[:3]:  # نمایش 3 تای اول
            expire_date = service.get('expire_date', '')
            days_left = (datetime.strptime(expire_date, '%Y-%m-%d') - datetime.now()).days if expire_date else 0
            
            traffic_percent = 0
            if service.get('remaining_traffic_gb') and service.get('traffic_gb'):
                traffic_percent = (service['remaining_traffic_gb'] / service['traffic_gb']) * 100
            
            status_emoji = "🟢" if days_left > 7 else ("🟡" if days_left > 3 else "🔴")
            
            text += f"\n{status_emoji} <b>{service['plan_name']}</b>\n"
            text += f"   ⏰ {days_left} روز مانده\n"
            if traffic_percent > 0:
                text += f"   📊 {traffic_percent:.0f}% حجم باقیمانده\n"
    else:
        text += "\n❌ سرویس فعالی ندارید\n"
    
    text += "\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # آمار خرید
    if purchase_stats and purchase_stats['total_purchases']:
        text += f"🛍️ <b>آمار خرید:</b>\n"
        text += f"   • تعداد: {purchase_stats['total_purchases']} خرید\n"
        text += f"   • مبلغ کل: {purchase_stats['total_spent']:,} تومان\n"
        if purchase_stats['last_purchase']:
            last_purchase = purchase_stats['last_purchase'][:10]
            text += f"   • آخرین خرید: {last_purchase}\n"
    else:
        text += "🛍️ <b>هنوز خریدی نداشتید</b>\n"
    
    keyboard = [
        [
            InlineKeyboardButton("📦 سرویس‌ها", callback_data="user_services"),
            InlineKeyboardButton("💰 کیف پول", callback_data="wallet_menu")
        ],
        [
            InlineKeyboardButton("⭐ امتیازات", callback_data="loyalty_menu"),
            InlineKeyboardButton("📊 آمار مصرف", callback_data="usage_stats")
        ],
        [
            InlineKeyboardButton("📜 تاریخچه", callback_data="purchase_history"),
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="user_settings")
        ],
        [BackButtons.to_main()]
    ]
    
    if query:
        try:
            await query.message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception:
            await query.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    return ConversationHandler.END


async def show_usage_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار مصرف کاربر"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # مصرف 30 روز اخیر
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    daily_usage = query_db("""
        SELECT 
            DATE(created_at) as date,
            SUM(price) as daily_spent
        FROM orders
        WHERE user_id = ? AND DATE(created_at) >= ?
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at) DESC
        LIMIT 30
    """, (user_id, thirty_days_ago)) or []
    
    text = """
📊 <b>آمار مصرف 30 روز اخیر</b>

━━━━━━━━━━━━━━━━━━━━━━━━

"""
    
    if daily_usage:
        total_month = sum(day['daily_spent'] for day in daily_usage)
        avg_daily = total_month / len(daily_usage)
        
        text += f"💰 <b>مجموع:</b> {total_month:,} تومان\n"
        text += f"📈 <b>میانگین روزانه:</b> {avg_daily:,.0f} تومان\n\n"
        
        text += "📅 <b>روزهای اخیر:</b>\n\n"
        for day in daily_usage[:10]:
            date = day['date']
            amount = day['daily_spent']
            text += f"• {date}: {amount:,} تومان\n"
    else:
        text += "❌ در 30 روز اخیر خریدی نداشته‌اید.\n"
    
    keyboard = [[BackButtons.custom("🔙 بازگشت", "dashboard")]]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END


async def show_user_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش سرویس‌های کاربر"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    services = query_db("""
        SELECT o.*, p.name as plan_name
        FROM orders o
        JOIN plans p ON o.plan_id = p.id
        WHERE o.user_id = ?
        ORDER BY o.status = 'active' DESC, o.created_at DESC
    """, (user_id,)) or []
    
    text = "📦 <b>سرویس‌های من</b>\n\n"
    
    if not services:
        text += "❌ هنوز سرویسی ندارید.\n\n"
        text += "💡 برای خرید سرویس، از منوی اصلی استفاده کنید."
    else:
        active = [s for s in services if s['status'] == 'active']
        inactive = [s for s in services if s['status'] != 'active']
        
        if active:
            text += "🟢 <b>فعال:</b>\n\n"
            for service in active:
                text += f"• <b>{service['plan_name']}</b>\n"
                text += f"  ⏰ تا: {service.get('expire_date', 'نامشخص')}\n"
                if service.get('remaining_traffic_gb'):
                    text += f"  📊 {service['remaining_traffic_gb']:.1f} GB باقیمانده\n"
                text += "\n"
        
        if inactive:
            text += "\n⚫ <b>منقضی شده:</b>\n\n"
            for service in inactive[:5]:
                text += f"• {service['plan_name']}\n"
                text += f"  📅 {service.get('expire_date', 'نامشخص')}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ خرید سرویس جدید", callback_data="start_purchase")],
        [BackButtons.custom("🔙 بازگشت", "dashboard")]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END

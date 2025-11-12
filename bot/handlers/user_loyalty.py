"""
Handler های سیستم امتیاز برای کاربران
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from ..loyalty_system import LoyaltySystem, POINT_REWARDS
from ..helpers.back_buttons import BackButtons


async def show_loyalty_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی باشگاه مشتریان"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    
    # بررسی ورود روزانه
    daily_points = LoyaltySystem.check_daily_login(user_id)
    if daily_points > 0:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 <b>ورود روزانه ثبت شد!</b>\n\n+{daily_points} امتیاز دریافت کردید! 🎁",
            parse_mode=ParseMode.HTML
        )
    
    # بررسی تولد
    birthday_points = LoyaltySystem.check_birthday(user_id)
    if birthday_points > 0:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎂 <b>تولدت مبارک!</b> 🎉\n\n"
                 f"به مناسبت روز تولد، {birthday_points} امتیاز هدیه گرفتی! 🎁",
            parse_mode=ParseMode.HTML
        )
    
    # دریافت آمار کاربر
    stats_text = LoyaltySystem.get_user_stats_text(user_id)
    
    keyboard = [
        [InlineKeyboardButton("📜 تاریخچه امتیازات", callback_data="loyalty_history")],
        [InlineKeyboardButton("💰 تبدیل امتیاز به تخفیف", callback_data="loyalty_redeem")],
        [InlineKeyboardButton("🎁 هدایای ویژه", callback_data="loyalty_rewards")],
        [BackButtons.to_main()]
    ]
    
    if query:
        try:
            await query.message.edit_text(
                stats_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception:
            await query.message.reply_text(
                stats_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        await update.message.reply_text(
            stats_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    return ConversationHandler.END


async def show_loyalty_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تاریخچه امتیازات"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    history = LoyaltySystem.get_points_history(user_id, limit=15)
    
    if not history:
        text = "📜 <b>تاریخچه امتیازات</b>\n\n❌ هنوز فعالیتی ثبت نشده است."
    else:
        text = "📜 <b>تاریخچه امتیازات</b>\n\n"
        
        for item in history:
            points = item['points']
            action = item['action']
            desc = item['description'] or action
            date = item['created_at'][:10]  # فقط تاریخ
            
            emoji = "➕" if points > 0 else "➖"
            text += f"{emoji} <b>{points:+,}</b> امتیاز - {desc}\n"
            text += f"   📅 {date}\n\n"
    
    keyboard = [[BackButtons.custom("🔙 بازگشت", "loyalty_menu")]]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END


async def show_loyalty_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش صفحه تبدیل امتیاز"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_points = LoyaltySystem.get_user_points(user_id)
    current_points = user_points['current_points']
    
    text = f"""
💰 <b>تبدیل امتیاز به تخفیف</b>

━━━━━━━━━━━━━━━━━━━━━━━━

💎 <b>امتیاز قابل استفاده شما:</b> {current_points:,} امتیاز

💡 <b>نرخ تبدیل:</b>
   • 100 امتیاز = 10,000 تومان تخفیف
   • 500 امتیاز = 50,000 تومان تخفیف
   • 1000 امتیاز = 100,000 تومان تخفیف

━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>نحوه استفاده:</b>
امتیازات شما در هنگام خرید به صورت خودکار محاسبه می‌شوند.

همچنین می‌توانید هنگام خرید، تعداد امتیاز مورد استفاده را مشخص کنید.
"""
    
    keyboard = [
        [InlineKeyboardButton("🛍️ خرید با امتیاز", callback_data="start_purchase_with_points")],
        [BackButtons.custom("🔙 بازگشت", "loyalty_menu")]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END


async def show_loyalty_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش هدایای ویژه"""
    query = update.callback_query
    await query.answer()
    
    text = f"""
🎁 <b>هدایای ویژه باشگاه مشتریان</b>

━━━━━━━━━━━━━━━━━━━━━━━━

⭐ <b>راه‌های کسب امتیاز:</b>

✅ <b>ثبت نام:</b> {POINT_REWARDS['signup']} امتیاز (یکبار)
🛍️ <b>اولین خرید:</b> {POINT_REWARDS['first_purchase']} امتیاز
💰 <b>خرید:</b> {POINT_REWARDS['purchase']} امتیاز به ازای هر 10,000 تومان
👥 <b>معرفی دوستان:</b> {POINT_REWARDS['referral']} امتیاز برای هر نفر
⭐ <b>نظر دادن:</b> {POINT_REWARDS['review']} امتیاز
📅 <b>ورود روزانه:</b> {POINT_REWARDS['daily_login']} امتیاز
🎂 <b>تولد:</b> {POINT_REWARDS['birthday']} امتیاز (سالانه)

━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>مزایای سطوح بالاتر:</b>

🥉 <b>برنز:</b> 0% تخفیف
🥈 <b>نقره:</b> 5% تخفیف (100+ امتیاز)
🥇 <b>طلا:</b> 10% تخفیف (500+ امتیاز)
💎 <b>پلاتینیوم:</b> 15% تخفیف (1000+ امتیاز)
💠 <b>الماس:</b> 20% تخفیف (2500+ امتیاز)

━━━━━━━━━━━━━━━━━━━━━━━━

💡 هر چه بیشتر خرید کنید و دوستان خود را دعوت کنید،
   سطح بالاتری می‌گیرید و تخفیف بیشتری دریافت می‌کنید!
"""
    
    keyboard = [
        [InlineKeyboardButton("👥 دعوت دوستان", callback_data="show_referral")],
        [BackButtons.custom("🔙 بازگشت", "loyalty_menu")]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END

"""
Handler های ادمین برای مدیریت کیف پول
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..wallet_system import WalletSystem
from ..db import query_db, execute_db
from ..states import ADMIN_MAIN_MENU
from ..helpers.back_buttons import BackButtons
from ..config import logger


async def admin_wallet_tx_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی مدیریت تراکنش‌های کیف پول"""
    query = update.callback_query
    if query:
        await query.answer()
    
    # دریافت تراکنش‌های در انتظار
    pending_txs = WalletSystem.get_pending_transactions()
    
    text = f"""
💸 <b>مدیریت درخواست‌های کیف پول</b>

━━━━━━━━━━━━━━━━━━━━━━━━

⏳ <b>در انتظار تایید:</b> {len(pending_txs)} مورد

━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    if pending_txs:
        text += "\n📋 <b>درخواست‌های اخیر:</b>\n\n"
        
        for tx in pending_txs[:5]:  # نمایش 5 تای اول
            user_name = tx.get('first_name', 'کاربر')
            if tx.get('username'):
                user_name += f" (@{tx['username']})"
            
            text += f"• #{tx['id']} - {user_name}\n"
            text += f"  💰 {tx['amount']:,} تومان\n"
            text += f"  📅 {tx['created_at'][:16]}\n\n"
    else:
        text += "\n✅ همه درخواست‌ها بررسی شده‌اند.\n"
    
    keyboard = [
        [InlineKeyboardButton(f"⏳ درخواست‌های در انتظار ({len(pending_txs)})", callback_data='admin_wallet_tx_pending')],
        [InlineKeyboardButton("✅ تایید شده‌ها", callback_data='admin_wallet_tx_approved')],
        [InlineKeyboardButton("❌ رد شده‌ها", callback_data='admin_wallet_tx_rejected')],
        [InlineKeyboardButton("📊 آمار کلی", callback_data='admin_wallet_stats')],
        [BackButtons.to_admin_main()]
    ]
    
    if query:
        await query.message.edit_text(
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
    
    return ADMIN_MAIN_MENU


async def admin_wallet_tx_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش درخواست‌های در انتظار"""
    query = update.callback_query
    await query.answer()
    
    pending_txs = WalletSystem.get_pending_transactions()
    
    if not pending_txs:
        await query.answer("✅ درخواست جدیدی وجود ندارد", show_alert=True)
        return ADMIN_MAIN_MENU
    
    text = f"⏳ <b>درخواست‌های در انتظار ({len(pending_txs)})</b>\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # نمایش کیبورد برای هر درخواست
    keyboard = []
    
    for tx in pending_txs[:10]:  # حداکثر 10 تا
        user_name = tx.get('first_name', 'کاربر')
        text += f"<b>#{tx['id']}</b> - {user_name}\n"
        text += f"💰 {tx['amount']:,} تومان\n"
        text += f"📅 {tx['created_at'][:16]}\n\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"✅ تایید #{tx['id']}",
                callback_data=f"wallet_tx_approve_{tx['id']}"
            ),
            InlineKeyboardButton(
                f"❌ رد #{tx['id']}",
                callback_data=f"wallet_tx_reject_{tx['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔄 بروزرسانی", callback_data='admin_wallet_tx_pending')])
    keyboard.append([BackButtons.custom("🔙 بازگشت", "admin_wallet_tx_menu")])
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ADMIN_MAIN_MENU


async def admin_wallet_tx_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید تراکنش توسط ادمین"""
    query = update.callback_query
    admin_id = query.from_user.id
    
    tx_id = int(query.data.split('_')[-1])
    
    # تایید تراکنش
    success, message = WalletSystem.approve_transaction(tx_id, admin_id)
    
    if not success:
        await query.answer(f"❌ {message}", show_alert=True)
        return ADMIN_MAIN_MENU
    
    # دریافت اطلاعات تراکنش برای اطلاع به کاربر
    tx = query_db(
        "SELECT * FROM wallet_transactions WHERE id = ?",
        (tx_id,),
        one=True
    )
    
    if tx:
        # اطلاع به کاربر
        try:
            await context.bot.send_message(
                chat_id=tx['user_id'],
                text=f"""
✅ <b>شارژ کیف پول تایید شد!</b>

━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>مبلغ:</b> {tx['amount']:,} تومان
🆔 <b>شماره تراکنش:</b> #{tx_id}
📅 <b>تاریخ:</b> {tx['created_at'][:16]}

━━━━━━━━━━━━━━━━━━━━━━━━

💎 موجودی جدید شما: {WalletSystem.get_balance(tx['user_id']):,} تومان

از خرید شما متشکریم! 🙏
""",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error sending approval notification: {e}")
    
    await query.answer("✅ تراکنش تایید شد", show_alert=True)
    
    # بروزرسانی پیام
    await admin_wallet_tx_pending(update, context)
    
    return ADMIN_MAIN_MENU


async def admin_wallet_tx_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد تراکنش توسط ادمین"""
    query = update.callback_query
    admin_id = query.from_user.id
    
    tx_id = int(query.data.split('_')[-1])
    
    # رد تراکنش
    success, message = WalletSystem.reject_transaction(tx_id, admin_id)
    
    if not success:
        await query.answer(f"❌ {message}", show_alert=True)
        return ADMIN_MAIN_MENU
    
    # دریافت اطلاعات تراکنش
    tx = query_db(
        "SELECT * FROM wallet_transactions WHERE id = ?",
        (tx_id,),
        one=True
    )
    
    if tx:
        # اطلاع به کاربر
        try:
            await context.bot.send_message(
                chat_id=tx['user_id'],
                text=f"""
❌ <b>درخواست شارژ کیف پول رد شد</b>

━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>مبلغ:</b> {tx['amount']:,} تومان
🆔 <b>شماره تراکنش:</b> #{tx_id}

━━━━━━━━━━━━━━━━━━━━━━━━

دلیل: رسید نامعتبر یا اطلاعات ناقص

💬 لطفاً با پشتیبانی تماس بگیرید.
""",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error sending rejection notification: {e}")
    
    await query.answer("❌ تراکنش رد شد", show_alert=True)
    
    # بروزرسانی پیام
    await admin_wallet_tx_pending(update, context)
    
    return ADMIN_MAIN_MENU


async def admin_wallet_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آمار کلی کیف پول"""
    query = update.callback_query
    await query.answer()
    
    # آمار کلی
    total_stats = query_db("""
        SELECT 
            COUNT(DISTINCT user_id) as total_users,
            SUM(CASE WHEN status = 'approved' AND direction = 'credit' THEN amount ELSE 0 END) as total_deposits,
            SUM(CASE WHEN status = 'approved' AND direction = 'debit' THEN amount ELSE 0 END) as total_withdrawals,
            SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_amount
        FROM wallet_transactions
    """, one=True)
    
    # موجودی کل
    total_balance = query_db("""
        SELECT SUM(balance) as total FROM user_wallets
    """, one=True)
    
    # تراکنش‌های امروز
    today_stats = query_db("""
        SELECT 
            COUNT(*) as count,
            SUM(amount) as amount
        FROM wallet_transactions
        WHERE DATE(created_at) = DATE('now')
        AND status = 'approved'
        AND direction = 'credit'
    """, one=True)
    
    text = f"""
📊 <b>آمار کیف پول</b>

━━━━━━━━━━━━━━━━━━━━━━━━

💎 <b>موجودی کل سیستم:</b>
   {total_balance['total'] if total_balance else 0:,} تومان

👥 <b>کاربران فعال:</b>
   {total_stats['total_users'] if total_stats else 0} نفر

━━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>آمار کل:</b>

   📥 شارژ: {total_stats['total_deposits'] if total_stats else 0:,} تومان
   📤 برداشت: {total_stats['total_withdrawals'] if total_stats else 0:,} تومان
   ⏳ در انتظار: {total_stats['pending_amount'] if total_stats else 0:,} تومان

━━━━━━━━━━━━━━━━━━━━━━━━

📅 <b>امروز:</b>

   📥 {today_stats['count'] if today_stats else 0} تراکنش
   💰 {today_stats['amount'] if today_stats else 0:,} تومان
"""
    
    keyboard = [[BackButtons.custom("🔙 بازگشت", "admin_wallet_tx_menu")]]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ADMIN_MAIN_MENU

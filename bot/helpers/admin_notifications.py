# -*- coding: utf-8 -*-
"""Admin notification helpers for purchase logs and other events"""

from telegram import Bot
from telegram.constants import ParseMode
from ..config import ADMIN_ID, logger
from ..db import query_db


async def send_purchase_log(bot: Bot, order_id: int, user_id: int, plan_name: str, final_price: int, payment_method: str = "نامشخص"):
    """
    Send purchase notification to admin
    
    Args:
        bot: Telegram bot instance
        order_id: Order ID
        user_id: User ID who made the purchase
        plan_name: Plan name
        final_price: Final price paid
        payment_method: Payment method used
    """
    try:
        # Get user info
        user_info = query_db("SELECT first_name, username FROM users WHERE user_id = ?", (user_id,), one=True)
        first_name = user_info.get('first_name', 'نامشخص') if user_info else 'نامشخص'
        username = user_info.get('username', '') if user_info else ''
        user_display = f"@{username}" if username else first_name
        
        # Get purchase logs chat
        settings = query_db("SELECT value FROM settings WHERE key IN ('purchase_logs_enabled', 'purchase_logs_chat_id')")
        settings_dict = {s['key']: s['value'] for s in settings} if settings else {}
        
        enabled = settings_dict.get('purchase_logs_enabled', '1') == '1'
        if not enabled:
            return
        
        # Determine target chat
        chat_id_raw = settings_dict.get('purchase_logs_chat_id', '').strip()
        if chat_id_raw:
            target_chat = chat_id_raw if chat_id_raw.startswith('@') else (int(chat_id_raw) if chat_id_raw.lstrip('-').isdigit() else ADMIN_ID)
        else:
            target_chat = ADMIN_ID
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        text = (
            f"🎉 <b>خرید جدید ثبت شد!</b>\n\n"
            f"👤 <b>کاربر:</b> {user_display}\n"
            f"🆔 <b>یوزر آیدی:</b> <code>{user_id}</code>\n"
            f"📦 <b>پلن:</b> {plan_name}\n"
            f"💰 <b>مبلغ:</b> {final_price:,} تومان\n"
            f"💳 <b>روش پرداخت:</b> {payment_method}\n"
            f"🔢 <b>شماره سفارش:</b> #{order_id}\n"
            f"🕐 <b>زمان:</b> <code>{timestamp}</code>"
        )
        
        await bot.send_message(chat_id=target_chat, text=text, parse_mode=ParseMode.HTML)
        logger.info(f"Purchase log sent for order {order_id} to chat {target_chat}")
        
    except Exception as e:
        logger.error(f"Failed to send purchase log for order {order_id}: {e}", exc_info=True)
        # Fallback to admin DM
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🎉 خرید جدید: کاربر {user_id} | پلن: {plan_name} | مبلغ: {final_price:,} تومان | سفارش: #{order_id}",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass


async def send_renewal_log(bot: Bot, order_id: int, user_id: int, plan_name: str, final_price: int, payment_method: str = "نامشخص"):
    """
    Send renewal notification to admin
    
    Args:
        bot: Telegram bot instance
        order_id: Order ID
        user_id: User ID who renewed
        plan_name: Plan name
        final_price: Final price paid
        payment_method: Payment method used
    """
    try:
        # Get user info
        user_info = query_db("SELECT first_name, username FROM users WHERE user_id = ?", (user_id,), one=True)
        first_name = user_info.get('first_name', 'نامشخص') if user_info else 'نامشخص'
        username = user_info.get('username', '') if user_info else ''
        user_display = f"@{username}" if username else first_name
        
        # Get purchase logs chat
        settings = query_db("SELECT value FROM settings WHERE key IN ('purchase_logs_enabled', 'purchase_logs_chat_id')")
        settings_dict = {s['key']: s['value'] for s in settings} if settings else {}
        
        enabled = settings_dict.get('purchase_logs_enabled', '1') == '1'
        if not enabled:
            return
        
        # Determine target chat
        chat_id_raw = settings_dict.get('purchase_logs_chat_id', '').strip()
        if chat_id_raw:
            target_chat = chat_id_raw if chat_id_raw.startswith('@') else (int(chat_id_raw) if chat_id_raw.lstrip('-').isdigit() else ADMIN_ID)
        else:
            target_chat = ADMIN_ID
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        text = (
            f"🔄 <b>تمدید سرویس انجام شد!</b>\n\n"
            f"👤 <b>کاربر:</b> {user_display}\n"
            f"🆔 <b>یوزر آیدی:</b> <code>{user_id}</code>\n"
            f"📦 <b>پلن:</b> {plan_name}\n"
            f"💰 <b>مبلغ:</b> {final_price:,} تومان\n"
            f"💳 <b>روش پرداخت:</b> {payment_method}\n"
            f"🔢 <b>شماره سفارش:</b> #{order_id}\n"
            f"🕐 <b>زمان:</b> <code>{timestamp}</code>"
        )
        
        await bot.send_message(chat_id=target_chat, text=text, parse_mode=ParseMode.HTML)
        logger.info(f"Renewal log sent for order {order_id} to chat {target_chat}")
        
    except Exception as e:
        logger.error(f"Failed to send renewal log for order {order_id}: {e}", exc_info=True)
        # Fallback to admin DM
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔄 تمدید: کاربر {user_id} | پلن: {plan_name} | مبلغ: {final_price:,} تومان | سفارش: #{order_id}",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

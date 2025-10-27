"""User notification jobs for traffic and expiry warnings"""

from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from ..db import query_db, execute_db
from ..config import logger
from ..panel import VpnPanelAPI


async def check_low_traffic_and_expiry(context):
    """
    Check for services with low traffic or near expiry
    Send notifications to users
    """
    try:
        await check_low_traffic(context)
        await check_near_expiry(context)
    except Exception as e:
        logger.error(f"Error in check_low_traffic_and_expiry: {e}")


async def check_low_traffic(context):
    """
    Check services with low traffic and notify users
    Notification at 80% and 95% usage
    """
    try:
        # Get active orders
        orders = query_db("""
            SELECT o.id, o.user_id, o.marzban_username, o.panel_id,
                   p.name as plan_name, p.traffic_gb,
                   o.notified_traffic_80, o.notified_traffic_95
            FROM orders o
            LEFT JOIN plans p ON o.plan_id = p.id
            WHERE o.status = 'approved'
            AND o.marzban_username IS NOT NULL
            AND o.panel_id IS NOT NULL
        """) or []
        
        for order in orders:
            try:
                # Get panel info
                panel = query_db("SELECT * FROM panels WHERE id = ?", (order['panel_id'],), one=True)
                if not panel:
                    continue
                
                # Get service stats from panel - pass panel_id not the whole dict
                api = VpnPanelAPI(panel_id=order['panel_id'])
                result = await api.get_user(order['marzban_username'])
                
                # Handle both tuple (user_data, message) and dict returns
                if isinstance(result, tuple):
                    user_data, _ = result
                else:
                    user_data = result
                
                if not user_data or not isinstance(user_data, dict):
                    continue
                
                # Calculate usage percentage
                used = user_data.get('used_traffic', 0) / (1024**3)  # Convert to GB
                total = float(order['traffic_gb'] or 0)
                
                if total == 0:  # Unlimited traffic
                    continue
                
                usage_percent = (used / total) * 100
                
                # Check 80% threshold
                if usage_percent >= 80 and not order.get('notified_traffic_80'):
                    await send_traffic_warning(
                        context.bot,
                        order['user_id'],
                        order['id'],
                        order['plan_name'],
                        usage_percent,
                        used,
                        total,
                        level='warning'
                    )
                    execute_db("UPDATE orders SET notified_traffic_80 = 1 WHERE id = ?", (order['id'],))
                
                # Check 95% threshold
                elif usage_percent >= 95 and not order.get('notified_traffic_95'):
                    await send_traffic_warning(
                        context.bot,
                        order['user_id'],
                        order['id'],
                        order['plan_name'],
                        usage_percent,
                        used,
                        total,
                        level='critical'
                    )
                    execute_db("UPDATE orders SET notified_traffic_95 = 1 WHERE id = ?", (order['id'],))
                
            except Exception as e:
                logger.error(f"Error checking traffic for order {order['id']}: {e}")
                continue
        
        logger.info(f"Traffic check completed for {len(orders)} orders")
        
    except Exception as e:
        logger.error(f"Error in check_low_traffic: {e}")


async def check_near_expiry(context):
    """
    Check services near expiry and notify users
    Notification at 3 days and 1 day before expiry
    """
    try:
        now = datetime.now()
        three_days = now + timedelta(days=3)
        one_day = now + timedelta(days=1)
        
        # Get orders expiring in 3 days
        orders_3d = query_db("""
            SELECT o.id, o.user_id, o.marzban_username,
                   p.name as plan_name, o.timestamp, p.duration_days,
                   o.notified_expiry_3d, o.notified_expiry_1d
            FROM orders o
            LEFT JOIN plans p ON o.plan_id = p.id
            WHERE o.status = 'approved'
            AND datetime(o.timestamp, '+' || p.duration_days || ' days') <= ?
            AND datetime(o.timestamp, '+' || p.duration_days || ' days') > ?
            AND o.notified_expiry_3d != 1
        """, (three_days.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S'))) or []
        
        for order in orders_3d:
            try:
                expiry = datetime.strptime(order['timestamp'], '%Y-%m-%d %H:%M:%S') + timedelta(days=order['duration_days'])
                days_left = (expiry - now).days
                
                await send_expiry_warning(
                    context.bot,
                    order['user_id'],
                    order['id'],
                    order['plan_name'],
                    days_left,
                    expiry,
                    level='warning'
                )
                execute_db("UPDATE orders SET notified_expiry_3d = 1 WHERE id = ?", (order['id'],))
                
            except Exception as e:
                logger.error(f"Error sending 3-day expiry for order {order['id']}: {e}")
        
        # Get orders expiring in 1 day
        orders_1d = query_db("""
            SELECT o.id, o.user_id, o.marzban_username,
                   p.name as plan_name, o.timestamp, p.duration_days,
                   o.notified_expiry_1d
            FROM orders o
            LEFT JOIN plans p ON o.plan_id = p.id
            WHERE o.status = 'approved'
            AND datetime(o.timestamp, '+' || p.duration_days || ' days') <= ?
            AND datetime(o.timestamp, '+' || p.duration_days || ' days') > ?
            AND o.notified_expiry_1d != 1
        """, (one_day.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S'))) or []
        
        for order in orders_1d:
            try:
                expiry = datetime.strptime(order['timestamp'], '%Y-%m-%d %H:%M:%S') + timedelta(days=order['duration_days'])
                hours_left = int((expiry - now).total_seconds() / 3600)
                
                await send_expiry_warning(
                    context.bot,
                    order['user_id'],
                    order['id'],
                    order['plan_name'],
                    0,
                    expiry,
                    level='critical',
                    hours=hours_left
                )
                execute_db("UPDATE orders SET notified_expiry_1d = 1 WHERE id = ?", (order['id'],))
                
            except Exception as e:
                logger.error(f"Error sending 1-day expiry for order {order['id']}: {e}")
        
        logger.info(f"Expiry check completed: {len(orders_3d)} 3-day, {len(orders_1d)} 1-day")
        
    except Exception as e:
        logger.error(f"Error in check_near_expiry: {e}")


async def send_traffic_warning(bot, user_id, order_id, plan_name, usage_percent, used_gb, total_gb, level='warning'):
    """Send traffic warning notification"""
    
    if level == 'warning':
        icon = "⚠️"
        title = "هشدار حجم"
        message = f"حجم سرویس شما به <b>{usage_percent:.1f}%</b> رسیده است."
    else:  # critical
        icon = "🚨"
        title = "هشدار مهم - حجم تقریباً تمام شده"
        message = f"حجم سرویس شما به <b>{usage_percent:.1f}%</b> رسیده است و به زودی تمام خواهد شد!"
    
    text = (
        f"{icon} <b>{title}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{message}\n\n"
        f"📦 <b>پلن:</b> {plan_name}\n"
        f"📊 <b>حجم مصرفی:</b> {used_gb:.2f} GB / {total_gb:.0f} GB\n"
        f"📈 <b>درصد مصرف:</b> {usage_percent:.1f}%\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>برای جلوگیری از قطعی سرویس، همین حالا تمدید کنید!</i>"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 تمدید سرویس", callback_data=f"renew_service_{order_id}")],
        [InlineKeyboardButton("📱 سرویس‌های من", callback_data="my_services")]
    ]
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info(f"Traffic warning sent to user {user_id}, order {order_id}")
    except Exception as e:
        logger.error(f"Failed to send traffic warning to {user_id}: {e}")


async def send_expiry_warning(bot, user_id, order_id, plan_name, days_left, expiry_date, level='warning', hours=None):
    """Send expiry warning notification"""
    
    if level == 'warning':
        icon = "⏰"
        title = "یادآوری انقضای سرویس"
        time_text = f"{days_left} روز"
    else:  # critical
        icon = "🚨"
        title = "هشدار - سرویس به زودی منقضی می‌شود"
        time_text = f"{hours} ساعت" if hours else "کمتر از ۱ روز"
    
    expiry_str = expiry_date.strftime('%Y-%m-%d %H:%M')
    
    text = (
        f"{icon} <b>{title}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>پلن:</b> {plan_name}\n"
        f"⏳ <b>زمان باقیمانده:</b> <code>{time_text}</code>\n"
        f"📅 <b>تاریخ انقضا:</b> <code>{expiry_str}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>برای ادامه استفاده، سرویس خود را تمدید کنید!</i>"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 تمدید سرویس", callback_data=f"renew_service_{order_id}")],
        [InlineKeyboardButton("📱 سرویس‌های من", callback_data="my_services")]
    ]
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info(f"Expiry warning sent to user {user_id}, order {order_id}")
    except Exception as e:
        logger.error(f"Failed to send expiry warning to {user_id}: {e}")

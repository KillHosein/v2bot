# Replace the fragment (after '#') of a URI with a friendly name
def _with_name_fragment(uri: str, name: str) -> str:
    try:
        from urllib.parse import urlsplit, urlunsplit
        parts = urlsplit(uri)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, name))
    except Exception:
        # Fallback: replace last fragment occurrence
        if '#' in uri:
            return uri.split('#', 1)[0] + f"#{name}"
        return uri
from datetime import datetime
import requests, base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError, BadRequest
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters

from ..db import query_db, execute_db
from ..utils import register_new_user
from ..helpers.flow import set_flow, clear_flow
from ..helpers.keyboards import build_start_menu_keyboard
from ..panel import VpnPanelAPI
from ..utils import bytes_to_gb
from ..states import (
    WALLET_AWAIT_AMOUNT_CARD,
    WALLET_AWAIT_CUSTOM_AMOUNT_CARD,
    WALLET_AWAIT_AMOUNT_CRYPTO,
    WALLET_AWAIT_CUSTOM_AMOUNT_CRYPTO,
    WALLET_AWAIT_CUSTOM_AMOUNT_GATEWAY,
    WALLET_AWAIT_CARD_SCREENSHOT,
    WALLET_AWAIT_CRYPTO_SCREENSHOT,
)
from ..states import SUPPORT_AWAIT_TICKET
from ..config import ADMIN_ID, logger
from ..helpers.tg import ltr_code, notify_admins, safe_edit_text as _safe_edit_text, append_footer_buttons as _footer
from ..helpers.flow import set_flow, clear_flow
from .admin import auto_approve_wallet_order
import io
try:
    from ..helpers.tg import build_styled_qr as _build_qr
except Exception:
    _build_qr = None
import time

# Normalize Persian/Arabic digits to ASCII
_DIGIT_MAP = str.maketrans({
    '۰':'0','۱':'1','۲':'2','۳':'3','۴':'4','۵':'5','۶':'6','۷':'7','۸':'8','۹':'9',
    '٠':'0','١':'1','٢':'2','٣':'3','٤':'4','٥':'5','٦':'6','٧':'7','٨':'8','٩':'9'
})

def _normalize_amount_text(text: str) -> str:
    if not text:
        return ''
    t = text.translate(_DIGIT_MAP).strip()
    if t.startswith('/'):
        t = t[1:]
    return t


def _fetch_subscription_configs(sub_url: str, timeout_seconds: int = 15) -> list[str]:
    try:
        headers = {
            'Accept': 'text/plain, application/octet-stream, */*',
            'User-Agent': 'Mozilla/5.0',
        }
        r = requests.get(sub_url, headers=headers, timeout=timeout_seconds)
        r.raise_for_status()
        raw = (r.text or '').strip()
        if any(proto in raw for proto in ("vmess://","vless://","trojan://","ss://","hy2://")):
            text = raw
        else:
            compact = "".join(raw.split())
            pad = len(compact) % 4
            if pad:
                compact += "=" * (4 - pad)
            try:
                decoded = base64.b64decode(compact, validate=False)
                text = decoded.decode('utf-8', errors='ignore')
            except Exception:
                text = raw
        lines = [ln.strip() for ln in (text or '').splitlines()]
        return [ln for ln in lines if ln and (ln.startswith('vmess://') or ln.startswith('vless://') or ln.startswith('trojan://') or ln.startswith('ss://') or ln.startswith('hy2://'))]
    except Exception:
        return []


async def get_free_config_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query_db("SELECT 1 FROM free_trials WHERE user_id = ?", (user_id,), one=True):
        try:
            await query.message.edit_text(
                "شما قبلاً تست را دریافت کرده‌اید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت به منو", callback_data='start_main')]]),
            )
        except Exception:
            try:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="شما قبلاً تست را دریافت کرده‌اید.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت به منو", callback_data='start_main')]])
                )
            except Exception:
                pass
        return

    # Use admin-selected panel for free trials if set; fallback to first
    cfg = query_db("SELECT value FROM settings WHERE key = 'free_trial_panel_id'", one=True)
    sel_id = (cfg.get('value') if cfg else '') or ''
    first_panel = None
    if sel_id.isdigit():
        first_panel = query_db("SELECT id FROM panels WHERE id = ?", (int(sel_id),), one=True)
    if not first_panel:
        first_panel = query_db("SELECT id FROM panels ORDER BY id LIMIT 1", one=True)
    if not first_panel:
        await query.message.edit_text(
            "❌ متاسفانه هیچ پنلی برای ارائه سرویس تنظیم نشده است.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت به منو", callback_data='start_main')]]),
        )
        return

    try:
        await query.message.edit_text("لطفا کمی صبر کنید... \U0001F552")
    except Exception:
        pass

    settings = {s['key']: s['value'] for s in query_db("SELECT key, value FROM settings WHERE key LIKE 'free_trial_%'")}
    trial_plan = {'traffic_gb': settings.get('free_trial_gb', '0.2'), 'duration_days': settings.get('free_trial_days', '1')}

    panel_api = VpnPanelAPI(panel_id=first_panel['id'])

    # Quick precheck: ensure at least one inbound is visible to API (best-effort)
    try:
        pre_inb = getattr(panel_api, 'list_inbounds', lambda: (None, 'NA'))()
        if isinstance(pre_inb, tuple):
            pre_list, _ = pre_inb
        else:
            pre_list = pre_inb
        if pre_list is None:
            # continue; maybe API requires create to login first
            pass
    except Exception:
        pass

    try:
        # For XUI-like panels, if a trial inbound is set, create on that inbound directly
        prow = query_db("SELECT panel_type FROM panels WHERE id = ?", (first_panel['id'],), one=True) or {}
        ptype = (prow.get('panel_type') or '').lower()
        trial_inb_row = query_db("SELECT value FROM settings WHERE key='free_trial_inbound_id'", one=True)
        trial_inb = int(trial_inb_row.get('value')) if (trial_inb_row and str(trial_inb_row.get('value') or '').isdigit()) else None
        
        # Delete existing user from panel first to prevent duplicate email error
        import re as _re
        base_username = f"user_{user_id}"
        try:
            if ptype in ('xui','x-ui','3xui','3x-ui','alireza','txui','tx-ui','tx ui') and trial_inb is not None:
                # Try to delete from specific inbound
                if hasattr(panel_api, 'delete_user_on_inbound'):
                    try:
                        panel_api.delete_user_on_inbound(trial_inb, base_username)
                    except Exception:
                        pass
            # Fallback: try generic delete
            if hasattr(panel_api, 'delete_user'):
                try:
                    panel_api.delete_user(base_username)
                except Exception:
                    pass
        except Exception:
            pass  # Best effort; continue to create
        
        if ptype in ('xui','x-ui','3xui','3x-ui','alireza','txui','tx-ui','tx ui') and trial_inb is not None and hasattr(panel_api, 'create_user_on_inbound'):
            username_created, sub_link, _msg = None, None, None
            try:
                username_created, sub_link, _msg = panel_api.create_user_on_inbound(trial_inb, user_id, trial_plan)
            except Exception as e:
                username_created, sub_link, _msg = None, None, str(e)
            marzban_username, config_link, message = username_created, sub_link, _msg
        else:
            marzban_username, config_link, message = await panel_api.create_user(user_id, trial_plan)
    except Exception as e:
        await query.message.edit_text(
            f"❌ ایجاد کاربر تست ناموفق بود.\nجزئیات: {e}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت به منو", callback_data='start_main')]]),
        )
        return

    if config_link:
        plan_id_row = query_db("SELECT id FROM plans LIMIT 1", one=True)
        plan_id = plan_id_row['id'] if plan_id_row else -1

        # Persist order; for XUI-like with selected inbound, save xui_inbound_id too
        xui_inb = None
        try:
            prow = query_db("SELECT panel_type FROM panels WHERE id = ?", (first_panel['id'],), one=True) or {}
            ptype = (prow.get('panel_type') or '').lower()
            if ptype in ('xui','x-ui','3xui','3x-ui','alireza','txui','tx-ui','tx ui'):
                trial_inb_row = query_db("SELECT value FROM settings WHERE key='free_trial_inbound_id'", one=True)
                if trial_inb_row and str(trial_inb_row.get('value') or '').isdigit():
                    xui_inb = int(trial_inb_row.get('value'))
        except Exception:
            xui_inb = None
        if xui_inb is not None:
            execute_db(
                "INSERT INTO orders (user_id, plan_id, panel_id, status, marzban_username, timestamp, xui_inbound_id, panel_type, is_trial) VALUES (?, ?, ?, ?, ?, ?, ?, (SELECT panel_type FROM panels WHERE id=?), 1)",
                (user_id, plan_id, first_panel['id'], 'approved', marzban_username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), xui_inb, first_panel['id']),
            )
        else:
            execute_db(
                "INSERT INTO orders (user_id, plan_id, panel_id, status, marzban_username, timestamp, panel_type, is_trial) VALUES (?, ?, ?, ?, ?, ?, (SELECT panel_type FROM panels WHERE id=?), 1)",
                (user_id, plan_id, first_panel['id'], 'approved', marzban_username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), first_panel['id']),
            )
        execute_db("INSERT INTO free_trials (user_id, timestamp) VALUES (?, ?)", (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        # If panel is XUI-like, send direct configs instead of subscription link
        try:
            ptype_row = query_db("SELECT panel_type FROM panels WHERE id = ?", (first_panel['id'],), one=True) or {}
            ptype = (ptype_row.get('panel_type') or '').lower()
        except Exception:
            ptype = ''
        if ptype in ('xui','x-ui','3xui','3x-ui','alireza','txui','tx-ui','tx ui'):
            confs = []
            ib_id = None
            # Prefer selected trial inbound
            if xui_inb is not None:
                ib_id = xui_inb
            else:
                # Fallback: first inbound
                try:
                    inbs, _m = getattr(panel_api, 'list_inbounds', lambda: (None,'NA'))()
                    if inbs:
                        ib_id = inbs[0].get('id')
                except Exception:
                    ib_id = None
            if ib_id is not None and hasattr(panel_api, 'get_configs_for_user_on_inbound'):
                try:
                    confs = panel_api.get_configs_for_user_on_inbound(int(ib_id), marzban_username) or []
                except Exception:
                    confs = []
            if not confs and isinstance(config_link, str) and config_link.startswith('http'):
                # Decode subscription content as a fallback
                try:
                    confs = _fetch_subscription_configs(config_link)
                except Exception:
                    confs = []
            if confs:
                # Show configs with user's username as display name instead of inbound tag
                try:
                    disp_name = order.get('marzban_username') or ''
                    confs_named = [(_with_name_fragment(c, disp_name) if disp_name else c) for c in confs]
                except Exception:
                    confs_named = confs
                cfg_text = "\n".join(f"<code>{c}</code>" for c in confs_named)
                footer = ((query_db("SELECT value FROM settings WHERE key = 'config_footer_text'", one=True) or {}).get('value') or '')
                text = (
                    f"✅ کانفیگ تست رایگان شما با موفقیت ساخته شد!\n\n"
                    f"<b>حجم:</b> {trial_plan['traffic_gb']} گیگابایت\n"
                    f"<b>مدت اعتبار:</b> {trial_plan['duration_days']} روز\n\n"
                    f"<b>کانفیگ شما:</b>\n{cfg_text}\n\n" + footer
                )
                await query.message.edit_text(
                    text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت به منو", callback_data='start_main')]]),
                )
            else:
                # As a last resort, mention link but mark as fallback
                text = (
                    f"✅ کانفیگ تست رایگان شما با موفقیت ساخته شد!\n\n"
                    f"<b>حجم:</b> {trial_plan['traffic_gb']} گیگابایت\n"
                    f"<b>مدت اعتبار:</b> {trial_plan['duration_days']} روز\n\n"
                    f"<b>لینک اشتراک (فقط درصورت نیاز):</b>\n<code>{config_link}</code>\n\n"
                    f"<b>آموزش اتصال :</b>\nhttps://t.me/madeingod_tm"
                )
                await query.message.edit_text(
                    text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت به منو", callback_data='start_main')]]),
                )
        else:
            # Default: marzban-like, send subscription link
            text = (
                f"✅ کانفیگ تست رایگان شما با موفقیت ساخته شد!\n\n"
                f"<b>حجم:</b> {trial_plan['traffic_gb']} گیگابایت\n"
                f"<b>مدت اعتبار:</b> {trial_plan['duration_days']} روز\n\n"
                f"لینک کانفیگ شما:\n<code>{config_link}</code>\n\n"
                f"<b>آموزش اتصال :</b>\n"
                f"https://t.me/madeingod_tm"
            )
            await query.message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت به منو", callback_data='start_main')]]),
            )
    else:
        # If message is empty, give a generic hint
        reason = message or "اطلاعات کافی از پنل دریافت نشد."
        await query.message.edit_text(
            f"❌ متاسفانه در حال حاضر امکان ارائه کانفیگ تست وجود ندارد.\nخطا: {reason}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت به منو", callback_data='start_main')]]),
        )


async def my_services_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Get page number from callback data (default: page 1)
    page = 1
    if '_page_' in query.data:
        try:
            page = int(query.data.split('_page_')[1])
        except Exception:
            page = 1
    
    orders = query_db(
        "SELECT * FROM orders WHERE user_id = ? AND status NOT IN ('deleted', 'canceled') ORDER BY timestamp DESC",
        (user_id,)
    )
    
    if not orders:
        keyboard = [
            [InlineKeyboardButton("🛒 خرید سرویس جدید", callback_data='buy_config_main')],
            [InlineKeyboardButton("🎁 دریافت تست رایگان", callback_data='get_free_config')],
            [
                InlineKeyboardButton("💰 کیف پول", callback_data='wallet_menu'),
                InlineKeyboardButton("💬 پشتیبانی", callback_data='support_menu')
            ],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')]
        ]
        text = (
            "📱 <b>سرویس‌های من</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "❌ شما در حال حاضر هیچ سرویسی ندارید.\n\n"
            "💡 <b>برای شروع می‌توانید:</b>\n"
            "🛒 یک سرویس جدید خریداری کنید\n"
            "🎁 از کانفیگ تست رایگان استفاده کنید\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        await query.message.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Pagination: 10 services per page
    per_page = 10
    total_pages = (len(orders) + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_orders = orders[start_idx:end_idx]
    
    # Build inline keyboard for orders on current page
    keyboard = []
    active_count = sum(1 for o in orders if (o.get('status') or '').lower() in ('active', 'approved'))
    pending_count = sum(1 for o in orders if (o.get('status') or '').lower() in ('pending', 'awaiting', 'processing'))
    expired_count = len(orders) - active_count - pending_count
    
    # Pre-fetch user info grouped by panel to avoid multiple logins
    panel_users_cache = {}
    for order in page_orders:
        if (order.get('status') or '').lower() in ('active', 'approved') and order.get('panel_id') and order.get('marzban_username'):
            panel_id = order['panel_id']
            if panel_id not in panel_users_cache:
                panel_users_cache[panel_id] = {}
    
    # Fetch all users for each panel once
    import asyncio
    for panel_id in panel_users_cache.keys():
        try:
            panel_api = VpnPanelAPI(panel_id=panel_id)
            # Get all users from this panel with timeout
            users_list, _ = await asyncio.wait_for(
                panel_api.get_all_users(limit=1000),
                timeout=5.0
            )
            if users_list:
                # Index by username for quick lookup
                for user_info in users_list:
                    username = user_info.get('username')
                    if username:
                        panel_users_cache[panel_id][username] = user_info
        except Exception:
            pass  # Silently fail - panel might be down
    
    for order in page_orders:
        # Show custom service name if user set one, otherwise show plan name
        service_name = order.get('desired_username') or order.get('plan_name') or f"سرویس #{order['id']}"
        status = (order.get('status') or 'unknown').lower()
        
        # Determine status icon
        if status in ('active', 'approved'):
            status_icon = "✅"
        elif status in ('pending', 'awaiting', 'processing'):
            status_icon = "⏳"
        else:
            status_icon = "❌"
        
        # Check if volume is exhausted using cached user info
        volume_indicator = ""
        if status in ('active', 'approved') and order.get('panel_id') and order.get('marzban_username'):
            try:
                panel_id = order['panel_id']
                username = order['marzban_username']
                user_info = panel_users_cache.get(panel_id, {}).get(username)
                
                if user_info:
                    total_bytes = int(user_info.get('data_limit', 0) or 0)
                    used_bytes = int(user_info.get('used_traffic', 0) or 0)
                    # If volume is exhausted (used >= total and total > 0)
                    if total_bytes > 0 and used_bytes >= total_bytes:
                        volume_indicator = " ❌"
            except Exception:
                pass  # Silently fail - just don't show indicator
        
        label = f"{status_icon} {service_name}{volume_indicator}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"view_service_{order['id']}")])    
    
    # Pagination buttons
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("◀️ قبلی", callback_data=f'my_services_page_{page-1}'))
        nav_row.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data='noop'))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("بعدی ▶️", callback_data=f'my_services_page_{page+1}'))
        keyboard.append(nav_row)
    
    # Quick actions
    keyboard.append([
        InlineKeyboardButton("🛒 خرید جدید", callback_data='buy_config_main'),
        InlineKeyboardButton("💰 کیف پول", callback_data='wallet_menu')
    ])
    keyboard.append([
        InlineKeyboardButton("💬 پشتیبانی", callback_data='support_menu'),
        InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')
    ])
    
    text = (
        f"📱 <b>سرویس‌های من</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>خلاصه آمار شما:</b>\n\n"
        f"   ✅ فعال: <b>{active_count}</b> سرویس\n"
        f"   ⏳ در انتظار: <b>{pending_count}</b> سرویس\n"
        f"   ❌ منقضی: <b>{expired_count}</b> سرویس\n"
        f"   📦 مجموع: <b>{len(orders)}</b> سرویس\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>برای مشاهده جزئیات، روی هر سرویس کلیک کنید.</i>"
    )
    
    # Try to edit, if fails (e.g., message has no text), send new message
    try:
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    except BadRequest as e:
        if "no text in the message to edit" in str(e).lower():
            # Delete old message and send new one
            try:
                await query.message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            raise


async def show_specific_service_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    order_id = int(query.data.split('_')[-1])
    await query.answer()

    order = query_db("SELECT * FROM orders WHERE id = ?", (order_id,), one=True)
    if not order or order['user_id'] != query.from_user.id:
        await query.message.edit_text(
            "❌ <b>خطا</b>\n\nاین سرویس یافت نشد یا حذف شده است.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')]]),
            parse_mode=ParseMode.HTML
        )
        return

    if not order.get('panel_id'):
        await query.message.edit_text(
            "❌ <b>خطای پیکربندی</b>\n\n"
            "اطلاعات پنل برای این سرویس یافت نشد.\n\n"
            "📞 لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📱 سرویس‌های من", callback_data='my_services')]]),
            parse_mode=ParseMode.HTML
        )
        return

    try:
        await query.message.edit_text("⏳ <b>در حال دریافت اطلاعات...</b>\n\nلطفاً چند لحظه صبر کنید.", parse_mode=ParseMode.HTML)
    except TelegramError:
        pass

    marzban_username = order['marzban_username']
    panel_id = order['panel_id']
    
    logger.info(f"[view_service] Fetching info for user={marzban_username}, panel={panel_id}")
    
    try:
        panel_api = VpnPanelAPI(panel_id=panel_id)
        logger.info(f"[view_service] Panel API created: {type(panel_api).__name__}")
    except Exception as e:
        logger.error(f"[view_service] Error creating panel API: {e}", exc_info=True)
        await query.message.edit_text(
            f"❌ <b>خطای اتصال به پنل</b>\n\n{str(e)}\n\n📞 لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📱 سرویس‌های من", callback_data='my_services')]]),
            parse_mode=ParseMode.HTML
        )
        return
    
    # Add timeout to prevent hanging
    try:
        import asyncio
        logger.info(f"[view_service] Calling get_user for {marzban_username}")
        user_info, message = await asyncio.wait_for(
            panel_api.get_user(marzban_username),
            timeout=15.0
        )
        logger.info(f"[view_service] get_user returned: user_info={'OK' if user_info else 'None'}, message={message}")
    except asyncio.TimeoutError:
        logger.error(f"[view_service] Timeout getting user {marzban_username} from panel {panel_id}")
        await query.message.edit_text(
            "⏱ <b>تایم اوت!</b>\n\nدرخواست به پنل طول کشید.\n\n🔄 لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📱 سرویس‌های من", callback_data='my_services')]]),
            parse_mode=ParseMode.HTML
        )
        return
    except Exception as e:
        logger.error(f"[view_service] Exception getting user {marzban_username}: {type(e).__name__}: {e}", exc_info=True)
        await query.message.edit_text(
            f"❌ <b>خطای اتصال</b>\n\n<code>{type(e).__name__}</code>\n{str(e)[:100]}\n\n🔄 لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📱 سرویس‌های من", callback_data='my_services')]]),
            parse_mode=ParseMode.HTML
        )
        return

    if not user_info:
        await query.message.edit_text(
            f"❌ <b>خطا در دریافت اطلاعات</b>\n\n{message}\n\n🔄 لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📱 سرویس‌های من", callback_data='my_services')]]),
            parse_mode=ParseMode.HTML
        )
        return

    # Compute traffic usage and expiry display
    total_bytes = int(user_info.get('data_limit', 0) or 0)
    used_bytes = int(user_info.get('used_traffic', 0) or 0)
    # If total is zero (unlimited), still show used in GB
    data_limit_gb = "نامحدود" if total_bytes == 0 else f"{bytes_to_gb(total_bytes)} گیگابایت"
    data_used_gb = bytes_to_gb(used_bytes)
    # Days remaining
    exp_ts = int(user_info.get('expire', 0) or 0)
    if exp_ts and exp_ts > 0:
        try:
            now_ts = int(datetime.now().timestamp())
            days_left = max(0, int((exp_ts - now_ts) / 86400))
            expire_display = f"{days_left} روز مانده"
        except Exception:
            expire_display = "نامحدود"
    else:
        expire_display = "نامحدود"
    sub_link = (
        f"{panel_api.base_url}{user_info['subscription_url']}"
        if user_info.get('subscription_url') and isinstance(user_info.get('subscription_url'), str) and not user_info['subscription_url'].startswith('http')
        else user_info.get('subscription_url', 'لینک یافت نشد')
    )

    # For 3x-UI/X-UI panels, try to show direct configs instead of sub link
    panel_type = (order.get('panel_type') or '').lower()
    if not panel_type and order.get('panel_id'):
        prow = query_db("SELECT panel_type FROM panels WHERE id = ?", (order['panel_id'],), one=True)
        if prow:
            panel_type = (prow.get('panel_type') or '').lower()
    link_label = "\U0001F517 لینک اشتراک:"
    link_value = f"<code>{sub_link}</code>"
    if panel_type in ('3xui','3x-ui','3x ui','xui','x-ui','sanaei','alireza','txui','tx-ui','tx ui'):
        link_label = "\U0001F517 کانفیگ‌ها:"
        link_value = "کانفیگی یافت نشد. دکمه 'دریافت لینک مجدد' را بزنید تا ساخته شود."
        try:
            confs = []
            if hasattr(panel_api, 'list_inbounds') and hasattr(panel_api, 'get_configs_for_user_on_inbound'):
                ib_id = None
                if order.get('xui_inbound_id'):
                    ib_id = int(order['xui_inbound_id'])
                else:
                    inbounds, _m = panel_api.list_inbounds()
                    if inbounds:
                        ib_id = inbounds[0].get('id')
                if ib_id is not None:
                    confs = panel_api.get_configs_for_user_on_inbound(ib_id, marzban_username) or []
            if not confs and sub_link and isinstance(sub_link, str) and sub_link.startswith('http'):
                confs = _fetch_subscription_configs(sub_link)
            if confs:
                cfgs = "\n".join(f"<code>{c}</code>" for c in confs[:1])
                # Try to also show subscription link under configs
                sub_abs = sub_link or ''
                if sub_abs and not sub_abs.startswith('http'):
                    sub_abs = f"{panel_api.base_url}{sub_abs}"
                if sub_abs:
                    link_value = f"{cfgs}\n\n<b>لینک ساب:</b>\n<code>{sub_abs}</code>"
                else:
                    link_value = cfgs
        except Exception:
            pass
    try:
        execute_db("UPDATE orders SET last_link = ? WHERE id = ?", (sub_link or '', order_id))
    except Exception:
        pass

    # Respect setting: user_show_quota_enabled
    try:
        show_quota = (query_db("SELECT value FROM settings WHERE key='user_show_quota_enabled'", one=True) or {}).get('value')
        show_quota = (show_quota or '1') == '1'
    except Exception:
        show_quota = True

    if show_quota:
        text = (
            f"📦 <b>مشخصات سرویس</b>\n"
            f"<code>{marzban_username}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>حجم کل:</b> {data_limit_gb}\n"
            f"📈 <b>حجم مصرفی:</b> {data_used_gb} گیگابایت\n"
            f"📅 <b>تاریخ انقضا:</b> {expire_display}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>{link_label}</b>\n{link_value}"
        )
    else:
        text = (
            f"📦 <b>مشخصات سرویس</b>\n"
            f"<code>{marzban_username}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>تاریخ انقضا:</b> {expire_display}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>{link_label}</b>\n{link_value}"
        )

    keyboard = [
        [InlineKeyboardButton("\U0001F504 تمدید سرویس", callback_data=f"renew_service_{order_id}")],
        [InlineKeyboardButton("\U0001F4CA بررسی وضعیت", callback_data=f"check_service_status_{order_id}")],
        [InlineKeyboardButton("\U0001F5D1 حذف سرویس", callback_data=f"delete_service_{order_id}")],
        [InlineKeyboardButton("\U0001F4DD سفارشات من", callback_data='my_services'), InlineKeyboardButton("\U0001F4B3 کارت به کارت", callback_data='card_to_card_info')],
        [InlineKeyboardButton("\U0001F519 بازگشت به منو", callback_data='start_main')],
    ]
    # Try to send QR image for the first config or sub link
    qr_target = None
    try:
        # Prefer first config if available in this scope
        if 'confs' in locals() and isinstance(confs, list) and confs:
            qr_target = confs[0]
        else:
            # Fallback to subscription link if present inside link_value
            # Extract last <code>...</code> block as best-effort
            import re as _re
            m = _re.findall(r"<code>([^<]+)</code>", link_value or '')
            if m:
                qr_target = m[0]
    except Exception:
        qr_target = None
    if qr_target and (_build_qr is not None):
        try:
            buf = _build_qr(qr_target)
            if buf:
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=buf, caption=text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
                return
        except Exception:
            pass
    # Hard fallback to simple qrcode
    if qr_target:
        try:
            import qrcode, io as _io
            _b = _io.BytesIO(); qrcode.make(qr_target).save(_b, format='PNG'); _b.seek(0)
            await context.bot.send_photo(chat_id=query.message.chat_id, photo=_b, caption=text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
            return
        except Exception:
            pass
    # Final fallback: send text only
    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))


async def view_service_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        order_id = int(query.data.split('_')[-1])
    except Exception:
        await query.answer("شناسه نامعتبر است", show_alert=True)
        return ConversationHandler.END

    order = query_db("SELECT * FROM orders WHERE id = ?", (order_id,), one=True)
    if not order or order['user_id'] != query.from_user.id:
        await query.answer("سرویس یافت نشد", show_alert=True)
        return ConversationHandler.END
    panel_api = VpnPanelAPI(panel_id=order['panel_id'])
    qr_target = None
    # Prefer individual config if X-UI like
    panel_type = (order.get('panel_type') or '').lower()
    if not panel_type and order.get('panel_id'):
        prow = query_db("SELECT panel_type FROM panels WHERE id = ?", (order['panel_id'],), one=True)
        if prow:
            panel_type = (prow.get('panel_type') or '').lower()
    try:
        if panel_type in ('3xui','3x-ui','3x ui','xui','x-ui','sanaei','alireza','txui','tx-ui','tx ui'):
            ib_id = None
            if order.get('xui_inbound_id'):
                ib_id = int(order['xui_inbound_id'])
            elif hasattr(panel_api, 'list_inbounds'):
                inbounds, _m = panel_api.list_inbounds()
                if inbounds:
                    ib_id = inbounds[0].get('id')
            confs = []
            if ib_id is not None and hasattr(panel_api, 'get_configs_for_user_on_inbound'):
                try:
                    confs = panel_api.get_configs_for_user_on_inbound(ib_id, order['marzban_username']) or []
                except Exception:
                    confs = []
            if confs:
                qr_target = confs[0]
    except Exception:
        qr_target = None
    # Fallback to subscription link
    if qr_target is None:
        try:
            user_info, message = await panel_api.get_user(order['marzban_username'])
            if user_info:
                sub = user_info.get('subscription_url') or ''
                if sub and not sub.startswith('http'):
                    sub = f"{panel_api.base_url}{sub}"
                qr_target = sub or None
        except Exception:
            qr_target = None
    if not qr_target:
        await query.answer("لینکی برای ساخت QR یافت نشد.", show_alert=True)
        return ConversationHandler.END
    sent = False
    if _build_qr is not None:
        try:
            buf = _build_qr(qr_target)
            if buf:
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=buf, caption="QR اشتراک شما", parse_mode=ParseMode.HTML)
                sent = True
        except Exception:
            sent = False
    if not sent:
        try:
            import qrcode, io as _io
            _b = _io.BytesIO(); qrcode.make(qr_target).save(_b, format='PNG'); _b.seek(0)
            await context.bot.send_photo(chat_id=query.message.chat_id, photo=_b, caption="QR اشتراک شما", parse_mode=ParseMode.HTML)
            sent = True
        except Exception:
            sent = False
    if not sent:
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"لینک:\n<code>{qr_target}</code>", parse_mode=ParseMode.HTML)
    return ConversationHandler.END


async def delete_service_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        order_id = int(query.data.split('_')[-1])
    except Exception:
        await query.answer("شناسه نامعتبر است", show_alert=True)
        return ConversationHandler.END
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"delete_service_yes_{order_id}"),
         InlineKeyboardButton("❌ خیر", callback_data=f"delete_service_no_{order_id}")]
    ])
    try:
        await query.message.edit_text("⚠️ آیا از حذف این سرویس اطمینان دارید؟\n\n❌ این عملیات قابل بازگشت نیست و تمام اطلاعات سرویس حذف خواهد شد.", reply_markup=kb)
    except Exception:
        try:
            await context.bot.send_message(chat_id=query.message.chat_id, text="آیا از حذف این سرویس اطمینان دارید؟", reply_markup=kb)
        except Exception:
            pass
    return ConversationHandler.END


async def delete_service_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split('_')
    if len(parts) < 4:
        await query.answer("شناسه نامعتبر", show_alert=True)
        return ConversationHandler.END
    
    # Check if user clicked "no" button
    if 'no' in query.data:
        order_id = int(parts[-1])
        try:
            await query.message.edit_text(
                "✅ عملیات لغو شد. سرویس شما حذف نشد.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📱 مشاهده سرویس", callback_data=f'view_service_{order_id}'),
                    InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')
                ]])
            )
        except Exception:
            pass
        return ConversationHandler.END
    
    # User clicked "yes", proceed with deletion
    order_id = int(parts[-1])
    order = query_db("SELECT * FROM orders WHERE id = ?", (order_id,), one=True)
    if not order or order['user_id'] != query.from_user.id:
        await query.answer("سرویس یافت نشد", show_alert=True)
        return ConversationHandler.END
    # Best-effort panel deletion
    deleted_on_panel = False
    try:
        if order.get('panel_id'):
            api = VpnPanelAPI(panel_id=order['panel_id'])
            panel_type = (order.get('panel_type') or '').lower()
            username = order.get('marzban_username') or ''
            inb = int(order.get('xui_inbound_id') or 0)
            cid = order.get('xui_client_id')
            # Try specific helpers if available
            if panel_type in ('3xui','3x-ui','3x ui','xui','x-ui','sanaei','alireza','txui','tx-ui','tx ui'):
                if hasattr(api, 'delete_user_on_inbound') and inb and username:
                    try:
                        deleted_on_panel = bool(api.delete_user_on_inbound(inb, username, client_id=cid))
                    except TypeError:
                        deleted_on_panel = bool(api.delete_user_on_inbound(inb, username))
                if not deleted_on_panel and hasattr(api, 'delete_user') and username:
                    try:
                        deleted_on_panel = bool(api.delete_user(username))
                    except Exception:
                        deleted_on_panel = False
            else:
                # Marzban/Marzneshin like
                if hasattr(api, 'delete_user') and username:
                    try:
                        deleted_on_panel = bool(api.delete_user(username))
                    except Exception:
                        deleted_on_panel = False
                elif hasattr(api, 'disable_user') and username:
                    try:
                        deleted_on_panel = bool(api.disable_user(username))
                    except Exception:
                        deleted_on_panel = False
    except Exception:
        deleted_on_panel = False
    # Mark deleted in DB
    try:
        execute_db("UPDATE orders SET status = 'deleted' WHERE id = ?", (order_id,))
    except Exception:
        pass
    msg = "✅ سرویس با موفقیت حذف شد." + ("\n\n✅ از پنل نیز حذف گردید." if deleted_on_panel else "\n\n⚠️ توجه: ممکن است از پنل حذف نشده باشد.")
    try:
        await query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')]]))
    except Exception:
        try:
            await context.bot.send_message(chat_id=query.message.chat_id, text=msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')]]))
        except Exception:
            pass
    return ConversationHandler.END


async def check_service_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if service panel is online and functional"""
    query = update.callback_query
    await query.answer()
    try:
        order_id = int(query.data.split('_')[-1])
    except Exception:
        await query.answer("شناسه نامعتبر", show_alert=True)
        return ConversationHandler.END
    
    order = query_db("SELECT * FROM orders WHERE id = ?", (order_id,), one=True)
    if not order or order['user_id'] != query.from_user.id:
        await query.answer("سرویس یافت نشد", show_alert=True)
        return ConversationHandler.END
    
    if not order.get('panel_id'):
        await query.message.edit_text(
            "❌ اطلاعات پنل برای این سرویس یافت نشد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=f"view_service_{order_id}")]])
        )
        return ConversationHandler.END
    
    try:
        await query.message.edit_text("🔍 در حال بررسی وضعیت پنل...")
    except Exception:
        pass
    
    try:
        panel_api = VpnPanelAPI(panel_id=order['panel_id'])
        
        # Try different methods to check connection
        is_online = False
        error_msg = None
        
        try:
            # Method 1: check_connection (if available)
            if hasattr(panel_api, 'check_connection'):
                is_online = await panel_api.check_connection()
            # Method 2: Try to get token or login (for XUI panels)
            elif hasattr(panel_api, 'get_token'):
                try:
                    panel_api.get_token()
                    is_online = True
                except Exception:
                    is_online = False
            # Method 3: Try a simple API call
            elif hasattr(panel_api, 'list_inbounds'):
                try:
                    inbounds, _ = panel_api.list_inbounds()
                    is_online = inbounds is not None
                except Exception:
                    is_online = False
            # Method 4: Try to get user info
            else:
                try:
                    user_info, _ = await panel_api.get_user(order.get('marzban_username', 'test'))
                    is_online = user_info is not None
                except Exception:
                    is_online = False
        except Exception as e:
            is_online = False
            error_msg = str(e)[:50]
        
        if is_online:
            status_text = "✅ <b>وضعیت پنل: آنلاین</b>\n\n🟢 پنل شما در حال حاضر فعال و قابل استفاده است."
        else:
            status_text = "🔴 <b>وضعیت پنل: آفلاین</b>\n\n⚠️ پنل در حال حاضر در دسترس نیست."
            if error_msg:
                status_text += f"\n\n📝 خطا: {error_msg}"
        
        # Delete old message and send new one to avoid "no text to edit" error
        try:
            await query.message.delete()
        except Exception:
            pass
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=status_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بررسی مجدد", callback_data=f"check_service_status_{order_id}")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data=f"view_service_{order_id}")]
            ])
        )
    except Exception as e:
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"❌ <b>خطا در بررسی وضعیت</b>\n\nخطا: {str(e)[:100]}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=f"view_service_{order_id}")]])
        )
    
    return ConversationHandler.END


async def refresh_service_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        order_id = int(query.data.split('_')[-1])
    except Exception:
        await query.answer("خطا در شناسه سرویس", show_alert=True)
        return ConversationHandler.END
    order = query_db("SELECT * FROM orders WHERE id = ?", (order_id,), one=True)
    if not order or order['user_id'] != query.from_user.id:
        await query.answer("سرویس یافت نشد", show_alert=True)
        return ConversationHandler.END
    if not order.get('panel_id') or not order.get('marzban_username'):
        await query.answer("اطلاعات سرویس ناقص است", show_alert=True)
        return ConversationHandler.END
    panel_api = VpnPanelAPI(panel_id=order['panel_id'])
    # Determine panel type
    panel_type = (order.get('panel_type') or '').lower()
    if not panel_type and order.get('panel_id'):
        prow = query_db("SELECT panel_type FROM panels WHERE id = ?", (order['panel_id'],), one=True)
        if prow:
            panel_type = (prow.get('panel_type') or '').lower()
    # For 3x-UI/X-UI/TX-UI: build configs instead of sub link
    if panel_type in ('3xui','3x-ui','3x ui','xui','x-ui','sanaei','alireza','txui','tx-ui','tx ui'):
        try:
            # ensure login for 3x-UI
            if hasattr(panel_api, 'get_token'):
                try:
                    panel_api.get_token()
                except Exception:
                    pass
            ib_id = None
            if order.get('xui_inbound_id'):
                ib_id = int(order['xui_inbound_id'])
            else:
                if hasattr(panel_api, 'list_inbounds'):
                    inbounds, _m = panel_api.list_inbounds()
                    if inbounds:
                        ib_id = inbounds[0].get('id')
            if ib_id is None:
                try:
                    await context.bot.send_message(chat_id=query.message.chat_id, text="اینباندی یافت نشد.")
                except Exception:
                    pass
                return ConversationHandler.END
            # try multiple times to account for propagation
            confs = []
            if hasattr(panel_api, 'get_configs_for_user_on_inbound'):
                for _ in range(4):
                    pref_id = (order.get('xui_client_id') or None)
                    confs = panel_api.get_configs_for_user_on_inbound(ib_id, order['marzban_username'], preferred_id=pref_id) or []
                    if confs:
                        break
                    time.sleep(1.0)
            if not confs:
                # decode subscription as fallback for display
                user_info, message = await panel_api.get_user(order['marzban_username'])
                if user_info:
                    sub = (
                        f"{panel_api.base_url}{user_info['subscription_url']}" if user_info.get('subscription_url') and not user_info['subscription_url'].startswith('http') else user_info.get('subscription_url', '')
                    )
                    if sub:
                        confs = _fetch_subscription_configs(sub)
            if not confs:
                try:
                    await context.bot.send_message(chat_id=query.message.chat_id, text="ساخت کانفیگ ناموفق بود - کمی بعد دوباره تلاش کنید.")
                except Exception:
                    pass
                return ConversationHandler.END
            cfg_text = "\n".join(f"<code>{c}</code>" for c in confs)
            sent = False
            if _build_qr:
                try:
                    buf = _build_qr(confs[0])
                    if buf:
                        await context.bot.send_photo(chat_id=query.message.chat_id, photo=buf, caption=("\U0001F517 کانفیگ‌های جدید:\n" + cfg_text), parse_mode=ParseMode.HTML)
                        sent = True
                except Exception:
                    sent = False
            if not sent:
                # Hard fallback to simple QR if available
                try:
                    import qrcode
                    import io as _io
                    _b = _io.BytesIO(); qrcode.make(confs[0]).save(_b, format='PNG'); _b.seek(0)
                    await context.bot.send_photo(chat_id=query.message.chat_id, photo=_b, caption=("\U0001F517 کانفیگ‌های جدید:\n" + cfg_text), parse_mode=ParseMode.HTML)
                    sent = True
                except Exception:
                    sent = False
            if not sent:
                await context.bot.send_message(chat_id=query.message.chat_id, text=("\U0001F517 کانفیگ‌های جدید:\n" + cfg_text), parse_mode=ParseMode.HTML)
        except Exception:
            try:
                await context.bot.send_message(chat_id=query.message.chat_id, text="خطا در ساخت کانفیگ")
            except Exception:
                pass
        return ConversationHandler.END
    # Default: fetch fresh link from panel
    user_info, message = await panel_api.get_user(order['marzban_username'])
    if not user_info:
        await query.answer("دریافت لینک از پنل ناموفق بود", show_alert=True)
        return ConversationHandler.END
    sub_link = (
        f"{panel_api.base_url}{user_info['subscription_url']}"
        if user_info.get('subscription_url') and not user_info['subscription_url'].startswith('http')
        else user_info.get('subscription_url', 'لینک یافت نشد')
    )
    try:
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"\U0001F517 لینک اشتراک به‌روز شده:\n<code>{sub_link}</code>", parse_mode=ParseMode.HTML)
    except Exception:
        pass
    return ConversationHandler.END


async def revoke_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        order_id = int(query.data.split('_')[-1])
    except Exception:
        await query.answer("خطا در شناسه سرویس", show_alert=True)
        return ConversationHandler.END
    order = query_db("SELECT * FROM orders WHERE id = ?", (order_id,), one=True)
    if not order or order['user_id'] != query.from_user.id:
        await query.answer("سرویس یافت نشد", show_alert=True)
        return ConversationHandler.END
    if not order.get('panel_id') or not order.get('marzban_username'):
        await query.answer("اطلاعات سرویس ناقص است", show_alert=True)
        return ConversationHandler.END
    panel_api = VpnPanelAPI(panel_id=order['panel_id'])
    # Marzneshin or Marzban or 3x-UI
    try:
        import requests as _rq
        # Try to ensure token if available
        if hasattr(panel_api, '_ensure_token'):
            try:
                panel_api._ensure_token()
            except Exception:
                try:
                    logger.warning("revoke_key: _ensure_token failed", exc_info=True)
                except Exception:
                    pass
        ok = False
        # Marzneshin endpoint
        try:
            url = f"{panel_api.base_url}/api/users/{order['marzban_username']}/revoke_sub"
            headers = {"Accept": "application/json"}
            if getattr(panel_api, 'token', None):
                headers["Authorization"] = f"Bearer {panel_api.token}"
            r = panel_api.session.post(url, headers=headers, timeout=12)
            ok = (r.status_code in (200, 201, 202, 204))
        except Exception:
            ok = False
            try:
                logger.error("revoke_key: marzneshin revoke_sub call failed", exc_info=True)
            except Exception:
                pass
        # 3x-UI rotate on specific inbound id first (ensure login)
        if not ok and (order.get('xui_inbound_id') and hasattr(panel_api, 'rotate_user_key_on_inbound')):
            if hasattr(panel_api, 'get_token'):
                try:
                    panel_api.get_token()
                except Exception:
                    try:
                        logger.warning("revoke_key: get_token failed", exc_info=True)
                    except Exception:
                        pass
            try:
                updated = panel_api.rotate_user_key_on_inbound(int(order['xui_inbound_id']), order['marzban_username'])
                ok = bool(updated)
            except Exception:
                ok = False
                try:
                    logger.error("revoke_key: rotate_user_key_on_inbound failed", exc_info=True)
                except Exception:
                    pass
        # 3x-UI rotate across inbounds as fallback
        if not ok and hasattr(panel_api, 'rotate_user_key'):
            try:
                ok = bool(panel_api.rotate_user_key(order['marzban_username']))
            except Exception:
                ok = False
                try:
                    logger.error("revoke_key: rotate_user_key failed", exc_info=True)
                except Exception:
                    pass
        # Marzban fallback
        if not ok and hasattr(panel_api, 'revoke_subscription'):
            try:
                ok, _msg = panel_api.revoke_subscription(order['marzban_username'])
            except Exception:
                ok = False
                try:
                    logger.error("revoke_key: marzban revoke_subscription failed", exc_info=True)
                except Exception:
                    pass
        if not ok:
            await query.answer("خطا در تغییر کلید", show_alert=True)
            return ConversationHandler.END
        # For 3x-UI: send configs instead of sub link
        panel_type = (order.get('panel_type') or '').lower()
        if not panel_type and order.get('panel_id'):
            prow = query_db("SELECT panel_type FROM panels WHERE id = ?", (order['panel_id'],), one=True)
            if prow:
                panel_type = (prow.get('panel_type') or '').lower()
        if panel_type in ('3xui','3x-ui','3x ui'):
            try:
                await context.bot.send_message(chat_id=query.message.chat_id, text=("\U0001F511 کلید جدید صادر شد، چند لحظه بعد 'دریافت لینک مجدد' را بزنید."), parse_mode=ParseMode.HTML)
            except Exception:
                pass
            return ConversationHandler.END
        # X-UI: recreate client to force new UUID and delete old
        if panel_type in ('xui','x-ui','sanaei','alireza') and hasattr(panel_api, 'recreate_user_key_on_inbound'):
            ib_id = None
            if order.get('xui_inbound_id'):
                ib_id = int(order['xui_inbound_id'])
            else:
                try:
                    inbounds, _m = panel_api.list_inbounds()
                    if inbounds:
                        ib_id = inbounds[0].get('id')
                except Exception:
                    ib_id = None
            if ib_id is None:
                await query.answer("اینباندی یافت نشد", show_alert=True)
                return ConversationHandler.END
            new_client = panel_api.recreate_user_key_on_inbound(ib_id, order['marzban_username'])
            if not new_client:
                await query.answer("خطا در تغییر کلید", show_alert=True)
                return ConversationHandler.END
            try:
                # Update username to new email if changed (X-UI path)
                new_username = new_client.get('email') or order['marzban_username']
                execute_db("UPDATE orders SET marzban_username = ?, xui_client_id = ? WHERE id = ?", (new_username, (new_client.get('id') or new_client.get('uuid')), order_id))
            except Exception:
                pass
            # Build and send new config (3x-UI path builder differs; for X-UI we may send sub link or raw config if available)
            try:
                # Try to reuse X-UI/3x-UI config builder with preferred new id
                if hasattr(panel_api, 'get_configs_for_user_on_inbound'):
                    confs = panel_api.get_configs_for_user_on_inbound(ib_id, order['marzban_username'], preferred_id=(new_client.get('id') or new_client.get('uuid'))) or []
                if confs:
                    try:
                        disp_name = (order.get('marzban_username') or '')
                        confs_named = [( _with_name_fragment(c, disp_name) if disp_name else c) for c in confs]
                    except Exception:
                        confs_named = confs
                    cfg_text = "\n".join(f"<code>{c}</code>" for c in confs_named)
                    if _build_qr:
                        try:
                            buf = _build_qr(confs[0])
                            if buf:
                                await context.bot.send_photo(chat_id=query.message.chat_id, photo=buf, caption=("\U0001F511 کلید جدید صادر شد:\n" + cfg_text), parse_mode=ParseMode.HTML)
                            else:
                                raise RuntimeError('no-buf')
                        except Exception:
                            try:
                                import qrcode, io as _io
                                _b = _io.BytesIO(); qrcode.make(confs[0]).save(_b, format='PNG'); _b.seek(0)
                                await context.bot.send_photo(chat_id=query.message.chat_id, photo=_b, caption=("\U0001F511 کلید جدید صادر شد:\n" + cfg_text), parse_mode=ParseMode.HTML)
                            except Exception:
                                await context.bot.send_message(chat_id=query.message.chat_id, text=("\U0001F511 کلید جدید صادر شد:\n" + cfg_text), parse_mode=ParseMode.HTML)
                    else:
                        await context.bot.send_message(chat_id=query.message.chat_id, text=("\U0001F511 کلید جدید صادر شد:\n" + cfg_text), parse_mode=ParseMode.HTML)
                    return ConversationHandler.END
                # Fallback to user info/sub link
                info, _m = await panel_api.get_user(order['marzban_username'])
                sub = (info.get('subscription_url') if info else '') or ''
                if sub and not sub.startswith('http'):
                    sub = f"{panel_api.base_url}{sub}"
                caption = f"\U0001F511 کلید جدید صادر شد:\n<code>{sub or 'لینک یافت نشد'}</code>"
                if _build_qr and sub:
                    try:
                        buf = _build_qr(sub)
                        if buf:
                            await context.bot.send_photo(chat_id=query.message.chat_id, photo=buf, caption=caption, parse_mode=ParseMode.HTML)
                        else:
                            raise RuntimeError('no-buf')
                    except Exception:
                        try:
                            import qrcode, io as _io
                            _b = _io.BytesIO(); qrcode.make(sub).save(_b, format='PNG'); _b.seek(0)
                            await context.bot.send_photo(chat_id=query.message.chat_id, photo=_b, caption=caption, parse_mode=ParseMode.HTML)
                        except Exception:
                            await context.bot.send_message(chat_id=query.message.chat_id, text=caption, parse_mode=ParseMode.HTML)
                else:
                    await context.bot.send_message(chat_id=query.message.chat_id, text=caption, parse_mode=ParseMode.HTML)
            except Exception:
                await query.answer("خطا در ارسال کانفیگ جدید", show_alert=True)
            return ConversationHandler.END
        # Default: fetch fresh link and send
        user_info, message = await panel_api.get_user(order['marzban_username'])
        if not user_info:
            await query.answer("لینک جدید دریافت نشد", show_alert=True)
            return ConversationHandler.END
        sub_link = (
            f"{panel_api.base_url}{user_info['subscription_url']}"
            if user_info.get('subscription_url') and not user_info['subscription_url'].startswith('http')
            else user_info.get('subscription_url', 'لینک یافت نشد')
        )
        try:
            execute_db("UPDATE orders SET last_link = ? WHERE id = ?", (sub_link or '', order_id))
        except Exception:
            pass
        caption = f"\U0001F511 کلید جدید صادر شد:\n<code>{sub_link}</code>"
        if _build_qr:
            try:
                buf = _build_qr(sub_link)
                if buf:
                    await context.bot.send_photo(chat_id=query.message.chat_id, photo=buf, caption=caption, parse_mode=ParseMode.HTML)
                else:
                    raise RuntimeError('no-buf')
            except Exception:
                try:
                    import qrcode, io as _io
                    _b = _io.BytesIO(); qrcode.make(sub_link).save(_b, format='PNG'); _b.seek(0)
                    await context.bot.send_photo(chat_id=query.message.chat_id, photo=_b, caption=caption, parse_mode=ParseMode.HTML)
                except Exception:
                    await context.bot.send_message(chat_id=query.message.chat_id, text=caption, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=query.message.chat_id, text=caption, parse_mode=ParseMode.HTML)
    except Exception:
        try:
            logger.error("revoke_key: unexpected error", exc_info=True)
        except Exception:
            pass
        await query.answer("خطا در ارسال کانفیگ جدید", show_alert=True)
    return ConversationHandler.END


async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    wallet_row = query_db("SELECT balance FROM user_wallets WHERE user_id = ?", (user_id,), one=True)
    balance = int(wallet_row['balance']) if wallet_row else 0
    
    # Get recent transactions count
    recent_tx = query_db(
        "SELECT COUNT(*) as count FROM wallet_transactions WHERE user_id = ? AND created_at >= datetime('now', '-30 days')",
        (user_id,),
        one=True
    )
    tx_count = recent_tx['count'] if recent_tx else 0
    
    text = (
        f"💎 <b>کیف پول من</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>موجودی فعلی:</b> <code>{balance:,}</code> تومان\n"
        f"📊 <b>تراکنش‌ها (30 روز):</b> {tx_count} مورد\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <b>مزایای کیف پول:</b>\n\n"
        f"   ✅ خرید و تمدید آسان و سریع\n"
        f"   ✅ بدون نیاز به ارسال رسید\n"
        f"   ✅ امکان استفاده از تخفیف‌ها\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔽 <i>یک روش شارژ را انتخاب کنید:</i>"
    )
    keyboard = [
        [InlineKeyboardButton("💳 کارت به کارت", callback_data='wallet_topup_card')],
        # Crypto and gateway payment methods removed - only card available for wallet topup
        [
            InlineKeyboardButton("📱 سرویس‌ها", callback_data='my_services'),
            InlineKeyboardButton("💬 پشتیبانی", callback_data='support_menu')
        ],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')]
    ]
    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))


def _amount_keyboard(method: str) -> InlineKeyboardMarkup:
    amounts = [50000, 100000, 200000, 500000, 1000000]
    keyboard = []
    row = []
    for amount in amounts:
        row.append(InlineKeyboardButton(f"{amount:,} تومان", callback_data=f'wallet_amt_{method}_{amount}'))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("مبلغ دلخواه", callback_data=f'wallet_amt_{method}_custom')])
    return InlineKeyboardMarkup(keyboard)


async def wallet_topup_gateway_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    # present preset amounts
    context.user_data['awaiting'] = 'wallet_gateway_amount'
    try:
        last = context.user_data.pop('wallet_prompt_msg_id', None)
        if last:
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=last)
    except Exception:
        pass
    sent = await context.bot.send_message(chat_id=query.message.chat_id, text="مبلغ را انتخاب کنید:", reply_markup=_amount_keyboard('gateway'))
    context.user_data['wallet_prompt_msg_id'] = sent.message_id
    return WALLET_AWAIT_AMOUNT_GATEWAY


async def wallet_topup_gateway_receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # disabled: only via buttons
    return ConversationHandler.END


async def _wallet_show_gateway_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    amount = context.user_data.get('wallet_topup_amount')
    if not amount:
        await update.message.reply_text("خطا: مبلغ یافت نشد.")
        return ConversationHandler.END
    settings = {s['key']: s['value'] for s in query_db("SELECT key, value FROM settings")}
    gateway_type = (settings.get('gateway_type') or 'zarinpal').lower()
    callback_url = (settings.get('gateway_callback_url') or '').strip()
    amount_rial = int(amount) * 10
    description = "شارژ کیف پول"
    cancel_text = "\U0001F519 لغو"
    cancel_cb = 'wallet_menu'
    if gateway_type == 'zarinpal':
        mid = (settings.get('zarinpal_merchant_id') or '').strip()
        if not mid:
            await update.message.reply_text("MerchantID تنظیم نشده است.")
            return ConversationHandler.END
        from .purchase import _zarinpal_request
        authority, start_url = _zarinpal_request(mid, amount_rial, description, callback_url or 'https://example.com/callback')
        if not (authority and start_url):
            await update.message.reply_text("خطا در ایجاد لینک زرین‌پال.")
            return ConversationHandler.END
        context.user_data['wallet_gateway'] = {'type': 'zarinpal', 'authority': authority, 'amount_rial': amount_rial}
        kb = [
            [InlineKeyboardButton("\U0001F6D2 رفتن به صفحه پرداخت", url=start_url)],
            [InlineKeyboardButton("\U0001F50D بررسی پرداخت", callback_data='wallet_verify_gateway')],
            [InlineKeyboardButton(cancel_text, callback_data=cancel_cb)],
        ]
        await update.message.reply_text(f"\U0001F6E0\uFE0F پرداخت آنلاین\n\nمبلغ: {amount:,} تومان", reply_markup=InlineKeyboardMarkup(kb))
        context.user_data.pop('awaiting', None)
        context.user_data.pop('wallet_prompt_msg_id', None)
        return ConversationHandler.END
    else:
        pin = (settings.get('aghapay_pin') or '').strip()
        if not pin or not callback_url:
            await update.message.reply_text("PIN یا Callback آقای پرداخت تنظیم نشده است.")
            return ConversationHandler.END
        from .purchase import _aghapay_create
        order_id_str = f"WAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        pay_url = _aghapay_create(pin, int(amount), callback_url, order_id_str, description)
        if not pay_url:
            await update.message.reply_text("خطا در ایجاد لینک آقای پرداخت.")
            return ConversationHandler.END
        context.user_data['wallet_gateway'] = {'type': 'aghapay', 'amount_rial': amount_rial, 'transid': pay_url.split('/')[-1]}
        kb = [
            [InlineKeyboardButton("\U0001F6D2 رفتن به صفحه پرداخت", url=pay_url)],
            [InlineKeyboardButton("\U0001F50D بررسی پرداخت", callback_data='wallet_verify_gateway')],
            [InlineKeyboardButton(cancel_text, callback_data=cancel_cb)],
        ]
        await update.message.reply_text(f"\U0001F6E0\uFE0F پرداخت آنلاین\n\nمبلغ: {amount:,} تومان", reply_markup=InlineKeyboardMarkup(kb))
        context.user_data.pop('awaiting', None)
        context.user_data.pop('wallet_prompt_msg_id', None)
        return ConversationHandler.END


async def wallet_verify_gateway(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    gw = context.user_data.get('wallet_gateway') or {}
    if not gw:
        await query.message.edit_text("اطلاعات پرداخت یافت نشد.")
        return ConversationHandler.END
    ok = False
    settings = {s['key']: s['value'] for s in query_db("SELECT key, value FROM settings")}
    if gw.get('type') == 'zarinpal':
        from .purchase import _zarinpal_verify
        ok, _ = _zarinpal_verify(settings.get('zarinpal_merchant_id') or '', gw.get('amount_rial', 0), gw.get('authority',''))
    else:
        from .purchase import _aghapay_verify
        ok = _aghapay_verify(settings.get('aghapay_pin') or '', int(context.user_data.get('wallet_topup_amount',0)), gw.get('transid',''))
    if not ok:
        await query.message.edit_text("پرداخت تایید نشد. دوباره امتحان کنید.")
        return ConversationHandler.END
    user_id = query.from_user.id
    amount = context.user_data.get('wallet_topup_amount')
    tx_id = execute_db("INSERT INTO wallet_transactions (user_id, amount, direction, method, status, created_at, reference) VALUES (?, ?, 'credit', 'gateway', 'pending', ?, ?)", (user_id, int(amount), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), gw.get('transid','')))
    
    # Get full user info from Telegram API
    try:
        telegram_user = await context.bot.get_chat(user_id)
        first_name = telegram_user.first_name or 'نامشخص'
        last_name = telegram_user.last_name or ''
        username = telegram_user.username or None
        full_name = f"{first_name} {last_name}".strip()
        user_mention = f"@{username}" if username else full_name
    except Exception:
        user_info_db = query_db("SELECT first_name FROM users WHERE user_id = ?", (user_id,), one=True)
        first_name = user_info_db.get('first_name', 'نامشخص') if user_info_db else 'نامشخص'
        full_name = first_name
        username = None
        user_mention = first_name
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("\u2705 تایید", callback_data=f"wallet_tx_approve_{tx_id}"), InlineKeyboardButton("\u274C رد", callback_data=f"wallet_tx_reject_{tx_id}")],
        [InlineKeyboardButton("\U0001F4B8 منوی درخواست‌ها", callback_data="admin_wallet_tx_menu")],
    ])
    text_notification = (
        f"💸 <b>درخواست شارژ کیف پول (Gateway)</b>\n\n"
        f"👤 <b>کاربر:</b> {user_mention}\n"
        f"📝 <b>نام:</b> {full_name}\n"
        f"🔖 <b>یوزرنیم تلگرام:</b> {'@' + username if username else '-'}\n"
        f"🆔 <b>یوزر آیدی:</b> <code>{user_id}</code>\n"
        f"💰 <b>مبلغ:</b> {int(amount):,} تومان\n"
        f"🔑 <b>TransID:</b> <code>{gw.get('transid','-')}</code>\n"
        f"🕐 <b>زمان:</b> <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
    )
    await notify_admins(
        context.bot,
        text=text_notification,
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )
    await query.message.edit_text("درخواست شارژ شما ثبت شد و پس از تایید ادمین به موجودی افزوده می‌شود.")
    context.user_data.pop('wallet_gateway', None)
    context.user_data.pop('wallet_topup_amount', None)
    return ConversationHandler.END


async def wallet_topup_card_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['awaiting'] = 'wallet_card_amount'
    set_flow(context, 'wallet')
    try:
        last = context.user_data.pop('wallet_prompt_msg_id', None)
        if last:
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=last)
    except Exception:
        pass
    sent = await context.bot.send_message(chat_id=query.message.chat_id, text="مبلغ را انتخاب کنید:", reply_markup=_amount_keyboard('card'))
    context.user_data['wallet_prompt_msg_id'] = sent.message_id
    return WALLET_AWAIT_AMOUNT_CARD


async def wallet_topup_card_receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # This function is now only called from the custom amount flow, 
    # so we don't need to handle callback queries here.
    if not update.message:
        return ConversationHandler.END

    # The amount is already set in context by wallet_topup_custom_amount_receive
    amount = context.user_data.get('wallet_topup_amount')
    user_id = update.effective_user.id

    cards = query_db("SELECT card_number, holder_name FROM cards")
    if not cards:
        await update.message.reply_text("در حال حاضر امکان پرداخت کارت به کارت وجود ندارد.")
        return ConversationHandler.END

    card_info_lines = [f"{card['card_number']} - {card['holder_name']}" for card in cards]
    card_info_text = "\n".join(card_info_lines)
    
    invoice_text = (
        f"**واریز به کارت**\n\n"
        f"لطفا مبلغ **{amount:,} تومان** را به یکی از کارت‌های زیر واریز کرده و سپس از رسید خود اسکرین‌شات گرفته و در همین صفحه ارسال نمایید.\n\n"
        f"{card_info_text}"
    )
    
    await update.message.reply_text(invoice_text, parse_mode=ParseMode.MARKDOWN)
    context.user_data['awaiting'] = 'wallet_upload'
    context.user_data['wallet_method'] = 'card'
    
    return WALLET_AWAIT_SCREENSHOT


async def wallet_topup_crypto_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['awaiting'] = 'wallet_crypto_amount'
    set_flow(context, 'wallet')
    try:
        last = context.user_data.pop('wallet_prompt_msg_id', None)
        if last:
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=last)
    except Exception:
        pass
    sent = await context.bot.send_message(chat_id=query.message.chat_id, text="مبلغ را انتخاب کنید:", reply_markup=_amount_keyboard('crypto'))
    context.user_data['wallet_prompt_msg_id'] = sent.message_id
    return WALLET_AWAIT_AMOUNT_CRYPTO


async def wallet_topup_crypto_receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # disabled: only via buttons
    return ConversationHandler.END


async def wallet_topup_amount_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # disabled
    return ConversationHandler.END


async def wallet_select_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split('_')  # wallet_amt_<method>_<amount>
    if len(parts) != 4:
        return ConversationHandler.END
    method = parts[2]
    try:
        amount = int(parts[3])
    except Exception:
        await query.message.edit_text("مبلغ نامعتبر.")
        return ConversationHandler.END
    context.user_data['wallet_topup_amount'] = amount
    context.user_data['wallet_method'] = method
    if method == 'gateway':
        # call gateway flow using dummy update with message
        dummy = type('obj', (object,), {'message': query.message})
        return await _wallet_show_gateway_message(dummy, context)
    if method == 'card':
        # proceed to card list and then show upload button
        context.user_data['awaiting'] = 'wallet_upload'
        cards = query_db("SELECT card_number, holder_name FROM cards")
        if not cards:
            await query.message.edit_text("خطا: هیچ کارت بانکی در سیستم ثبت نشده است.")
            return ConversationHandler.END
        lines = [f"\U0001F4B0 مبلغ: {amount:,} تومان", "\nبه یکی از کارت‌های زیر واریز کنید و سپس روی دکمه زیر بزنید و رسید را ارسال کنید:"]
        for c in cards:
            lines.append(f"- {c['holder_name']}\n{ltr_code(c['card_number'])}")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("ارسال اسکرین‌شات", callback_data='wallet_upload_start_card')], [InlineKeyboardButton("\U0001F519 بازگشت", callback_data='wallet_menu')]])
        await query.message.edit_text("\n\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
        context.user_data.pop('wallet_prompt_msg_id', None)
        return WALLET_AWAIT_CARD_SCREENSHOT
    if method == 'crypto':
        context.user_data['awaiting'] = 'wallet_upload'
        wallets = query_db("SELECT asset, chain, address, memo FROM wallets ORDER BY id DESC")
        if not wallets:
            await query.message.edit_text("هیچ ولتی ثبت نشده است. لطفا بعدا تلاش کنید.")
            return ConversationHandler.END
        lines = ["لطفا مبلغ معادل را به یکی از ولت‌های زیر واریز کرده و سپس روی دکمه زیر بزنید و رسید را ارسال کنید:"]
        for w in wallets:
            memo = f"\nMEMO: {w['memo']}" if w.get('memo') else ''
            lines.append(f"- {w['asset']} ({w['chain']}):\n{w['address']}{memo}")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("ارسال اسکرین‌شات", callback_data='wallet_upload_start_crypto')], [InlineKeyboardButton("\U0001F519 بازگشت", callback_data='wallet_menu')]])
        await query.message.edit_text("\n\n".join(lines), reply_markup=kb)
        context.user_data.pop('wallet_prompt_msg_id', None)
        return WALLET_AWAIT_CRYPTO_SCREENSHOT
    return ConversationHandler.END


async def support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = get_message_text(
        'support_menu',
        "💬 <b>پشتیبانی و راهنمایی</b>\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n👋 سلام! چگونه می‌توانیم کمکتان کنیم؟\n\n📝 <b>ثبت تیکت پشتیبانی:</b>\n   • پیام یا سوال خود را ارسال کنید\n   • پاسخ سریع کارشناسان را دریافت کنید\n\n📚 <b>مرکز آموزش:</b>\n   • راهنمای گام به گام\n   • ویدیوهای آموزشی\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n⏰ <b>ساعات پاسخگویی:</b> همه روزه 9 صبح - 12 شب\n\n💡 <i>پیش از ثبت تیکت، لطفاً آموزش‌ها را بررسی کنید.</i>"
    )
    
    kb = [
        [InlineKeyboardButton("📝 ثبت تیکت جدید", callback_data='ticket_create_start')],
        [
            InlineKeyboardButton("📚 آموزش‌ها", callback_data='tutorials_menu'),
            InlineKeyboardButton("📱 سرویس‌ها", callback_data='my_services')
        ],
        [
            InlineKeyboardButton("💰 کیف پول", callback_data='wallet_menu'),
            InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')
        ]
    ]
    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))


async def ticket_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = get_message_text(
        'support_ticket_create',
        "📝 <b>ثبت تیکت جدید</b>\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n👋 لطفاً پیام، سوال یا مشکل خود را ارسال کنید.\n\n✅ هر نوع پیامی (متن، عکس، فایل) پذیرفته می‌شود.\n━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='support_menu')]])
    )
    return SUPPORT_AWAIT_TICKET


async def ticket_receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        return
    # State-driven: invoked only in SUPPORT_AWAIT_TICKET
    user_id = update.effective_user.id
    # Persist main ticket row if not exists
    ticket_id = execute_db("INSERT INTO tickets (user_id, content_type, text, file_id, created_at, status) VALUES (?, ?, ?, ?, ?, 'pending')",
                           (user_id, 'meta', '', None, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    # Detect content
    content_type = 'text'
    text = update.message.text or ''
    file_id = None
    if update.message.photo:
        content_type = 'photo'
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        content_type = 'document'
        file_id = update.message.document.file_id
        text = update.message.caption or ''
    elif update.message.video:
        content_type = 'video'
        file_id = update.message.video.file_id
        text = update.message.caption or ''
    elif update.message.voice:
        content_type = 'voice'
        file_id = update.message.voice.file_id
    elif update.message.audio:
        content_type = 'audio'
        file_id = update.message.audio.file_id
    # Save threaded message
    execute_db("INSERT INTO ticket_messages (ticket_id, sender, content_type, text, file_id, created_at) VALUES (?, 'user', ?, ?, ?, ?)",
               (ticket_id, content_type, text, file_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    # Forward original message and controls to all admins
    admin_kb = [[InlineKeyboardButton("✉️ پاسخ", callback_data=f"ticket_reply_{ticket_id}"), InlineKeyboardButton("🗑 حذف", callback_data=f"ticket_delete_{ticket_id}")],[InlineKeyboardButton("📨 منوی تیکت‌ها", callback_data='admin_tickets_menu')]]
    summary = f"تیکت #{ticket_id}\nکاربر: `{user_id}`\nزمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    from ..helpers.tg import get_all_admin_ids
    for aid in get_all_admin_ids():
        try:
            await context.bot.forward_message(chat_id=aid, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
        except Exception:
            pass
        try:
            await context.bot.send_message(chat_id=aid, text=summary, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(admin_kb))
        except Exception:
            pass
    await update.message.reply_text(
        "✅ <b>تیکت ثبت شد!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎫 <b>شماره تیکت:</b> #{ticket_id}\n\n"
        "👥 تیم پشتیبانی در کمترین زمان پاسخ خواهد داد.\n"
        "🔔 پاسخ مستقیماً به شما ارسال می‌شود.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END


async def tutorials_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rows = query_db("SELECT id, title FROM tutorials ORDER BY sort_order, id DESC")
    
    if not rows:
        text = (
            "📚 <b>مرکز آموزش</b>\n\n"
            "❌ در حال حاضر هیچ آموزشی ثبت نشده است.\n\n"
            "💡 به زودی آموزش‌ها اضافه خواهند شد."
        )
        kb = [
            [
                InlineKeyboardButton("📱 سرویس‌ها", callback_data='my_services'),
                InlineKeyboardButton("💬 پشتیبانی", callback_data='support_menu')
            ],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')]
        ]
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))
        return
    
    text = (
        f"📚 <b>مرکز آموزش</b>\n\n"
        f"📊 تعداد آموزش‌ها: {len(rows)} عدد\n\n"
        f"💡 برای مشاهده هر آموزش، روی آن کلیک کنید:"
    )
    
    kb = []
    for r in rows:
        kb.append([InlineKeyboardButton(f"📖 {r['title']}", callback_data=f"tutorial_show_{r['id']}")])
    
    # Quick menu
    kb.append([
        InlineKeyboardButton("📱 سرویس‌ها", callback_data='my_services'),
        InlineKeyboardButton("💬 پشتیبانی", callback_data='support_menu')
    ])
    kb.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')])
    
    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))


async def tutorial_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tid = int(query.data.split('_')[-1])
    items = query_db("SELECT content_type, file_id, COALESCE(caption,'') AS caption FROM tutorial_media WHERE tutorial_id = ? ORDER BY sort_order, id", (tid,))
    if not items:
        await query.message.edit_text("برای این آموزش محتوایی ثبت نشده است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت", callback_data='tutorials_menu')]]))
        return
    # send sequentially
    for it in items[:20]:
        ct = it['content_type']; fid = it['file_id']; cap = it['caption']
        if ct == 'photo':
            await context.bot.send_photo(chat_id=query.message.chat_id, photo=fid, caption=cap)
        elif ct == 'video':
            await context.bot.send_video(chat_id=query.message.chat_id, video=fid, caption=cap)
        elif ct == 'document':
            await context.bot.send_document(chat_id=query.message.chat_id, document=fid, caption=cap)
        elif ct == 'voice':
            await context.bot.send_voice(chat_id=query.message.chat_id, voice=fid, caption=cap)
        elif ct == 'audio':
            await context.bot.send_audio(chat_id=query.message.chat_id, audio=fid, caption=cap)
        elif ct == 'text':
            await context.bot.send_message(chat_id=query.message.chat_id, text=fid)
    kb = [
        [InlineKeyboardButton("🔁 آموزش‌ها", callback_data='tutorials_menu')],
        [
            InlineKeyboardButton("📱 سرویس‌ها", callback_data='my_services'),
            InlineKeyboardButton("💬 پشتیبانی", callback_data='support_menu')
        ],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')]
    ]
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="✅ پایان آموزش\n\n💡 برای بازگشت به لیست آموزش‌ها روی دکمه زیر کلیک کنید.",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    # generate deep-link
    link = f"https://t.me/{(await context.bot.get_me()).username}?start={uid}"
    total = query_db("SELECT COUNT(*) AS c FROM referrals WHERE referrer_id = ?", (uid,), one=True) or {'c': 0}
    buyers = query_db("SELECT COUNT(DISTINCT o.user_id) AS c FROM orders o JOIN referrals r ON r.referee_id = o.user_id WHERE r.referrer_id = ? AND o.status='approved'", (uid,), one=True) or {'c': 0}
    cfg = query_db("SELECT value FROM settings WHERE key = 'referral_commission_percent'", one=True)
    percent = int((cfg.get('value') if cfg else '10') or 10)
    text = (
        "معرفی به دوستان\n\n"
        f"لینک اختصاصی شما:\n{link}\n\n"
        f"تعداد زیرمجموعه‌ها: {int(total.get('c') or 0)}\n"
        f"تعداد خریداران: {int(buyers.get('c') or 0)}\n\n"
        f"در صورتی که افرادی که با لینک شما وارد ربات می‌شوند خرید انجام دهند، {percent}% مبلغ خریدشان به عنوان پاداش به کیف پول شما واریز می‌شود."
    )
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت", callback_data='start_main')]]))


async def reseller_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    # Mark intent so direct uploads are accepted even if button wasn't pressed
    context.user_data['reseller_intent'] = True
    settings = {s['key']: s['value'] for s in query_db("SELECT key, value FROM settings")} or {}
    if settings.get('reseller_enabled', '1') != '1':
        await query.message.edit_text("قابلیت نمایندگی موقتا غیرفعال است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت", callback_data='start_main')]]))
        return ConversationHandler.END
    # If already active reseller and not expired
    rs = query_db("SELECT status, expires_at, used_purchases, max_purchases, discount_percent FROM resellers WHERE user_id = ?", (uid,), one=True)
    if rs:
        # Days left and active eligibility
        exp_str = rs.get('expires_at') or ''
        expire_display = exp_str
        days_left = None
        try:
            if exp_str:
                exp_dt = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S")
                now_dt = datetime.now()
                seconds = (exp_dt - now_dt).total_seconds()
                days_left = max(0, int(seconds // 86400))
                expire_display = f"{days_left} روز مانده"
        except Exception:
            expire_display = exp_str or 'نامعلوم'

        status = (rs.get('status') or 'inactive').lower()
        under_cap = int(rs.get('max_purchases') or 0) == 0 or int(rs.get('used_purchases') or 0) < int(rs.get('max_purchases') or 0)
        is_active = (status == 'active') and under_cap and (days_left is None or days_left > 0)
        if is_active:
            text = (
                f"\U0001F4B5 وضعیت نمایندگی شما\n\n"
                f"وضعیت: فعال\n"
                f"درصد تخفیف: {int(rs.get('discount_percent') or settings.get('reseller_discount_percent') or 50)}%\n"
                f"سقف خرید: {int(rs.get('used_purchases') or 0)}/{int(rs.get('max_purchases') or settings.get('reseller_max_purchases') or 10)}\n"
                f"انقضا: {expire_display}\n"
            )
            kb = [[InlineKeyboardButton("\U0001F519 بازگشت", callback_data='start_main')]]
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END
        # else: inactive/expired/cap reached -> fall through to purchase offer
    # Show purchase offer
    fee = int((settings.get('reseller_fee_toman') or '200000') or 200000)
    percent = int((settings.get('reseller_discount_percent') or '50') or 50)
    days = int((settings.get('reseller_duration_days') or '30') or 30)
    cap = int((settings.get('reseller_max_purchases') or '10') or 10)
    text = (
        "دریافت نمایندگی\n\n"
        f"با دریافت نمایندگی می‌توانید اشتراک‌ها را با {percent}% تخفیف تهیه کنید.\n"
        f"هزینه دریافت نمایندگی: {fee:,} تومان\n"
        f"سقف خرید اشتراک: {cap} عدد\n"
        f"مدت زمان استفاده: {days} روز\n\n"
        "برای ادامه، روی دکمه زیر بزنید:"
    )
    kb = [[InlineKeyboardButton("پرداخت و دریافت", callback_data='reseller_pay_start')], [InlineKeyboardButton("\U0001F519 بازگشت", callback_data='start_main')]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return ConversationHandler.END


async def reseller_pay_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['reseller_intent'] = True
    settings = {s['key']: s['value'] for s in query_db("SELECT key, value FROM settings")} or {}
    fee = int((settings.get('reseller_fee_toman') or '200000') or 200000)
    text = (
        f"پرداخت هزینه نمایندگی ({fee:,} تومان)\n\nروش پرداخت خود را انتخاب کنید:"
    )
    kb = [
        [InlineKeyboardButton("\U0001F4B3 کارت به کارت", callback_data='reseller_pay_card')],
        [InlineKeyboardButton("\U0001F4B0 رمزارز", callback_data='reseller_pay_crypto')],
        [InlineKeyboardButton("\U0001F6E0\uFE0F درگاه پرداخت", callback_data='reseller_pay_gateway')],
        [InlineKeyboardButton("\U0001F519 بازگشت", callback_data='reseller_menu')],
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return ConversationHandler.END


async def reseller_pay_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    settings = {s['key']: s['value'] for s in query_db("SELECT key, value FROM settings")} or {}
    fee = int((settings.get('reseller_fee_toman') or '200000') or 200000)
    cards = query_db("SELECT card_number, holder_name FROM cards") or []
    if not cards:
        await query.message.edit_text("هیچ کارت بانکی تنظیم نشده است.")
        return ConversationHandler.END
    lines = [f"\U0001F4B0 مبلغ: {fee:,} تومان", "\nبه یکی از کارت‌های زیر واریز کنید و سپس روی دکمه زیر بزنید و رسید را ارسال کنید:"]
    for c in cards:
        lines.append(f"- {c['holder_name']}\n{ltr_code(c['card_number'])}")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("ارسال اسکرین‌شات", callback_data='reseller_upload_start_card')],[InlineKeyboardButton("\U0001F519 بازگشت", callback_data='reseller_pay_start')]])
    await query.message.edit_text("\n\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
    context.user_data['reseller_payment'] = {'method': 'card', 'amount': fee}
    context.user_data['awaiting'] = 'reseller_upload'
    return RESELLER_AWAIT_UPLOAD


async def reseller_pay_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    settings = {s['key']: s['value'] for s in query_db("SELECT key, value FROM settings")} or {}
    fee = int((settings.get('reseller_fee_toman') or '200000') or 200000)
    wallets = query_db("SELECT asset, chain, address, memo FROM wallets ORDER BY id DESC") or []
    if not wallets:
        await query.message.edit_text("هیچ ولتی ثبت نشده است. لطفا بعدا تلاش کنید.")
        return ConversationHandler.END
    lines = [f"\U0001F4B0 مبلغ: {fee:,} تومان", "لطفا مبلغ معادل را به یکی از ولت‌های زیر واریز کرده و سپس روی دکمه زیر بزنید و رسید را ارسال کنید:"]
    for w in wallets:
        memo = f"\nMEMO: {w['memo']}" if w.get('memo') else ''
        lines.append(f"- {w['asset']} ({w['chain']}):\n{w['address']}{memo}")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("ارسال اسکرین‌شات", callback_data='reseller_upload_start_crypto')],[InlineKeyboardButton("\U0001F519 بازگشت", callback_data='reseller_pay_start')]])
    await query.message.edit_text("\n\n".join(lines), reply_markup=kb)
    context.user_data['reseller_payment'] = {'method': 'crypto', 'amount': fee}
    context.user_data['awaiting'] = 'reseller_upload'
    return RESELLER_AWAIT_UPLOAD


async def reseller_pay_gateway(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    settings = {s['key']: s['value'] for s in query_db("SELECT key, value FROM settings")} or {}
    fee = int((settings.get('reseller_fee_toman') or '200000') or 200000)
    gateway_type = (settings.get('gateway_type') or 'zarinpal').lower()
    callback_url = (settings.get('gateway_callback_url') or '').strip()
    amount_rial = int(fee) * 10
    if gateway_type == 'zarinpal':
        from .purchase import _zarinpal_request
        mid = (settings.get('zarinpal_merchant_id') or '').strip()
        if not mid:
            await query.message.edit_text("MerchantID تنظیم نشده است.")
            return ConversationHandler.END
        authority, start_url = _zarinpal_request(mid, amount_rial, "پرداخت دریافت نمایندگی", callback_url or 'https://example.com/callback')
        if not (authority and start_url):
            await query.message.edit_text("خطا در ایجاد لینک زرین‌پال.")
            return ConversationHandler.END
        context.user_data['reseller_gateway'] = {'type': 'zarinpal', 'authority': authority, 'amount_rial': amount_rial}
        context.user_data['reseller_payment'] = {'method': 'gateway', 'amount': fee}
        context.user_data['awaiting'] = 'reseller_upload'
        kb = [
            [InlineKeyboardButton("\U0001F6D2 رفتن به صفحه پرداخت", url=start_url)],
            [InlineKeyboardButton("\U0001F50D بررسی پرداخت", callback_data='reseller_verify_gateway')],
            [InlineKeyboardButton("\U0001F519 بازگشت", callback_data='reseller_pay_start')],
        ]
        await query.message.edit_text(f"\U0001F6E0\uFE0F پرداخت آنلاین\n\nمبلغ: {fee:,} تومان", reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END
    else:
        from .purchase import _aghapay_create
        pin = (settings.get('aghapay_pin') or '').strip()
        if not pin or not callback_url:
            await query.message.edit_text("PIN یا Callback آقای پرداخت تنظیم نشده است.")
            return ConversationHandler.END
        order_id_str = f"RES-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        pay_url = _aghapay_create(pin, int(fee), callback_url, order_id_str, "پرداخت دریافت نمایندگی")
        if not pay_url:
            await query.message.edit_text("خطا در ایجاد لینک آقای پرداخت.")
            return ConversationHandler.END
        context.user_data['reseller_gateway'] = {'type': 'aghapay', 'amount_rial': amount_rial, 'transid': pay_url.split('/')[-1]}
        context.user_data['reseller_payment'] = {'method': 'gateway', 'amount': fee}
        context.user_data['awaiting'] = 'reseller_upload'
        kb = [
            [InlineKeyboardButton("\U0001F6D2 رفتن به صفحه پرداخت", url=pay_url)],
            [InlineKeyboardButton("\U0001F50D بررسی پرداخت", callback_data='reseller_verify_gateway')],
            [InlineKeyboardButton("\U0001F519 بازگشت", callback_data='reseller_pay_start')],
        ]
        await query.message.edit_text(f"\U0001F6E0\uFE0F پرداخت آنلاین\n\nمبلغ: {fee:,} تومان", reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END


async def reseller_verify_gateway(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    gw = context.user_data.get('reseller_gateway') or {}
    if not gw:
        await query.message.edit_text("اطلاعات پرداخت یافت نشد.")
        return ConversationHandler.END
    ok = False
    settings = {s['key']: s['value'] for s in query_db("SELECT key, value FROM settings")} or {}
    if gw.get('type') == 'zarinpal':
        from .purchase import _zarinpal_verify
        ok, ref_id = _zarinpal_verify(settings.get('zarinpal_merchant_id') or '', gw.get('amount_rial', 0), gw.get('authority',''))
        reference = ref_id
    else:
        from .purchase import _aghapay_verify
        fee = int((settings.get('reseller_fee_toman') or '200000') or 200000)
        ok = _aghapay_verify(settings.get('aghapay_pin') or '', fee, gw.get('transid',''))
        reference = gw.get('transid','')
    if not ok:
        await query.message.edit_text("پرداخت تایید نشد. دوباره امتحان کنید.")
        return ConversationHandler.END
    # Log request and notify admins
    user = query.from_user
    settings = {s['key']: s['value'] for s in query_db("SELECT key, value FROM settings")} or {}
    fee = int((settings.get('reseller_fee_toman') or '200000') or 200000)
    rr_id = execute_db(
        "INSERT INTO reseller_requests (user_id, amount, method, status, created_at, reference) VALUES (?, ?, ?, 'pending', ?, ?)",
        (user.id, fee, gw.get('type','gateway'), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reference)
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("\u2705 تایید نمایندگی", callback_data=f"reseller_approve_{rr_id}"), InlineKeyboardButton("\u274C رد", callback_data=f"reseller_reject_{rr_id}")]])
    await notify_admins(context.bot, text=(f"\U0001F4B5 درخواست دریافت نمایندگی\n\nکاربر: `{user.id}`\nمبلغ: {fee:,} تومان\nروش: {gw.get('type','gateway')}\nRef: {reference}"), parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    await query.message.edit_text("\u2705 پرداخت شما ثبت شد و برای تایید به ادمین ارسال شد. لطفا منتظر بمانید.")
    context.user_data.pop('reseller_gateway', None)
    return ConversationHandler.END


async def reseller_upload_start_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['awaiting'] = 'reseller_upload'
    context.user_data['reseller_payment'] = context.user_data.get('reseller_payment') or {'method': 'card'}
    await query.message.edit_text("رسید/اسکرین‌شات پرداخت نمایندگی را ارسال کنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت", callback_data='reseller_pay_start')]]))
    return RESELLER_AWAIT_UPLOAD


async def reseller_upload_start_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['awaiting'] = 'reseller_upload'
    context.user_data['reseller_payment'] = context.user_data.get('reseller_payment') or {'method': 'crypto'}
    await query.message.edit_text("رسید/اسکرین‌شات پرداخت نمایندگی را ارسال کنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت", callback_data='reseller_pay_start')]]))
    return RESELLER_AWAIT_UPLOAD


async def reseller_upload_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Accept if explicitly awaiting OR if payment context exists (fallback when user skips the button)
    if context.user_data.get('awaiting') != 'reseller_upload' and not (context.user_data.get('reseller_payment') or context.user_data.get('reseller_intent')):
        return ConversationHandler.END
    user_id = update.effective_user.id
    pay = context.user_data.get('reseller_payment') or {}
    method = pay.get('method') or 'card'
    amount = int(pay.get('amount') or 0)
    if amount <= 0:
        settings = {s['key']: s['value'] for s in query_db("SELECT key, value FROM settings")} or {}
        amount = int((settings.get('reseller_fee_toman') or '200000') or 200000)
    file_id = None
    caption_extra = ''
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    elif update.message.text:
        caption_extra = update.message.text
    rr_id = execute_db(
        "INSERT INTO reseller_requests (user_id, amount, method, status, created_at, screenshot_file_id, meta) VALUES (?, ?, ?, 'pending', ?, ?, ?)",
        (user_id, int(amount), method, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file_id, caption_extra[:500])
    )
    
    # Get full user info from Telegram API
    try:
        telegram_user = await context.bot.get_chat(user_id)
        first_name = telegram_user.first_name or 'نامشخص'
        last_name = telegram_user.last_name or ''
        username = telegram_user.username or None
        full_name = f"{first_name} {last_name}".strip()
        user_mention = f"@{username}" if username else full_name
    except Exception:
        user_info_db = query_db("SELECT first_name FROM users WHERE user_id = ?", (user_id,), one=True)
        first_name = user_info_db.get('first_name', 'نامشخص') if user_info_db else 'نامشخص'
        full_name = first_name
        username = None
        user_mention = first_name
    
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("\u2705 تایید نمایندگی", callback_data=f"reseller_approve_{rr_id}"), InlineKeyboardButton("\u274C رد", callback_data=f"reseller_reject_{rr_id}")]])
    caption = (
        f"💵 <b>درخواست دریافت نمایندگی ({'Card' if method=='card' else 'Crypto'})</b>\n\n"
        f"👤 <b>کاربر:</b> {user_mention}\n"
        f"📝 <b>نام:</b> {full_name}\n"
        f"🔖 <b>یوزرنیم تلگرام:</b> {'@' + username if username else '-'}\n"
        f"🆔 <b>یوزر آیدی:</b> <code>{user_id}</code>\n"
        f"💰 <b>مبلغ:</b> {int(amount):,} تومان\n"
        f"🕐 <b>زمان:</b> <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
    )
    if file_id:
        await notify_admins(context.bot, photo=file_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await notify_admins(context.bot, text=f"{caption}\n\n{caption_extra}", parse_mode=ParseMode.HTML, reply_markup=kb)
    await update.message.reply_text("درخواست نمایندگی ثبت شد و پس از تایید ادمین فعال می‌شود.")
    context.user_data.pop('awaiting', None)
    context.user_data.pop('reseller_payment', None)
    context.user_data.pop('reseller_intent', None)
    return ConversationHandler.END


async def composite_upload_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    flag = context.user_data.get('awaiting')
    # Accept wallet uploads even if user skipped the explicit button, as long as amount/method exist
    if flag == 'wallet_upload' or (
        (context.user_data.get('wallet_topup_amount') and context.user_data.get('wallet_method') in ('card','crypto'))
    ):
        # Ensure awaiting is set so downstream logic proceeds
        context.user_data['awaiting'] = 'wallet_upload'
        return await wallet_upload_router(update, context)
    # Accept reseller uploads on intent/pay context too
    if flag == 'reseller_upload' or context.user_data.get('reseller_payment') or context.user_data.get('reseller_intent'):
        context.user_data['awaiting'] = 'reseller_upload'
        return await reseller_upload_router(update, context)
    return ConversationHandler.END

async def wallet_upload_start_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['awaiting'] = 'wallet_upload'
    context.user_data['wallet_method'] = 'card'
    await query.message.edit_text("رسید/اسکرین‌شات یا هر پیامی مرتبط با پرداخت را ارسال کنید تا برای ادمین ارسال شود.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت", callback_data='wallet_menu')]]))
    return WALLET_AWAIT_CARD_SCREENSHOT


async def wallet_upload_start_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['awaiting'] = 'wallet_upload'
    context.user_data['wallet_method'] = 'crypto'
    await query.message.edit_text("رسید/اسکرین‌شات یا هر پیامی مرتبط با پرداخت را ارسال کنید تا برای ادمین ارسال شود.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 بازگشت", callback_data='wallet_menu')]]))
    return WALLET_AWAIT_CRYPTO_SCREENSHOT


async def wallet_upload_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get('awaiting') != 'wallet_upload':
        # Soft-accept if user has amount+method in context
        if not (context.user_data.get('wallet_topup_amount') and (context.user_data.get('wallet_method') in ('card','crypto'))):
            return ConversationHandler.END
        context.user_data['awaiting'] = 'wallet_upload'
    user_id = update.effective_user.id
    amount = context.user_data.get('wallet_topup_amount')
    method = context.user_data.get('wallet_method') or 'card'
    if not amount or method not in ('card','crypto'):
        try:
            await update.message.reply_text("برای ثبت شارژ، ابتدا مبلغ را انتخاب کنید و روش پرداخت را مشخص کنید.")
        except Exception:
            pass
        return ConversationHandler.END
    file_id = None
    sent_as = 'text'
    caption_extra = ''
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        sent_as = 'photo'
    elif update.message.document:
        file_id = update.message.document.file_id
        sent_as = 'document'
    elif getattr(update.message, 'video', None):
        file_id = update.message.video.file_id
        sent_as = 'video'
    elif getattr(update.message, 'voice', None):
        file_id = update.message.voice.file_id
        sent_as = 'voice'
    elif getattr(update.message, 'audio', None):
        file_id = update.message.audio.file_id
        sent_as = 'audio'
    elif update.message.text:
        caption_extra = update.message.text
    tx_id = execute_db(
        "INSERT INTO wallet_transactions (user_id, amount, direction, method, status, created_at, screenshot_file_id, meta) VALUES (?, ?, 'credit', ?, 'pending', ?, ?, ?)",
        (user_id, int(amount), method, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file_id, caption_extra[:500])
    )
    # notify admin accordingly - get full user info from Telegram API
    try:
        telegram_user = await context.bot.get_chat(user_id)
        first_name = telegram_user.first_name or 'نامشخص'
        last_name = telegram_user.last_name or ''
        username = telegram_user.username or None
        full_name = f"{first_name} {last_name}".strip()
        user_mention = f"@{username}" if username else full_name
    except Exception:
        user_info_db = query_db("SELECT first_name FROM users WHERE user_id = ?", (user_id,), one=True)
        first_name = user_info_db.get('first_name', 'نامشخص') if user_info_db else 'نامشخص'
        full_name = first_name
        username = None
        user_mention = first_name
    
    caption = (
        f"💸 <b>درخواست شارژ کیف پول ({'Card' if method=='card' else 'Crypto'})</b>\n\n"
        f"👤 <b>کاربر:</b> {user_mention}\n"
        f"📝 <b>نام:</b> {full_name}\n"
        f"🔖 <b>یوزرنیم تلگرام:</b> {'@' + username if username else '-'}\n"
        f"🆔 <b>یوزر آیدی:</b> <code>{user_id}</code>\n"
        f"💰 <b>مبلغ:</b> {int(amount):,} تومان\n"
        f"🕐 <b>زمان:</b> <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("\u2705 تایید", callback_data=f"wallet_tx_approve_{tx_id}"), InlineKeyboardButton("\u274C رد", callback_data=f"wallet_tx_reject_{tx_id}")],[InlineKeyboardButton("\U0001F4B8 منوی درخواست‌ها", callback_data="admin_wallet_tx_menu")]])
    if sent_as == 'photo' and file_id:
        await notify_admins(context.bot, photo=file_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    elif sent_as == 'document' and file_id:
        await notify_admins(context.bot, document=file_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    elif sent_as in ('video','voice','audio') and file_id:
        # Fallback: send as document if we can't stream it directly to admins
        await notify_admins(context.bot, document=file_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await notify_admins(context.bot, text=f"{caption}\n\n{caption_extra}", parse_mode=ParseMode.HTML, reply_markup=kb)
    await update.message.reply_text("درخواست شارژ ثبت شد و پس از تایید ادمین اعمال می‌شود.")
    context.user_data.pop('awaiting', None)
    context.user_data.pop('wallet_method', None)
    context.user_data.pop('wallet_topup_amount', None)
    clear_flow(context)
    return ConversationHandler.END


async def wallet_topup_custom_amount_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks the user to enter a custom top-up amount."""
    query = update.callback_query
    await query.answer()

    method = query.data.split('_')[-2] # e.g., 'card', 'crypto', 'gateway'
    context.user_data['wallet_method'] = method

    await query.edit_message_text("لطفاً مبلغ مورد نظر خود را به تومان وارد کنید:")

    if method == 'card':
        return WALLET_AWAIT_CUSTOM_AMOUNT_CARD
    elif method == 'crypto':
        return WALLET_AWAIT_CUSTOM_AMOUNT_CRYPTO
    elif method == 'gateway':
        return WALLET_AWAIT_CUSTOM_AMOUNT_GATEWAY
    
    return ConversationHandler.END


async def wallet_topup_custom_amount_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives and validates the custom top-up amount."""
    amount_str = _normalize_amount_text(update.message.text)
    try:
        amount = int(amount_str)
        if amount <= 0:
            raise ValueError("Amount must be positive.")
    except (ValueError, TypeError):
        await update.message.reply_text("مبلغ وارد شده نامعتبر است. لطفاً یک عدد صحیح مثبت وارد کنید.")
        # Re-prompt by returning the same state
        method = context.user_data.get('wallet_method')
        if method == 'card':
            return WALLET_AWAIT_CUSTOM_AMOUNT_CARD
        elif method == 'crypto':
            return WALLET_AWAIT_CUSTOM_AMOUNT_CRYPTO
        elif method == 'gateway':
            return WALLET_AWAIT_CUSTOM_AMOUNT_GATEWAY
        return ConversationHandler.END

    context.user_data['wallet_topup_amount'] = amount

    # Now, route to the correct handler based on the method
    method = context.user_data.get('wallet_method')
    if method == 'card':
        context.user_data['awaiting'] = 'wallet_upload'
        cards = query_db("SELECT card_number, holder_name FROM cards")
        if not cards:
            await update.message.reply_text("خطا: هیچ کارت بانکی در سیستم ثبت نشده است.")
            return ConversationHandler.END
        lines = [f"\U0001F4B0 مبلغ: {amount:,} تومان", "\nبه یکی از کارت‌های زیر واریز کنید و سپس روی دکمه زیر بزنید و رسید را ارسال کنید:"]
        for c in cards:
            lines.append(f"- {c['holder_name']}\n{ltr_code(c['card_number'])}")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("ارسال اسکرین‌شات", callback_data='wallet_upload_start_card')], [InlineKeyboardButton("\U0001F519 بازگشت", callback_data='wallet_menu')]])
        await update.message.reply_text("\n\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
        context.user_data.pop('wallet_prompt_msg_id', None)
        return WALLET_AWAIT_CARD_SCREENSHOT
    elif method == 'crypto':
        context.user_data['awaiting'] = 'wallet_upload'
        wallets = query_db("SELECT asset, chain, address, memo FROM wallets ORDER BY id DESC")
        if not wallets:
            await update.message.reply_text("هیچ ولتی ثبت نشده است. لطفا بعدا تلاش کنید.")
            return ConversationHandler.END
        lines = ["لطفا مبلغ معادل را به یکی از ولت‌های زیر واریز کرده و سپس روی دکمه زیر بزنید و رسید را ارسال کنید:"]
        for w in wallets:
            memo = f"\nMEMO: {w['memo']}" if w.get('memo') else ''
            lines.append(f"- {w['asset']} ({w['chain']}):\n{w['address']}{memo}")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("ارسال اسکرین‌شات", callback_data='wallet_upload_start_crypto')], [InlineKeyboardButton("\U0001F519 بازگشت", callback_data='wallet_menu')]])
        await update.message.reply_text("\n\n".join(lines), reply_markup=kb)
        context.user_data.pop('wallet_prompt_msg_id', None)
        return WALLET_AWAIT_CRYPTO_SCREENSHOT
    elif method == 'gateway':
        # This one is a bit different, it needs to be routed to show the gateway message
        dummy = type('obj', (object,), {'message': update.message})
        return await _wallet_show_gateway_message(dummy, context)
    
    return ConversationHandler.END

async def wallet_topup_card_receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # This path is now disabled and logic is moved to select_amount/custom_amount handlers
    if update.callback_query:
        await update.callback_query.answer("این دکمه غیرفعال است.", show_alert=True)
    return ConversationHandler.END

async def purchase_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # ... existing code ...
    if payment_method == 'wallet':
        # Check balance
        user_id = update.effective_user.id
        balance = query_db("SELECT balance FROM user_wallets WHERE user_id = ?", (user_id,), one=True)
        if not balance or balance['balance'] < plan['price']:
            await query.answer("موجودی کیف پول شما کافی نیست.", show_alert=True)
            return PURCHASE_AWAIT_PAYMENT_METHOD

        # Create order first, but keep it in a special pending state
        order_id = execute_db(
            "INSERT INTO orders (user_id, plan_id, status, final_price, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, plan['id'], 'pending_wallet', plan['price'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        if not order_id:
            await query.edit_message_text("خطا در ثبت سفارش. لطفا دوباره تلاش کنید.")
            return ConversationHandler.END

        # Attempt auto-approval
        auto_approved = await auto_approve_wallet_order(order_id, context, update.effective_user)

        if auto_approved:
            # On success, now we can deduct balance and log the transaction
            new_balance = balance['balance'] - plan['price']
            execute_db("UPDATE user_wallets SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            execute_db(
                "INSERT INTO wallet_transactions (user_id, amount, direction, method, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, -plan['price'], 'debit', 'wallet', 'approved', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            await query.edit_message_text(
                f"🎉 <b>پرداخت با موفقیت انجام شد!</b>\n\n"
                f"✅ سرویس شما به صورت خودکار ایجاد و ارسال شد\n"
                f"💰 موجودی جدید: {new_balance:,} تومان",
                parse_mode=ParseMode.HTML
            )
            # Send interactive menu and main menu automatically
            try:
                keyboard = [
                    [InlineKeyboardButton("📱 سرویس‌های من", callback_data='my_services')],
                    [InlineKeyboardButton("📚 آموزش اتصال", callback_data='tutorials_menu'), InlineKeyboardButton("💬 پشتیبانی", callback_data='support_menu')],
                    [InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')]
                ]
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "✨ <b>سرویس شما آماده است!</b>\n\n"
                        "📦 لینک اشتراک و QR Code برای شما ارسال شد\n"
                        "📚 برای اتصال، دکمه «آموزش اتصال» را بزنید\n"
                        "🔄 وضعیت سرویس را از «سرویس‌های من» ببینید"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
                
                # Send main menu automatically after 2 seconds
                import asyncio
                await asyncio.sleep(2)
                
                # Import and call start_command
                from .common import start_command
                class FakeUser:
                    def __init__(self, user_id, first_name=""):
                        self.id = user_id
                        self.first_name = first_name
                        self.username = None
                        self.is_bot = False
                
                class FakeMessage:
                    def __init__(self, chat_id, user):
                        self.chat_id = chat_id
                        self.from_user = user
                        self.text = "/start"
                        
                    async def reply_text(self, text, **kwargs):
                        await context.bot.send_message(chat_id=self.chat_id, text=text, **kwargs)
                
                fake_user = FakeUser(user_id)
                fake_message = FakeMessage(user_id, fake_user)
                
                fake_update = type('obj', (object,), {
                    'effective_user': fake_user,
                    'message': fake_message,
                    'callback_query': None
                })()
                
                await start_command(fake_update, context)
                
            except Exception:
                pass
        else:
            # On failure, notify admin for manual approval.
            # The order is already in 'pending_wallet' state.
            await query.edit_message_text(
                f"پرداخت شما به مبلغ {plan['price']:,} تومان رزرو شد. "
                f"در حال حاضر امکان ساخت خودکار سرویس وجود ندارد. سفارش شما برای تایید به ادمین ارسال شد و پس از تایید، مبلغ از حساب شما کسر خواهد شد."
            )
            admin_id = int(ADMIN_ID)
            plan_name = plan['name']
            user_info = update.effective_user.first_name
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ تایید و ساخت", callback_data=f"approve_auto_{order_id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{order_id}")
            ]])
            await context.bot.send_message(
                admin_id,
                f"⚠️ سفارش کیف پول نیازمند تایید دستی\n\n"
                f"کاربر: {user_info}\n"
                f"پلن: {plan_name}\n"
                f"مبلغ: {plan['price']:,} تومان",
                reply_markup=kb
            )
        
        clear_flow(context)
        return ConversationHandler.END

    if payment_method == 'gateway':
        settings = {s['key']: s['value'] for s in query_db("SELECT key, value FROM settings")}
        # ... existing code ...

async def purchase_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the purchase conversation, displaying available plans."""
    query = update.callback_query
    await query.answer()

    try:
        plans = query_db("SELECT * FROM plans")
        if not plans:
            await query.edit_message_text("در حال حاضر پلنی برای فروش وجود ندارد.")
            return ConversationHandler.END

        text = "لطفا یکی از پلن‌های زیر را انتخاب کنید:"
        keyboard = []
        for plan in plans:
            try:
                # Defensive check for price to prevent crashes on bad data
                price = int(plan.get('price', 0))
                plan_name = f"\U0001F4E6 {plan['name']} - {price:,} تومان"
                keyboard.append([InlineKeyboardButton(plan_name, callback_data=f"plan_{plan['id']}")])
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping plan with invalid price. Plan ID: {plan.get('id')}. Error: {e}")
                continue  # Skip this plan and log a warning

        if not keyboard:
            await query.edit_message_text("در حال حاضر پلنی برای فروش وجود ندارد (ممکن است اطلاعات پلن‌های موجود ناقص باشد).")
            return ConversationHandler.END

        keyboard.append([InlineKeyboardButton("بازگشت", callback_data="start_main")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return PURCHASE_AWAIT_PLAN
    except Exception as e:
        logger.error(f"Critical error in purchase_start: {e}", exc_info=True)


async def card_to_card_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show card-to-card payment information"""
    query = update.callback_query
    await query.answer()
    
    # Get card information from database
    cards = query_db("SELECT card_number, holder_name FROM cards")
    
    if not cards:
        text = (
            "💳 <b>اطلاعات کارت به کارت</b>\n\n"
            "❌ در حال حاضر اطلاعات کارتی ثبت نشده است.\n\n"
            "لطفاً با پشتیبانی تماس بگیرید."
        )
    else:
        text = "💳 <b>اطلاعات کارت به کارت</b>\n\n"
        for idx, card in enumerate(cards, 1):
            text += (
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔹 <b>کارت {idx}:</b>\n"
                f"📇 شماره کارت: <code>{card['card_number']}</code>\n"
                f"👤 به نام: {card['holder_name']}\n\n"
            )
        text += (
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ پس از واریز، حتماً اسکرین‌شات رسید را ارسال کنید."
        )
    
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data='start_main')]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
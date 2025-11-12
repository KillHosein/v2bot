"""
راهنمای نصب و اتصال اپلیکیشن
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
import qrcode
from io import BytesIO

from ..db import query_db
from telegram.ext import ConversationHandler
from ..helpers.back_buttons import BackButtons


# لینک‌های دانلود اپلیکیشن‌ها
APP_LINKS = {
    'v2rayng_android': 'https://github.com/2dust/v2rayNG/releases/latest',
    'v2rayn_windows': 'https://github.com/2dust/v2rayN/releases/latest',
    'streisand_ios': 'https://apps.apple.com/app/id6450534064',
    'fair_vpn_ios': 'https://apps.apple.com/app/id1533873488',
    'nekobox_android': 'https://github.com/MatsuriDayo/NekoBoxForAndroid/releases/latest',
}


async def show_app_guide_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی راهنمای اپلیکیشن"""
    query = update.callback_query
    if query:
        await query.answer()
    
    text = """
📱 <b>راهنمای اتصال</b>

برای استفاده از سرویس، ابتدا باید یک اپلیکیشن VPN نصب کنید.

🔽 <b>سیستم عامل خود را انتخاب کنید:</b>
"""
    
    keyboard = [
        [InlineKeyboardButton("🤖 Android", callback_data="app_guide_android")],
        [InlineKeyboardButton("🍎 iOS (آیفون)", callback_data="app_guide_ios")],
        [InlineKeyboardButton("🪟 Windows", callback_data="app_guide_windows")],
        [InlineKeyboardButton("🍏 macOS", callback_data="app_guide_macos")],
        [BackButtons.to_main()]
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
    
    return ConversationHandler.END


async def show_android_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنمای اندروید"""
    query = update.callback_query
    await query.answer()
    
    text = f"""
🤖 <b>راهنمای نصب برای Android</b>

━━━━━━━━━━━━━━━━━━━━━━━━

📲 <b>گام 1: دانلود اپلیکیشن</b>

پیشنهاد ما: <b>V2RayNG</b> (رایگان و بهترین)

🔗 دانلود مستقیم:
<a href="{APP_LINKS['v2rayng_android']}">کلیک کنید</a>

━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ <b>گام 2: اضافه کردن سرویس</b>

دو روش دارید:

<b>روش 1 - اسکن QR Code (آسان‌تر):</b>
1️⃣ روی دکمه QR Code بزنید
2️⃣ اپ را باز کنید
3️⃣ روی + در گوشه بالا بزنید
4️⃣ "Import config from QRcode" را بزنید
5️⃣ QR Code را اسکن کنید

<b>روش 2 - کپی لینک:</b>
1️⃣ روی دکمه "کپی لینک" بزنید
2️⃣ اپ را باز کنید
3️⃣ روی + در گوشه بالا بزنید
4️⃣ "Import config from clipboard" را بزنید

━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>گام 3: اتصال</b>

1️⃣ روی سرور کلیک کنید
2️⃣ دکمه اتصال (پایین صفحه) را بزنید
3️⃣ درخواست VPN را تایید کنید

✅ متصل شدید! اینترنت آزاد را لذت ببرید! 🌐

━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>نکات مهم:</b>
• حتماً "Auto Select" را فعال کنید
• اگر قطع شد، سرور دیگری امتحان کنید
• برای سرعت بهتر، پروتکل Reality را انتخاب کنید
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📥 دانلود V2RayNG", url=APP_LINKS['v2rayng_android']),
        ],
        [
            InlineKeyboardButton("📥 دانلود NekoBox", url=APP_LINKS['nekobox_android']),
        ],
        [BackButtons.custom("🔙 بازگشت", "app_guide_menu")]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    
    return ConversationHandler.END


async def show_ios_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنمای iOS"""
    query = update.callback_query
    await query.answer()
    
    text = f"""
🍎 <b>راهنمای نصب برای iOS (آیفون)</b>

━━━━━━━━━━━━━━━━━━━━━━━━

📲 <b>گام 1: دانلود اپلیکیشن</b>

پیشنهاد ما: <b>Streisand</b> (رایگان)

🔗 دانلود از App Store:
<a href="{APP_LINKS['streisand_ios']}">کلیک کنید</a>

یا اپ <b>Fair VPN</b>:
<a href="{APP_LINKS['fair_vpn_ios']}">کلیک کنید</a>

━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ <b>گام 2: اضافه کردن سرویس</b>

<b>روش 1 - اسکن QR Code:</b>
1️⃣ روی دکمه QR Code بزنید
2️⃣ اپ را باز کنید
3️⃣ روی + کلیک کنید
4️⃣ "Scan QR Code" را بزنید
5️⃣ QR Code را اسکن کنید

<b>روش 2 - کپی لینک:</b>
1️⃣ روی دکمه "کپی لینک" بزنید
2️⃣ اپ را باز کنید
3️⃣ روی + کلیک کنید
4️⃣ "Import from clipboard" را بزنید

━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>گام 3: اتصال</b>

1️⃣ روی سرور کلیک کنید
2️⃣ دکمه اتصال را بزنید
3️⃣ "Allow" را برای VPN بزنید

✅ متصل شدید! 🌐

━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>نکته مهم:</b>
اپ‌های iOS ممکن است برخی سرورها را پشتیبانی نکنند.
اگر مشکلی داشتید، با پشتیبانی تماس بگیرید.
"""
    
    keyboard = [
        [InlineKeyboardButton("📥 Streisand", url=APP_LINKS['streisand_ios'])],
        [InlineKeyboardButton("📥 Fair VPN", url=APP_LINKS['fair_vpn_ios'])],
        [BackButtons.custom("🔙 بازگشت", "app_guide_menu")]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    
    return ConversationHandler.END


async def show_windows_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنمای ویندوز"""
    query = update.callback_query
    await query.answer()
    
    text = f"""
🪟 <b>راهنمای نصب برای Windows</b>

━━━━━━━━━━━━━━━━━━━━━━━━

📲 <b>گام 1: دانلود اپلیکیشن</b>

پیشنهاد ما: <b>V2RayN</b>

🔗 دانلود مستقیم:
<a href="{APP_LINKS['v2rayn_windows']}">کلیک کنید</a>

فایل <code>v2rayN-windows-64.zip</code> را دانلود کنید.

━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ <b>گام 2: نصب</b>

1️⃣ فایل ZIP را Extract کنید
2️⃣ <code>v2rayN.exe</code> را اجرا کنید
3️⃣ ممکن است Windows Defender هشدار بدهد، "More info" و "Run anyway" را بزنید

━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ <b>گام 3: اضافه کردن سرویس</b>

<b>روش 1 - اسکن QR Code:</b>
1️⃣ روی آیکون برنامه (System Tray) کلیک راست کنید
2️⃣ "Import from QR Code from Screen" را بزنید
3️⃣ QR Code را روی صفحه نمایش دهید

<b>روش 2 - از Clipboard:</b>
1️⃣ لینک را کپی کنید
2️⃣ روی آیکون کلیک راست کنید
3️⃣ "Import from clipboard" را بزنید

━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>گام 4: اتصال</b>

1️⃣ روی سرور دوبار کلیک کنید
2️⃣ از منو "System Proxy" را روی "Auto Config" بگذارید
3️⃣ دکمه "Start" را بزنید

✅ متصل شدید! 🌐
"""
    
    keyboard = [
        [InlineKeyboardButton("📥 دانلود V2RayN", url=APP_LINKS['v2rayn_windows'])],
        [BackButtons.custom("🔙 بازگشت", "app_guide_menu")]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    
    return ConversationHandler.END


async def generate_qr_code(subscription_link: str) -> BytesIO:
    """ساخت QR Code برای لینک"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(subscription_link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    bio = BytesIO()
    bio.name = 'qrcode.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    
    return bio


async def send_service_qr(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int):
    """ارسال QR Code سرویس"""
    user_id = update.effective_user.id
    
    # دریافت اطلاعات سرویس
    service = query_db("""
        SELECT o.*, p.name as plan_name
        FROM orders o
        JOIN plans p ON o.plan_id = p.id
        WHERE o.id = ? AND o.user_id = ?
    """, (order_id, user_id), one=True)
    
    if not service or not service.get('config_link'):
        await update.callback_query.answer("❌ سرویس یافت نشد!", show_alert=True)
        return
    
    # ساخت QR Code
    qr_image = await generate_qr_code(service['config_link'])
    
    caption = f"""
📱 <b>QR Code سرویس {service['plan_name']}</b>

این QR Code را با اپلیکیشن VPN خود اسکن کنید.

💡 برای راهنمای نصب، از دکمه‌های زیر استفاده کنید.
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🤖 راهنمای Android", callback_data="app_guide_android"),
            InlineKeyboardButton("🍎 راهنمای iOS", callback_data="app_guide_ios")
        ],
        [InlineKeyboardButton("📋 کپی لینک", callback_data=f"copy_config_{order_id}")]
    ]
    
    await context.bot.send_photo(
        chat_id=user_id,
        photo=qr_image,
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

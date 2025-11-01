"""
Persian Texts with Professional Emojis
Centralized beautiful Persian messages for the bot
"""

class WelcomeTexts:
    """Welcome and greeting messages"""
    
    @staticmethod
    def main_welcome(name: str = "کاربر") -> str:
        return f"""
╔══════════════════════════════╗
║  🌟 خوش آمدید {name} عزیز  ║
╚══════════════════════════════╝

🔹 به ربات فروش VPN خوش آمدید
💎 سرویس پرسرعت و پایدار
🌍 دسترسی آزاد به اینترنت

┌─────────────────────────┐
│  ⚡ خدمات ما:            │
├─────────────────────────┤
│  ✅ کانفیگ اختصاصی      │
│  🚀 سرعت بالا           │
│  🛡 امنیت کامل          │
│  💰 قیمت مناسب          │
│  📞 پشتیبانی 24/7       │
└─────────────────────────┘

🎯 از منوی زیر یکی را انتخاب کنید:
"""

    @staticmethod
    def admin_welcome(name: str = "ادمین") -> str:
        return f"""
╔══════════════════════════════╗
║  👨‍💼 پنل مدیریت - {name}  ║
╚══════════════════════════════╝

🎛 کنترل کامل بر روی سیستم
📊 آمار و گزارش‌های دقیق
⚙️ تنظیمات پیشرفته

🔽 منوی مدیریت:
"""


class ServiceTexts:
    """Service related messages"""
    
    @staticmethod
    def no_services() -> str:
        return """
╔══════════════════════════════╗
║  📦 سرویس‌های من             ║
╚══════════════════════════════╝

😔 شما هنوز سرویسی ندارید!

💡 برای خرید سرویس جدید:
   👇 از دکمه زیر استفاده کنید
"""
    
    @staticmethod
    def service_active(name: str, days_left: int, traffic_left: str) -> str:
        status_emoji = "✅" if days_left > 7 else "⚠️"
        return f"""
╔══════════════════════════════╗
║  {status_emoji} سرویس فعال  ║
╚══════════════════════════════╝

📌 <b>نام سرویس:</b> {name}

⏰ <b>زمان باقیمانده:</b>
   🕐 {days_left} روز

📊 <b>حجم باقیمانده:</b>
   💾 {traffic_left}

┌─────────────────────────┐
│  عملیات:                │
└─────────────────────────┘
"""
    
    @staticmethod
    def service_expired() -> str:
        return """
╔══════════════════════════════╗
║  ❌ سرویس منقضی شده          ║
╚══════════════════════════════╝

😢 متأسفانه سرویس شما به پایان رسیده

💡 برای تمدید یا خرید جدید:
   👇 از دکمه‌های زیر استفاده کنید
"""


class WalletTexts:
    """Wallet related messages"""
    
    @staticmethod
    def wallet_balance(balance: int) -> str:
        return f"""
╔══════════════════════════════╗
║  💰 کیف پول من              ║
╚══════════════════════════════╝

💵 <b>موجودی فعلی:</b>
   💎 {balance:,} تومان

┌─────────────────────────┐
│  📌 راهنما:              │
├─────────────────────────┤
│  • افزایش موجودی         │
│  • پرداخت با کیف پول     │
│  • تاریخچه تراکنش‌ها      │
└─────────────────────────┘

🔽 یک گزینه را انتخاب کنید:
"""
    
    @staticmethod
    def wallet_low_balance(balance: int) -> str:
        return f"""
⚠️ <b>موجودی کم!</b>

💰 موجودی فعلی: <code>{balance:,}</code> تومان

💡 لطفاً کیف پول خود را شارژ کنید
"""


class PurchaseTexts:
    """Purchase flow messages"""
    
    @staticmethod
    def select_plan() -> str:
        return """
╔══════════════════════════════╗
║  🛒 خرید سرویس جدید          ║
╚══════════════════════════════╝

🎯 پلن مورد نظر خود را انتخاب کنید:

💡 <i>همه پلن‌ها شامل:</i>
   ✅ اتصال پرسرعت
   ✅ بدون محدودیت زمانی
   ✅ پشتیبانی رایگان
   ✅ تست رایگان برای خریدهای بالا
"""
    
    @staticmethod
    def plan_selected(name: str, price: int, days: int, traffic: str) -> str:
        return f"""
╔══════════════════════════════╗
║  ✨ مشخصات پلن انتخابی        ║
╚══════════════════════════════╝

📦 <b>نام پلن:</b> {name}

💰 <b>قیمت:</b> {price:,} تومان
⏱ <b>مدت زمان:</b> {days} روز
📊 <b>حجم:</b> {traffic}

┌─────────────────────────┐
│  ویژگی‌ها:               │
├─────────────────────────┤
│  ✅ پشتیبانی 24 ساعته    │
│  ✅ سرعت بالا            │
│  ✅ بدون قطعی           │
└─────────────────────────┘

🔽 روش پرداخت را انتخاب کنید:
"""
    
    @staticmethod
    def payment_pending() -> str:
        return """
╔══════════════════════════════╗
║  ⏳ در انتظار تأیید          ║
╚══════════════════════════════╝

✅ رسید شما ارسال شد!

⏰ پرداخت شما در صف بررسی است
👨‍💼 کارشناسان ما به زودی آن را تأیید می‌کنند

⚡ معمولاً کمتر از 10 دقیقه طول می‌کشد

📌 وضعیت سفارش خود را از:
   👉 سرویس‌های من بررسی کنید
"""


class SupportTexts:
    """Support and ticket messages"""
    
    @staticmethod
    def support_menu() -> str:
        return """
╔══════════════════════════════╗
║  💬 پشتیبانی                 ║
╚══════════════════════════════╝

👋 چطور می‌تونیم کمکتون کنیم؟

📌 <b>راه‌های ارتباطی:</b>

🎫 تیکت جدید
   • ثبت مشکل یا سوال
   • پاسخ سریع تیم پشتیبانی

📚 سوالات متداول
   • راهنمای استفاده
   • حل مشکلات رایج

🔽 یک گزینه را انتخاب کنید:
"""
    
    @staticmethod
    def ticket_created() -> str:
        return """
╔══════════════════════════════╗
║  ✅ تیکت ثبت شد              ║
╚══════════════════════════════╝

🎫 تیکت شما با موفقیت ثبت شد!

⏰ تیم پشتیبانی به زودی پاسخ می‌دهد
📱 از طریق همین ربات پاسخ دریافت می‌کنید

⚡ معمولاً ظرف 1-2 ساعت پاسخ داده می‌شود

🙏 از صبر و شکیبایی شما متشکریم
"""


class AdminTexts:
    """Admin panel messages"""
    
    @staticmethod
    def stats_overview(users: int, active: int, revenue_today: int, revenue_month: int) -> str:
        return f"""
╔══════════════════════════════╗
║  📊 آمار سیستم               ║
╚══════════════════════════════╝

👥 <b>کاربران:</b>
   • کل: <code>{users:,}</code> نفر
   • فعال: <code>{active:,}</code> نفر

💰 <b>درآمد:</b>
   • امروز: <code>{revenue_today:,}</code> تومان
   • این ماه: <code>{revenue_month:,}</code> تومان

━━━━━━━━━━━━━━━━━━━━━━
🔄 بروز شده: اکنون
"""
    
    @staticmethod
    def user_banned(user_id: int) -> str:
        return f"""
🚫 <b>کاربر مسدود شد</b>

👤 کاربر: <code>{user_id}</code>
✅ وضعیت: مسدود شده

⚠️ این کاربر دیگر نمی‌تواند از ربات استفاده کند
"""
    
    @staticmethod
    def user_unbanned(user_id: int) -> str:
        return f"""
✅ <b>کاربر آزاد شد</b>

👤 کاربر: <code>{user_id}</code>
🟢 وضعیت: فعال

💡 این کاربر می‌تواند دوباره از ربات استفاده کند
"""


class ErrorTexts:
    """Error messages"""
    
    @staticmethod
    def general_error() -> str:
        return """
❌ <b>خطا!</b>

😕 متأسفانه مشکلی پیش آمد

💡 لطفاً:
   • دوباره تلاش کنید
   • یا با پشتیبانی تماس بگیرید

🙏 از صبر شما متشکریم
"""
    
    @staticmethod
    def insufficient_balance(balance: int, required: int) -> str:
        return f"""
⚠️ <b>موجودی کافی نیست!</b>

💰 موجودی فعلی: <code>{balance:,}</code> تومان
💵 مبلغ مورد نیاز: <code>{required:,}</code> تومان
📉 کمبود: <code>{required - balance:,}</code> تومان

💡 لطفاً ابتدا کیف پول خود را شارژ کنید
"""
    
    @staticmethod
    def service_not_found() -> str:
        return """
❌ <b>سرویس یافت نشد!</b>

😕 این سرویس وجود ندارد یا حذف شده است

💡 از منوی سرویس‌های من بررسی کنید
"""


class SuccessTexts:
    """Success messages"""
    
    @staticmethod
    def payment_approved() -> str:
        return """
╔══════════════════════════════╗
║  ✅ پرداخت تأیید شد           ║
╚══════════════════════════════╝

🎉 تبریک! پرداخت شما تأیید شد

✨ سرویس شما فعال شده است
📱 از منوی «سرویس‌های من» مشاهده کنید

🙏 از خرید شما متشکریم
🌟 از سرویس لذت ببرید!
"""
    
    @staticmethod
    def service_renewed() -> str:
        return """
╔══════════════════════════════╗
║  ♻️ سرویس تمدید شد           ║
╚══════════════════════════════╝

✅ تمدید با موفقیت انجام شد!

⏰ زمان جدید سرویس اضافه شد
💎 از سرویس خود لذت ببرید

🙏 از اعتماد شما سپاسگزاریم
"""


# Helper functions for quick access
def welcome(name: str = "کاربر") -> str:
    """Quick welcome message"""
    return WelcomeTexts.main_welcome(name)


def admin_welcome(name: str = "ادمین") -> str:
    """Quick admin welcome"""
    return WelcomeTexts.admin_welcome(name)


def error() -> str:
    """Quick error message"""
    return ErrorTexts.general_error()


def success_payment() -> str:
    """Quick payment success"""
    return SuccessTexts.payment_approved()

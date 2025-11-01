"""
Internationalization (i18n) System
Multi-language support for the bot
"""
from typing import Dict, Optional
from .db import query_db, execute_db
from .cache_manager import cached

# Default translations
TRANSLATIONS = {
    'fa': {
        # Menu
        'menu_main': '🏠 منوی اصلی',
        'menu_services': '📱 سرویس‌های من',
        'menu_buy': '🛒 خرید سرویس',
        'menu_wallet': '💰 کیف پول',
        'menu_support': '💬 پشتیبانی',
        'menu_tutorials': '📚 آموزش‌ها',
        'menu_referral': '🎁 دعوت دوستان',
        
        # Common
        'back': '🔙 بازگشت',
        'cancel': '❌ لغو',
        'confirm': '✅ تأیید',
        'loading': '⏳ در حال بارگذاری...',
        'error': '❌ خطا',
        'success': '✅ موفقیت',
        
        # Services
        'service_active': 'فعال',
        'service_expired': 'منقضی شده',
        'service_pending': 'در انتظار',
        'renew_service': '🔄 تمدید سرویس',
        'delete_service': '🗑️ حذف سرویس',
        
        # Wallet
        'wallet_balance': 'موجودی: {amount} تومان',
        'wallet_topup': '💳 شارژ کیف پول',
        'wallet_history': '📊 تاریخچه تراکنش‌ها',
        
        # Support
        'ticket_create': '📝 ثبت تیکت جدید',
        'ticket_pending': 'در انتظار پاسخ',
        'ticket_closed': 'بسته شده',
        
        # Messages
        'welcome': '👋 سلام {name}!\n\nبه ربات ما خوش آمدید.',
        'no_services': 'شما هیچ سرویسی ندارید.',
        'payment_success': '✅ پرداخت با موفقیت انجام شد!',
        'payment_failed': '❌ پرداخت ناموفق بود.',
    },
    
    'en': {
        # Menu
        'menu_main': '🏠 Main Menu',
        'menu_services': '📱 My Services',
        'menu_buy': '🛒 Buy Service',
        'menu_wallet': '💰 Wallet',
        'menu_support': '💬 Support',
        'menu_tutorials': '📚 Tutorials',
        'menu_referral': '🎁 Invite Friends',
        
        # Common
        'back': '🔙 Back',
        'cancel': '❌ Cancel',
        'confirm': '✅ Confirm',
        'loading': '⏳ Loading...',
        'error': '❌ Error',
        'success': '✅ Success',
        
        # Services
        'service_active': 'Active',
        'service_expired': 'Expired',
        'service_pending': 'Pending',
        'renew_service': '🔄 Renew Service',
        'delete_service': '🗑️ Delete Service',
        
        # Wallet
        'wallet_balance': 'Balance: {amount} Toman',
        'wallet_topup': '💳 Top Up Wallet',
        'wallet_history': '📊 Transaction History',
        
        # Support
        'ticket_create': '📝 Create New Ticket',
        'ticket_pending': 'Awaiting Response',
        'ticket_closed': 'Closed',
        
        # Messages
        'welcome': '👋 Hello {name}!\n\nWelcome to our bot.',
        'no_services': 'You have no services.',
        'payment_success': '✅ Payment successful!',
        'payment_failed': '❌ Payment failed.',
    },
    
    'ar': {
        # Menu
        'menu_main': '🏠 القائمة الرئيسية',
        'menu_services': '📱 خدماتي',
        'menu_buy': '🛒 شراء خدمة',
        'menu_wallet': '💰 المحفظة',
        'menu_support': '💬 الدعم',
        'menu_tutorials': '📚 دروس',
        'menu_referral': '🎁 دعوة الأصدقاء',
        
        # Common
        'back': '🔙 رجوع',
        'cancel': '❌ إلغاء',
        'confirm': '✅ تأكيد',
        'loading': '⏳ جاري التحميل...',
        'error': '❌ خطأ',
        'success': '✅ نجح',
        
        # Services
        'service_active': 'نشط',
        'service_expired': 'منتهي',
        'service_pending': 'قيد الانتظار',
        'renew_service': '🔄 تجديد الخدمة',
        'delete_service': '🗑️ حذف الخدمة',
        
        # Wallet
        'wallet_balance': 'الرصيد: {amount} تومان',
        'wallet_topup': '💳 شحن المحفظة',
        'wallet_history': '📊 سجل المعاملات',
        
        # Support
        'ticket_create': '📝 إنشاء تذكرة جديدة',
        'ticket_pending': 'في انتظار الرد',
        'ticket_closed': 'مغلق',
        
        # Messages
        'welcome': '👋 مرحبا {name}!\n\nمرحبا بك في بوتنا.',
        'no_services': 'ليس لديك خدمات.',
        'payment_success': '✅ تم الدفع بنجاح!',
        'payment_failed': '❌ فشل الدفع.',
    }
}


class I18n:
    """Internationalization manager"""
    
    def __init__(self, default_lang: str = 'fa'):
        self.default_lang = default_lang
        self._load_custom_translations()
    
    def _load_custom_translations(self):
        """Load custom translations from database"""
        try:
            custom = query_db("SELECT lang, key, value FROM translations")
            for row in custom:
                lang = row['lang']
                key = row['key']
                value = row['value']
                
                if lang not in TRANSLATIONS:
                    TRANSLATIONS[lang] = {}
                TRANSLATIONS[lang][key] = value
        except Exception:
            pass  # Table might not exist yet
    
    @cached(ttl=600, key_prefix="i18n")
    def get_user_lang(self, user_id: int) -> str:
        """Get user's preferred language"""
        try:
            result = query_db(
                "SELECT language FROM user_preferences WHERE user_id = ?",
                (user_id,),
                one=True
            )
            return result['language'] if result else self.default_lang
        except Exception:
            return self.default_lang
    
    def set_user_lang(self, user_id: int, lang: str):
        """Set user's preferred language"""
        try:
            execute_db(
                """INSERT OR REPLACE INTO user_preferences (user_id, language)
                   VALUES (?, ?)""",
                (user_id, lang)
            )
            # Clear cache
            from .cache_manager import get_cache
            get_cache().delete(f"i18n:get_user_lang:{user_id}")
        except Exception as e:
            from .config import logger
            logger.error(f"Set user lang error: {e}")
    
    def t(self, key: str, lang: Optional[str] = None, **kwargs) -> str:
        """Translate a key"""
        if lang is None:
            lang = self.default_lang
        
        # Try to get translation for the language
        text = TRANSLATIONS.get(lang, {}).get(key)
        
        # Fallback to default language
        if text is None:
            text = TRANSLATIONS.get(self.default_lang, {}).get(key, key)
        
        # Format with kwargs
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get list of available languages"""
        return {
            'fa': '🇮🇷 فارسی',
            'en': '🇬🇧 English',
            'ar': '🇸🇦 العربية'
        }


# Global instance
_i18n = None

def get_i18n() -> I18n:
    """Get or create i18n instance"""
    global _i18n
    if _i18n is None:
        _i18n = I18n()
    return _i18n


def t(key: str, user_id: Optional[int] = None, **kwargs) -> str:
    """Quick translation function"""
    i18n = get_i18n()
    lang = i18n.get_user_lang(user_id) if user_id else None
    return i18n.t(key, lang, **kwargs)


# Database migration for translations
def setup_i18n_tables():
    """Create i18n tables"""
    try:
        from .db import execute_db
        
        # User preferences table
        execute_db("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                language TEXT NOT NULL DEFAULT 'fa',
                theme TEXT DEFAULT 'default',
                notifications_enabled INTEGER DEFAULT 1
            )
        """)
        
        # Custom translations table
        execute_db("""
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lang TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                UNIQUE(lang, key)
            )
        """)
        
        from .config import logger
        logger.info("✅ i18n tables created")
        
    except Exception as e:
        from .config import logger
        logger.error(f"i18n setup error: {e}")

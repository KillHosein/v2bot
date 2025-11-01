"""
Standardized Back Buttons Helper
Provides consistent back buttons across all admin handlers
"""
from telegram import InlineKeyboardButton


class BackButtons:
    """Helper class for creating consistent back buttons"""
    
    # Standard callback data
    ADMIN_MAIN = 'admin_main'
    START_MAIN = 'start_main'
    ADMIN_USERS = 'admin_users_menu'
    ADMIN_SETTINGS = 'admin_settings_manage'
    ADMIN_PANELS = 'admin_panels_menu'
    ADMIN_PLANS = 'admin_plan_manage'
    ADMIN_TICKETS = 'admin_tickets_menu'
    ADMIN_TUTORIALS = 'admin_tutorials_menu'
    ADMIN_MESSAGES = 'admin_messages_menu'
    ADMIN_STATS = 'admin_stats'
    ADMIN_WALLETS = 'admin_wallets_menu'
    ADMIN_CARDS = 'admin_cards_menu'
    ADMIN_DISCOUNT = 'admin_discount_menu'
    ADMIN_BROADCAST = 'admin_broadcast_menu'
    ADMIN_CRON = 'admin_cron_menu'
    ADMIN_RESELLER = 'admin_reseller_menu'
    ADMIN_ADVANCED_STATS = 'admin_advanced_stats'
    ADMIN_MONITORING = 'admin_monitoring_menu'
    
    @staticmethod
    def to_admin_main(text="🔙 بازگشت به پنل ادمین"):
        """Back to admin main menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_MAIN)
    
    @staticmethod
    def to_start(text="🏠 منوی اصلی"):
        """Back to user start menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.START_MAIN)
    
    @staticmethod
    def to_users(text="🔙 بازگشت"):
        """Back to users menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_USERS)
    
    @staticmethod
    def to_settings(text="🔙 بازگشت به تنظیمات"):
        """Back to settings menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_SETTINGS)
    
    @staticmethod
    def to_panels(text="🔙 بازگشت"):
        """Back to panels menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_PANELS)
    
    @staticmethod
    def to_plans(text="🔙 بازگشت"):
        """Back to plans menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_PLANS)
    
    @staticmethod
    def to_tickets(text="🔙 بازگشت"):
        """Back to tickets menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_TICKETS)
    
    @staticmethod
    def to_tutorials(text="🔙 بازگشت"):
        """Back to tutorials menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_TUTORIALS)
    
    @staticmethod
    def to_messages(text="🔙 بازگشت"):
        """Back to messages menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_MESSAGES)
    
    @staticmethod
    def to_stats(text="🔙 بازگشت"):
        """Back to stats menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_STATS)
    
    @staticmethod
    def to_wallets(text="🔙 بازگشت"):
        """Back to wallets menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_WALLETS)
    
    @staticmethod
    def to_cards(text="🔙 بازگشت"):
        """Back to cards menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_CARDS)
    
    @staticmethod
    def to_advanced_stats(text="🔙 بازگشت"):
        """Back to advanced stats"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_ADVANCED_STATS)
    
    @staticmethod
    def to_monitoring(text="🔙 بازگشت"):
        """Back to monitoring menu"""
        return InlineKeyboardButton(text, callback_data=BackButtons.ADMIN_MONITORING)
    
    @staticmethod
    def custom(text, callback_data):
        """Custom back button"""
        return InlineKeyboardButton(text, callback_data=callback_data)
    
    @staticmethod
    def refresh(callback_data, text="🔄 بروزرسانی"):
        """Refresh button"""
        return InlineKeyboardButton(text, callback_data=callback_data)
    
    @staticmethod
    def cancel(text="❌ لغو"):
        """Cancel button"""
        return InlineKeyboardButton(text, callback_data='cancel_flow')


# Quick access functions
def back_to_admin() -> InlineKeyboardButton:
    """Quick: Back to admin main"""
    return BackButtons.to_admin_main()


def back_to_start() -> InlineKeyboardButton:
    """Quick: Back to start"""
    return BackButtons.to_start()


def refresh_button(callback_data: str) -> InlineKeyboardButton:
    """Quick: Refresh button"""
    return BackButtons.refresh(callback_data)

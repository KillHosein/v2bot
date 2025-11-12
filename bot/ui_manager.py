"""
Advanced UI Manager with Beautiful Buttons and Text
Provides professional UI components and user-friendly messages
"""
from typing import List, Dict, Optional, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from enum import Enum


class ButtonStyle(Enum):
    """Button styling options"""
    PRIMARY = "primary"
    SUCCESS = "success"
    DANGER = "danger"
    WARNING = "warning"
    INFO = "info"
    PREMIUM = "premium"
    GLASS = "glass"


class UIManager:
    """Professional UI management system"""
    
    def __init__(self):
        # Beautiful emojis for different contexts
        self.emojis = {
            # Main menu
            'home': '🏠',
            'dashboard': '📊',
            'wallet': '💳',
            'shop': '🛍️',
            'services': '💎',
            'support': '🆘',
            'settings': '⚙️',
            'back': '◀️',
            'next': '▶️',
            'close': '❌',
            
            # Status
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'loading': '⏳',
            'done': '✨',
            'new': '🆕',
            'hot': '🔥',
            'premium': '👑',
            'vip': '💎',
            
            # Actions
            'buy': '🛒',
            'pay': '💰',
            'add': '➕',
            'remove': '➖',
            'edit': '✏️',
            'delete': '🗑️',
            'refresh': '🔄',
            'search': '🔍',
            'filter': '🔽',
            'sort': '↕️',
            
            # Features
            'speed': '⚡',
            'security': '🔒',
            'cloud': '☁️',
            'unlimited': '♾️',
            'gift': '🎁',
            'discount': '🏷️',
            'coin': '🪙',
            'star': '⭐',
            'trophy': '🏆',
            'medal': '🥇',
            
            # Animations
            'rocket': '🚀',
            'fire': '🔥',
            'sparkles': '✨',
            'rainbow': '🌈',
            'party': '🎉',
            'celebration': '🎊'
        }
        
        # Professional text templates
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load professional text templates"""
        return {
            'welcome': """
{emoji_sparkles} **خوش آمدید به {bot_name}** {emoji_sparkles}

سلام {user_name} عزیز! 👋

ما اینجا هستیم تا بهترین تجربه VPN رو برای شما فراهم کنیم.

🎯 **امکانات ویژه برای شما:**
• سرعت نور ⚡ با سرورهای اختصاصی
• امنیت نظامی 🔒 برای حفاظت از اطلاعات شما
• پشتیبانی 24/7 🆘 همیشه در کنار شما
• تضمین بازگشت وجه 💰 100% تضمینی

✨ **همین الان شروع کنید!**
            """,
            
            'main_menu': """
📱 **منوی اصلی** 

👤 {user_name} | 💰 موجودی: {balance} تومان

🔥 **دسترسی سریع:**
از دکمه‌های زیر استفاده کنید
            """,
            
            'purchase_intro': """
🛍️ **فروشگاه VPN پرمیوم**

🌟 **پلن‌های ویژه امروز:**
{plans}

💡 **نکته:** با خرید پلن‌های بلندمدت تا 50% تخفیف بگیرید!
            """,
            
            'wallet_info': """
💳 **کیف پول دیجیتال شما**

💰 **موجودی فعلی:** {balance} تومان
📊 **کل تراکنش‌ها:** {transactions}
🎁 **اعتبار هدیه:** {gift_credit} تومان

📈 **آمار کیف پول:**
• واریزی‌ها: {deposits} تومان
• مصرف شده: {spent} تومان
• صرفه‌جویی: {saved} تومان
            """,
            
            'service_active': """
✅ **سرویس {service_name} فعال است!**

🔗 **لینک اتصال شما:**
`{config_link}`

📱 **اتصال سریع:**
فقط روی لینک بالا کلیک کنید!

⏰ **اعتبار باقیمانده:** {days_left} روز
📊 **ترافیک مصرفی:** {traffic_used} از {traffic_total}

🚀 **سرعت سرور:** {speed} Mbps
🌍 **لوکیشن:** {location}
            """,
            
            'support_welcome': """
🆘 **مرکز پشتیبانی VIP**

👨‍💻 تیم ما 24/7 آماده پاسخگویی هستند!

📞 **راه‌های ارتباطی:**
• پشتیبانی آنلاین (پاسخ در 1 دقیقه)
• تیکت (پاسخ در 1 ساعت)
• تماس تلفنی (فقط VIP)

💬 **سوال دارید؟**
یکی از گزینه‌های زیر رو انتخاب کنید:
            """,
            
            'payment_success': """
🎉 **پرداخت موفق!** 🎉

✅ تبریک! پرداخت شما با موفقیت انجام شد.

📋 **جزئیات تراکنش:**
• مبلغ: {amount} تومان
• کد پیگیری: {transaction_id}
• زمان: {timestamp}

🎁 **هدیه ویژه:** 
{bonus_text}

⚡ **سرویس شما فعال شد!**
برای مشاهده جزئیات به بخش "سرویس‌های من" مراجعه کنید.
            """,
            
            'error_friendly': """
😔 **اوه! مشکلی پیش آمد**

متاسفیم که این اتفاق افتاد. تیم فنی ما در حال بررسی هستند.

🔧 **راه‌حل‌های پیشنهادی:**
• دوباره امتحان کنید
• اینترنت خود را چک کنید
• با پشتیبانی تماس بگیرید

💬 کد خطا: `{error_code}`
            """,
            
            'premium_offer': """
👑 **پیشنهاد ویژه VIP** 👑

🔥 **فقط برای شما!** 🔥

🎁 **بسته PREMIUM شامل:**
✓ سرعت 10 برابر ⚡
✓ سرور اختصاصی 🖥️
✓ IP ثابت 🔒
✓ پشتیبانی VIP 24/7 👨‍💻
✓ بدون محدودیت حجم ♾️
✓ 10 دستگاه همزمان 📱

💰 **قیمت ویژه:** ~~500,000~~ **299,000 تومان**
⏰ **فقط تا:** {deadline}

🚀 **همین الان فعال کنید!**
            """
        }
    
    def create_button(self, 
                     text: str,
                     callback_data: str,
                     style: ButtonStyle = ButtonStyle.PRIMARY,
                     emoji: Optional[str] = None) -> InlineKeyboardButton:
        """Create a beautiful styled button"""
        # Add style prefix
        if style == ButtonStyle.SUCCESS:
            prefix = "✅ "
        elif style == ButtonStyle.DANGER:
            prefix = "⛔ "
        elif style == ButtonStyle.WARNING:
            prefix = "⚠️ "
        elif style == ButtonStyle.INFO:
            prefix = "ℹ️ "
        elif style == ButtonStyle.PREMIUM:
            prefix = "👑 "
        elif style == ButtonStyle.GLASS:
            prefix = "💎 "
        else:
            prefix = ""
        
        # Add custom emoji if provided
        if emoji:
            if emoji in self.emojis:
                prefix = f"{self.emojis[emoji]} "
            else:
                prefix = f"{emoji} "
        
        # Create button with styled text
        button_text = f"{prefix}{text}"
        
        return InlineKeyboardButton(text=button_text, callback_data=callback_data)
    
    def create_menu(self, buttons: List[List[Tuple[str, str, Optional[str]]]]) -> InlineKeyboardMarkup:
        """
        Create a beautiful menu with styled buttons
        Each button is a tuple of (text, callback_data, emoji/style)
        """
        keyboard = []
        
        for row in buttons:
            button_row = []
            for button_data in row:
                text = button_data[0]
                callback = button_data[1]
                style_or_emoji = button_data[2] if len(button_data) > 2 else None
                
                # Determine if it's a style or emoji
                if style_or_emoji and style_or_emoji in self.emojis:
                    button = self.create_button(text, callback, emoji=style_or_emoji)
                else:
                    button = self.create_button(text, callback, emoji=style_or_emoji)
                
                button_row.append(button)
            
            keyboard.append(button_row)
        
        return InlineKeyboardMarkup(keyboard)
    
    def main_menu(self, user_name: str, balance: int = 0) -> InlineKeyboardMarkup:
        """Create beautiful main menu"""
        buttons = [
            [
                ("خرید VPN", "buy_vpn", "shop"),
                ("سرویس‌های من", "my_services", "services")
            ],
            [
                ("کیف پول", "wallet", "wallet"),
                ("امتیازات", "rewards", "star")
            ],
            [
                ("راهنما", "guide", "info"),
                ("پشتیبانی", "support", "support")
            ],
            [
                ("دعوت دوستان", "referral", "gift"),
                ("تنظیمات", "settings", "settings")
            ]
        ]
        
        return self.create_menu(buttons)
    
    def purchase_menu(self, plans: List[Dict]) -> InlineKeyboardMarkup:
        """Create beautiful purchase menu"""
        buttons = []
        
        for plan in plans:
            # Create attractive plan button
            if plan.get('is_popular'):
                emoji = "fire"
                badge = " 🔥 پرفروش"
            elif plan.get('is_new'):
                emoji = "new"
                badge = " 🆕 جدید"
            elif plan.get('discount'):
                emoji = "discount"
                badge = f" 🏷️ {plan['discount']}% تخفیف"
            else:
                emoji = "buy"
                badge = ""
            
            button_text = f"{plan['name']} - {plan['price']:,} تومان{badge}"
            buttons.append([(button_text, f"buy_plan_{plan['id']}", emoji)])
        
        # Add back button
        buttons.append([("بازگشت", "main_menu", "back")])
        
        return self.create_menu(buttons)
    
    def wallet_menu(self, balance: int) -> InlineKeyboardMarkup:
        """Create beautiful wallet menu"""
        buttons = [
            [
                ("💵 شارژ کیف پول", "wallet_charge", None),
                ("📊 تاریخچه", "wallet_history", None)
            ],
            [
                ("🎁 کد هدیه", "gift_code", None),
                ("💸 برداشت", "withdraw", None)
            ],
            [("🔙 بازگشت", "main_menu", None)]
        ]
        
        return self.create_menu(buttons)
    
    def format_text(self, 
                   template_name: str,
                   **kwargs) -> str:
        """Format text with template and variables"""
        template = self.templates.get(template_name, "")
        
        # Add default emojis to kwargs
        for key, value in self.emojis.items():
            kwargs[f'emoji_{key}'] = value
        
        # Format template with variables
        try:
            return template.format(**kwargs).strip()
        except KeyError as e:
            # Return template with missing keys as placeholders
            return template.strip()
    
    def success_message(self, title: str, description: str = "") -> str:
        """Create beautiful success message"""
        return f"""
✅ **{title}**

{description}

{self.emojis['sparkles']} عملیات با موفقیت انجام شد!
        """.strip()
    
    def error_message(self, title: str, description: str = "", error_code: str = "") -> str:
        """Create beautiful error message"""
        return self.format_text('error_friendly', error_code=error_code)
    
    def loading_message(self, action: str = "در حال پردازش") -> str:
        """Create loading message"""
        return f"""
{self.emojis['loading']} **{action}...**

لطفا چند لحظه صبر کنید...
        """.strip()
    
    def progress_bar(self, current: int, total: int, width: int = 10) -> str:
        """Create visual progress bar"""
        percentage = (current / total) * 100 if total > 0 else 0
        filled = int((percentage / 100) * width)
        empty = width - filled
        
        bar = "▓" * filled + "░" * empty
        
        return f"[{bar}] {percentage:.0f}%"
    
    def format_number(self, number: int, suffix: str = "") -> str:
        """Format number with thousand separators"""
        if number >= 1_000_000:
            return f"{number/1_000_000:.1f}M{suffix}"
        elif number >= 1_000:
            return f"{number/1_000:.1f}K{suffix}"
        else:
            return f"{number:,}{suffix}"
    
    def create_pagination(self, 
                         current_page: int,
                         total_pages: int,
                         callback_prefix: str) -> List[InlineKeyboardButton]:
        """Create pagination buttons"""
        buttons = []
        
        # Previous button
        if current_page > 1:
            buttons.append(
                InlineKeyboardButton(
                    "◀️ قبلی",
                    callback_data=f"{callback_prefix}_page_{current_page-1}"
                )
            )
        
        # Page indicator
        buttons.append(
            InlineKeyboardButton(
                f"📄 {current_page}/{total_pages}",
                callback_data="noop"
            )
        )
        
        # Next button
        if current_page < total_pages:
            buttons.append(
                InlineKeyboardButton(
                    "بعدی ▶️",
                    callback_data=f"{callback_prefix}_page_{current_page+1}"
                )
            )
        
        return buttons
    
    def create_confirm_dialog(self, 
                            message: str,
                            confirm_callback: str,
                            cancel_callback: str = "cancel") -> Tuple[str, InlineKeyboardMarkup]:
        """Create confirmation dialog"""
        text = f"""
⚠️ **تایید عملیات**

{message}

آیا مطمئن هستید؟
        """.strip()
        
        buttons = [
            [
                ("✅ بله، ادامه", confirm_callback, None),
                ("❌ خیر، لغو", cancel_callback, None)
            ]
        ]
        
        return text, self.create_menu(buttons)
    
    def create_rating_buttons(self, callback_prefix: str) -> InlineKeyboardMarkup:
        """Create star rating buttons"""
        buttons = [[]]
        
        for i in range(1, 6):
            stars = "⭐" * i
            buttons[0].append(
                InlineKeyboardButton(stars, callback_data=f"{callback_prefix}_rate_{i}")
            )
        
        return InlineKeyboardMarkup(buttons)


# Global UI manager
_ui_manager = None

def get_ui_manager() -> UIManager:
    """Get or create UI manager instance"""
    global _ui_manager
    if _ui_manager is None:
        _ui_manager = UIManager()
    return _ui_manager

"""
Language Selection and Preferences Handlers
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from ..i18n import get_i18n, t


async def language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    i18n = get_i18n()
    current_lang = i18n.get_user_lang(user_id)
    
    text = "🌍 <b>انتخاب زبان / Choose Language / اختر اللغة</b>\n\n"
    text += "لطفاً زبان خود را انتخاب کنید:\n"
    text += "Please select your language:\n"
    text += "يرجى اختيار لغتك:\n\n"
    text += f"زبان فعلی / Current: <b>{i18n.get_available_languages()[current_lang]}</b>"
    
    keyboard = []
    for lang_code, lang_name in i18n.get_available_languages().items():
        check = "✅ " if lang_code == current_lang else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{check}{lang_name}",
                callback_data=f'set_lang_{lang_code}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton(t('back', user_id), callback_data='start_main')])
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user's preferred language"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang_code = query.data.split('_')[-1]
    
    i18n = get_i18n()
    i18n.set_user_lang(user_id, lang_code)
    
    messages = {
        'fa': '✅ زبان با موفقیت به فارسی تغییر کرد.',
        'en': '✅ Language successfully changed to English.',
        'ar': '✅ تم تغيير اللغة بنجاح إلى العربية.'
    }
    
    keyboard = [[InlineKeyboardButton(t('menu_main', user_id), callback_data='start_main')]]
    
    await query.message.edit_text(
        messages.get(lang_code, messages['fa']),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def preferences_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user preferences menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    i18n = get_i18n()
    lang = i18n.get_user_lang(user_id)
    
    text = t('preferences_title', user_id) if 'preferences_title' in TRANSLATIONS.get(lang, {}) else "⚙️ تنظیمات"
    text += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += f"🌍 زبان: <b>{i18n.get_available_languages()[lang]}</b>\n"
    text += "🔔 اعلان‌ها: <b>فعال</b>\n"
    text += "🎨 تم: <b>پیش‌فرض</b>\n"
    
    keyboard = [
        [InlineKeyboardButton("🌍 تغییر زبان", callback_data='language_menu')],
        [InlineKeyboardButton("🔔 مدیریت اعلان‌ها", callback_data='notifications_settings')],
        [InlineKeyboardButton(t('back', user_id), callback_data='start_main')]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

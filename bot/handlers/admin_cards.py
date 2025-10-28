from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from ..db import query_db, execute_db
from ..states import ADMIN_CARDS_MENU, ADMIN_CARDS_AWAIT_NUMBER, ADMIN_CARDS_AWAIT_HOLDER
from ..helpers.tg import safe_edit_text as _safe_edit_text


async def admin_cards_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message_sender = None
    query = update.callback_query
    if query:
        await query.answer()
        message_sender = 'edit'
    elif update.message:
        message_sender = 'reply'
    if not message_sender:
        return ADMIN_CARDS_MENU

    cards = query_db("SELECT id, card_number, holder_name FROM cards")
    keyboard = []
    text = "\U0001F4B3 **مدیریت کارت‌های بانکی**\n\n"
    if cards:
        text += "لیست کارت‌های فعلی:"
        for card in cards:
            keyboard.append([
                InlineKeyboardButton(f"{card['card_number']}", callback_data=f"noop_{card['id']}"),
                InlineKeyboardButton("\u270F\uFE0F ویرایش", callback_data=f"card_edit_{card['id']}"),
                InlineKeyboardButton("\u274C حذف", callback_data=f"card_delete_{card['id']}")
            ])
    else:
        text += "هیچ کارتی ثبت نشده است."
    keyboard.append([InlineKeyboardButton("\u2795 افزودن کارت جدید", callback_data="card_add_start")])
    keyboard.append([InlineKeyboardButton("\U0001F519 بازگشت به تنظیمات", callback_data="admin_settings_manage")])

    if message_sender == 'edit':
        try:
            await _safe_edit_text(query.message, text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        except Exception:
            try:
                await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
            except Exception:
                pass
    else:
        try:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass
    return ADMIN_CARDS_MENU


async def admin_card_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    card_id = int(query.data.split('_')[-1])
    execute_db("DELETE FROM cards WHERE id = ?", (card_id,))
    await query.answer("کارت با موفقیت حذف شد.", show_alert=True)
    return await admin_cards_menu(update, context)


async def admin_card_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['new_card'] = {}
    text = "➕ **افزودن کارت جدید**\n\nلطفا شماره کارت ۱۶ رقمی را وارد کنید:"
    try:
        await _safe_edit_text(query.message, text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        try:
            await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass
    return ADMIN_CARDS_AWAIT_NUMBER


async def admin_card_add_receive_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # If editing number
    editing_id = context.user_data.get('editing_card_id')
    editing_field = context.user_data.get('editing_card_field')
    if editing_id and editing_field == 'number':
        new_number = update.message.text.strip()
        execute_db("UPDATE cards SET card_number = ? WHERE id = ?", (new_number, editing_id))
        context.user_data.pop('editing_card_id', None)
        context.user_data.pop('editing_card_field', None)
        
        # Build and send the updated cards menu
        cards = query_db("SELECT id, card_number, holder_name FROM cards")
        keyboard = []
        text = "\U0001F4B3 **مدیریت کارت‌های بانکی**\n\n"
        if cards:
            text += "✅ شماره کارت بروزرسانی شد.\n\nلیست کارت‌های فعلی:"
            for card in cards:
                keyboard.append([
                    InlineKeyboardButton(f"{card['card_number']}", callback_data=f"noop_{card['id']}"),
                    InlineKeyboardButton("\u270F\uFE0F ویرایش", callback_data=f"card_edit_{card['id']}"),
                    InlineKeyboardButton("\u274C حذف", callback_data=f"card_delete_{card['id']}")
                ])
        else:
            text += "هیچ کارتی ثبت نشده است."
        keyboard.append([InlineKeyboardButton("\u2795 افزودن کارت جدید", callback_data="card_add_start")])
        keyboard.append([InlineKeyboardButton("\U0001F519 بازگشت به تنظیمات", callback_data="admin_settings_manage")])
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        return ADMIN_CARDS_MENU
    # Else creation flow
    context.user_data['new_card'] = context.user_data.get('new_card') or {}
    context.user_data['new_card']['number'] = update.message.text.strip()
    await update.message.reply_text("✅ شماره کارت ثبت شد.\n\nحالا **نام و نام خانوادگی** صاحب کارت را وارد کنید:", parse_mode=ParseMode.MARKDOWN)
    return ADMIN_CARDS_AWAIT_HOLDER


async def admin_card_add_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # If editing holder name
    editing_id = context.user_data.get('editing_card_id')
    editing_field = context.user_data.get('editing_card_field')
    if editing_id and editing_field == 'holder':
        holder_name = (update.message.text or '').strip()
        execute_db("UPDATE cards SET holder_name = ? WHERE id = ?", (holder_name, editing_id))
        context.user_data.pop('editing_card_id', None)
        context.user_data.pop('editing_card_field', None)
        
        # Build and send the updated cards menu
        cards = query_db("SELECT id, card_number, holder_name FROM cards")
        keyboard = []
        text = "\U0001F4B3 **مدیریت کارت‌های بانکی**\n\n"
        if cards:
            text += "✅ نام دارنده بروزرسانی شد.\n\nلیست کارت‌های فعلی:"
            for card in cards:
                keyboard.append([
                    InlineKeyboardButton(f"{card['card_number']}", callback_data=f"noop_{card['id']}"),
                    InlineKeyboardButton("\u270F\uFE0F ویرایش", callback_data=f"card_edit_{card['id']}"),
                    InlineKeyboardButton("\u274C حذف", callback_data=f"card_delete_{card['id']}")
                ])
        else:
            text += "هیچ کارتی ثبت نشده است."
        keyboard.append([InlineKeyboardButton("\u2795 افزودن کارت جدید", callback_data="card_add_start")])
        keyboard.append([InlineKeyboardButton("\U0001F519 بازگشت به تنظیمات", callback_data="admin_settings_manage")])
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        return ADMIN_CARDS_MENU
    # Else creation flow
    card_number = context.user_data['new_card']['number']
    holder_name = update.message.text
    execute_db("INSERT INTO cards (card_number, holder_name) VALUES (?, ?)", (card_number, holder_name))
    context.user_data.clear()
    
    # Build and send the updated cards menu with success message
    cards = query_db("SELECT id, card_number, holder_name FROM cards")
    keyboard = []
    text = "\U0001F4B3 **مدیریت کارت‌های بانکی**\n\n"
    if cards:
        text += "✅ کارت جدید با موفقیت ثبت شد.\n\nلیست کارت‌های فعلی:"
        for card in cards:
            keyboard.append([
                InlineKeyboardButton(f"{card['card_number']}", callback_data=f"noop_{card['id']}"),
                InlineKeyboardButton("\u270F\uFE0F ویرایش", callback_data=f"card_edit_{card['id']}"),
                InlineKeyboardButton("\u274C حذف", callback_data=f"card_delete_{card['id']}")
            ])
    else:
        text += "هیچ کارتی ثبت نشده است."
    keyboard.append([InlineKeyboardButton("\u2795 افزودن کارت جدید", callback_data="card_add_start")])
    keyboard.append([InlineKeyboardButton("\U0001F519 بازگشت به تنظیمات", callback_data="admin_settings_manage")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    return ADMIN_CARDS_MENU


async def admin_card_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    card_id = int(query.data.split('_')[-1])
    card = query_db("SELECT id, card_number, holder_name FROM cards WHERE id = ?", (card_id,), one=True)
    if not card:
        await query.answer("کارت یافت نشد", show_alert=True)
        return ADMIN_CARDS_MENU
    context.user_data['editing_card_id'] = card_id
    text = (
        f"ویرایش کارت:\n\n"
        f"شماره فعلی: {card['card_number']}\n"
        f"نام دارنده: {card['holder_name']}\n\n"
        f"کدام مورد را می‌خواهید تغییر دهید؟"
    )
    kb = [
        [InlineKeyboardButton("شماره کارت", callback_data="card_edit_field_number"), InlineKeyboardButton("نام دارنده", callback_data="card_edit_field_holder")],
        [InlineKeyboardButton("\U0001F519 بازگشت", callback_data="admin_cards_menu")],
    ]
    try:
        await _safe_edit_text(query.message, text, reply_markup=InlineKeyboardMarkup(kb))
    except Exception:
        try:
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        except Exception:
            pass
    return ADMIN_CARDS_MENU


async def admin_card_edit_ask_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    field = query.data.split('_')[-1]  # number|holder
    if 'editing_card_id' not in context.user_data:
        await query.answer("جلسه ویرایش منقضی شده است.", show_alert=True)
        return ADMIN_CARDS_MENU
    context.user_data['editing_card_field'] = field
    if field == 'number':
        text = "✏️ **ویرایش شماره کارت**\n\nشماره کارت جدید (۱۶ رقمی) را وارد کنید:"
        try:
            await _safe_edit_text(query.message, text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            try:
                await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                pass
        return ADMIN_CARDS_AWAIT_NUMBER
    else:
        text = "✏️ **ویرایش نام دارنده**\n\nنام و نام خانوادگی جدید صاحب کارت را وارد کنید:"
        try:
            await _safe_edit_text(query.message, text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            try:
                await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                pass
        return ADMIN_CARDS_AWAIT_HOLDER
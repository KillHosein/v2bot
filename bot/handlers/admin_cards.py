from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from ..db import query_db, execute_db
from ..states import ADMIN_CARDS_MENU, ADMIN_CARDS_AWAIT_NUMBER, ADMIN_CARDS_AWAIT_HOLDER
from ..helpers.tg import safe_edit_text as _safe_edit_text
from ..config import logger


async def admin_cards_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"[CARDS_MENU] Called - update.callback_query={update.callback_query is not None}, update.message={update.message is not None}")
    message_sender = None
    query = update.callback_query
    if query:
        await query.answer()
        message_sender = 'edit'
        logger.info(f"[CARDS_MENU] Using edit mode - query.data={query.data}")
    elif update.message:
        message_sender = 'reply'
        logger.info(f"[CARDS_MENU] Using reply mode - message_id={update.message.message_id}")
    if not message_sender:
        logger.warning("[CARDS_MENU] No message_sender detected, returning ADMIN_CARDS_MENU")
        return ADMIN_CARDS_MENU

    cards = query_db("SELECT id, card_number, holder_name FROM cards")
    keyboard = []
    text = "\U0001F4B3 **مدیریت کارت‌های بانکی**\n\n"
    
    # Display success message if exists
    success_msg = context.user_data.pop('success_message', None)
    if success_msg:
        text += f"{success_msg}\n\n"
    
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
    keyboard.append([InlineKeyboardButton("\U0001F519 بازگشت", callback_data="admin_main")])

    if message_sender == 'edit':
        try:
            await _safe_edit_text(query.message, text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
            logger.info(f"[CARDS_MENU] Edited message successfully - message_id={query.message.message_id}")
        except Exception as e:
            logger.error(f"[CARDS_MENU] Edit failed: {e}, trying reply")
            try:
                msg = await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
                logger.info(f"[CARDS_MENU] Replied with new message - message_id={msg.message_id}")
            except Exception as e2:
                logger.error(f"[CARDS_MENU] Reply also failed: {e2}")
    else:
        try:
            msg = await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
            logger.info(f"[CARDS_MENU] Sent new message in reply mode - message_id={msg.message_id}")
        except Exception as e:
            logger.error(f"[CARDS_MENU] Send failed: {e}")
    
    logger.info(f"[CARDS_MENU] Returning state ADMIN_CARDS_MENU")
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
        # Save the message ID to delete later
        context.user_data['prompt_message_id'] = query.message.message_id
    except Exception:
        try:
            msg = await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            context.user_data['prompt_message_id'] = msg.message_id
        except Exception:
            pass
    return ADMIN_CARDS_AWAIT_NUMBER


async def admin_card_add_receive_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"[CARDS_RECEIVE_NUMBER] User input: {update.message.text[:20]}... - message_id={update.message.message_id}")
    # Clean up messages
    try:
        # Delete prompt message if exists
        prompt_msg_id = context.user_data.pop('prompt_message_id', None)
        if prompt_msg_id:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_msg_id)
            logger.info(f"[CARDS_RECEIVE_NUMBER] Deleted prompt message {prompt_msg_id}")
        # Delete user's input message
        await update.message.delete()
        logger.info(f"[CARDS_RECEIVE_NUMBER] Deleted user input message {update.message.message_id}")
    except Exception as e:
        logger.error(f"[CARDS_RECEIVE_NUMBER] Cleanup failed: {e}")
    
    # If editing number
    editing_id = context.user_data.get('editing_card_id')
    editing_field = context.user_data.get('editing_card_field')
    if editing_id and editing_field == 'number':
        new_number = update.message.text.strip()
        execute_db("UPDATE cards SET card_number = ? WHERE id = ?", (new_number, editing_id))
        # Clear editing state
        context.user_data.pop('editing_card_id', None)
        context.user_data.pop('editing_card_field', None)
        context.user_data.pop('prompt_message_id', None)
        logger.info(f"[CARDS_RECEIVE_NUMBER] Card number updated: {new_number[:4]}****")
        # Build and send cards menu directly in conversation context
        cards = query_db("SELECT id, card_number, holder_name FROM cards")
        keyboard = []
        text = "\U0001F4B3 **مدیریت کارت‌های بانکی**\n\n✅ شماره کارت بروزرسانی شد.\n\n"
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
        keyboard.append([InlineKeyboardButton("\U0001F519 بازگشت", callback_data="admin_main")])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        return ADMIN_CARDS_MENU
    # Else creation flow
    context.user_data['new_card'] = context.user_data.get('new_card') or {}
    context.user_data['new_card']['number'] = update.message.text.strip()
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ شماره کارت ثبت شد.\n\nحالا **نام و نام خانوادگی** صاحب کارت را وارد کنید:", parse_mode=ParseMode.MARKDOWN)
    context.user_data['prompt_message_id'] = msg.message_id
    return ADMIN_CARDS_AWAIT_HOLDER


async def admin_card_add_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Clean up messages
    try:
        # Delete prompt message if exists
        prompt_msg_id = context.user_data.pop('prompt_message_id', None)
        if prompt_msg_id:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_msg_id)
        # Delete user's input message
        await update.message.delete()
    except Exception:
        pass
    
    # If editing holder name
    editing_id = context.user_data.get('editing_card_id')
    editing_field = context.user_data.get('editing_card_field')
    if editing_id and editing_field == 'holder':
        holder_name = (update.message.text or '').strip()
        execute_db("UPDATE cards SET holder_name = ? WHERE id = ?", (holder_name, editing_id))
        # Clear editing state
        context.user_data.pop('editing_card_id', None)
        context.user_data.pop('editing_card_field', None)
        context.user_data.pop('prompt_message_id', None)
        # Build and send cards menu directly
        cards = query_db("SELECT id, card_number, holder_name FROM cards")
        keyboard = []
        text = "\U0001F4B3 **مدیریت کارت‌های بانکی**\n\n✅ نام دارنده بروزرسانی شد.\n\n"
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
        keyboard.append([InlineKeyboardButton("\U0001F519 بازگشت", callback_data="admin_main")])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        return ADMIN_CARDS_MENU
    # Else creation flow
    card_number = context.user_data['new_card']['number']
    holder_name = update.message.text.strip()
    execute_db("INSERT INTO cards (card_number, holder_name) VALUES (?, ?)", (card_number, holder_name))
    context.user_data.clear()
    # Build and send cards menu directly
    cards = query_db("SELECT id, card_number, holder_name FROM cards")
    keyboard = []
    text = "\U0001F4B3 **مدیریت کارت‌های بانکی**\n\n✅ کارت جدید با موفقیت ثبت شد.\n\n"
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
    keyboard.append([InlineKeyboardButton("\U0001F519 بازگشت", callback_data="admin_main")])
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
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
        [InlineKeyboardButton("\U0001F519 بازگشت", callback_data="admin_main")],
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
    field = query.data.split('_')[-1]  # number|holder
    if 'editing_card_id' not in context.user_data:
        await query.answer("جلسه ویرایش منقضی شده است.", show_alert=True)
        return ADMIN_CARDS_MENU
    await query.answer()
    context.user_data['editing_card_field'] = field
    if field == 'number':
        text = "✏️ **ویرایش شماره کارت**\n\nشماره کارت جدید (۱۶ رقمی) را وارد کنید:"
        try:
            await _safe_edit_text(query.message, text, parse_mode=ParseMode.MARKDOWN)
            context.user_data['prompt_message_id'] = query.message.message_id
        except Exception:
            try:
                msg = await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
                context.user_data['prompt_message_id'] = msg.message_id
            except Exception:
                pass
        return ADMIN_CARDS_AWAIT_NUMBER
    else:
        text = "✏️ **ویرایش نام دارنده**\n\nنام و نام خانوادگی جدید صاحب کارت را وارد کنید:"
        try:
            await _safe_edit_text(query.message, text, parse_mode=ParseMode.MARKDOWN)
            context.user_data['prompt_message_id'] = query.message.message_id
        except Exception:
            try:
                msg = await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
                context.user_data['prompt_message_id'] = msg.message_id
            except Exception:
                pass
        return ADMIN_CARDS_AWAIT_HOLDER
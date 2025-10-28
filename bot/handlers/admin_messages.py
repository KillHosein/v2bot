from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..db import query_db, execute_db, get_message_text
from ..states import (
    ADMIN_MESSAGES_MENU,
    ADMIN_MESSAGES_SELECT,
    ADMIN_MESSAGES_EDIT_TEXT,
    ADMIN_BUTTON_ADD_AWAIT_TEXT,
    ADMIN_BUTTON_ADD_AWAIT_TARGET,
    ADMIN_BUTTON_ADD_AWAIT_URL,
    ADMIN_BUTTON_ADD_AWAIT_ROW,
    ADMIN_BUTTON_ADD_AWAIT_COL,
    ADMIN_MESSAGES_ADD_AWAIT_NAME,
    ADMIN_MESSAGES_ADD_AWAIT_CONTENT,
)
from ..helpers.tg import safe_edit_text as _safe_edit_text

PAGE_SIZE = 10


def _md_escape(text: str) -> str:
    if not text:
        return ''
    return (
        text.replace('\\', r'\\')
            .replace('_', r'\_')
            .replace('*', r'\*')
            .replace('`', r'\`')
            .replace('[', r'\[')
            .replace(']', r'\]')
            .replace('(', r'\(')
            .replace(')', r'\)')
    )


async def admin_messages_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from ..config import logger
    import time
    
    query = update.callback_query
    await query.answer()
    
    start_time = time.time()
    logger.info(f"[admin_messages_menu] START - callback_id={query.id}, data={query.data}")
    
    # Prevent duplicate execution
    callback_id = f"{query.id}_{query.data}" if query else None
    last_callback = context.user_data.get('last_messages_callback')
    if callback_id and callback_id == last_callback:
        logger.warning(f"[admin_messages_menu] DUPLICATE PREVENTED - same callback_id={callback_id}")
        return ADMIN_MESSAGES_MENU
    if callback_id:
        context.user_data['last_messages_callback'] = callback_id
    
    page = 0
    if query and query.data.startswith('admin_messages_menu_page_'):
        try:
            page = int(query.data.split('_')[-1])
        except Exception:
            page = 0
    context.user_data['msg_page'] = page

    total = query_db("SELECT COUNT(*) AS c FROM messages", one=True) or {'c': 0}
    total = int(total.get('c') or 0)
    offset = page * PAGE_SIZE
    rows = query_db("SELECT message_name FROM messages ORDER BY message_name LIMIT ? OFFSET ?", (PAGE_SIZE, offset))

    keyboard = []
    if rows and len(rows) > 0:
        for m in rows:
            keyboard.append([InlineKeyboardButton(m['message_name'], callback_data=f"msg_select_{m['message_name']}")])
    else:
        keyboard.append([InlineKeyboardButton('❌ پیامی وجود ندارد', callback_data='noop')])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton('⬅️ قبلی', callback_data=f"admin_messages_menu_page_{page-1}"))
    if offset + PAGE_SIZE < total:
        nav.append(InlineKeyboardButton('بعدی ➡️', callback_data=f"admin_messages_menu_page_{page+1}"))
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton("➕ افزودن پیام جدید", callback_data="msg_add_start")])
    keyboard.append([InlineKeyboardButton("\U0001F519 بازگشت", callback_data="admin_main")])

    menu_text = get_message_text('admin_messages_menu', 'مدیریت پیام‌ها و صفحات:')
    
    logger.info(f"[admin_messages_menu] DATA - total={total}, rows={len(rows) if rows else 0}, keyboard_rows={len(keyboard)}")
    
    try:
        logger.info(f"[admin_messages_menu] EDITING MESSAGE - message_id={query.message.message_id}")
        result = await _safe_edit_text(query.message, menu_text, reply_markup=InlineKeyboardMarkup(keyboard))
        logger.info(f"[admin_messages_menu] EDIT SUCCESS - result={result is not None}")
    except Exception as e:
        logger.error(f"[admin_messages_menu] EDIT FAILED - error={e}")
        try:
            result = await query.message.reply_text(menu_text, reply_markup=InlineKeyboardMarkup(keyboard))
            logger.info(f"[admin_messages_menu] REPLY SUCCESS")
        except Exception as e2:
            logger.error(f"[admin_messages_menu] REPLY FAILED - error={e2}")
    
    elapsed = time.time() - start_time
    logger.info(f"[admin_messages_menu] END - elapsed={elapsed:.3f}s, returning ADMIN_MESSAGES_MENU")
    return ADMIN_MESSAGES_MENU


async def msg_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        await _safe_edit_text(query.message, "نام انگلیسی و منحصر به فرد برای پیام جدید وارد کنید (مثال: `about_us`):", parse_mode=ParseMode.MARKDOWN)
        context.user_data['prompt_message_id'] = query.message.message_id
    except Exception:
        try:
            msg = await query.message.reply_text("نام انگلیسی و منحصر به فرد برای پیام جدید وارد کنید (مثال: `about_us`):", parse_mode=ParseMode.MARKDOWN)
            context.user_data['prompt_message_id'] = msg.message_id
        except Exception:
            pass
    return ADMIN_MESSAGES_ADD_AWAIT_NAME


async def msg_add_receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Clean up previous prompt
    try:
        prompt_msg_id = context.user_data.pop('prompt_message_id', None)
        if prompt_msg_id:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_msg_id)
        await update.message.delete()
    except Exception:
        pass
    
    message_name = (update.message.text or '').strip()
    if not message_name.isascii() or ' ' in message_name:
        msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ خطا: نام باید انگلیسی و بدون فاصله باشد.")
        context.user_data['prompt_message_id'] = msg.message_id
        return ADMIN_MESSAGES_ADD_AWAIT_NAME
    if query_db("SELECT 1 FROM messages WHERE message_name = ?", (message_name,), one=True):
        msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ این نام قبلا وجود دارد. نام دیگری وارد کنید.")
        context.user_data['prompt_message_id'] = msg.message_id
        return ADMIN_MESSAGES_ADD_AWAIT_NAME
    context.user_data['new_message_name'] = message_name
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ نام ثبت شد.\n\nمحتوای پیام را ارسال کنید (متن/عکس/ویدیو/سند/صدا):")
    context.user_data['prompt_message_id'] = msg.message_id
    return ADMIN_MESSAGES_ADD_AWAIT_CONTENT


async def msg_add_receive_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Clean up previous messages
    try:
        prompt_msg_id = context.user_data.pop('prompt_message_id', None)
        if prompt_msg_id:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_msg_id)
        await update.message.delete()
    except Exception:
        pass
    
    message_name = context.user_data.get('new_message_name')
    if not message_name:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="ابتدا نام پیام را وارد کنید.")
        return ADMIN_MESSAGES_ADD_AWAIT_NAME
    file_id = None
    file_type = None
    text = None
    if update.message.text:
        text = update.message.text
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = 'photo'
        text = update.message.caption or ''
    elif update.message.video:
        file_id = update.message.video.file_id
        file_type = 'video'
        text = update.message.caption or ''
    elif update.message.document:
        file_id = update.message.document.file_id
        file_type = 'document'
        text = update.message.caption or ''
    elif update.message.voice:
        file_id = update.message.voice.file_id
        file_type = 'voice'
        text = update.message.caption or ''
    elif update.message.audio:
        file_id = update.message.audio.file_id
        file_type = 'audio'
        text = update.message.caption or ''
    execute_db(
        "INSERT INTO messages (message_name, text, file_id, file_type) VALUES (?, ?, ?, ?)",
        (message_name, text, file_id, file_type),
    )
    context.user_data.pop('new_message_name', None)
    
    # Send success message
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ پیام `{message_name}` با موفقیت ثبت شد.", parse_mode=ParseMode.MARKDOWN)
    
    # Return to paginated list
    fake_query = type('obj', (object,), {'data': f"admin_messages_menu_page_{context.user_data.get('msg_page', 0)}", 'message': update.message, 'answer': (lambda *args, **kwargs: None)})
    fake_update = type('obj', (object,), {'callback_query': fake_query, 'message': update.message})
    return await admin_messages_menu(fake_update, context)


async def admin_messages_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    message_name = query.data.replace('msg_select_', '')
    context.user_data['editing_message_name'] = message_name
    # Load preview
    row = query_db("SELECT text, file_id, file_type FROM messages WHERE message_name = ?", (message_name,), one=True) or {}
    preview = _md_escape((row.get('text') or '')[:500]) or 'متن خالی'
    keyboard = [
        [InlineKeyboardButton("✏️ ویرایش متن", callback_data="msg_action_edit_text")],
        [InlineKeyboardButton("🔗 ویرایش دکمه‌ها", callback_data="msg_action_edit_buttons")],
        [InlineKeyboardButton("🗑 حذف پیام", callback_data="msg_delete_current")],
        [InlineKeyboardButton("\U0001F519 بازگشت", callback_data=f"admin_messages_menu_page_{context.user_data.get('msg_page', 0)}")],
    ]
    try:
        await _safe_edit_text(query.message, f"پیام: `{message_name}`\n\nپیش‌نمایش:\n{preview}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    except Exception:
        try:
            await query.message.reply_text(f"پیام: `{message_name}`\n\nپیش‌نمایش:\n{preview}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass
    return ADMIN_MESSAGES_SELECT


async def admin_messages_edit_text_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    message_name = context.user_data['editing_message_name']
    try:
        await _safe_edit_text(query.message, f"✏️ **ویرایش متن پیام `{message_name}`**\n\nمتن جدید را ارسال کنید:", parse_mode=ParseMode.MARKDOWN)
        context.user_data['prompt_message_id'] = query.message.message_id
    except Exception:
        try:
            msg = await query.message.reply_text(f"✏️ **ویرایش متن پیام `{message_name}`**\n\nمتن جدید را ارسال کنید:", parse_mode=ParseMode.MARKDOWN)
            context.user_data['prompt_message_id'] = msg.message_id
        except Exception:
            pass
    return ADMIN_MESSAGES_EDIT_TEXT


async def admin_messages_edit_text_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Clean up messages
    try:
        prompt_msg_id = context.user_data.pop('prompt_message_id', None)
        if prompt_msg_id:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_msg_id)
        await update.message.delete()
    except Exception:
        pass
    
    message_name = context.user_data.get('editing_message_name')
    if not message_name:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="ابتدا یک پیام را انتخاب کنید.")
        return ADMIN_MESSAGES_MENU
    execute_db("UPDATE messages SET text = ? WHERE message_name = ?", (update.message.text, message_name))
    
    # Clear any remaining state
    context.user_data.pop('prompt_message_id', None)
    
    # Build and send the updated message select menu inline
    row = query_db("SELECT text, file_id, file_type FROM messages WHERE message_name = ?", (message_name,), one=True) or {}
    preview = _md_escape((row.get('text') or '')[:500]) or '\u0645\u062a\u0646 \u062e\u0627\u0644\u06cc'
    keyboard = [
        [InlineKeyboardButton("\u270f\ufe0f \u0648\u06cc\u0631\u0627\u06cc\u0634 \u0645\u062a\u0646", callback_data="msg_action_edit_text")],
        [InlineKeyboardButton("\ud83d\udd17 \u0648\u06cc\u0631\u0627\u06cc\u0634 \u062f\u06a9\u0645\u0647\u200c\u0647\u0627", callback_data="msg_action_edit_buttons")],
        [InlineKeyboardButton("\ud83d\uddd1 \u062d\u0630\u0641 \u067e\u06cc\u0627\u0645", callback_data="msg_delete_current")],
        [InlineKeyboardButton("\\U0001F519 \u0628\u0627\u0632\u06af\u0634\u062a", callback_data=f"admin_messages_menu_page_{context.user_data.get('msg_page', 0)}")],
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"\u2705 **\u0645\u062a\u0646 \u0628\u0631\u0648\u0632\u0631\u0633\u0627\u0646\u06cc \u0634\u062f**\n\n\u067e\u06cc\u0627\u0645: `{message_name}`\n\n\u067e\u06cc\u0634\u200c\u0646\u0645\u0627\u06cc\u0634:\n{preview}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    return ADMIN_MESSAGES_SELECT


async def admin_messages_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    message_name = context.user_data.get('editing_message_name')
    if not message_name:
        return await admin_messages_menu(update, context)
    execute_db("DELETE FROM messages WHERE message_name = ?", (message_name,))
    await _safe_edit_text(query.message, "✅ پیام حذف شد.")
    # Go back to list
    return await admin_messages_menu(update, context)


async def admin_buttons_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    message_name = context.user_data.get('editing_message_name')
    if not message_name:
        await query.answer("لطفاً ابتدا یک پیام را انتخاب کنید.", show_alert=True)
        return await admin_messages_menu(update, context)

    # Ensure default buttons exist for start_main so they show up for editing
    if message_name == 'start_main':
        existing_rows = query_db("SELECT target, row, col FROM buttons WHERE menu_name = ?", (message_name,)) or []
        existing_targets = {r.get('target') for r in existing_rows}

        # Desired layout: row1: [buy_config_main, get_free_config]; row2: [my_services, ...]
        buy_info = next(({'row': r['row'], 'col': r['col']} for r in existing_rows if r['target'] == 'buy_config_main'), None)
        trial_status = query_db("SELECT value FROM settings WHERE key = 'free_trial_status'", one=True)
        trial_enabled = bool(trial_status and (trial_status.get('value') == '1'))

        # Ensure buy button
        if 'buy_config_main' not in existing_targets:
            execute_db(
                "INSERT INTO buttons (menu_name, text, target, is_url, row, col) VALUES (?, ?, ?, ?, ?, ?)",
                (message_name, "\U0001F4E1 خرید کانفیگ", 'buy_config_main', 0, 1, 1),
            )
            buy_info = {'row': 1, 'col': 1}
        elif not buy_info:
            buy_info = {'row': 1, 'col': 1}

        # Ensure get_free_config next to buy; add or reposition
        gf_row = next(({'row': r['row'], 'col': r['col']} for r in existing_rows if r['target'] == 'get_free_config'), None)
        if trial_enabled:
            desired_col = 2 if int(buy_info['col']) == 1 else 1
            if 'get_free_config' not in existing_targets:
                execute_db(
                    "INSERT INTO buttons (menu_name, text, target, is_url, row, col) VALUES (?, ?, ?, ?, ?, ?)",
                    (message_name, "\U0001F381 دریافت تست", 'get_free_config', 0, int(buy_info['row']), desired_col),
                )
            elif not (gf_row and int(gf_row['row']) == int(buy_info['row']) and int(gf_row['col']) == desired_col):
                execute_db("UPDATE buttons SET row = ?, col = ? WHERE menu_name = ? AND target = ?", (int(buy_info['row']), desired_col, message_name, 'get_free_config'))

        # Ensure my_services under them (row+1). Add or reposition to first available col in that row.
        ms_row = next(({'row': r['row'], 'col': r['col']} for r in existing_rows if r['target'] == 'my_services'), None)
        target_row = int(buy_info['row']) + 1
        # Check occupancy on target_row
        row_occupancy = {(int(r['col'])) for r in (query_db("SELECT row, col FROM buttons WHERE menu_name = ? AND row = ?", (message_name, target_row)) or [])}
        desired_ms_col = 1 if 1 not in row_occupancy else 2
        if 'my_services' not in existing_targets:
            execute_db(
                "INSERT INTO buttons (menu_name, text, target, is_url, row, col) VALUES (?, ?, ?, ?, ?, ?)",
                (message_name, "\U0001F4DD سرویس‌های من", 'my_services', 0, target_row, desired_ms_col),
            )
        elif not (ms_row and int(ms_row['row']) == target_row and int(ms_row['col']) in (1, 2)):
            execute_db("UPDATE buttons SET row = ?, col = ? WHERE menu_name = ? AND target = ?", (target_row, desired_ms_col, message_name, 'my_services'))

        # Add other core buttons if missing (append in subsequent columns/rows)
        core_extras = [
            ("\U0001F4B3 کیف پول من", 'wallet_menu'),
            ("\U0001F4AC پشتیبانی", 'support_menu'),
            ("\U0001F4D6 آموزش‌ها", 'tutorials_menu'),
            ("\U0001F517 معرفی به دوستان", 'referral_menu'),
        ]
        max_row_row = query_db("SELECT COALESCE(MAX(row), 0) AS m FROM buttons WHERE menu_name = ?", (message_name,), one=True) or {'m': 0}
        next_row = int(max_row_row.get('m') or 0)
        col_cursor = 1
        for text, target in core_extras:
            if target in existing_targets:
                continue
            if col_cursor == 1:
                next_row += 1
            execute_db(
                "INSERT INTO buttons (menu_name, text, target, is_url, row, col) VALUES (?, ?, ?, ?, ?, ?)",
                (message_name, text, target, 0, next_row, col_cursor),
            )
            col_cursor = 2 if col_cursor == 1 else 1

    rows = query_db("SELECT id, text, row, col FROM buttons WHERE menu_name = ? ORDER BY row, col", (message_name,))
    keyboard = []
    if rows:
        for b in rows:
            keyboard.append([
                InlineKeyboardButton(f"{b['text']} (r{b['row']},c{b['col']})", callback_data=f"noop_{b['id']}"),
                InlineKeyboardButton("✏️", callback_data=f"btn_edit_{b['id']}"),
                InlineKeyboardButton("🗑", callback_data=f"btn_delete_{b['id']}")
            ])
    keyboard.append([InlineKeyboardButton("➕ افزودن دکمه جدید", callback_data="btn_add_new")])
    keyboard.append([InlineKeyboardButton("\U0001F519 بازگشت", callback_data=f"msg_select_{message_name}")])
    try:
        await _safe_edit_text(query.message, f"ویرایش دکمه‌های پیام `{message_name}`:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    except Exception:
        try:
            await query.message.reply_text(f"ویرایش دکمه‌های پیام `{message_name}`:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass
    return ADMIN_MESSAGES_SELECT


async def admin_button_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    button_id = int(query.data.replace("btn_delete_", ""))
    execute_db("DELETE FROM buttons WHERE id = ?", (button_id,))
    await query.answer("حذف شد", show_alert=True)
    return await admin_buttons_menu(update, context)


async def admin_button_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    button_id = int(query.data.replace("btn_edit_", ""))
    b = query_db("SELECT id, text, target, is_url, row, col, menu_name FROM buttons WHERE id = ?", (button_id,), one=True)
    if not b:
        await query.answer("دکمه یافت نشد", show_alert=True)
        return await admin_buttons_menu(update, context)
    context.user_data['editing_button_id'] = button_id
    context.user_data['editing_button_menu'] = b['menu_name']
    text = (
        f"ویرایش دکمه:\n\n"
        f"متن: {b['text']}\n"
        f"هدف: {b['target']}\n"
        f"نوع: {'URL' if int(b.get('is_url') or 0) == 1 else 'Callback'}\n"
        f"مکان: r{b['row']}, c{b['col']}\n\n"
        f"کدام مورد را تغییر می‌دهید؟"
    )
    kb = [
        [InlineKeyboardButton("متن", callback_data="btn_edit_field_text"), InlineKeyboardButton("هدف", callback_data="btn_edit_field_target")],
        [InlineKeyboardButton("نوع (URL/Callback)", callback_data="btn_edit_field_isurl")],
        [InlineKeyboardButton("سطر", callback_data="btn_edit_field_row"), InlineKeyboardButton("ستون", callback_data="btn_edit_field_col")],
        [InlineKeyboardButton("\U0001F519 بازگشت", callback_data="msg_action_edit_buttons")],
    ]
    try:
        await _safe_edit_text(query.message, text, reply_markup=InlineKeyboardMarkup(kb))
    except Exception:
        try:
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        except Exception:
            pass
    return ADMIN_MESSAGES_SELECT


async def admin_button_edit_ask_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    field = query.data.replace('btn_edit_field_', '')
    if not context.user_data.get('editing_button_id'):
        return await admin_buttons_menu(update, context)
    if field == 'isurl':
        bid = context.user_data['editing_button_id']
        kb = [
            [InlineKeyboardButton("URL", callback_data=f"btn_set_isurl_{bid}_1")],
            [InlineKeyboardButton("Callback", callback_data=f"btn_set_isurl_{bid}_0")],
            [InlineKeyboardButton("\U0001F519 بازگشت", callback_data="msg_action_edit_buttons")],
        ]
        try:
            await _safe_edit_text(query.message, "نوع دکمه را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
        except Exception:
            try:
                await query.message.reply_text("نوع دکمه را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
            except Exception:
                await query.answer("خطایی در ویرایش دکمه رخ داد.", show_alert=True)
                return await admin_buttons_menu(update, context)
    return ADMIN_MESSAGES_SELECT

    prompts = {
        'text': "متن جدید دکمه را ارسال کنید:",
        'target': "callback_data یا لینک URL جدید را ارسال کنید:",
        'row': "شماره سطر (۱ به بالا) را بفرستید:",
        'col': "شماره ستون (۱ به بالا) را بفرستید:",
    }
    context.user_data['editing_button_field'] = field
    await _safe_edit_text(query.message, prompts[field])
    return {
        'text': ADMIN_BUTTON_ADD_AWAIT_TEXT,
        'target': ADMIN_BUTTON_ADD_AWAIT_TARGET,
        'row': ADMIN_BUTTON_ADD_AWAIT_ROW,
        'col': ADMIN_BUTTON_ADD_AWAIT_COL,
    }[field]


async def admin_button_edit_set_is_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        _, _, _, bid, val = query.data.split('_')
        button_id = int(bid)
        is_url_val = int(val)
        execute_db("UPDATE buttons SET is_url = ? WHERE id = ?", (is_url_val, button_id))
        await query.answer("نوع دکمه بروزرسانی شد.", show_alert=True)
    except Exception:
        await query.answer("خطا در بروزرسانی نوع دکمه.", show_alert=True)
    return await admin_buttons_menu(update, context)


async def admin_button_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    context.user_data['new_button'] = {'menu_name': context.user_data['editing_message_name']}
    await _safe_edit_text(query.message, "لطفا متن دکمه جدید را وارد کنید:")
    return ADMIN_BUTTON_ADD_AWAIT_TEXT


async def admin_button_add_receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Edit-mode: update text
    if context.user_data.get('editing_button_id') and context.user_data.get('editing_button_field') == 'text':
        btn_id = context.user_data['editing_button_id']
        execute_db("UPDATE buttons SET text = ? WHERE id = ?", (update.message.text, btn_id))
        await update.message.reply_text("✅ متن دکمه بروزرسانی شد.")
        context.user_data.pop('editing_button_id', None)
        context.user_data.pop('editing_button_field', None)
        return await admin_buttons_menu(update, context)
    # Add-mode
    context.user_data['new_button']['text'] = update.message.text
    await update.message.reply_text("لطفا callback_data یا لینک URL را وارد کنید:")
    return ADMIN_BUTTON_ADD_AWAIT_TARGET


async def admin_button_add_receive_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Edit-mode: update target
    if context.user_data.get('editing_button_id') and context.user_data.get('editing_button_field') == 'target':
        btn_id = context.user_data['editing_button_id']
        execute_db("UPDATE buttons SET target = ? WHERE id = ?", (update.message.text, btn_id))
        await update.message.reply_text("✅ هدف دکمه بروزرسانی شد.")
        context.user_data.pop('editing_button_id', None)
        context.user_data.pop('editing_button_field', None)
        return await admin_buttons_menu(update, context)
    # Add-mode
    context.user_data['new_button']['target'] = update.message.text
    await update.message.reply_text(
        "نوع دکمه را مشخص کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("لینک URL", callback_data="btn_isurl_1")], [InlineKeyboardButton("Callback", callback_data="btn_isurl_0")]]),
    )
    return ADMIN_BUTTON_ADD_AWAIT_URL


async def admin_button_add_receive_is_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    context.user_data['new_button']['is_url'] = int(query.data.replace("btn_isurl_", ""))
    try:
        await _safe_edit_text(query.message, "شماره سطر (row) را وارد کنید (۱ به بالا):")
    except Exception:
        try:
            await query.message.reply_text("شماره سطر (row) را وارد کنید (۱ به بالا):")
        except Exception:
            pass
    return ADMIN_BUTTON_ADD_AWAIT_ROW


async def admin_button_add_receive_row(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Edit-mode: update row
    if context.user_data.get('editing_button_id') and context.user_data.get('editing_button_field') == 'row':
        try:
            new_row = int(update.message.text)
            btn_id = context.user_data['editing_button_id']
            execute_db("UPDATE buttons SET row = ? WHERE id = ?", (new_row, btn_id))
            await update.message.reply_text("✅ سطر دکمه بروزرسانی شد.")
            context.user_data.pop('editing_button_id', None)
            context.user_data.pop('editing_button_field', None)
            return await admin_buttons_menu(update, context)
        except Exception:
            await update.message.reply_text("مقدار نامعتبر است. یک عدد وارد کنید:")
            return ADMIN_BUTTON_ADD_AWAIT_ROW
    # Add-mode
    try:
        context.user_data['new_button']['row'] = int(update.message.text)
        await update.message.reply_text("شماره ستون (col) را وارد کنید (۱ به بالا):")
        return ADMIN_BUTTON_ADD_AWAIT_COL
    except Exception:
        await update.message.reply_text("مقدار نامعتبر است. یک عدد وارد کنید:")
        return ADMIN_BUTTON_ADD_AWAIT_ROW


async def admin_button_add_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Edit-mode: update col
    if context.user_data.get('editing_button_id') and context.user_data.get('editing_button_field') == 'col':
        try:
            new_col = int(update.message.text)
            btn_id = context.user_data['editing_button_id']
            execute_db("UPDATE buttons SET col = ? WHERE id = ?", (new_col, btn_id))
            await update.message.reply_text("✅ ستون دکمه بروزرسانی شد.")
            context.user_data.pop('editing_button_id', None)
            context.user_data.pop('editing_button_field', None)
            return await admin_buttons_menu(update, context)
        except Exception:
            await update.message.reply_text("مقدار نامعتبر است. دوباره وارد کنید:")
            return ADMIN_BUTTON_ADD_AWAIT_COL
    # Add-mode
    try:
        context.user_data['new_button']['col'] = int(update.message.text)
        b = context.user_data['new_button']
        execute_db("INSERT INTO buttons (menu_name, text, target, is_url, row, col) VALUES (?, ?, ?, ?, ?, ?)", (b['menu_name'], b['text'], b['target'], int(b.get('is_url') or 0), b['row'], b['col']))
        await update.message.reply_text("✅ دکمه اضافه شد.")
    except Exception:
        await update.message.reply_text("مقدار نامعتبر است. دوباره وارد کنید:")
        return ADMIN_BUTTON_ADD_AWAIT_COL
    context.user_data.pop('new_button', None)
    return await admin_buttons_menu(update, context)
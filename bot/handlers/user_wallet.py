"""
Handler های کیف پول کاربر - نسخه بهبود یافته
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..wallet_system import WalletSystem
from ..db import query_db, execute_db
from ..states import WALLET_AWAIT_AMOUNT_CARD, WALLET_AWAIT_SCREENSHOT
from telegram.ext import ConversationHandler
from ..helpers.back_buttons import BackButtons
from ..helpers.tg import ltr_code, notify_admins
from ..config import logger
from datetime import datetime


async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی اصلی کیف پول"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    
    # دریافت آمار کیف پول
    stats = WalletSystem.get_wallet_stats(user_id)
    
    balance = stats['balance']
    total_deposited = stats['total_deposited']
    total_spent = stats['total_spent']
    recent_tx = stats['recent_tx_count']
    
    # محاسبه درصد استفاده
    usage_percent = 0
    if total_deposited > 0:
        usage_percent = int((total_spent / total_deposited) * 100)
    
    text = f"""
💎 <b>کیف پول من</b>

━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>موجودی فعلی:</b>
   <code>{balance:,}</code> تومان

📊 <b>آمار کل:</b>
   📥 شارژ: {total_deposited:,} تومان
   📤 خرج: {total_spent:,} تومان
   📈 استفاده: {usage_percent}%

📅 <b>تراکنش‌ها (30 روز):</b> {recent_tx} مورد

━━━━━━━━━━━━━━━━━━━━━━━━

✨ <b>مزایای کیف پول:</b>

   ✅ خرید و تمدید فوری
   ✅ بدون نیاز به ارسال رسید
   ✅ امکان استفاده از امتیازات
   ✅ پرداخت سریع‌تر
   ✅ کاهش زمان انتظار

━━━━━━━━━━━━━━━━━━━━━━━━

🔽 <i>یک گزینه را انتخاب کنید:</i>
"""
    
    keyboard = [
        [
            InlineKeyboardButton("➕ شارژ کیف پول", callback_data='wallet_charge_menu'),
            InlineKeyboardButton("📜 تاریخچه", callback_data='wallet_history')
        ],
        [
            InlineKeyboardButton("🛍️ خرید با کیف پول", callback_data='buy_config_main'),
        ],
        [BackButtons.to_main()]
    ]
    
    if query:
        try:
            await query.message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception:
            await query.message.reply_text(
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


async def wallet_charge_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی انتخاب روش شارژ"""
    query = update.callback_query
    await query.answer()
    
    text = """
➕ <b>شارژ کیف پول</b>

━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>روش پرداخت را انتخاب کنید:</b>

<b>💳 کارت به کارت</b> (پیشنهاد ما)
   • سریع و آسان
   • بدون کارمزد اضافی
   • تایید حداکثر 10 دقیقه

━━━━━━━━━━━━━━━━━━━━━━━━

⚡ مبالغ پیشنهادی:
   • 50,000 تومان
   • 100,000 تومان
   • 200,000 تومان
   • 500,000 تومان
   • یا مبلغ دلخواه
"""
    
    keyboard = [
        [InlineKeyboardButton("💳 کارت به کارت", callback_data='wallet_topup_card')],
        [BackButtons.custom("🔙 بازگشت", "wallet_menu")]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END


def _amount_keyboard(method: str) -> InlineKeyboardMarkup:
    """کیبورد انتخاب مبلغ"""
    amounts = [50000, 100000, 200000, 500000, 1000000]
    keyboard = []
    row = []
    
    for amount in amounts:
        row.append(InlineKeyboardButton(
            f"{amount:,} تومان",
            callback_data=f'wallet_amt_{method}_{amount}'
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(
        "💵 مبلغ دلخواه",
        callback_data=f'wallet_amt_{method}_custom'
    )])
    keyboard.append([BackButtons.custom("🔙 بازگشت", "wallet_charge_menu")])
    
    return InlineKeyboardMarkup(keyboard)


async def wallet_topup_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فرآیند شارژ با کارت"""
    query = update.callback_query
    await query.answer()
    
    text = "💳 <b>شارژ با کارت به کارت</b>\n\n📌 مبلغ مورد نظر را انتخاب کنید:"
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=_amount_keyboard('card')
    )
    
    return ConversationHandler.END


async def wallet_select_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب مبلغ از دکمه‌ها"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')  # wallet_amt_<method>_<amount>
    if len(parts) != 4:
        await query.answer("خطا در پردازش درخواست", show_alert=True)
        return ConversationHandler.END
    
    method = parts[2]
    amount_str = parts[3]
    
    if amount_str == 'custom':
        # درخواست مبلغ دلخواه
        context.user_data['wallet_method'] = method
        context.user_data['awaiting_wallet_custom_amount'] = True
        
        await query.message.edit_text(
            "💵 <b>مبلغ دلخواه</b>\n\n"
            "لطفاً مبلغ مورد نظر را به تومان وارد کنید:\n\n"
            "💡 حداقل: 10,000 تومان\n"
            "💡 حداکثر: 50,000,000 تومان\n\n"
            "برای لغو /cancel را ارسال کنید.",
            parse_mode=ParseMode.HTML
        )
        return WALLET_AWAIT_AMOUNT_CARD
    
    try:
        amount = int(amount_str)
    except ValueError:
        await query.answer("مبلغ نامعتبر!", show_alert=True)
        return ConversationHandler.END
    
    context.user_data['wallet_topup_amount'] = amount
    context.user_data['wallet_method'] = method
    
    if method == 'card':
        return await show_card_payment_info(query, context, amount)
    
    return ConversationHandler.END


async def wallet_receive_custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت مبلغ دلخواه از کاربر"""
    if not update.message or not update.message.text:
        return WALLET_AWAIT_AMOUNT_CARD
    
    try:
        amount = int(update.message.text.replace(',', '').replace(' ', ''))
        
        if amount < 10000:
            await update.message.reply_text(
                "❌ حداقل مبلغ شارژ 10,000 تومان است."
            )
            return WALLET_AWAIT_AMOUNT_CARD
        
        if amount > 50000000:
            await update.message.reply_text(
                "❌ حداکثر مبلغ شارژ 50,000,000 تومان است."
            )
            return WALLET_AWAIT_AMOUNT_CARD
        
        context.user_data['wallet_topup_amount'] = amount
        method = context.user_data.get('wallet_method', 'card')
        
        if method == 'card':
            # به صورت یک query ساختگی می‌سازیم
            class FakeQuery:
                def __init__(self, message):
                    self.message = message
            
            fake_query = FakeQuery(update.message)
            return await show_card_payment_info(fake_query, context, amount)
        
    except ValueError:
        await update.message.reply_text(
            "❌ لطفاً فقط عدد وارد کنید (مثال: 150000)"
        )
        return WALLET_AWAIT_AMOUNT_CARD
    
    return ConversationHandler.END


async def show_card_payment_info(query, context: ContextTypes.DEFAULT_TYPE, amount: int):
    """نمایش اطلاعات پرداخت کارتی"""
    # دریافت کارت‌های بانکی با fallback برای ستون‌های مفقود
    try:
        cards = query_db("SELECT card_number, holder_name, bank_name FROM cards") or []
    except Exception as e:
        # Fallback اگر ستون bank_name وجود نداشت
        if "no such column: bank_name" in str(e):
            cards = query_db("SELECT card_number, holder_name FROM cards") or []
            # اضافه کردن bank_name پیش‌فرض
            cards = [{'card_number': card['card_number'], 'holder_name': card['holder_name'], 'bank_name': 'بانک'} for card in cards]
        else:
            cards = []
    
    if not cards:
        text = "❌ در حال حاضر امکان پرداخت کارت به کارت وجود ندارد.\n\nلطفاً با پشتیبانی تماس بگیرید."
        keyboard = [[BackButtons.custom("🔙 بازگشت", "wallet_menu")]]
        
        try:
            await query.message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as edit_error:
            # اگر edit نشد، پیام جدید ارسال کن
            if "Message is not modified" in str(edit_error):
                await query.message.reply_text(
                    text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        return ConversationHandler.END
    
    # ساخت متن اطلاعات کارت
    text = f"""
💳 <b>واریز به کارت بانکی</b>

━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>مبلغ قابل پرداخت:</b>
   <code>{amount:,}</code> تومان

━━━━━━━━━━━━━━━━━━━━━━━━

📌 <b>کارت‌های مقصد:</b>

"""
    
    for i, card in enumerate(cards, 1):
        bank = card.get('bank_name', 'بانک')
        text += f"<b>{i}. {bank}</b>\n"
        text += f"   کارت: {ltr_code(card['card_number'])}\n"
        text += f"   نام: {card['holder_name']}\n\n"
    
    text += """━━━━━━━━━━━━━━━━━━━━━━━━

📸 <b>مراحل پرداخت:</b>

1️⃣ مبلغ را به یکی از کارت‌ها واریز کنید
2️⃣ از رسید واریز عکس بگیرید
3️⃣ روی دکمه "ارسال رسید" بزنید
4️⃣ عکس رسید را ارسال کنید

⏰ رسید شما حداکثر 10 دقیقه بررسی می‌شود.
"""
    
    keyboard = [
        [InlineKeyboardButton("📸 ارسال رسید", callback_data='wallet_upload_receipt')],
        [BackButtons.custom("🔙 انصراف", "wallet_menu")]
    ]
    
    try:
        await query.message.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as edit_error:
        # اگر edit نشد، پیام جدید ارسال کن
        if "Message is not modified" in str(edit_error):
            await query.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    return ConversationHandler.END


async def wallet_upload_receipt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع آپلود رسید"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['awaiting'] = 'wallet_upload'
    
    text = """
📸 <b>ارسال رسید واریز</b>

━━━━━━━━━━━━━━━━━━━━━━━━

لطفاً عکس رسید واریز خود را ارسال کنید.

✅ عکس باید واضح و خوانا باشد
✅ مبلغ و تاریخ واریز مشخص باشد

💡 می‌توانید عکس را مستقیماً ارسال کنید.

برای انصراف /cancel را ارسال کنید.
"""
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML
    )
    
    return WALLET_AWAIT_SCREENSHOT


async def wallet_receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت اسکرین‌شات رسید"""
    if not update.message:
        return WALLET_AWAIT_SCREENSHOT
    
    user_id = update.effective_user.id
    amount = context.user_data.get('wallet_topup_amount')
    method = context.user_data.get('wallet_method', 'card')
    
    if not amount:
        await update.message.reply_text("❌ خطا: مبلغ مشخص نشده است.")
        return ConversationHandler.END
    
    # دریافت فایل عکس
    if update.message.photo:
        photo = update.message.photo[-1]  # بزرگترین سایز
        file_id = photo.file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text(
            "❌ لطفاً یک عکس ارسال کنید.\n\n"
            "برای انصراف /cancel را ارسال کنید."
        )
        return WALLET_AWAIT_SCREENSHOT
    
    # ثبت تراکنش
    success, tx_id, message = WalletSystem.add_credit(
        user_id=user_id,
        amount=amount,
        method=method,
        reference=file_id,
        description=f"شارژ کیف پول - {method}",
        auto_approve=False
    )
    
    if not success:
        await update.message.reply_text(f"❌ {message}")
        return ConversationHandler.END
    
    # دریافت اطلاعات کاربر
    try:
        user = await context.bot.get_chat(user_id)
        first_name = user.first_name or 'نامشخص'
        last_name = user.last_name or ''
        username = user.username
        full_name = f"{first_name} {last_name}".strip()
    except Exception:
        user_info = query_db(
            "SELECT first_name FROM users WHERE user_id = ?",
            (user_id,),
            one=True
        )
        first_name = user_info.get('first_name', 'نامشخص') if user_info else 'نامشخص'
        full_name = first_name
        username = None
    
    # ارسال به ادمین
    admin_text = f"""
💸 <b>درخواست شارژ کیف پول</b>

━━━━━━━━━━━━━━━━━━━━━━━━

👤 <b>کاربر:</b> {full_name}
🔖 <b>یوزرنیم:</b> {'@' + username if username else '-'}
🆔 <b>ID:</b> <code>{user_id}</code>

💰 <b>مبلغ:</b> {amount:,} تومان
💳 <b>روش:</b> کارت به کارت

🆔 <b>شماره تراکنش:</b> #{tx_id}
🕐 <b>زمان:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━

📸 رسید واریز در پیام بعدی ارسال می‌شود.
"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"wallet_tx_approve_{tx_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"wallet_tx_reject_{tx_id}")
        ],
        [InlineKeyboardButton("📋 لیست درخواست‌ها", callback_data="admin_wallet_tx_menu")]
    ])
    
    # ارسال متن و عکس به ادمین
    await notify_admins(
        context.bot,
        text=admin_text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    
    # ارسال عکس به ادمین
    await notify_admins(
        context.bot,
        text=f"📸 رسید درخواست #{tx_id}",
        photo=file_id
    )
    
    # پیام تایید به کاربر
    await update.message.reply_text(
        "✅ <b>درخواست شما ثبت شد!</b>\n\n"
        f"💰 مبلغ: {amount:,} تومان\n"
        f"🆔 شماره پیگیری: #{tx_id}\n\n"
        "⏰ درخواست شما در صف بررسی قرار گرفت.\n"
        "پس از تایید، موجودی به کیف پول شما اضافه می‌شود.\n\n"
        "💡 معمولاً حداکثر 10 دقیقه طول می‌کشد.",
        parse_mode=ParseMode.HTML
    )
    
    # پاک کردن context
    context.user_data.pop('wallet_topup_amount', None)
    context.user_data.pop('wallet_method', None)
    context.user_data.pop('awaiting', None)
    
    return ConversationHandler.END


async def wallet_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تاریخچه تراکنش‌ها"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # دریافت تراکنش‌ها
    transactions = WalletSystem.get_transactions(user_id, limit=15)
    
    if not transactions:
        text = "📜 <b>تاریخچه تراکنش‌ها</b>\n\n❌ هنوز تراکنشی ثبت نشده است."
        keyboard = [[BackButtons.custom("🔙 بازگشت", "wallet_menu")]]
        
        await query.message.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END
    
    text = "📜 <b>تاریخچه تراکنش‌های اخیر</b>\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for tx in transactions:
        text += WalletSystem.format_transaction_text(tx, show_user=False)
        text += "\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    keyboard = [[BackButtons.custom("🔙 بازگشت", "wallet_menu")]]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END


async def wallet_transactions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle wallet transactions view"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Get transactions from database
    transactions = query_db(
        "SELECT * FROM wallet_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", 
        (user_id,)
    ) or []
    
    if not transactions:
        text = "📊 <b>تراکنش‌های کیف پول</b>\n\n❌ هیچ تراکنشی یافت نشد."
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به کیف پول", callback_data='wallet_menu')]]
    else:
        text = "📊 <b>تراکنش‌های کیف پول</b>\n\n"
        for tx in transactions:
            amount_str = f"+{tx['amount']:,}" if tx['amount'] > 0 else f"{tx['amount']:,}"
            text += f"💰 {amount_str} تومان\n"
            text += f"📅 {tx['created_at'][:10]}\n"  
            text += f"📝 {tx.get('description', 'بدون توضیح')}\n"
            text += f"🔖 وضعیت: {tx.get('status', 'تکمیل شده')}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 بروزرسانی", callback_data='wallet_transactions')],
            [InlineKeyboardButton("🔙 بازگشت به کیف پول", callback_data='wallet_menu')],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')]
        ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

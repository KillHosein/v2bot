"""
Enhanced Handlers with Beautiful UI and Professional Messages
Example handlers showing how to use the new UI manager
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from ..ui_manager import get_ui_manager
from ..ai_assistant import get_ai_assistant
from ..rate_limiter import rate_limit
from ..security_manager import get_security_manager
from ..db import query_db
from ..wallet_system import WalletSystem
from ..advanced_logging import log_performance
from ..error_handler import handle_errors


ui = get_ui_manager()
ai = get_ai_assistant()
security = get_security_manager()


@handle_errors("start_command")
@log_performance("start_command")
@rate_limit(endpoint='start', check_spam=False)
async def enhanced_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced start command with beautiful UI"""
    user = update.effective_user
    
    # Get user data
    user_data = query_db(
        "SELECT * FROM users WHERE user_id = ?",
        (user.id,),
        one=True
    )
    
    # Get wallet balance
    wallet = WalletSystem()
    balance = wallet.get_balance(user.id)
    
    # Create beautiful welcome message
    welcome_text = ui.format_text(
        'welcome',
        bot_name='WingsBot Premium',
        user_name=user.first_name,
        balance=f"{balance:,}"
    )
    
    # Create main menu
    keyboard = ui.main_menu(user.first_name, balance)
    
    # Send with animation
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    
    # Send typing animation
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action='typing'
    )
    
    # AI suggestion
    response, action, confidence = await ai.process_message(
        "سلام",
        user.id,
        context={'user_name': user.first_name}
    )
    
    if confidence > 0.7 and action:
        await update.message.reply_text(
            f"💡 **پیشنهاد هوشمند:**\n{response}",
            parse_mode=ParseMode.MARKDOWN
        )


@handle_errors("buy_vpn_handler")
@log_performance("buy_vpn_handler")
@rate_limit(endpoint='purchase', check_spam=True)
async def enhanced_buy_vpn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced VPN purchase with beautiful UI"""
    query = update.callback_query
    await query.answer()
    
    # Show loading
    await query.message.edit_text(
        ui.loading_message("در حال بارگذاری پلن‌ها"),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Get plans from database
    plans = query_db("""
        SELECT * FROM vpn_plans 
        WHERE is_active = 1 
        ORDER BY price ASC
    """)
    
    # Format plans for display
    formatted_plans = []
    for plan in plans or []:
        formatted_plans.append({
            'id': plan['id'],
            'name': plan['name'],
            'price': plan['price'],
            'duration': plan['duration'],
            'is_popular': plan.get('is_popular', False),
            'is_new': plan.get('is_new', False),
            'discount': plan.get('discount', 0)
        })
    
    # Create purchase text
    plans_text = ""
    for i, plan in enumerate(formatted_plans, 1):
        if plan['is_popular']:
            badge = "🔥 **پرفروش**"
        elif plan['is_new']:
            badge = "🆕 **جدید**"
        elif plan['discount']:
            badge = f"🏷️ **{plan['discount']}% تخفیف**"
        else:
            badge = ""
        
        plans_text += f"""
{i}. **{plan['name']}** {badge}
   💰 قیمت: {plan['price']:,} تومان
   ⏱ مدت: {plan['duration']} روز
   ⚡ سرعت: نامحدود
   📱 دستگاه: 3 کاربر همزمان
"""
    
    # Create message
    message = ui.format_text(
        'purchase_intro',
        plans=plans_text
    )
    
    # Create menu
    keyboard = ui.purchase_menu(formatted_plans)
    
    # Send updated message
    await query.message.edit_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


@handle_errors("wallet_handler")
@log_performance("wallet_handler")
@rate_limit(endpoint='wallet')
async def enhanced_wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced wallet with beautiful UI"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Get wallet data
    wallet = WalletSystem()
    balance = wallet.get_balance(user_id)
    transactions = wallet.get_transaction_history(user_id, limit=5)
    
    # Calculate stats
    total_deposits = sum(t['amount'] for t in transactions if t['direction'] == 'credit')
    total_spent = sum(t['amount'] for t in transactions if t['direction'] == 'debit')
    saved = max(0, total_deposits - total_spent)
    
    # Create wallet message
    wallet_text = ui.format_text(
        'wallet_info',
        balance=f"{balance:,}",
        transactions=len(transactions),
        gift_credit=0,  # TODO: Implement gift credit
        deposits=f"{total_deposits:,}",
        spent=f"{total_spent:,}",
        saved=f"{saved:,}"
    )
    
    # Create menu
    keyboard = ui.wallet_menu(balance)
    
    # Send message
    await query.message.edit_text(
        wallet_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    
    # Add progress visualization
    if balance > 0:
        progress = ui.progress_bar(balance, 1000000)  # Progress to 1M
        await query.message.reply_text(
            f"📊 **پیشرفت به سطح VIP:**\n{progress}",
            parse_mode=ParseMode.MARKDOWN
        )


@handle_errors("support_handler")
@log_performance("support_handler")
@rate_limit(endpoint='support')
async def enhanced_support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced support with beautiful UI"""
    query = update.callback_query
    await query.answer()
    
    # Create support message
    support_text = ui.format_text('support_welcome')
    
    # Create support menu buttons
    buttons = [
        [
            ("💬 چت آنلاین", "support_chat", "support"),
            ("📝 ثبت تیکت", "support_ticket", "edit")
        ],
        [
            ("📚 سوالات متداول", "support_faq", "info"),
            ("📹 آموزش ویدیویی", "support_video", "play")
        ],
        [
            ("☎️ تماس VIP", "support_call_vip", "premium"),
        ],
        [
            ("🔙 بازگشت", "main_menu", "back")
        ]
    ]
    
    keyboard = ui.create_menu(buttons)
    
    # Send message
    await query.message.edit_text(
        support_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


@handle_errors("payment_success")
@log_performance("payment_success")
async def enhanced_payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  amount: int, transaction_id: str):
    """Enhanced payment success notification"""
    query = update.callback_query
    
    # Calculate bonus
    bonus = ""
    if amount >= 500000:
        bonus = "🎁 10% اعتبار هدیه دریافت کردید!"
    elif amount >= 200000:
        bonus = "🎁 5% اعتبار هدیه دریافت کردید!"
    
    # Create success message
    success_text = ui.format_text(
        'payment_success',
        amount=f"{amount:,}",
        transaction_id=transaction_id,
        timestamp=datetime.now().strftime("%Y/%m/%d %H:%M"),
        bonus_text=bonus
    )
    
    # Send with celebration animation
    await query.message.reply_text("🎊🎉🎊")
    
    await query.message.reply_text(
        success_text,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Send service activation details
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action='typing'
    )
    
    await asyncio.sleep(1)
    
    # Create buttons for next actions
    buttons = [
        [
            ("📱 مشاهده سرویس", "view_service", "services"),
            ("📲 اشتراک با دوستان", "share_service", "gift")
        ],
        [
            ("🏠 منوی اصلی", "main_menu", "home")
        ]
    ]
    
    keyboard = ui.create_menu(buttons)
    
    await query.message.reply_text(
        "**حالا چه کاری انجام دهیم؟**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


@handle_errors("premium_offer")
async def show_premium_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium VIP offer with countdown"""
    from datetime import datetime, timedelta
    
    query = update.callback_query
    await query.answer()
    
    # Calculate deadline
    deadline = (datetime.now() + timedelta(hours=24)).strftime("%Y/%m/%d %H:%M")
    
    # Create premium offer message
    offer_text = ui.format_text(
        'premium_offer',
        deadline=deadline
    )
    
    # Create action buttons
    buttons = [
        [("🚀 فعال‌سازی فوری", "activate_premium", "rocket")],
        [
            ("💡 اطلاعات بیشتر", "premium_info", "info"),
            ("🎁 کد تخفیف", "discount_code", "gift")
        ],
        [("❌ بعداً", "dismiss_offer", "close")]
    ]
    
    keyboard = ui.create_menu(buttons)
    
    # Send with premium style
    await query.message.reply_text(
        offer_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


# Service status with beautiful formatting
@handle_errors("service_status")
@log_performance("service_status")
async def show_service_status(update: Update, context: ContextTypes.DEFAULT_TYPE, service_id: int):
    """Show service status with beautiful formatting"""
    query = update.callback_query
    
    # Get service details
    service = query_db(
        "SELECT * FROM user_services WHERE id = ? AND user_id = ?",
        (service_id, query.from_user.id),
        one=True
    )
    
    if not service:
        await query.answer("سرویس یافت نشد", show_alert=True)
        return
    
    # Calculate remaining days
    from datetime import datetime
    expire_date = datetime.fromisoformat(service['expire_date'])
    days_left = (expire_date - datetime.now()).days
    
    # Create status message
    status_text = ui.format_text(
        'service_active',
        service_name=service['name'],
        config_link=service['config_link'],
        days_left=days_left,
        traffic_used=ui.format_number(service.get('traffic_used', 0), 'GB'),
        traffic_total=ui.format_number(service.get('traffic_total', 100), 'GB'),
        speed=service.get('speed', 100),
        location=service.get('location', '🇩🇪 آلمان')
    )
    
    # Create action buttons
    buttons = [
        [
            ("🔄 تمدید سرویس", f"renew_service_{service_id}", "refresh"),
            ("📊 آمار مصرف", f"service_stats_{service_id}", "dashboard")
        ],
        [
            ("🔗 کپی لینک", f"copy_link_{service_id}", "link"),
            ("📱 QR Code", f"qr_code_{service_id}", "qr")
        ],
        [
            ("🆘 پشتیبانی", "support", "support"),
            ("🔙 بازگشت", "my_services", "back")
        ]
    ]
    
    keyboard = ui.create_menu(buttons)
    
    # Send message
    await query.message.edit_text(
        status_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


# Error handler with friendly message
@handle_errors("generic_error")
async def handle_generic_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error_code: str):
    """Handle errors with friendly messages"""
    
    error_message = ui.error_message(
        "مشکلی پیش آمد",
        "متاسفیم که این اتفاق افتاد. تیم فنی در حال بررسی هستند.",
        error_code
    )
    
    # Create help buttons
    buttons = [
        [
            ("🔄 تلاش مجدد", "retry", "refresh"),
            ("🆘 پشتیبانی", "support", "support")
        ],
        [("🏠 منوی اصلی", "main_menu", "home")]
    ]
    
    keyboard = ui.create_menu(buttons)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            error_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            error_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )


# Example of confirmation dialog
async def delete_service_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, service_id: int):
    """Show confirmation before deleting service"""
    query = update.callback_query
    
    # Create confirmation dialog
    text, keyboard = ui.create_confirm_dialog(
        "آیا از حذف این سرویس مطمئن هستید؟\n\n⚠️ این عمل قابل بازگشت نیست!",
        f"delete_service_confirmed_{service_id}",
        "cancel_delete"
    )
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


# Example of rating system
async def rate_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user to rate service"""
    query = update.callback_query
    
    message = """
⭐ **امتیازدهی به سرویس**

لطفا به کیفیت سرویس ما امتیاز دهید:
    """
    
    keyboard = ui.create_rating_buttons("service")
    
    await query.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


# Register enhanced handlers
def register_enhanced_handlers(application):
    """Register all enhanced handlers"""
    # Commands
    application.add_handler(CommandHandler("start", enhanced_start_command))
    
    # Callbacks
    application.add_handler(CallbackQueryHandler(enhanced_buy_vpn, pattern="^buy_vpn$"))
    application.add_handler(CallbackQueryHandler(enhanced_wallet_menu, pattern="^wallet$"))
    application.add_handler(CallbackQueryHandler(enhanced_support_menu, pattern="^support$"))
    application.add_handler(CallbackQueryHandler(show_premium_offer, pattern="^premium_offer$"))
    
    # Import other required modules
    import asyncio
    from datetime import datetime


# Export for use in main app
__all__ = [
    'enhanced_start_command',
    'enhanced_buy_vpn',
    'enhanced_wallet_menu',
    'enhanced_support_menu',
    'enhanced_payment_success',
    'show_premium_offer',
    'show_service_status',
    'handle_generic_error',
    'delete_service_confirm',
    'rate_service',
    'register_enhanced_handlers'
]

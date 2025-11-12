#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to add missing button handlers to fix button issues
اسکریپت افزودن مدیریت کننده‌های مفقود دکمه‌ها
"""

import os
import re

def add_missing_handlers():
    """Add missing button handlers to appropriate files"""
    
    # Define the missing handlers and their implementations
    missing_handlers = {
        'wallet_transactions': {
            'handler_name': 'wallet_transactions_handler',
            'file': 'handlers/user_wallet.py',
            'pattern': '^wallet_transactions$',
            'implementation': '''
async def wallet_transactions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle wallet transactions view"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Get transactions from database
    transactions = query_db(
        "SELECT * FROM wallet_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50", 
        (user_id,)
    ) or []
    
    if not transactions:
        text = "📊 <b>تراکنش‌های کیف پول</b>\\n\\n❌ هیچ تراکنشی یافت نشد."
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به کیف پول", callback_data='wallet_menu')]]
    else:
        text = "📊 <b>تراکنش‌های کیف پول</b>\\n\\n"
        for tx in transactions:
            amount_str = f"+{tx['amount']:,}" if tx['amount'] > 0 else f"{tx['amount']:,}"
            text += f"💰 {amount_str} تومان\\n"
            text += f"📅 {tx['created_at']}\\n"
            text += f"📝 {tx.get('description', 'بدون توضیح')}\\n\\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به کیف پول", callback_data='wallet_menu')],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')]
        ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
'''
        },
        
        'usage_stats': {
            'handler_name': 'usage_stats_handler',
            'file': 'handlers/user.py',
            'pattern': '^usage_stats$',
            'implementation': '''
async def usage_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle usage statistics view"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Get user's services and their usage
    services = query_db(
        "SELECT * FROM orders WHERE user_id = ? AND status = 'approved'", 
        (user_id,)
    ) or []
    
    if not services:
        text = "📊 <b>آمار استفاده</b>\\n\\n❌ هیچ سرویس فعالی یافت نشد."
    else:
        text = "📊 <b>آمار استفاده سرویس‌ها</b>\\n\\n"
        for service in services:
            plan = query_db("SELECT name FROM plans WHERE id = ?", (service['plan_id'],), one=True)
            plan_name = plan['name'] if plan else 'نامشخص'
            
            text += f"🔹 <b>{plan_name}</b>\\n"
            text += f"📅 از: {service['created_at'][:10]}\\n"
            text += f"⏰ انقضا: {service.get('expire_date', 'نامحدود')}\\n"
            text += f"📊 وضعیت: فعال\\n\\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data='usage_stats')],
        [InlineKeyboardButton("📱 سرویس‌های من", callback_data='my_services')],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data='start_main')]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
'''
        },
        
        'user_settings': {
            'handler_name': 'user_settings_handler', 
            'file': 'handlers/user.py',
            'pattern': '^user_settings$',
            'implementation': '''
async def user_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user settings menu"""
    query = update.callback_query
    await query.answer()
    
    text = "⚙️ <b>تنظیمات کاربر</b>\\n\\nانتخاب کنید:"
    
    keyboard = [
        [InlineKeyboardButton("🌐 تغییر زبان", callback_data='language_menu')],
        [InlineKeyboardButton("🔔 تنظیمات اعلان‌ها", callback_data='notifications_settings')],
        [InlineKeyboardButton("📊 آمار استفاده", callback_data='usage_stats')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='start_main')]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
'''
        },
        
        'language_menu': {
            'handler_name': 'language_menu_handler',
            'file': 'handlers/user_language.py', 
            'pattern': '^language_menu$',
            'implementation': '''
async def language_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection menu"""
    query = update.callback_query
    await query.answer()
    
    text = "🌐 <b>انتخاب زبان</b>\\n\\nزبان مورد نظر را انتخاب کنید:"
    
    keyboard = [
        [InlineKeyboardButton("🇮🇷 فارسی", callback_data='set_language_fa')],
        [InlineKeyboardButton("🇺🇸 English", callback_data='set_language_en')], 
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='set_language_ru')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='user_settings')]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
'''
        },
        
        'notifications_settings': {
            'handler_name': 'notifications_settings_handler',
            'file': 'handlers/user.py',
            'pattern': '^notifications_settings$', 
            'implementation': '''
async def notifications_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle notification settings"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Get current notification settings
    settings = query_db(
        "SELECT * FROM user_settings WHERE user_id = ?", 
        (user_id,), 
        one=True
    ) or {}
    
    expiry_notif = settings.get('expiry_notifications', True)
    payment_notif = settings.get('payment_notifications', True) 
    promo_notif = settings.get('promo_notifications', True)
    
    text = "🔔 <b>تنظیمات اعلان‌ها</b>\\n\\n"
    text += f"⏰ اعلان انقضا: {'✅ فعال' if expiry_notif else '❌ غیرفعال'}\\n"
    text += f"💳 اعلان پرداخت: {'✅ فعال' if payment_notif else '❌ غیرفعال'}\\n" 
    text += f"🎁 اعلان‌های تبلیغاتی: {'✅ فعال' if promo_notif else '❌ غیرفعال'}"
    
    keyboard = [
        [InlineKeyboardButton(
            f"⏰ اعلان انقضا: {'✅' if expiry_notif else '❌'}", 
            callback_data=f'toggle_notif_expiry_{not expiry_notif}'
        )],
        [InlineKeyboardButton(
            f"💳 اعلان پرداخت: {'✅' if payment_notif else '❌'}", 
            callback_data=f'toggle_notif_payment_{not payment_notif}'
        )],
        [InlineKeyboardButton(
            f"🎁 اعلان تبلیغاتی: {'✅' if promo_notif else '❌'}", 
            callback_data=f'toggle_notif_promo_{not promo_notif}'
        )],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='user_settings')]
    ]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
'''
        }
    }
    
    # Add handlers to app.py
    app_py_path = os.path.join('bot', 'app.py')
    
    print("Adding missing button handlers...")
    
    # Read current app.py content
    with open(app_py_path, 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    # Find the USER_MAIN_MENU section to add new handlers
    user_main_pattern = r'(USER_MAIN_MENU: \[[\s\S]*?\])'
    match = re.search(user_main_pattern, app_content)
    
    if match:
        user_main_section = match.group(1)
        
        # Add new handlers to USER_MAIN_MENU
        new_handlers = []
        for callback, info in missing_handlers.items():
            handler_line = f"                CallbackQueryHandler({info['handler_name']}, pattern='{info['pattern']}'),"
            new_handlers.append(handler_line)
        
        # Insert new handlers before the closing bracket
        updated_section = user_main_section.replace(
            '            ],',
            '                # Added missing handlers\n' + '\\n'.join(new_handlers) + '\\n            ],'
        )
        
        app_content = app_content.replace(user_main_section, updated_section)
        
        # Write updated app.py
        with open(app_py_path, 'w', encoding='utf-8') as f:
            f.write(app_content)
        
        print(f"✅ Added {len(missing_handlers)} handler patterns to app.py")
    
    # Add handler implementations to respective files
    for callback, info in missing_handlers.items():
        file_path = os.path.join('bot', info['file'])
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Add the handler implementation
            file_content += f"\\n\\n{info['implementation']}"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            print(f"✅ Added {info['handler_name']} to {info['file']}")
        else:
            print(f"⚠️  File {info['file']} not found, skipping {callback}")
    
    print("\\n🎉 Missing button handlers have been added!")
    print("📌 Please review the code and test the new handlers.")

def create_stub_handlers():
    """Create stub handlers for remaining missing buttons"""
    
    remaining_buttons = [
        'show_referral', 'loyalty_rewards', 'start_purchase', 'app_guide_windows',
        'start_purchase_with_points', 'loyalty_redeem', 'user_services', 
        'gateway_verify_purchase', 'app_guide_macos', 'purchase_history',
        'loyalty_history', 'cancel'
    ]
    
    stub_file_path = os.path.join('bot', 'handlers', 'stub_handlers.py')
    
    stub_content = '''# -*- coding: utf-8 -*-
"""
Stub handlers for missing button callbacks
مدیریت کننده‌های موقت برای دکمه‌های مفقود
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

'''
    
    for button in remaining_buttons:
        handler_name = f"{button}_handler"
        stub_content += f'''
async def {handler_name}(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stub handler for {button} button"""
    query = update.callback_query
    await query.answer()
    
    text = "🚧 <b>در دست توسعه</b>\\n\\nاین قابلیت به زودی اضافه خواهد شد."
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='start_main')]]
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
'''
    
    # Write stub handlers file
    with open(stub_file_path, 'w', encoding='utf-8') as f:
        f.write(stub_content)
    
    print(f"✅ Created stub handlers for {len(remaining_buttons)} buttons in {stub_file_path}")

def main():
    """Main function"""
    print("Button Handler Fixer")
    print("=" * 50)
    
    # Change to bot directory 
    if os.path.exists('bot'):
        print("📂 Working in bot directory")
        
        # Add missing handlers
        add_missing_handlers()
        
        # Create stub handlers for remaining buttons
        create_stub_handlers()
        
        print("\\n✅ All missing button handlers have been addressed!")
        print("\\n📋 Next steps:")
        print("   1. Review the added code")
        print("   2. Test the new handlers")  
        print("   3. Implement the stub handlers properly")
        print("   4. Add imports to app.py if needed")
        
    else:
        print("❌ Bot directory not found!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
اسکریپت رفع خودکار مشکلات
این اسکریپت مشکلات را شناسایی و به صورت خودکار برطرف می‌کند
"""

import os
import sys
import re

def fix_app_py():
    """اضافه کردن import ها و handler های گم شده به app.py"""
    print("\n🔧 رفع مشکلات app.py...")
    
    app_file = "bot/app.py"
    if not os.path.exists(app_file):
        print("  ❌ app.py یافت نشد!")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changes_made = False
    
    # اضافه کردن import ها اگر وجود ندارند
    if 'from .handlers.user_wallet import' not in content:
        print("  ➕ اضافه کردن import های wallet...")
        
        import_block = """
# Advanced Features v3.0 - Wallet
from .handlers.user_wallet import (
    wallet_menu, wallet_charge_menu, wallet_topup_card,
    wallet_select_amount, wallet_receive_custom_amount,
    wallet_upload_receipt_start, wallet_receive_screenshot, wallet_history
)
from .handlers.admin_wallet_new import (
    admin_wallet_tx_menu, admin_wallet_tx_pending,
    admin_wallet_tx_approve, admin_wallet_tx_reject, admin_wallet_stats
)

# Advanced Features v3.0 - Loyalty
from .handlers.user_loyalty import (
    show_loyalty_menu, show_loyalty_history,
    show_loyalty_redeem, show_loyalty_rewards
)

# Advanced Features v3.0 - Dashboard  
from .handlers.user_dashboard import (
    show_user_dashboard, show_usage_stats, show_user_services
)

# Advanced Features v3.0 - App Guide
from .handlers.app_guide import (
    show_app_guide_menu, show_android_guide,
    show_ios_guide, show_windows_guide
)
"""
        # پیدا کردن آخرین import
        lines = content.split('\n')
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('from .') or line.startswith('import '):
                last_import_idx = i
        
        lines.insert(last_import_idx + 1, import_block)
        content = '\n'.join(lines)
        changes_made = True
        print("    ✅ Import ها اضافه شدند")
    
    # اضافه کردن handler registration
    if 'wallet_menu' in content and 'CallbackQueryHandler(wallet_menu' not in content:
        print("  ➕ اضافه کردن handler registration...")
        
        handlers_block = """
    # ═══════════════════════════════════════════════
    # Advanced Features v3.0 - Handlers
    # ═══════════════════════════════════════════════
    
    # User handlers
    application.add_handler(CallbackQueryHandler(wallet_menu, pattern=r'^wallet_menu$'), group=2)
    application.add_handler(CallbackQueryHandler(wallet_charge_menu, pattern=r'^wallet_charge_menu$'), group=2)
    application.add_handler(CallbackQueryHandler(wallet_topup_card, pattern=r'^wallet_topup_card$'), group=2)
    application.add_handler(CallbackQueryHandler(wallet_select_amount, pattern=r'^wallet_amt_'), group=2)
    application.add_handler(CallbackQueryHandler(wallet_upload_receipt_start, pattern=r'^wallet_upload_receipt$'), group=2)
    application.add_handler(CallbackQueryHandler(wallet_history, pattern=r'^wallet_history$'), group=2)
    
    application.add_handler(CallbackQueryHandler(show_loyalty_menu, pattern=r'^loyalty_menu$'), group=2)
    application.add_handler(CallbackQueryHandler(show_loyalty_history, pattern=r'^loyalty_history$'), group=2)
    application.add_handler(CallbackQueryHandler(show_loyalty_redeem, pattern=r'^loyalty_redeem$'), group=2)
    application.add_handler(CallbackQueryHandler(show_loyalty_rewards, pattern=r'^loyalty_rewards$'), group=2)
    
    application.add_handler(CallbackQueryHandler(show_user_dashboard, pattern=r'^dashboard$'), group=2)
    application.add_handler(CallbackQueryHandler(show_usage_stats, pattern=r'^usage_stats$'), group=2)
    application.add_handler(CallbackQueryHandler(show_user_services, pattern=r'^user_services$'), group=2)
    
    application.add_handler(CallbackQueryHandler(show_app_guide_menu, pattern=r'^app_guide_menu$'), group=2)
    application.add_handler(CallbackQueryHandler(show_android_guide, pattern=r'^app_guide_android$'), group=2)
    application.add_handler(CallbackQueryHandler(show_ios_guide, pattern=r'^app_guide_ios$'), group=2)
    application.add_handler(CallbackQueryHandler(show_windows_guide, pattern=r'^app_guide_windows$'), group=2)
    
    # Admin handlers
    application.add_handler(CallbackQueryHandler(admin_wallet_tx_menu, pattern=r'^admin_wallet_tx_menu$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_wallet_tx_pending, pattern=r'^admin_wallet_tx_pending$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_wallet_tx_approve, pattern=r'^wallet_tx_approve_'), group=3)
    application.add_handler(CallbackQueryHandler(admin_wallet_tx_reject, pattern=r'^wallet_tx_reject_'), group=3)
    application.add_handler(CallbackQueryHandler(admin_wallet_stats, pattern=r'^admin_wallet_stats$'), group=3)
    
    logger.info("✅ Advanced features v3.0 handlers registered")
"""
        
        # اضافه کردن قبل از start_bot
        if 'def start_bot' in content:
            content = content.replace('def start_bot', handlers_block + '\n\ndef start_bot')
            changes_made = True
            print("    ✅ Handler ها ثبت شدند")
    
    if changes_made:
        with open(app_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  ✅ app.py بروزرسانی شد")
        return True
    else:
        print("  ✅ app.py نیازی به تغییر ندارد")
        return True


def create_missing_files():
    """ساخت فایل‌های گم شده"""
    print("\n📦 بررسی و ساخت فایل‌های گم شده...")
    
    # لیست فایل‌های ضروری
    files_to_check = {
        'bot/wallet_system.py': 'System file',
        'bot/loyalty_system.py': 'System file', 
        'bot/smart_notifications.py': 'System file',
        'bot/handlers/user_wallet.py': 'Handler file',
        'bot/handlers/admin_wallet_new.py': 'Handler file',
        'bot/handlers/user_loyalty.py': 'Handler file',
        'bot/handlers/user_dashboard.py': 'Handler file',
        'bot/handlers/app_guide.py': 'Handler file',
    }
    
    missing = []
    for file, description in files_to_check.items():
        if not os.path.exists(file):
            missing.append(f"{file} ({description})")
    
    if missing:
        print(f"  ⚠️  {len(missing)} فایل گم شده:")
        for f in missing:
            print(f"     - {f}")
        print("\n  💡 لطفاً این فایل‌ها را از repository clone کنید")
        return False
    
    print("  ✅ همه فایل‌ها موجود است")
    return True


def main():
    """تابع اصلی"""
    print("╔════════════════════════════════════════════════╗")
    print("║   🔧 رفع خودکار مشکلات v3.0                   ║")
    print("╚════════════════════════════════════════════════╝")
    
    success_count = 0
    total_steps = 2
    
    # گام 1: رفع مشکلات app.py
    if fix_app_py():
        success_count += 1
    
    # گام 2: بررسی فایل‌های گم شده
    if create_missing_files():
        success_count += 1
    
    print("\n" + "="*50)
    print(f"📊 نتیجه: {success_count}/{total_steps} موفق")
    
    if success_count == total_steps:
        print("\n✅ همه مشکلات برطرف شد!")
        print("\n🚀 حالا می‌توانید ربات را اجرا کنید:")
        print("   python -m bot.run")
        return 0
    else:
        print("\n⚠️  برخی مشکلات باقی مانده")
        print("💡 لطفاً خطاها را بررسی کنید")
        return 1


if __name__ == '__main__':
    sys.exit(main())

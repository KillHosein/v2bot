#!/usr/bin/env python3
"""
اسکریپت یکپارچه‌سازی کامل v3.0
این اسکریپت تمام handler ها و سیستم‌های جدید را integrate می‌کند
"""

import sys
import os

def add_imports_to_app():
    """افزودن import های جدید به app.py"""
    
    app_file = "bot/app.py"
    
    if not os.path.exists(app_file):
        print(f"❌ فایل {app_file} یافت نشد!")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Import های جدید که باید اضافه شوند
    new_imports = """
# Advanced Features v3.0 - Wallet System
from .handlers.user_wallet import (
    wallet_menu,
    wallet_charge_menu,
    wallet_topup_card,
    wallet_select_amount,
    wallet_receive_custom_amount,
    wallet_upload_receipt_start,
    wallet_receive_screenshot,
    wallet_history
)
from .handlers.admin_wallet_new import (
    admin_wallet_tx_menu,
    admin_wallet_tx_pending,
    admin_wallet_tx_approve,
    admin_wallet_tx_reject,
    admin_wallet_stats
)

# Advanced Features v3.0 - Loyalty System
from .handlers.user_loyalty import (
    show_loyalty_menu,
    show_loyalty_history,
    show_loyalty_redeem,
    show_loyalty_rewards
)

# Advanced Features v3.0 - Dashboard
from .handlers.user_dashboard import (
    show_user_dashboard,
    show_usage_stats,
    show_user_services
)

# Advanced Features v3.0 - App Guide
from .handlers.app_guide import (
    show_app_guide_menu,
    show_android_guide,
    show_ios_guide,
    show_windows_guide
)
"""
    
    # چک کنیم که قبلا اضافه نشده باشد
    if 'user_wallet' in content:
        print("✅ Import های جدید قبلا اضافه شده‌اند")
        return True
    
    # پیدا کردن جای مناسب برای اضافه کردن (بعد از آخرین import)
    lines = content.split('\n')
    last_import_idx = 0
    
    for i, line in enumerate(lines):
        if line.startswith('from .') or line.startswith('import '):
            last_import_idx = i
    
    # اضافه کردن import های جدید
    lines.insert(last_import_idx + 1, new_imports)
    
    # نوشتن فایل
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ Import های جدید به app.py اضافه شدند")
    return True


def add_handlers_to_app():
    """افزودن handler های جدید"""
    
    app_file = "bot/app.py"
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    handlers_code = """
    # ═══════════════════════════════════════════════════════════
    # Advanced Features v3.0 - User Handlers
    # ═══════════════════════════════════════════════════════════
    
    # Wallet handlers
    application.add_handler(CallbackQueryHandler(wallet_menu, pattern=r'^wallet_menu$'), group=2)
    application.add_handler(CallbackQueryHandler(wallet_charge_menu, pattern=r'^wallet_charge_menu$'), group=2)
    application.add_handler(CallbackQueryHandler(wallet_topup_card, pattern=r'^wallet_topup_card$'), group=2)
    application.add_handler(CallbackQueryHandler(wallet_select_amount, pattern=r'^wallet_amt_'), group=2)
    application.add_handler(CallbackQueryHandler(wallet_upload_receipt_start, pattern=r'^wallet_upload_receipt$'), group=2)
    application.add_handler(CallbackQueryHandler(wallet_history, pattern=r'^wallet_history$'), group=2)
    
    # Loyalty system handlers
    application.add_handler(CallbackQueryHandler(show_loyalty_menu, pattern=r'^loyalty_menu$'), group=2)
    application.add_handler(CallbackQueryHandler(show_loyalty_history, pattern=r'^loyalty_history$'), group=2)
    application.add_handler(CallbackQueryHandler(show_loyalty_redeem, pattern=r'^loyalty_redeem$'), group=2)
    application.add_handler(CallbackQueryHandler(show_loyalty_rewards, pattern=r'^loyalty_rewards$'), group=2)
    
    # Dashboard handlers
    application.add_handler(CallbackQueryHandler(show_user_dashboard, pattern=r'^dashboard$'), group=2)
    application.add_handler(CallbackQueryHandler(show_usage_stats, pattern=r'^usage_stats$'), group=2)
    application.add_handler(CallbackQueryHandler(show_user_services, pattern=r'^user_services$'), group=2)
    
    # App guide handlers
    application.add_handler(CallbackQueryHandler(show_app_guide_menu, pattern=r'^app_guide_menu$'), group=2)
    application.add_handler(CallbackQueryHandler(show_android_guide, pattern=r'^app_guide_android$'), group=2)
    application.add_handler(CallbackQueryHandler(show_ios_guide, pattern=r'^app_guide_ios$'), group=2)
    application.add_handler(CallbackQueryHandler(show_windows_guide, pattern=r'^app_guide_windows$'), group=2)
    
    # ═══════════════════════════════════════════════════════════
    # Advanced Features v3.0 - Admin Handlers
    # ═══════════════════════════════════════════════════════════
    
    # Admin wallet handlers
    application.add_handler(CallbackQueryHandler(admin_wallet_tx_menu, pattern=r'^admin_wallet_tx_menu$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_wallet_tx_pending, pattern=r'^admin_wallet_tx_pending$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_wallet_tx_approve, pattern=r'^wallet_tx_approve_'), group=3)
    application.add_handler(CallbackQueryHandler(admin_wallet_tx_reject, pattern=r'^wallet_tx_reject_'), group=3)
    application.add_handler(CallbackQueryHandler(admin_wallet_stats, pattern=r'^admin_wallet_stats$'), group=3)
    
    logger.info("✅ Advanced features v3.0 handlers registered")
"""
    
    # چک کنیم handler ها قبلا اضافه نشده باشند
    if 'wallet_menu' in content and 'Advanced Features v3.0' in content:
        print("✅ Handler های جدید قبلا اضافه شده‌اند")
        return True
    
    # پیدا کردن جای مناسب (قبل از آخرین خط start_bot)
    if 'def start_bot' in content:
        # قبل از تابع start_bot اضافه کن
        content = content.replace('def start_bot', handlers_code + '\n\ndef start_bot')
    else:
        print("⚠️  تابع start_bot یافت نشد، handler ها را دستی اضافه کنید")
        return False
    
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Handler های جدید به app.py اضافه شدند")
    return True


def setup_databases():
    """راه‌اندازی دیتابیس‌های جدید"""
    print("\n📦 راه‌اندازی دیتابیس‌ها...")
    
    try:
        from bot.wallet_system import WalletSystem
        WalletSystem.setup_tables()
        print("  ✅ Wallet tables created")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    try:
        from bot.loyalty_system import LoyaltySystem
        LoyaltySystem.setup_tables()
        print("  ✅ Loyalty tables created")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    try:
        from bot.smart_notifications import SmartNotification
        SmartNotification.setup_tables()
        print("  ✅ Notification tables created")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    return True


def run_migration():
    """اجرای migration"""
    print("\n🔄 اجرای migration...")
    
    try:
        from bot.migrate_v3 import migrate_to_v3
        if migrate_to_v3():
            print("  ✅ Migration completed")
            return True
        else:
            print("  ❌ Migration failed")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """تابع اصلی"""
    print("╔════════════════════════════════════════════════╗")
    print("║   🚀 یکپارچه‌سازی کامل v3.0                   ║")
    print("╚════════════════════════════════════════════════╝")
    print()
    
    steps = [
        ("📝 اضافه کردن Import ها", add_imports_to_app),
        ("🔗 اضافه کردن Handler ها", add_handlers_to_app),
        ("📦 راه‌اندازی دیتابیس", setup_databases),
        ("🔄 اجرای Migration", run_migration),
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        try:
            if step_func():
                success_count += 1
                print(f"✅ {step_name} - موفق")
            else:
                print(f"❌ {step_name} - ناموفق")
        except Exception as e:
            print(f"❌ {step_name} - خطا: {e}")
    
    print("\n" + "="*50)
    print(f"\n📊 نتیجه: {success_count}/{len(steps)} مرحله موفق\n")
    
    if success_count == len(steps):
        print("╔════════════════════════════════════════════════╗")
        print("║   ✅ یکپارچه‌سازی با موفقیت انجام شد!         ║")
        print("╚════════════════════════════════════════════════╝")
        print()
        print("🔄 برای اعمال تغییرات:")
        print("   sudo systemctl restart v2bot")
        print()
        print("📋 برای مشاهده لاگ:")
        print("   sudo journalctl -u v2bot -f --no-pager")
        print()
        return 0
    else:
        print("⚠️  برخی مراحل با خطا مواجه شدند")
        print("   لطفاً خطاها را بررسی کنید")
        return 1


if __name__ == '__main__':
    sys.exit(main())

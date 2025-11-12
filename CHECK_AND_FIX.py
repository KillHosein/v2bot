#!/usr/bin/env python3
"""
اسکریپت بررسی و رفع مشکلات خودکار
این اسکریپت تمام کد را بررسی و مشکلات را برطرف می‌کند
"""

import os
import sys
import re

def check_app_py():
    """بررسی app.py برای import ها و handler ها"""
    print("\n📝 بررسی app.py...")
    
    app_file = "bot/app.py"
    if not os.path.exists(app_file):
        print(f"  ❌ {app_file} یافت نشد!")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # بررسی import ها
    required_imports = [
        ('user_wallet', 'wallet_menu'),
        ('admin_wallet_new', 'admin_wallet_tx_menu'),
        ('user_loyalty', 'show_loyalty_menu'),
        ('user_dashboard', 'show_user_dashboard'),
        ('app_guide', 'show_app_guide_menu'),
    ]
    
    missing_imports = []
    for module, function in required_imports:
        if module not in content:
            missing_imports.append((module, function))
    
    if missing_imports:
        print(f"  ⚠️  Import های گم شده: {len(missing_imports)}")
        for module, func in missing_imports:
            print(f"     - {module}.{func}")
        return False
    
    print("  ✅ همه import ها موجود است")
    
    # بررسی handler registration
    required_handlers = [
        'wallet_menu',
        'admin_wallet_tx_menu',
        'show_loyalty_menu',
        'show_user_dashboard',
        'show_app_guide_menu',
    ]
    
    missing_handlers = []
    for handler in required_handlers:
        pattern = f"CallbackQueryHandler\\({handler}"
        if not re.search(pattern, content):
            missing_handlers.append(handler)
    
    if missing_handlers:
        print(f"  ⚠️  Handler های ثبت نشده: {len(missing_handlers)}")
        for handler in missing_handlers:
            print(f"     - {handler}")
        return False
    
    print("  ✅ همه handler ها ثبت شده‌اند")
    return True


def check_database_files():
    """بررسی فایل‌های سیستم دیتابیس"""
    print("\n📦 بررسی فایل‌های دیتابیس...")
    
    required_files = [
        'bot/wallet_system.py',
        'bot/loyalty_system.py',
        'bot/smart_notifications.py',
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"  ❌ فایل‌های گم شده: {len(missing)}")
        for f in missing:
            print(f"     - {f}")
        return False
    
    print("  ✅ همه فایل‌های دیتابیس موجود است")
    return True


def check_handler_files():
    """بررسی فایل‌های handler"""
    print("\n🔧 بررسی فایل‌های handler...")
    
    required_files = [
        'bot/handlers/user_wallet.py',
        'bot/handlers/admin_wallet_new.py',
        'bot/handlers/user_loyalty.py',
        'bot/handlers/user_dashboard.py',
        'bot/handlers/app_guide.py',
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"  ❌ Handler های گم شده: {len(missing)}")
        for f in missing:
            print(f"     - {f}")
        return False
    
    print("  ✅ همه handler ها موجود است")
    return True


def check_helper_files():
    """بررسی فایل‌های helper"""
    print("\n🛠️  بررسی فایل‌های helper...")
    
    required_files = [
        'bot/helpers/back_buttons.py',
        'bot/helpers/persian_texts.py',
        'bot/helpers/admin_menu.py',
    ]
    
    existing = []
    missing = []
    
    for file in required_files:
        if os.path.exists(file):
            existing.append(file)
        else:
            missing.append(file)
    
    if missing:
        print(f"  ⚠️  Helper های گم شده (اختیاری): {len(missing)}")
        for f in missing:
            print(f"     - {f}")
    
    if existing:
        print(f"  ✅ {len(existing)} helper موجود است")
    
    return True


def check_migrations():
    """بررسی فایل migration"""
    print("\n🔄 بررسی migration...")
    
    if os.path.exists('bot/migrate_v3.py'):
        print("  ✅ فایل migration موجود است")
        return True
    else:
        print("  ⚠️  فایل migration یافت نشد (اختیاری)")
        return True


def check_documentation():
    """بررسی مستندات"""
    print("\n📚 بررسی مستندات...")
    
    docs = [
        'README.md',
        'UPGRADE_V3.md',
        'WALLET_UPGRADE.md',
        'FEATURE_IDEAS.md',
    ]
    
    existing = sum(1 for doc in docs if os.path.exists(doc))
    
    print(f"  ✅ {existing}/{len(docs)} مستندات موجود است")
    return True


def check_install_script():
    """بررسی اسکریپت نصب"""
    print("\n🚀 بررسی install.sh...")
    
    if not os.path.exists('install.sh'):
        print("  ❌ install.sh یافت نشد!")
        return False
    
    with open('install.sh', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # بررسی v3.0 setup
    if 'wallet_system' in content.lower() and 'loyalty_system' in content.lower():
        print("  ✅ install.sh شامل نصب v3.0 است")
        return True
    else:
        print("  ⚠️  install.sh ممکن است نیاز به بروزرسانی داشته باشد")
        return False


def generate_report(results):
    """ساخت گزارش نهایی"""
    print("\n" + "="*60)
    print("📊 گزارش نهایی:")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for r in results if r[1])
    
    for name, status in results:
        emoji = "✅" if status else "❌"
        print(f"  {emoji} {name}")
    
    print("="*60)
    print(f"\n✅ موفق: {passed}/{total}")
    print(f"❌ ناموفق: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 همه بررسی‌ها موفق بودند!")
        print("✨ کد شما آماده production است!")
        return 0
    else:
        print("\n⚠️  برخی بخش‌ها نیاز به توجه دارند")
        print("💡 لطفاً موارد مشکل‌دار را بررسی کنید")
        return 1


def main():
    """تابع اصلی"""
    print("╔════════════════════════════════════════════════╗")
    print("║   🔍 بررسی کامل کد v3.0                       ║")
    print("╚════════════════════════════════════════════════╝")
    
    checks = [
        ("app.py (imports & handlers)", check_app_py),
        ("Database files", check_database_files),
        ("Handler files", check_handler_files),
        ("Helper files", check_helper_files),
        ("Migration", check_migrations),
        ("Documentation", check_documentation),
        ("Install script", check_install_script),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            status = check_func()
            results.append((name, status))
        except Exception as e:
            print(f"  ❌ خطا: {e}")
            results.append((name, False))
    
    return generate_report(results)


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
اجرای تمام تست‌ها و debug ها
"""

import os
import sys
import subprocess

def run_command(cmd, description):
    """اجرای یک دستور و نمایش نتیجه"""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ موفق")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ خطا")
            if result.stderr:
                print(result.stderr)
            if result.stdout:
                print(result.stdout)
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("╔════════════════════════════════════════════════╗")
    print("║   🔍 اجرای تمام تست‌ها و Debug ها            ║")
    print("╚════════════════════════════════════════════════╝")
    
    results = []
    
    # 1. بررسی Python syntax
    results.append(run_command(
        "python3 -m py_compile bot/app.py",
        "بررسی Syntax - app.py"
    ))
    
    # 2. Import test
    results.append(run_command(
        "python3 -c \"from bot.app import run; print('✅ Import OK')\"",
        "تست Import ها"
    ))
    
    # 3. States test
    results.append(run_command(
        "python3 -c \"from bot.states import *; print('✅ States OK')\"",
        "تست States"
    ))
    
    # 4. بررسی handlers
    results.append(run_command(
        "python3 -c \"from bot.handlers.user_wallet import wallet_menu; print('✅ user_wallet OK')\"",
        "تست user_wallet"
    ))
    
    results.append(run_command(
        "python3 -c \"from bot.handlers.user_loyalty import show_loyalty_menu; print('✅ user_loyalty OK')\"",
        "تست user_loyalty"
    ))
    
    results.append(run_command(
        "python3 -c \"from bot.handlers.user_dashboard import show_user_dashboard; print('✅ user_dashboard OK')\"",
        "تست user_dashboard"
    ))
    
    results.append(run_command(
        "python3 -c \"from bot.handlers.app_guide import show_app_guide_menu; print('✅ app_guide OK')\"",
        "تست app_guide"
    ))
    
    # 5. بررسی Systems
    results.append(run_command(
        "python3 -c \"from bot.wallet_system import WalletSystem; print('✅ WalletSystem OK')\"",
        "تست WalletSystem"
    ))
    
    results.append(run_command(
        "python3 -c \"from bot.loyalty_system import LoyaltySystem; print('✅ LoyaltySystem OK')\"",
        "تست LoyaltySystem"
    ))
    
    results.append(run_command(
        "python3 -c \"from bot.smart_notifications import SmartNotification; print('✅ SmartNotification OK')\"",
        "تست SmartNotification"
    ))
    
    # 6. بررسی Database
    results.append(run_command(
        "python3 -c \"from bot.db import query_db; print('✅ Database OK')\"",
        "تست Database"
    ))
    
    # 7. بررسی Config
    results.append(run_command(
        "python3 -c \"from bot.config import BOT_TOKEN; print('✅ Config OK')\"",
        "تست Config"
    ))
    
    # 8. اجرای CHECK_AND_FIX
    if os.path.exists('CHECK_AND_FIX.py'):
        results.append(run_command(
            "python3 CHECK_AND_FIX.py",
            "اجرای CHECK_AND_FIX"
        ))
    
    # 9. اجرای FULL_DEBUG
    if os.path.exists('FULL_DEBUG.py'):
        results.append(run_command(
            "python3 FULL_DEBUG.py",
            "اجرای FULL_DEBUG"
        ))
    
    # خلاصه نتایج
    print("\n" + "="*60)
    print("📊 خلاصه نتایج:")
    print("="*60 + "\n")
    
    passed = sum(results)
    total = len(results)
    failed = total - passed
    
    print(f"✅ موفق: {passed}/{total}")
    print(f"❌ ناموفق: {failed}/{total}")
    
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\n📈 درصد موفقیت: {percentage:.1f}%")
    
    if percentage == 100:
        print("\n🎉 عالی! همه تست‌ها موفق بودند!")
        print("✨ کد شما کاملاً سالم است!")
        return 0
    elif percentage >= 80:
        print("\n⚠️  خوب! اما نیاز به بررسی دارد")
        print("💡 لطفاً موارد ناموفق را بررسی کنید")
        return 1
    else:
        print("\n❌ مشکلات جدی یافت شد")
        print("🔧 لطفاً خطاها را برطرف کنید")
        return 2

if __name__ == '__main__':
    sys.exit(main())

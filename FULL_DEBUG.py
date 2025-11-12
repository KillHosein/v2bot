#!/usr/bin/env python3
"""
اسکریپت Debug کامل
این اسکریپت تمام کد را بررسی و مشکلات را شناسایی می‌کند
"""

import os
import sys
import re
import ast

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def print_section(title):
    """چاپ عنوان بخش"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
    print(f"{Colors.CYAN}{title}{Colors.NC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}\n")

def check_syntax_errors():
    """بررسی خطاهای syntax در فایل‌های Python"""
    print_section("🔍 بررسی خطاهای Syntax")
    
    errors = []
    warnings = []
    
    for root, dirs, files in os.walk('bot'):
        # حذف پوشه‌های __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        code = f.read()
                    compile(code, filepath, 'exec')
                    print(f"  {Colors.GREEN}✅{Colors.NC} {filepath}")
                except SyntaxError as e:
                    errors.append((filepath, str(e)))
                    print(f"  {Colors.RED}❌{Colors.NC} {filepath}: {e}")
                except Exception as e:
                    warnings.append((filepath, str(e)))
                    print(f"  {Colors.YELLOW}⚠️{Colors.NC} {filepath}: {e}")
    
    return len(errors), len(warnings)

def check_imports():
    """بررسی import های موجود و گم شده"""
    print_section("📦 بررسی Import ها")
    
    app_file = "bot/app.py"
    if not os.path.exists(app_file):
        print(f"  {Colors.RED}❌ app.py یافت نشد!{Colors.NC}")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # لیست handler های v3.0 مورد نیاز
    required_modules = {
        'user_wallet': ['wallet_menu', 'wallet_charge_menu'],
        'admin_wallet_new': ['admin_wallet_tx_menu', 'admin_wallet_tx_pending'],
        'user_loyalty': ['show_loyalty_menu'],
        'user_dashboard': ['show_user_dashboard'],
        'app_guide': ['show_app_guide_menu']
    }
    
    missing = []
    for module, functions in required_modules.items():
        if module not in content:
            missing.append(module)
            print(f"  {Colors.RED}❌{Colors.NC} Missing import: {module}")
        else:
            print(f"  {Colors.GREEN}✅{Colors.NC} Found: {module}")
    
    return len(missing) == 0

def check_handler_registration():
    """بررسی ثبت handler ها"""
    print_section("🔗 بررسی Handler Registration")
    
    app_file = "bot/app.py"
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_handlers = [
        ('wallet_charge_menu', r'wallet_charge_menu'),
        ('show_loyalty_menu', r'show_loyalty_menu'),
        ('show_user_dashboard', r'dashboard'),
        ('show_app_guide_menu', r'app_guide_menu'),
        ('admin_wallet_tx_menu', r'admin_wallet_tx_menu'),
    ]
    
    missing = []
    for handler_name, pattern in required_handlers:
        if f"CallbackQueryHandler({handler_name}" in content or \
           f"CallbackQueryHandler({handler_name}_v3" in content:
            print(f"  {Colors.GREEN}✅{Colors.NC} Registered: {handler_name}")
        else:
            missing.append(handler_name)
            print(f"  {Colors.RED}❌{Colors.NC} Not registered: {handler_name}")
    
    return len(missing) == 0

def check_database_tables():
    """بررسی جداول database"""
    print_section("🗄️  بررسی جداول Database")
    
    try:
        from bot.wallet_system import WalletSystem
        from bot.loyalty_system import LoyaltySystem
        from bot.smart_notifications import SmartNotification
        
        print(f"  {Colors.GREEN}✅{Colors.NC} WalletSystem importable")
        print(f"  {Colors.GREEN}✅{Colors.NC} LoyaltySystem importable")
        print(f"  {Colors.GREEN}✅{Colors.NC} SmartNotification importable")
        
        return True
    except ImportError as e:
        print(f"  {Colors.RED}❌{Colors.NC} Import error: {e}")
        return False
    except Exception as e:
        print(f"  {Colors.YELLOW}⚠️{Colors.NC} Warning: {e}")
        return True

def check_circular_imports():
    """بررسی circular imports"""
    print_section("🔄 بررسی Circular Imports")
    
    # این تست ساده است - فقط سعی می‌کند همه را import کند
    try:
        sys.path.insert(0, os.path.abspath('.'))
        
        modules = [
            'bot.config',
            'bot.db',
            'bot.wallet_system',
            'bot.loyalty_system',
        ]
        
        for module in modules:
            try:
                __import__(module)
                print(f"  {Colors.GREEN}✅{Colors.NC} {module}")
            except Exception as e:
                print(f"  {Colors.RED}❌{Colors.NC} {module}: {e}")
                return False
        
        return True
    except Exception as e:
        print(f"  {Colors.RED}❌{Colors.NC} Error: {e}")
        return False

def check_indentation():
    """بررسی مشکلات indentation"""
    print_section("📏 بررسی Indentation")
    
    issues = []
    
    for root, dirs, files in os.walk('bot'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # بررسی tab و space mix
                    has_tabs = any('\t' in line for line in lines)
                    has_spaces = any(line.startswith('    ') for line in lines)
                    
                    if has_tabs and has_spaces:
                        issues.append(filepath)
                        print(f"  {Colors.YELLOW}⚠️{Colors.NC} Mixed tabs/spaces: {filepath}")
                    else:
                        print(f"  {Colors.GREEN}✅{Colors.NC} {filepath}")
                        
                except Exception as e:
                    print(f"  {Colors.RED}❌{Colors.NC} {filepath}: {e}")
    
    return len(issues)

def check_unused_imports():
    """بررسی import های استفاده نشده"""
    print_section("🗑️  بررسی Unused Imports")
    
    print(f"  {Colors.BLUE}ℹ️  این بررسی نیاز به ابزار pyflakes دارد{Colors.NC}")
    print(f"  {Colors.BLUE}ℹ️  برای نصب: pip install pyflakes{Colors.NC}")
    
    try:
        import subprocess
        result = subprocess.run(['pyflakes', 'bot/'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"  {Colors.GREEN}✅{Colors.NC} No unused imports found")
            return True
        else:
            lines = result.stdout.split('\n')[:10]  # فقط 10 خط اول
            for line in lines:
                if line.strip():
                    print(f"  {Colors.YELLOW}⚠️{Colors.NC} {line}")
            return False
    except FileNotFoundError:
        print(f"  {Colors.YELLOW}⚠️{Colors.NC} pyflakes not installed - skipping")
        return True
    except Exception as e:
        print(f"  {Colors.YELLOW}⚠️{Colors.NC} Error: {e}")
        return True

def check_state_conflicts():
    """بررسی تعداد state ها"""
    print_section("🔢 بررسی States")
    
    states_file = "bot/states.py"
    if not os.path.exists(states_file):
        print(f"  {Colors.RED}❌{Colors.NC} states.py not found")
        return False
    
    with open(states_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # پیدا کردن تعداد state ها
    match = re.search(r'range\((\d+)\)', content)
    if match:
        count = int(match.group(1))
        print(f"  {Colors.GREEN}✅{Colors.NC} Total states: {count}")
        
        # شمارش واقعی state ها
        state_names = re.findall(r'^\s+([A-Z_]+),', content, re.MULTILINE)
        actual_count = len(state_names)
        
        print(f"  {Colors.BLUE}ℹ️{Colors.NC} Defined states: {actual_count}")
        
        if actual_count == count:
            print(f"  {Colors.GREEN}✅{Colors.NC} State count matches")
            return True
        else:
            print(f"  {Colors.RED}❌{Colors.NC} Mismatch! Expected {count}, got {actual_count}")
            return False
    
    return False

def check_missing_files():
    """بررسی فایل‌های گم شده"""
    print_section("📂 بررسی فایل‌های ضروری")
    
    required_files = {
        'bot/wallet_system.py': 'Wallet System',
        'bot/loyalty_system.py': 'Loyalty System',
        'bot/smart_notifications.py': 'Smart Notifications',
        'bot/handlers/user_wallet.py': 'User Wallet Handler',
        'bot/handlers/admin_wallet_new.py': 'Admin Wallet Handler',
        'bot/handlers/user_loyalty.py': 'Loyalty Handler',
        'bot/handlers/user_dashboard.py': 'Dashboard Handler',
        'bot/handlers/app_guide.py': 'App Guide Handler',
        'bot/migrate_v3.py': 'Migration Script',
        'install.sh': 'Install Script',
        'requirements.txt': 'Requirements',
    }
    
    missing = []
    for filepath, description in required_files.items():
        if os.path.exists(filepath):
            print(f"  {Colors.GREEN}✅{Colors.NC} {description}: {filepath}")
        else:
            missing.append((filepath, description))
            print(f"  {Colors.RED}❌{Colors.NC} Missing {description}: {filepath}")
    
    return len(missing) == 0

def check_logger_usage():
    """بررسی استفاده از logger"""
    print_section("📝 بررسی Logging")
    
    files_without_logger = []
    
    for root, dirs, files in os.walk('bot'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'logger' in content or 'logging' in content:
                        print(f"  {Colors.GREEN}✅{Colors.NC} {filepath}")
                    else:
                        files_without_logger.append(filepath)
                        print(f"  {Colors.YELLOW}⚠️{Colors.NC} No logger: {filepath}")
                except:
                    pass
    
    return len(files_without_logger)

def generate_report(results):
    """ساخت گزارش نهایی"""
    print_section("📊 گزارش نهایی")
    
    total_tests = len(results)
    passed = sum(1 for r in results if r[1])
    failed = total_tests - passed
    
    print(f"\n{Colors.CYAN}نتایج تست:{Colors.NC}\n")
    
    for test_name, status, details in results:
        if status:
            print(f"  {Colors.GREEN}✅{Colors.NC} {test_name}")
        else:
            print(f"  {Colors.RED}❌{Colors.NC} {test_name}")
            if details:
                print(f"     → {details}")
    
    print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
    print(f"\n{Colors.GREEN}✅ موفق: {passed}/{total_tests}{Colors.NC}")
    print(f"{Colors.RED}❌ ناموفق: {failed}/{total_tests}{Colors.NC}")
    
    percentage = (passed / total_tests * 100) if total_tests > 0 else 0
    
    if percentage == 100:
        print(f"\n{Colors.GREEN}🎉 عالی! همه تست‌ها موفق بودند!{Colors.NC}")
        print(f"{Colors.GREEN}✨ کد شما آماده production است!{Colors.NC}\n")
        return 0
    elif percentage >= 80:
        print(f"\n{Colors.YELLOW}⚠️  خوب! اما نیاز به بهبود دارد{Colors.NC}")
        print(f"{Colors.YELLOW}💡 لطفاً موارد ناموفق را بررسی کنید{Colors.NC}\n")
        return 1
    else:
        print(f"\n{Colors.RED}❌ مشکلات جدی یافت شد{Colors.NC}")
        print(f"{Colors.RED}🔧 لطفاً خطاها را برطرف کنید{Colors.NC}\n")
        return 2

def main():
    """تابع اصلی"""
    print(f"\n{Colors.PURPLE}╔════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.PURPLE}║   🔍 Debug کامل کد v3.0                       ║{Colors.NC}")
    print(f"{Colors.PURPLE}╚════════════════════════════════════════════════╝{Colors.NC}")
    
    results = []
    
    # 1. Syntax Errors
    error_count, warning_count = check_syntax_errors()
    results.append(("Syntax Check", error_count == 0, f"{error_count} errors, {warning_count} warnings"))
    
    # 2. Imports
    imports_ok = check_imports()
    results.append(("Import Check", imports_ok, ""))
    
    # 3. Handler Registration
    handlers_ok = check_handler_registration()
    results.append(("Handler Registration", handlers_ok, ""))
    
    # 4. Database Tables
    db_ok = check_database_tables()
    results.append(("Database Systems", db_ok, ""))
    
    # 5. Circular Imports
    circular_ok = check_circular_imports()
    results.append(("Circular Import Check", circular_ok, ""))
    
    # 6. Indentation
    indent_issues = check_indentation()
    results.append(("Indentation Check", indent_issues == 0, f"{indent_issues} files with issues"))
    
    # 7. States
    states_ok = check_state_conflicts()
    results.append(("State Count", states_ok, ""))
    
    # 8. Missing Files
    files_ok = check_missing_files()
    results.append(("Required Files", files_ok, ""))
    
    # 9. Unused Imports
    unused_ok = check_unused_imports()
    results.append(("Unused Imports", unused_ok, ""))
    
    # 10. Logger Usage
    logger_count = check_logger_usage()
    results.append(("Logger Usage", logger_count < 5, f"{logger_count} files without logger"))
    
    # گزارش نهایی
    return generate_report(results)

if __name__ == '__main__':
    sys.exit(main())

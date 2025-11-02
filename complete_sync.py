#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت یکسان‌سازی کامل همه handler ها
این اسکریپت تمام handler های ادمین را با BackButtons استاندارد می‌کند
"""

import os
import re

# رنگ‌ها برای خروجی (اختیاری)
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
CHECK = '✓'
CROSS = '✗'

# لیست handler ها و تنظیمات
HANDLERS = {
    'bot/handlers/admin_plans.py': {
        'patterns': [
            (r'InlineKeyboardButton\("\\U0001F519 بازگشت", callback_data="admin_main"\)', 'BackButtons.to_admin_main()'),
        ]
    },
    'bot/handlers/admin_messages.py': {
        'patterns': [
            (r'InlineKeyboardButton\("\\U0001F519 بازگشت", callback_data="admin_main"\)', 'BackButtons.to_admin_main()'),
        ]
    },
    'bot/handlers/admin_discounts.py': {
        'patterns': [
            (r'InlineKeyboardButton\("\\U0001F519 بازگشت به پنل اصلی", callback_data="admin_main"\)', 'BackButtons.to_admin_main()'),
        ]
    },
    'bot/handlers/admin_cards.py': {
        'patterns': [
            (r'InlineKeyboardButton\("\\U0001F519 بازگشت", callback_data="admin_main"\)', 'BackButtons.to_admin_main()'),
        ]
    },
    'bot/handlers/admin_wallets.py': {
        'patterns': [
            (r'InlineKeyboardButton\("\\U0001F519 بازگشت به تنظیمات", callback_data="admin_settings_manage"\)', 'BackButtons.to_settings()'),
            (r'InlineKeyboardButton\("\\U0001F519 بازگشت", callback_data="admin_wallets_menu"\)', 'BackButtons.to_wallets()'),
        ]
    },
    'bot/handlers/admin_tutorials.py': {
        'patterns': [
            (r"InlineKeyboardButton\('\\\\U0001F519 بازگشت', callback_data='admin_main'\)", 'BackButtons.to_admin_main()'),
            (r"InlineKeyboardButton\('\\\\U0001F519 بازگشت', callback_data='admin_tutorials_menu'\)", 'BackButtons.to_tutorials()'),
        ]
    },
    'bot/handlers/admin_tickets.py': {
        'patterns': [
            (r"InlineKeyboardButton\('\\\\U0001F519 بازگشت', callback_data='admin_main'\)", 'BackButtons.to_admin_main()'),
            (r"InlineKeyboardButton\('\\\\U0001F519 بازگشت', callback_data='admin_tickets_menu'\)", 'BackButtons.to_tickets()'),
        ]
    },
    'bot/handlers/admin_stats_broadcast.py': {
        'patterns': [
            (r'InlineKeyboardButton\("\\U0001F519 بازگشت", callback_data="admin_main"\)', 'BackButtons.to_admin_main()'),
        ]
    },
    'bot/handlers/admin_cron.py': {
        'patterns': [
            (r'InlineKeyboardButton\("\\U0001F519 بازگشت", callback_data="admin_main"\)', 'BackButtons.to_admin_main()'),
        ]
    },
}

IMPORT_LINE = 'from ..helpers.back_buttons import BackButtons\n'


def add_import_to_file(filepath):
    """اضافه کردن import BackButtons به فایل"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # بررسی وجود import
        if 'from ..helpers.back_buttons import BackButtons' in content:
            return True, "already exists"
        
        # پیدا کردن آخرین خط import از ..
        lines = content.split('\n')
        insert_index = -1
        
        for i, line in enumerate(lines):
            if line.startswith('from ..') or line.startswith('from ..'):
                insert_index = i
        
        if insert_index == -1:
            # پیدا کردن اولین خط خالی بعد از imports
            for i, line in enumerate(lines):
                if i > 0 and line.strip() == '' and lines[i-1].startswith(('import', 'from')):
                    insert_index = i
                    break
        
        if insert_index >= 0:
            lines.insert(insert_index + 1, IMPORT_LINE.rstrip())
            new_content = '\n'.join(lines)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True, "added"
        else:
            return False, "could not find insertion point"
            
    except Exception as e:
        return False, str(e)


def fix_buttons_in_file(filepath, patterns):
    """جایگزینی دکمه‌های بازگشت با BackButtons"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacements_made = 0
        
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                replacements_made += 1
                content = new_content
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"{replacements_made} replacements"
        else:
            return True, "no changes needed"
            
    except Exception as e:
        return False, str(e)


def main():
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}   یکسان‌سازی کامل Handler های ادمین{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    total = len(HANDLERS)
    success = 0
    errors = []
    
    for filepath, config in HANDLERS.items():
        print(f"{YELLOW}Processing:{RESET} {filepath}")
        
        if not os.path.exists(filepath):
            print(f"  {RED}{CROSS} File not found{RESET}")
            errors.append(f"{filepath}: not found")
            continue
        
        # اضافه کردن import
        import_ok, import_msg = add_import_to_file(filepath)
        if import_ok:
            print(f"  {GREEN}{CHECK} Import: {import_msg}{RESET}")
        else:
            print(f"  {RED}{CROSS} Import failed: {import_msg}{RESET}")
            errors.append(f"{filepath}: import failed - {import_msg}")
        
        # جایگزینی دکمه‌ها
        buttons_ok, buttons_msg = fix_buttons_in_file(filepath, config['patterns'])
        if buttons_ok:
            print(f"  {GREEN}{CHECK} Buttons: {buttons_msg}{RESET}")
            success += 1
        else:
            print(f"  {RED}{CROSS} Buttons failed: {buttons_msg}{RESET}")
            errors.append(f"{filepath}: buttons failed - {buttons_msg}")
        
        print()
    
    # خلاصه
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{GREEN}{CHECK} Done! {success}/{total} handlers processed{RESET}")
    
    if errors:
        print(f"\n{RED}Errors:{RESET}")
        for error in errors:
            print(f"  {RED}{CROSS} {error}{RESET}")
    
    print(f"\n{YELLOW}Next steps:{RESET}")
    print(f"  1. git add -A")
    print(f"  2. git commit -m 'Complete synchronization of all handlers'")
    print(f"  3. git push origin main")
    print(f"  4. On server: git pull && sudo systemctl restart wingsbot")
    print(f"\n{BLUE}{'='*60}{RESET}\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Cancelled by user{RESET}\n")
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}\n")

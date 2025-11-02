#!/usr/bin/env python3
"""
رفع کامل تمام handler های ادمین - اجرای سریع
"""
import re
import os

# لیست فایل‌ها و تغییرات مورد نیاز
handlers = {
    'bot/handlers/admin_panels.py': {
        'import_after': 'from ..states import',
        'replacements': [
            ('InlineKeyboardButton("\\U0001F519 بازگشت", callback_data="admin_main")', 'BackButtons.to_admin_main()'),
        ]
    },
    'bot/handlers/admin_plans.py': {
        'import_after': 'from ..states import',
        'replacements': [
            ('InlineKeyboardButton("\\U0001F519 بازگشت", callback_data="admin_main")', 'BackButtons.to_admin_main()'),
        ]
    },
    'bot/handlers/admin_messages.py': {
        'import_after': 'from ..states import',
        'replacements': [
            ('InlineKeyboardButton("\\U0001F519 بازگشت", callback_data="admin_main")', 'BackButtons.to_admin_main()'),
        ]
    },
    'bot/handlers/admin_discounts.py': {
        'import_after': 'from ..states import',
        'replacements': [
            ('InlineKeyboardButton("\\U0001F519 بازگشت به پنل اصلی", callback_data="admin_main")', 'BackButtons.to_admin_main()'),
        ]
    },
    'bot/handlers/admin_cards.py': {
        'import_after': 'from ..states import',
        'replacements': [
            ('InlineKeyboardButton("\\U0001F519 بازگشت", callback_data="admin_main")', 'BackButtons.to_admin_main()'),
        ]
    },
    'bot/handlers/admin_wallets.py': {
        'import_after': 'from ..db import',
        'replacements': [
            ('InlineKeyboardButton("\\U0001F519 بازگشت به تنظیمات", callback_data="admin_settings_manage")', 'BackButtons.to_settings()'),
            ('InlineKeyboardButton("\\U0001F519 بازگشت", callback_data="admin_wallets_menu")', 'BackButtons.to_wallets()'),
        ]
    },
    'bot/handlers/admin_tutorials.py': {
        'import_after': 'from ..db import',
        'replacements': [
            ('InlineKeyboardButton("\\U0001F519 بازگشت", callback_data=\'admin_main\')', 'BackButtons.to_admin_main()'),
            ('InlineKeyboardButton("\\U0001F519 بازگشت", callback_data=\'admin_tutorials_menu\')', 'BackButtons.to_tutorials()'),
        ]
    },
    'bot/handlers/admin_tickets.py': {
        'import_after': 'from ..db import',
        'replacements': [
            ('InlineKeyboardButton("\\U0001F519 بازگشت", callback_data=\'admin_main\')', 'BackButtons.to_admin_main()'),
            ('InlineKeyboardButton("\\U0001F519 بازگشت", callback_data=\'admin_tickets_menu\')', 'BackButtons.to_tickets()'),
        ]
    },
    'bot/handlers/admin_stats_broadcast.py': {
        'import_after': 'from ..db import',
        'replacements': [
            ('InlineKeyboardButton("\\U0001F519 بازگشت", callback_data="admin_main")', 'BackButtons.to_admin_main()'),
        ]
    },
    'bot/handlers/admin_cron.py': {
        'import_after': 'from ..db import',
        'replacements': [
            ('InlineKeyboardButton("\\U0001F519 بازگشت", callback_data="admin_main")', 'BackButtons.to_admin_main()'),
        ]
    },
}

import_line = 'from ..helpers.back_buttons import BackButtons\n'

fixed_count = 0
for filepath, config in handlers.items():
    if not os.path.exists(filepath):
        print(f"⚠️  {filepath} - not found")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # چک کردن import
    if 'from ..helpers.back_buttons import BackButtons' in content:
        print(f"✅ {filepath} - already has import")
    else:
        # اضافه کردن import
        pattern = config['import_after']
        lines = content.split('\n')
        new_lines = []
        import_added = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            if pattern in line and not import_added:
                # پیدا کردن آخرین import مربوطه
                j = i + 1
                while j < len(lines) and (lines[j].strip().startswith('from') or lines[j].strip() == '' or lines[j].strip().startswith(')')):
                    new_lines.append(lines[j])
                    j += 1
                    i = j - 1
                new_lines.append(import_line)
                import_added = True
        
        if not import_added:
            # اگر پیدا نشد، اضافه کن بعد از اولین بلوک import
            for i, line in enumerate(lines):
                if line.strip() == '' and i > 0 and lines[i-1].startswith('from'):
                    lines.insert(i, import_line)
                    break
            content = '\n'.join(lines)
        else:
            content = '\n'.join(new_lines)
    
    # جایگزینی دکمه‌ها
    for old, new in config['replacements']:
        content = content.replace(old, new)
    
    # نوشتن فایل
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    fixed_count += 1
    print(f"✅ {filepath} - FIXED")

print(f"\n🎉 {fixed_count} handler رفع شد!")

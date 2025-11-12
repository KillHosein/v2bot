#!/usr/bin/env python3
"""
تبدیل ساده و مطمئن: فقط مهم‌ترین متن‌ها را تبدیل می‌کند
"""

import os
import re

# نقشه تبدیل‌ها: (فایل, متن قدیم, کد جدید)
CONVERSIONS = [
    # common.py - صفحه اصلی
    (
        'bot/handlers/common.py',
        'message_data = query_db("SELECT text FROM messages WHERE message_name = \'start_main\'", one=True)\n    text = message_data.get(\'text\') if message_data else "خوش آمدید!"',
        'text = get_message_text(\'start_main\', "خوش آمدید!")'
    ),
    
    # purchase.py - خرید
    (
        'bot/handlers/purchase.py',
        'message_data = query_db("SELECT text FROM messages WHERE message_name = \'buy_config_main\'", one=True)\n    text = message_data.get(\'text\') if message_data else "پلن موردنظر خود را انتخاب کنید:"',
        'text = get_message_text(\'buy_config_main\', "پلن موردنظر خود را انتخاب کنید:")'
    ),
]

def apply_fixes():
    """اعمال تبدیل‌ها"""
    fixed_count = 0
    
    for filepath, old_text, new_text in CONVERSIONS:
        if not os.path.exists(filepath):
            print(f"⚠️  {filepath} not found")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_text in content:
            content = content.replace(old_text, new_text)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Fixed: {filepath}")
            fixed_count += 1
        else:
            print(f"⏭  {filepath}: Already fixed or not found")
    
    return fixed_count

if __name__ == '__main__':
    print("🔧 Applying simple fixes...")
    count = apply_fixes()
    print(f"\n✅ Fixed {count} files")
    print("\nRestart the bot to see changes!")

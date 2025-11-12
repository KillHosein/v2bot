#!/usr/bin/env python3
"""
اسکریپت اصلاح تمام دکمه‌های بازگشت پنل ادمین
"""

import os
import re

# نقشه درست callback data ها
CORRECT_CALLBACKS = {
    # Admin Main
    'admin_main': 'admin_main_menu',
    'admin_panel': 'admin_main_menu',
    'back_to_admin': 'admin_main_menu',
    
    # Users
    'admin_user_management': 'admin_users_menu',
    'back_to_users': 'admin_users_menu',
    
    # Orders
    'admin_orders': 'admin_orders_menu',
    'back_to_orders': 'admin_orders_menu',
    
    # Panels
    'admin_panel_menu': 'admin_panels_menu',
    'back_to_panels': 'admin_panels_menu',
    
    # Plans
    'admin_plan': 'admin_plan_manage',
    'back_to_plans': 'admin_plan_manage',
    
    # Settings
    'admin_setting': 'admin_settings_manage',
    'back_to_settings': 'admin_settings_manage',
    
    # Messages
    'admin_message': 'admin_messages_menu',
    'back_to_messages': 'admin_messages_menu',
    
    # Tickets
    'admin_ticket': 'admin_tickets_menu',
    'back_to_tickets': 'admin_tickets_menu',
    
    # Stats
    'admin_stat': 'admin_stats',
    'back_to_stats': 'admin_stats',
    
    # Wallets
    'admin_wallet': 'admin_wallets_menu',
    'back_to_wallets': 'admin_wallets_menu',
    
    # Cards
    'admin_card': 'admin_cards_menu',
    'back_to_cards': 'admin_cards_menu',
}

def fix_back_buttons_in_file(filepath):
    """اصلاح دکمه‌های بازگشت در یک فایل"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixed_count = 0
        
        # 1. استانداردسازی متن دکمه بازگشت
        patterns = [
            (r'بازگشت به پنل', '🔙 بازگشت'),
            (r'بازگشت به منو', '🔙 بازگشت'),
            (r'بازگشت به منوی', '🔙 بازگشت'),
            (r'برگشت', '🔙 بازگشت'),
        ]
        
        for old_pattern, new_text in patterns:
            if old_pattern in content:
                content = content.replace(old_pattern, new_text)
                fixed_count += 1
        
        # 2. اصلاح callback data های اشتباه
        for wrong_callback, correct_callback in CORRECT_CALLBACKS.items():
            # پیدا کردن الگوهای callback_data
            pattern = f"callback_data=['\"]({wrong_callback})['\"]"
            if re.search(pattern, content):
                content = re.sub(pattern, f"callback_data='{correct_callback}'", content)
                fixed_count += 1
        
        # 3. اطمینان از وجود BackButtons import در فایل‌های admin
        if 'admin' in filepath and 'InlineKeyboardButton' in content:
            if 'from ..helpers.back_buttons import BackButtons' not in content and \
               'from .helpers.back_buttons import BackButtons' not in content:
                # اضافه کردن import
                if 'from telegram import' in content:
                    # پیدا کردن اولین import از telegram
                    import_line = content.find('from telegram import')
                    next_newline = content.find('\n', import_line)
                    
                    if filepath.startswith('bot/handlers'):
                        import_statement = '\nfrom ..helpers.back_buttons import BackButtons\n'
                    else:
                        import_statement = '\nfrom .helpers.back_buttons import BackButtons\n'
                    
                    content = content[:next_newline] + import_statement + content[next_newline:]
                    fixed_count += 1
        
        # اگر تغییری داشتیم، بنویس
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, fixed_count
        
        return False, 0
        
    except Exception as e:
        print(f"  ❌ Error in {filepath}: {e}")
        return False, 0

def scan_and_fix():
    """اسکن و اصلاح تمام فایل‌های admin"""
    
    print("╔════════════════════════════════════════════════╗")
    print("║   🔧 اصلاح دکمه‌های بازگشت پنل ادمین         ║")
    print("╚════════════════════════════════════════════════╝\n")
    
    files_fixed = 0
    total_fixes = 0
    
    # اسکن handler های admin
    admin_dirs = [
        'bot/handlers',
        'bot/helpers',
    ]
    
    for directory in admin_dirs:
        if not os.path.exists(directory):
            continue
            
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    
                    fixed, count = fix_back_buttons_in_file(filepath)
                    
                    if fixed:
                        print(f"  ✅ Fixed: {filepath} ({count} changes)")
                        files_fixed += 1
                        total_fixes += count
                    else:
                        print(f"  ℹ️  OK: {filepath}")
    
    print("\n" + "="*60)
    print(f"\n📊 خلاصه:")
    print(f"  ✅ فایل‌های اصلاح شده: {files_fixed}")
    print(f"  🔧 تعداد تغییرات: {total_fixes}")
    
    if files_fixed > 0:
        print(f"\n🎉 دکمه‌های بازگشت اصلاح شدند!")
        print(f"\n💡 حالا تست کنید:")
        print(f"   python -m bot.run")
    else:
        print(f"\n✅ همه دکمه‌های بازگشت درست هستند!")
    
    print()
    return 0

def generate_back_button_guide():
    """ساخت راهنمای استفاده از دکمه‌های بازگشت"""
    
    guide = """# 🔙 راهنمای دکمه‌های بازگشت

## استفاده صحیح

### ❌ اشتباه:
```python
keyboard.append([
    InlineKeyboardButton("بازگشت به پنل", callback_data='admin_main')
])
```

### ✅ درست:
```python
from ..helpers.back_buttons import BackButtons

keyboard.append([BackButtons.to_admin_main()])
```

## تمام دکمه‌های موجود:

### پنل ادمین:
- `BackButtons.to_admin_main()` → پنل اصلی ادمین
- `BackButtons.to_start_main()` → منوی اصلی

### بخش‌های ادمین:
- `BackButtons.to_users()` → کاربران
- `BackButtons.to_settings()` → تنظیمات
- `BackButtons.to_panels()` → پنل‌ها
- `BackButtons.to_plans()` → پلن‌ها
- `BackButtons.to_tickets()` → تیکت‌ها
- `BackButtons.to_tutorials()` → آموزش‌ها
- `BackButtons.to_messages()` → پیام‌ها
- `BackButtons.to_stats()` → آمار
- `BackButtons.to_wallets()` → کیف پول‌ها
- `BackButtons.to_cards()` → کارت‌ها
- `BackButtons.to_advanced_stats()` → آمار پیشرفته
- `BackButtons.to_monitoring()` → مانیتورینگ

## Callback Data های صحیح:

| بخش | Callback Data |
|---|---|
| پنل ادمین | `admin_main_menu` |
| کاربران | `admin_users_menu` |
| سفارشات | `admin_orders_menu` |
| پنل‌ها | `admin_panels_menu` |
| پلن‌ها | `admin_plan_manage` |
| تنظیمات | `admin_settings_manage` |
| پیام‌ها | `admin_messages_menu` |
| تیکت‌ها | `admin_tickets_menu` |
| آمار | `admin_stats` |
| کیف پول‌ها | `admin_wallets_menu` |
| کارت‌ها | `admin_cards_menu` |

## مثال کامل:

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ..helpers.back_buttons import BackButtons

async def some_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("گزینه 1", callback_data='option1')],
        [InlineKeyboardButton("گزینه 2", callback_data='option2')],
        [BackButtons.to_admin_main()]  # دکمه بازگشت
    ]
    
    await update.callback_query.edit_message_text(
        "متن پیام",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
```

## نکات مهم:

1. ✅ همیشه از `BackButtons` استفاده کنید
2. ✅ متن یکپارچه: `🔙 بازگشت`
3. ✅ Callback data صحیح
4. ❌ از متن‌های مختلف استفاده نکنید
5. ❌ Callback data دستی ننویسید
"""
    
    with open('BACK_BUTTONS_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("  ✅ راهنما ساخته شد: BACK_BUTTONS_GUIDE.md")

if __name__ == '__main__':
    import sys
    
    # اصلاح فایل‌ها
    result = scan_and_fix()
    
    # ساخت راهنما
    generate_back_button_guide()
    
    sys.exit(result)

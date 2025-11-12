#!/usr/bin/env python3
"""
تبدیل خودکار تمام متن‌های hard-coded به get_message_text()
این اسکریپت تمام فایل‌های handler را پردازش و تبدیل می‌کند
"""

import os
import re
import sqlite3
from pathlib import Path

# نقشه نام پیام‌ها و الگوهای شناسایی آن‌ها
MESSAGE_PATTERNS = {
    # Support
    'support_menu': r'💬.*پشتیبانی.*راهنمایی',
    'support_ticket_created': r'✅.*تیکت ثبت شد',
    'support_ticket_replied': r'📨.*پاسخ جدید.*تیکت',
    'support_ticket_closed': r'✅.*تیکت بسته شد',
    
    # Services
    'services_empty': r'❌.*هیچ سرویسی ندارید',
    'services_list_header': r'📱.*سرویس‌های من',
    'service_detail': r'📦.*مشخصات سرویس',
    'service_renewed': r'✅.*تمدید موفق',
    
    # Wallet
    'wallet_balance': r'💎.*کیف پول من',
    'wallet_deposit_pending': r'⏳.*درخواست.*ثبت شد',
    'wallet_deposit_approved': r'✅.*واریز تایید شد',
    'wallet_insufficient': r'❌.*موجودی.*ناکافی',
    
    # Trial
    'trial_already_used': r'شما قبلاً تست را دریافت',
    'trial_activated': r'🎉.*تست رایگان فعال',
    'trial_available': r'🎁.*تست رایگان در دسترس',
    
    # Purchase
    'purchase_success': r'🎉.*خرید موفق',
    'purchase_cancelled': r'❌.*خرید لغو شد',
    
    # Discount
    'discount_applied': r'✅.*تخفیف.*اعمال شد',
    'discount_invalid': r'❌.*کد تخفیف.*نامعتبر',
    
    # Errors
    'error_generic': r'❌.*خطا',
}

def find_message_name(text_snippet):
    """پیدا کردن نام پیام بر اساس محتوا"""
    for msg_name, pattern in MESSAGE_PATTERNS.items():
        if re.search(pattern, text_snippet, re.DOTALL | re.IGNORECASE):
            return msg_name
    return None

def extract_multiline_string(content, start_pos):
    """استخراج رشته چندخطی از موقعیت مشخص"""
    # پیدا کردن اولین " یا '
    quote_char = None
    i = start_pos
    while i < len(content):
        if content[i] in ('"', "'"):
            quote_char = content[i]
            break
        i += 1
    
    if not quote_char:
        return None, -1
    
    # استخراج رشته
    string_start = i
    i += 1
    result = []
    is_multiline = False
    
    # بررسی triple quote
    if i + 1 < len(content) and content[i:i+2] == quote_char * 2:
        is_multiline = True
        i += 2
        end_marker = quote_char * 3
    else:
        end_marker = quote_char
    
    while i < len(content):
        if content[i:i+len(end_marker)] == end_marker:
            string_end = i + len(end_marker)
            full_string = content[string_start:string_end]
            return full_string, string_end
        result.append(content[i])
        i += 1
    
    return None, -1

def convert_file(filepath):
    """تبدیل یک فایل"""
    print(f"\n📁 Processing: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if get_message_text is imported
    has_import = 'get_message_text' in content
    
    # Find all Persian text strings
    changes = []
    
    # Pattern for finding reply_text, edit_text, send_message with Persian text
    patterns = [
        (r'\.reply_text\s*\(\s*["\']([^"\']*[آ-ی][^"\']*)["\']', 'reply_text'),
        (r'\.edit_text\s*\(\s*["\']([^"\']*[آ-ی][^"\']*)["\']', 'edit_text'),
        (r'\.send_message\s*\([^,]*,\s*text\s*=\s*["\']([^"\']*[آ-ی][^"\']*)["\']', 'send_message'),
    ]
    
    for pattern, method_type in patterns:
        for match in re.finditer(pattern, content, re.DOTALL):
            text = match.group(1)
            if len(text) < 10:  # متن‌های خیلی کوتاه را نادیده بگیر
                continue
            
            msg_name = find_message_name(text)
            if msg_name:
                # ذخیره برای تبدیل
                changes.append({
                    'pos': match.start(),
                    'old': match.group(0),
                    'text': text,
                    'msg_name': msg_name,
                    'method': method_type
                })
    
    if not changes:
        print(f"  ⏭  No changes needed")
        return False
    
    # اعمال تغییرات (از آخر به اول تا موقعیت‌ها خراب نشوند)
    new_content = content
    changes_applied = 0
    
    for change in sorted(changes, key=lambda x: x['pos'], reverse=True):
        msg_name = change['msg_name']
        text = change['text'].replace('\\n', '\n').replace('\\"', '"')
        
        # ساخت کد جدید
        if change['method'] == 'reply_text':
            new_code = f"reply_text(get_message_text('{msg_name}', '{change['text']}')"
        elif change['method'] == 'edit_text':
            new_code = f"edit_text(get_message_text('{msg_name}', '{change['text']}')"
        else:  # send_message
            new_code = f"send_message(..., text=get_message_text('{msg_name}', '{change['text']}')"
        
        # جایگزینی
        old_code = change['old']
        # فقط متن داخل را عوض کن، نه کل دستور
        text_part = f"'{change['text']}'"
        new_text_part = f"get_message_text('{msg_name}', '{change['text']}')"
        
        if text_part in old_code:
            new_full_code = old_code.replace(text_part, new_text_part)
            new_content = new_content.replace(old_code, new_full_code, 1)
            changes_applied += 1
            print(f"  ✅ Converted: {msg_name}")
    
    # اضافه کردن import اگر نیاز بود
    if changes_applied > 0 and not has_import:
        # پیدا کردن خط import از db
        import_pattern = r'from \.\.db import ([^\n]+)'
        match = re.search(import_pattern, new_content)
        if match:
            old_import = match.group(0)
            imports = match.group(1).split(',')
            imports = [i.strip() for i in imports]
            if 'get_message_text' not in imports:
                imports.append('get_message_text')
                new_import = f"from ..db import {', '.join(imports)}"
                new_content = new_content.replace(old_import, new_import, 1)
                print(f"  ✅ Added import")
    
    if changes_applied > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✅ Saved {changes_applied} changes")
        return True
    
    return False

def main():
    """پردازش تمام فایل‌ها"""
    print("🚀 Starting automatic message conversion...")
    print("="*60)
    
    handlers_dir = Path('bot/handlers')
    if not handlers_dir.exists():
        print("❌ bot/handlers directory not found!")
        print("   Run this script from project root")
        return
    
    # لیست فایل‌های هدف
    target_files = [
        'user.py',
        'common.py',
        'purchase.py',
        'renewal.py',
    ]
    
    converted_count = 0
    
    for filename in target_files:
        filepath = handlers_dir / filename
        if filepath.exists():
            if convert_file(str(filepath)):
                converted_count += 1
        else:
            print(f"\n⚠️  {filename} not found")
    
    print("\n" + "="*60)
    print(f"✅ Conversion complete!")
    print(f"📊 Files converted: {converted_count}/{len(target_files)}")
    print("\n📝 Next steps:")
    print("   1. Review changes: git diff")
    print("   2. Test the bot locally")
    print("   3. Commit: git add . && git commit -m 'Auto-convert messages'")
    print("   4. Push: git push origin main")
    print("   5. Deploy and restart bot")

if __name__ == '__main__':
    main()

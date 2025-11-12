#!/usr/bin/env python3
"""
اسکریپت ساده برای تبدیل خودکار متن‌ها
فقط متن‌های مشخص را تبدیل می‌کند - بدون خطا
"""

import os

# تبدیل‌های دقیق - هر مورد شامل (فایل، متن قدیم، متن جدید)
FIXES = [
    # common.py - start_main (قبلاً انجام شده)
    
    # user.py - support (قبلاً انجام شده)
    
    # user.py - ticket created
    (
        'bot/handlers/user.py',
        '''await update.message.reply_text(
        "✅ <b>تیکت ثبت شد!</b>\\n\\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\\n"
        f"🎫 <b>شماره تیکت:</b> #{ticket_id}\\n\\n"
        "👥 تیم پشتیبانی در کمترین زمان پاسخ خواهد داد.\\n"
        "🔔 پاسخ مستقیماً به شما ارسال می‌شود.\\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.HTML
    )''',
        '''text = get_message_text(
        'support_ticket_created',
        "✅ <b>تیکت ثبت شد!</b>\\n\\n━━━━━━━━━━━━━━━━━━━━━━━━\\n🎫 <b>شماره تیکت:</b> #{ticket_id}\\n\\n👥 تیم پشتیبانی در کمترین زمان پاسخ خواهد داد.\\n🔔 پاسخ مستقیماً به شما ارسال می‌شود.\\n━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    text = text.format(ticket_id=ticket_id)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)'''
    ),
]

def apply_fixes():
    """اعمال تبدیل‌ها"""
    print("🔧 Applying fixes...")
    fixed_count = 0
    
    for filepath, old_text, new_text in FIXES:
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
            print(f"⏭  {filepath}: Already fixed or pattern changed")
    
    return fixed_count

if __name__ == '__main__':
    print("="*60)
    print("🚀 Auto-fix for message conversions")
    print("="*60)
    
    count = apply_fixes()
    
    print("\n" + "="*60)
    if count > 0:
        print(f"✅ Fixed {count} file(s)")
        print("\n📝 Next:")
        print("   1. Test locally")
        print("   2. git add . && git commit && git push")
        print("   3. Restart bot on server")
    else:
        print("✅ All fixes already applied or files not found")
    print("="*60)

#!/usr/bin/env python3
"""
Script to find and fix all admin back buttons in handlers
"""
import os
import re

# Files to check
handler_files = [
    'bot/handlers/admin_advanced_analytics.py',
    'bot/handlers/admin_monitoring.py',
    'bot/handlers/admin_tickets.py',
    'bot/handlers/admin_tutorials.py',
    'bot/handlers/admin_stats_broadcast.py',
    'bot/handlers/admin_messages.py',
    'bot/handlers/admin_panels.py',
    'bot/handlers/admin_plans.py',
    'bot/handlers/admin_cards.py',
    'bot/handlers/admin_wallets.py',
    'bot/handlers/admin_discounts.py',
    'bot/handlers/admin_settings.py',
    'bot/handlers/admin_users.py',
]

# Pattern to find back buttons
pattern = r"InlineKeyboardButton\(['\"].*بازگشت.*['\"],\s*callback_data=['\"]([^'\"]+)['\"]"

results = {}

for filepath in handler_files:
    if not os.path.exists(filepath):
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        matches = re.findall(pattern, content)
        if matches:
            results[filepath] = matches

print("🔍 دکمه‌های بازگشت یافت شده:\n")
for file, callbacks in results.items():
    print(f"\n📁 {file}:")
    for cb in set(callbacks):
        print(f"   ✅ {cb}")

print("\n" + "="*60)
print("\n✨ callback_data های صحیح:")
print("   • admin_main - برگشت به پنل اصلی ادمین")
print("   • start_main - برگشت به منوی اصلی")
print("\n❌ callback_data های احتمالاً اشتباه:")
print("   • admin_stats_menu (وجود ندارد)")
print("   • admin_menu (شاید باید admin_main باشد)")

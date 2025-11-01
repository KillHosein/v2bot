#!/usr/bin/env python3
"""
Script to add BackButtons import to all admin handlers
"""
import os
import re

handlers_to_update = [
    'bot/handlers/admin_users.py',
    'bot/handlers/admin_tutorials.py',
    'bot/handlers/admin_tickets.py',
    'bot/handlers/admin_system.py',
    'bot/handlers/admin_stats_broadcast.py',
    'bot/handlers/admin_settings.py',
    'bot/handlers/admin_plans.py',
    'bot/handlers/admin_panels.py',
    'bot/handlers/admin_messages.py',
    'bot/handlers/admin_discounts.py',
    'bot/handlers/admin_cards.py',
    'bot/handlers/admin_wallets.py',
    'bot/handlers/admin_cron.py',
]

for filepath in handlers_to_update:
    if not os.path.exists(filepath):
        print(f"❌ Skipping {filepath} - not found")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already imported
    if 'from ..helpers.back_buttons import BackButtons' in content:
        print(f"✅ {filepath} - already has BackButtons import")
        continue
    
    # Find the imports section and add BackButtons
    import_pattern = r'(from \.\.db import.*?\n)'
    match = re.search(import_pattern, content)
    
    if match:
        # Add after db imports
        new_content = content.replace(
            match.group(0),
            match.group(0) + 'from ..helpers.back_buttons import BackButtons\n'
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ {filepath} - added BackButtons import")
    else:
        print(f"⚠️  {filepath} - could not find import section")

print("\n✨ Done!")

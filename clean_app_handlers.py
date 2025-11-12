#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to clean duplicate handlers in app.py
اسکریپت پاک کردن handler های تکراری در app.py
"""

import re
import os
from typing import Set, List, Tuple

def extract_handlers_from_app():
    """Extract all handler registrations from app.py"""
    app_path = 'bot/app.py'
    
    if not os.path.exists(app_path):
        print("ERROR: app.py not found!")
        return None
        
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all handler lines
    handler_pattern = r'application\.add_handler\(CallbackQueryHandler\([^)]+\)[^)]*\)'
    handler_lines = re.findall(handler_pattern, content)
    
    return content, handler_lines

def clean_duplicate_handlers():
    """Remove duplicate handler registrations and organize them"""
    
    content, handler_lines = extract_handlers_from_app()
    if content is None:
        return
    
    print(f"Found {len(handler_lines)} handler registrations")
    
    # Track unique handlers by their pattern
    seen_patterns = set()
    unique_handlers = []
    duplicates_removed = 0
    
    for handler_line in handler_lines:
        # Extract pattern from handler line
        pattern_match = re.search(r'pattern=r?[\'"]([^\'"]+)[\'"]', handler_line)
        if pattern_match:
            pattern = pattern_match.group(1)
            if pattern not in seen_patterns:
                seen_patterns.add(pattern)
                unique_handlers.append(handler_line)
            else:
                duplicates_removed += 1
                print(f"Removing duplicate: {pattern}")
    
    print(f"Removed {duplicates_removed} duplicate handlers")
    print(f"Keeping {len(unique_handlers)} unique handlers")
    
    # Create organized handler registration
    organized_handlers = create_organized_handlers(unique_handlers)
    
    return organized_handlers

def create_organized_handlers(handlers: List[str]) -> str:
    """Organize handlers into categories"""
    
    # Categories for organization
    categories = {
        'commands': [],
        'admin_core': [],
        'admin_advanced': [],
        'user_core': [],
        'user_services': [],
        'wallet': [],
        'settings': [],
        'stubs': [],
        'utilities': []
    }
    
    # Categorize each handler
    for handler in handlers:
        if 'start_command' in handler or 'version_command' in handler:
            categories['commands'].append(handler)
        elif ('admin_' in handler and 
              ('stats' in handler or 'approve' in handler or 'reject' in handler or 'manual' in handler or 'xui' in handler or 'wallet_tx' in handler)):
            categories['admin_core'].append(handler)
        elif ('admin_' in handler and 
              ('advanced' in handler or 'chart' in handler or 'monitoring' in handler or 'cache' in handler or 'analytics' in handler)):
            categories['admin_advanced'].append(handler)
        elif ('wallet' in handler or 'topup' in handler or 'transactions' in handler):
            categories['wallet'].append(handler)
        elif ('settings' in handler or 'language' in handler or 'notifications' in handler):
            categories['settings'].append(handler)
        elif ('my_services' in handler or 'support_menu' in handler or 'tutorials' in handler or 'start_main' in handler):
            categories['user_core'].append(handler)
        elif ('service' in handler and ('refresh' in handler or 'revoke' in handler or 'delete' in handler or 'view' in handler)):
            categories['user_services'].append(handler)
        elif ('_handler' in handler and ('stub' in handler.lower() or 'loyalty' in handler or 'guide' in handler)):
            categories['stubs'].append(handler)
        else:
            categories['utilities'].append(handler)
    
    # Build organized content
    organized_content = '''
    # ═══════════════════════════════════════════════════════════════════
    #                       ORGANIZED HANDLER REGISTRATION
    # ═══════════════════════════════════════════════════════════════════
    
    # ═══════════════════════════════════════════════════════════════════
    #                            COMMANDS
    # ═══════════════════════════════════════════════════════════════════
'''
    
    for handler in categories['commands']:
        organized_content += f"    {handler}\n"
    
    organized_content += '''
    # ═══════════════════════════════════════════════════════════════════
    #                         ADMIN CORE HANDLERS  
    # ═══════════════════════════════════════════════════════════════════
'''
    
    for handler in categories['admin_core']:
        organized_content += f"    {handler}\n"
    
    organized_content += '''
    # ═══════════════════════════════════════════════════════════════════
    #                       ADMIN ADVANCED FEATURES
    # ═══════════════════════════════════════════════════════════════════
'''
    
    for handler in categories['admin_advanced']:
        organized_content += f"    {handler}\n"
    
    organized_content += '''
    # ═══════════════════════════════════════════════════════════════════
    #                         USER CORE HANDLERS
    # ═══════════════════════════════════════════════════════════════════
'''
    
    for handler in categories['user_core']:
        organized_content += f"    {handler}\n"
    
    organized_content += '''
    # ═══════════════════════════════════════════════════════════════════
    #                        USER SERVICE ACTIONS
    # ═══════════════════════════════════════════════════════════════════
'''
    
    for handler in categories['user_services']:
        organized_content += f"    {handler}\n"
    
    organized_content += '''
    # ═══════════════════════════════════════════════════════════════════
    #                          WALLET SYSTEM
    # ═══════════════════════════════════════════════════════════════════
'''
    
    for handler in categories['wallet']:
        organized_content += f"    {handler}\n"
    
    organized_content += '''
    # ═══════════════════════════════════════════════════════════════════
    #                       SETTINGS & PREFERENCES
    # ═══════════════════════════════════════════════════════════════════
'''
    
    for handler in categories['settings']:
        organized_content += f"    {handler}\n"
    
    organized_content += '''
    # ═══════════════════════════════════════════════════════════════════
    #                      STUB & FUTURE FEATURES
    # ═══════════════════════════════════════════════════════════════════
'''
    
    for handler in categories['stubs']:
        organized_content += f"    {handler}\n"
    
    organized_content += '''
    # ═══════════════════════════════════════════════════════════════════
    #                       UTILITIES & FALLBACKS
    # ═══════════════════════════════════════════════════════════════════
'''
    
    for handler in categories['utilities']:
        organized_content += f"    {handler}\n"
    
    organized_content += '''
    # ═══════════════════════════════════════════════════════════════════
    #                         DYNAMIC HANDLER
    # ═══════════════════════════════════════════════════════════════════
    # Catch-all dynamic button handler (lowest priority)
    application.add_handler(CallbackQueryHandler(dynamic_button_handler), group=4)
'''
    
    return organized_content

def backup_and_clean():
    """Create backup and clean app.py"""
    
    # Create backup
    import shutil
    backup_path = 'bot/app.py.backup'
    shutil.copy('bot/app.py', backup_path)
    print(f"Backup created: {backup_path}")
    
    # Clean handlers
    organized_handlers = clean_duplicate_handlers()
    
    if organized_handlers:
        print("\nOrganized handler structure created!")
        print("Manual intervention required to replace the handler section in app.py")
        
        # Save organized handlers to file
        with open('organized_handlers.txt', 'w', encoding='utf-8') as f:
            f.write(organized_handlers)
        print("Organized handlers saved to: organized_handlers.txt")

def main():
    """Main function"""
    print("App.py Handler Cleanup Tool")
    print("=" * 60)
    
    backup_and_clean()
    
    print(f"\nNext steps:")
    print("1. Review organized_handlers.txt")
    print("2. Replace handler registration section in app.py") 
    print("3. Test the bot to ensure all handlers work")
    print("4. Remove duplicate handler lines manually")

if __name__ == "__main__":
    main()

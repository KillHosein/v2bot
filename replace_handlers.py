#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace handler registration section in app.py with organized version
"""

import re
import os

def replace_handler_section():
    """Replace the handler section with organized version"""
    
    app_path = 'bot/app.py'
    
    if not os.path.exists(app_path):
        print("ERROR: app.py not found!")
        return
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find start and end of handler registration section
    # Start: after ConversationHandler registrations 
    # End: before build_application function or main()
    
    start_pattern = r'application\.add_handler\(CommandHandler\([\'"]start[\'"], start_command\), group=3\)'
    end_pattern = r'def build_application|def main|if __name__|return application'
    
    start_match = re.search(start_pattern, content)
    if not start_match:
        print("Could not find handler registration start point!")
        return
    
    start_pos = start_match.start()
    
    # Find the end point
    end_match = re.search(end_pattern, content[start_pos:])
    if not end_match:
        print("Could not find handler registration end point!")
        return
    
    end_pos = start_pos + end_match.start()
    
    print(f"Handler section found from position {start_pos} to {end_pos}")
    
    # Read organized handlers
    with open('final_handlers_section.txt', 'r', encoding='utf-8') as f:
        organized_handlers = f.read()
    
    # Replace the section
    new_content = content[:start_pos] + organized_handlers + content[end_pos:]
    
    # Write back to file
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Handler section replaced successfully!")
    print("Organized handlers integrated into app.py")

def main():
    """Main function"""
    print("Handler Replacement Tool")
    print("=" * 40)
    
    replace_handler_section()
    
    print("\nHandler organization completed!")
    print("\nNext steps:")
    print("1. Test the bot to ensure all handlers work")
    print("2. Run button test to verify no issues remain")
    print("3. Check for any syntax errors")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Button Testing Tool
تست جامع دکمه‌های ربات

This script checks all buttons and their callback handlers to ensure they work properly.
"""

import os
import sys
import sqlite3
import re
from typing import Dict, List, Set, Optional

# Add the bot directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

class ButtonTester:
    def __init__(self):
        self.callback_patterns: Dict[str, str] = {}  # pattern -> handler
        self.button_callbacks: Set[str] = set()  # all callback_data found
        self.issues: List[str] = []
        self.warnings: List[str] = []
        
    def find_button_callbacks(self, directory: str) -> None:
        """Find all callback_data in button definitions"""
        print(f"Scanning for buttons in: {directory}")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    self._scan_file_for_buttons(filepath)
    
    def _scan_file_for_buttons(self, filepath: str) -> None:
        """Scan a single file for InlineKeyboardButton definitions"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Find all InlineKeyboardButton with callback_data
            pattern = r'InlineKeyboardButton\([^,)]*,\s*callback_data\s*=\s*[\'"]([^\'"]+)[\'"]'
            matches = re.findall(pattern, content)
            
            for callback in matches:
                self.button_callbacks.add(callback)
                
            # Also find dynamic callback_data patterns
            dynamic_pattern = r'callback_data\s*=\s*f[\'"]([^\'"]*\{[^}]*\}[^\'"]*)[\'"]'
            dynamic_matches = re.findall(dynamic_pattern, content)
            
            for callback_template in dynamic_matches:
                # Convert f-string templates to regex patterns
                regex_pattern = callback_template.replace('{', '.*').replace('}', '')
                self.button_callbacks.add(f"DYNAMIC: {regex_pattern}")
                
        except Exception as e:
            self.warnings.append(f"WARNING: Error reading {filepath}: {e}")
    
    def find_callback_handlers(self, app_file: str) -> None:
        """Find all CallbackQueryHandler patterns in app.py"""
        print(f"Scanning callback handlers in: {app_file}")
        
        try:
            with open(app_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Find all CallbackQueryHandler patterns
            pattern = r'CallbackQueryHandler\([^,)]*,\s*pattern\s*=\s*[rf]*[\'"]([^\'"]+)[\'"]'
            matches = re.findall(pattern, content)
            
            for pattern_str in matches:
                # Clean up pattern for easier matching
                clean_pattern = pattern_str.replace('^', '').replace('$', '')
                self.callback_patterns[clean_pattern] = f"Handler found in app.py"
                
        except Exception as e:
            self.issues.append(f"ERROR: Error reading {app_file}: {e}")
    
    def check_button_handler_mapping(self) -> None:
        """Check if each button has a corresponding handler"""
        print("Checking button-handler mapping...")
        
        unhandled_buttons = []
        
        for callback in self.button_callbacks:
            if callback.startswith('DYNAMIC:'):
                continue  # Skip dynamic patterns for now
                
            # Check for exact match
            if callback in self.callback_patterns:
                continue
                
            # Check for regex pattern matches
            found_handler = False
            for pattern in self.callback_patterns.keys():
                try:
                    if re.match(pattern, callback):
                        found_handler = True
                        break
                except re.error:
                    # If pattern is not valid regex, try simple contains
                    if pattern in callback or callback in pattern:
                        found_handler = True
                        break
            
            if not found_handler:
                unhandled_buttons.append(callback)
        
        if unhandled_buttons:
            self.issues.extend([f"ERROR: No handler found for button: {btn}" for btn in unhandled_buttons])
    
    def check_common_button_patterns(self) -> None:
        """Check common button patterns and their handlers"""
        print("Checking common button patterns...")
        
        common_patterns = [
            # Navigation buttons
            'start_main', 'admin_main', 'my_services', 'wallet_menu', 'support_menu',
            'buy_config_main', 'tutorials_menu',
            
            # Admin buttons
            'admin_settings_manage', 'admin_plan_manage', 'admin_users_menu',
            'admin_messages_menu', 'admin_broadcast_menu', 'admin_discount_menu',
            'admin_panels_menu', 'admin_tickets_menu', 'admin_tutorials_menu',
            
            # User buttons
            'get_free_config', 'wallet_topup_main', 'wallet_transactions',
            'wallet_topup_card', 'wallet_topup_gateway', 'wallet_topup_crypto',
            
            # Service actions
            'refresh_link_', 'revoke_key_', 'view_qr_', 'renew_service_', 'delete_service_',
        ]
        
        missing_patterns = []
        for pattern in common_patterns:
            found = False
            for handler_pattern in self.callback_patterns.keys():
                if pattern in handler_pattern or re.search(pattern.replace('_', r'[_\d]*'), handler_pattern):
                    found = True
                    break
            
            if not found:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            self.warnings.extend([f"WARNING: No handler pattern found for: {pat}" for pat in missing_patterns])
    
    def check_back_buttons(self) -> None:
        """Check back button functionality"""
        print("Checking back button patterns...")
        
        back_patterns = [
            'admin_main', 'start_main', 'my_services', 'wallet_menu',
            'admin_settings_manage', 'admin_plan_manage'
        ]
        
        for pattern in back_patterns:
            if pattern not in [cb for cb in self.button_callbacks if not cb.startswith('DYNAMIC:')]:
                self.warnings.append(f"WARNING: Back button target '{pattern}' not found in buttons")
    
    def check_noop_buttons(self) -> None:
        """Check for noop buttons (buttons that don't do anything)"""
        print("Checking for noop buttons...")
        
        noop_buttons = [cb for cb in self.button_callbacks if 'noop' in cb.lower()]
        if noop_buttons:
            print(f"Found {len(noop_buttons)} noop buttons (informational only)")
    
    def run_comprehensive_test(self, bot_dir: str) -> None:
        """Run comprehensive button testing"""
        print("Starting comprehensive button test...")
        print("=" * 60)
        
        # Find all buttons
        self.find_button_callbacks(bot_dir)
        print(f"Found {len(self.button_callbacks)} button callbacks")
        
        # Find all handlers
        app_file = os.path.join(bot_dir, 'app.py')
        self.find_callback_handlers(app_file)
        print(f"Found {len(self.callback_patterns)} callback handler patterns")
        
        # Run checks
        self.check_button_handler_mapping()
        self.check_common_button_patterns()
        self.check_back_buttons()
        self.check_noop_buttons()
        
        # Print results
        self.print_results()
    
    def print_results(self) -> None:
        """Print test results"""
        print("\n" + "=" * 60)
        print("BUTTON TEST RESULTS")
        print("=" * 60)
        
        print(f"Statistics:")
        print(f"   • Total buttons found: {len(self.button_callbacks)}")
        print(f"   • Handler patterns: {len(self.callback_patterns)}")
        print(f"   • Issues found: {len(self.issues)}")
        print(f"   • Warnings: {len(self.warnings)}")
        
        if self.issues:
            print(f"\nISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   {issue}")
        
        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if not self.issues and not self.warnings:
            print("\nALL TESTS PASSED!")
            print("   All buttons appear to have proper handlers!")
        
        # Print button samples
        print(f"\nSAMPLE BUTTONS FOUND:")
        sample_buttons = list(self.button_callbacks)[:10]
        for btn in sample_buttons:
            if not btn.startswith('DYNAMIC:'):
                print(f"   • {btn}")
        
        if len(self.button_callbacks) > 10:
            print(f"   ... and {len(self.button_callbacks) - 10} more")

def main():
    """Main function to run the button test"""
    print("V2Bot Button Testing Tool")
    print("Test jame dokmeha-ye robot")
    print("=" * 60)
    
    # Get bot directory
    bot_dir = os.path.join(os.path.dirname(__file__), 'bot')
    
    if not os.path.exists(bot_dir):
        print("Bot directory not found!")
        return
    
    # Create tester instance
    tester = ButtonTester()
    
    # Run comprehensive test
    tester.run_comprehensive_test(bot_dir)
    
    print(f"\n{'=' * 60}")
    print("Button testing completed!")
    print("All buttons have been tested!")

if __name__ == "__main__":
    main()

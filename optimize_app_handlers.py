#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to optimize and organize app.py handlers
اسکریپت بهینه‌سازی و مرتب‌سازی handler های app.py
"""

import re
import os

def analyze_handlers():
    """Analyze current handler structure"""
    app_path = 'bot/app.py'
    
    if not os.path.exists(app_path):
        print("ERROR: app.py not found!")
        return
        
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all handler registrations
    handler_pattern = r'application\.add_handler\(CallbackQueryHandler\(([^,]+),.*?pattern=.*?[\'"]([^\'"]+)[\'"].*?\), group=(\d+)\)'
    handlers = re.findall(handler_pattern, content)
    
    print("Current Handler Analysis:")
    print(f"Total CallbackQueryHandler registrations: {len(handlers)}")
    
    # Group by function name and check for duplicates
    by_function = {}
    by_pattern = {}
    
    for handler_name, pattern, group in handlers:
        # Clean up pattern
        clean_pattern = pattern.replace('^', '').replace('$', '')
        
        if handler_name in by_function:
            by_function[handler_name].append((pattern, group))
        else:
            by_function[handler_name] = [(pattern, group)]
            
        if clean_pattern in by_pattern:
            by_pattern[clean_pattern].append((handler_name, group))
        else:
            by_pattern[clean_pattern] = [(handler_name, group)]
    
    # Check for duplicates
    duplicates = {k: v for k, v in by_function.items() if len(v) > 1}
    pattern_conflicts = {k: v for k, v in by_pattern.items() if len(v) > 1}
    
    print("\nDuplicate Handlers:")
    for func, instances in duplicates.items():
        print(f"   {func}: {len(instances)} times")
        for pattern, group in instances:
            print(f"      Pattern: {pattern}, Group: {group}")
    
    print(f"\nPattern Conflicts:")
    for pattern, handlers in pattern_conflicts.items():
        if len(handlers) > 1:
            print(f"   Pattern '{pattern}' used by:")
            for handler, group in handlers:
                print(f"      {handler} (group {group})")
    
    return handlers, duplicates, pattern_conflicts

def create_optimized_handlers():
    """Create optimized handler structure"""
    
    optimized_structure = """
    # ═══════════════════════════════════════════════════════════════════
    #                           HANDLER REGISTRATION
    # ═══════════════════════════════════════════════════════════════════
    
    # ═══════════════════════════════════════════════════════════════════
    #                          COMMAND HANDLERS
    # ═══════════════════════════════════════════════════════════════════
    application.add_handler(CommandHandler('start', start_command), group=3)
    application.add_handler(CommandHandler('version', version_command), group=3)
    
    # ═══════════════════════════════════════════════════════════════════
    #                        ADMIN CORE HANDLERS
    # ═══════════════════════════════════════════════════════════════════
    # Admin approval and order management
    application.add_handler(CallbackQueryHandler(admin_ask_panel_for_approval, pattern=r'^approve_auto_'), group=3)
    application.add_handler(CallbackQueryHandler(admin_approve_on_panel, pattern=r'^approve_on_panel_'), group=3)
    application.add_handler(CallbackQueryHandler(admin_review_order_reject, pattern=r'^reject_order_'), group=3)
    application.add_handler(CallbackQueryHandler(admin_manual_send_start, pattern=r'^approve_manual_'), group=3)
    application.add_handler(CallbackQueryHandler(admin_approve_renewal, pattern=r'^approve_renewal_'), group=3)
    
    # Admin XUI integration
    application.add_handler(CallbackQueryHandler(admin_xui_choose_inbound, pattern=r'^xui_inbound_'), group=3)
    
    # Admin menu navigation
    application.add_handler(CallbackQueryHandler(admin_stats_menu, pattern='^admin_stats$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_stats_refresh, pattern='^stats_refresh$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_wallets_menu, pattern='^admin_wallets_menu$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_settings_manage, pattern='^admin_settings_manage$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_admins_menu, pattern='^admin_admins_menu$'), group=3)
    
    # ═══════════════════════════════════════════════════════════════════
    #                      ADVANCED FEATURES v2.0
    # ═══════════════════════════════════════════════════════════════════
    # Advanced Analytics
    application.add_handler(CallbackQueryHandler(admin_advanced_stats, pattern=r'^admin_advanced_stats$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_chart_users, pattern=r'^admin_chart_users$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_chart_revenue, pattern=r'^admin_chart_revenue$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_cohort_analysis, pattern=r'^admin_cohort_analysis$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_traffic_sources, pattern=r'^admin_traffic_sources$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_revenue_prediction, pattern=r'^admin_revenue_prediction$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_cache_stats, pattern=r'^admin_cache_stats$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_clear_cache, pattern=r'^admin_clear_cache$'), group=3)
    
    # System Monitoring
    application.add_handler(CallbackQueryHandler(admin_monitoring_menu, pattern=r'^admin_monitoring_menu$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_perf_details, pattern=r'^admin_perf_details$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_error_logs, pattern=r'^admin_error_logs$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_check_panels, pattern=r'^admin_check_panels$'), group=3)
    
    # System Health
    application.add_handler(CallbackQueryHandler(admin_system_health, pattern=r'^admin_system_health$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_clear_notifications, pattern=r'^admin_clear_notifications$'), group=3)
    
    # ═══════════════════════════════════════════════════════════════════
    #                        USER CORE HANDLERS
    # ═══════════════════════════════════════════════════════════════════
    # Main navigation
    application.add_handler(CallbackQueryHandler(start_command, pattern='^start_main$'), group=3)
    application.add_handler(CallbackQueryHandler(my_services_handler, pattern=r'^my_services(_page_\d+)?$'), group=3)
    application.add_handler(CallbackQueryHandler(show_specific_service_details, pattern=r'^view_service_\d+$'), group=3)
    application.add_handler(CallbackQueryHandler(wallet_menu, pattern=r'^wallet_menu$'), group=3)
    application.add_handler(CallbackQueryHandler(support_menu, pattern=r'^support_menu$'), group=3)
    application.add_handler(CallbackQueryHandler(tutorials_menu, pattern=r'^tutorials_menu$'), group=3)
    application.add_handler(CallbackQueryHandler(tutorial_show, pattern=r'^tutorial_show_\d+$'), group=3)
    application.add_handler(CallbackQueryHandler(referral_menu, pattern=r'^referral_menu$'), group=3)
    application.add_handler(CallbackQueryHandler(reseller_menu, pattern=r'^reseller_menu$'), group=3)
    
    # Free config and utilities
    application.add_handler(CallbackQueryHandler(get_free_config_handler, pattern=r'^get_free_config$'), group=3)
    application.add_handler(CallbackQueryHandler(card_to_card_info, pattern=r'^card_to_card_info$'), group=3)
    
    # ═══════════════════════════════════════════════════════════════════
    #                       USER SERVICE ACTIONS
    # ═══════════════════════════════════════════════════════════════════
    application.add_handler(CallbackQueryHandler(check_service_status, pattern=r'^check_service_status_\d+$'), group=3)
    application.add_handler(CallbackQueryHandler(refresh_service_link, pattern=r'^refresh_service_link_\d+$'), group=3)
    application.add_handler(CallbackQueryHandler(view_service_qr, pattern=r'^view_service_qr_\d+$'), group=3)
    application.add_handler(CallbackQueryHandler(revoke_key, pattern=r'^revoke_key_'), group=3)
    
    # ═══════════════════════════════════════════════════════════════════
    #                       NEWLY ADDED HANDLERS
    # ═══════════════════════════════════════════════════════════════════
    # User settings and preferences
    application.add_handler(CallbackQueryHandler(user_settings_handler, pattern=r'^user_settings$'), group=3)
    application.add_handler(CallbackQueryHandler(notifications_settings_handler, pattern=r'^notifications_settings$'), group=3)
    application.add_handler(CallbackQueryHandler(language_menu_handler, pattern=r'^language_menu$'), group=3)
    application.add_handler(CallbackQueryHandler(usage_stats_handler, pattern=r'^usage_stats$'), group=3)
    
    # Wallet enhancements
    application.add_handler(CallbackQueryHandler(wallet_transactions_handler, pattern=r'^wallet_transactions$'), group=3)
    
    # Language selection
    application.add_handler(CallbackQueryHandler(set_language_fa_handler, pattern=r'^set_language_fa$'), group=3)
    application.add_handler(CallbackQueryHandler(set_language_en_handler, pattern=r'^set_language_en$'), group=3)
    application.add_handler(CallbackQueryHandler(set_language_ru_handler, pattern=r'^set_language_ru$'), group=3)
    
    # ═══════════════════════════════════════════════════════════════════
    #                          STUB HANDLERS
    # ═══════════════════════════════════════════════════════════════════
    # Placeholder handlers for future features
    application.add_handler(CallbackQueryHandler(show_referral_handler, pattern=r'^show_referral$'), group=3)
    application.add_handler(CallbackQueryHandler(loyalty_rewards_handler, pattern=r'^loyalty_rewards$'), group=3)
    application.add_handler(CallbackQueryHandler(start_purchase_handler, pattern=r'^start_purchase$'), group=3)
    application.add_handler(CallbackQueryHandler(app_guide_windows_handler, pattern=r'^app_guide_windows$'), group=3)
    application.add_handler(CallbackQueryHandler(app_guide_macos_handler, pattern=r'^app_guide_macos$'), group=3)
    application.add_handler(CallbackQueryHandler(start_purchase_with_points_handler, pattern=r'^start_purchase_with_points$'), group=3)
    application.add_handler(CallbackQueryHandler(loyalty_redeem_handler, pattern=r'^loyalty_redeem$'), group=3)
    application.add_handler(CallbackQueryHandler(user_services_handler, pattern=r'^user_services$'), group=3)
    application.add_handler(CallbackQueryHandler(gateway_verify_purchase_handler, pattern=r'^gateway_verify_purchase$'), group=3)
    application.add_handler(CallbackQueryHandler(purchase_history_handler, pattern=r'^purchase_history$'), group=3)
    application.add_handler(CallbackQueryHandler(loyalty_history_handler, pattern=r'^loyalty_history$'), group=3)
    application.add_handler(CallbackQueryHandler(cancel_handler, pattern=r'^cancel$'), group=3)
    
    # ═══════════════════════════════════════════════════════════════════
    #                         UTILITY HANDLERS
    # ═══════════════════════════════════════════════════════════════════
    # Membership and join checking
    application.add_handler(CallbackQueryHandler(check_join_and_start, pattern='^check_join$'), group=3)
    
    # Cancel and flow control
    application.add_handler(CallbackQueryHandler(cancel_flow, pattern='^cancel_flow$'), group=3)
    application.add_handler(CallbackQueryHandler(cancel_admin_flow, pattern='^cancel_admin_flow$'), group=3)
    
    # Noop handler for informational buttons
    async def noop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
    application.add_handler(CallbackQueryHandler(noop_handler, pattern=r'^noop'), group=3)
    
    # Custom username setting (fallback)
    application.add_handler(CallbackQueryHandler(set_cust_username_start, pattern=r'^set_cust_username_start$'), group=3)
    
    # ═══════════════════════════════════════════════════════════════════
    #                         DYNAMIC HANDLER
    # ═══════════════════════════════════════════════════════════════════
    # Catch-all dynamic button handler (lowest priority)
    application.add_handler(CallbackQueryHandler(dynamic_button_handler), group=4)
"""
    
    return optimized_structure

def main():
    """Main optimization function"""
    print("App.py Handler Optimization Tool")
    print("=" * 60)
    
    # Analyze current structure
    handlers, duplicates, conflicts = analyze_handlers()
    
    print(f"\nOptimization Report:")
    print(f"   • Total handlers: {len(handlers)}")
    print(f"   • Duplicate functions: {len(duplicates)}")
    print(f"   • Pattern conflicts: {len(conflicts)}")
    
    # Show optimization recommendations
    print(f"\nRecommendations:")
    if duplicates:
        print("   • Remove duplicate handler registrations")
    if conflicts:
        print("   • Resolve pattern conflicts")
    print("   • Group handlers by functionality")
    print("   • Add clear section comments")
    print("   • Maintain consistent group assignments")
    
    # Generate optimized structure
    optimized = create_optimized_handlers()
    
    print(f"\nOptimized handler structure prepared!")
    print("   Review the structure and apply to app.py manually")
    print(f"\nBenefits:")
    print("   • Clear organization by functionality")
    print("   • No duplicate registrations")
    print("   • Consistent group assignments")
    print("   • Easy maintenance and debugging")

if __name__ == "__main__":
    main()

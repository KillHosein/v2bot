"""
Admin Monitoring Handlers
System health and performance monitoring for admins
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from ..monitoring import get_monitor
from ..config import logger


async def admin_monitoring_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show monitoring dashboard"""
    query = update.callback_query
    await query.answer()
    
    try:
        await query.message.edit_text("⏳ در حال بررسی وضعیت سیستم...", parse_mode=ParseMode.HTML)
    except Exception:
        pass
    
    monitor = get_monitor()
    
    # Run health check
    health = await monitor.run_full_health_check()
    perf = monitor.get_performance_stats()
    sys_stats = monitor.get_system_stats()
    
    # Build status message
    status_icon = "✅" if health['overall_status'] == 'healthy' else "⚠️"
    
    message = f"{status_icon} <b>داشبورد مانیتورینگ</b>\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Overall status
    message += f"🔧 <b>وضعیت کلی:</b> <code>{health['overall_status'].upper()}</code>\n\n"
    
    # Performance
    message += "📊 <b>عملکرد:</b>\n"
    message += f"   • Uptime: <code>{perf['uptime_formatted']}</code>\n"
    message += f"   • تعداد درخواست‌ها: <code>{perf['total_requests']:,}</code>\n"
    message += f"   • نرخ خطا: <code>{perf['error_rate']:.2f}%</code>\n"
    message += f"   • RPS: <code>{perf['requests_per_minute']:.1f}/min</code>\n\n"
    
    # System resources
    if sys_stats:
        message += "💻 <b>منابع سیستم:</b>\n"
        message += f"   • CPU: <code>{sys_stats['cpu']['percent']:.1f}%</code>\n"
        message += f"   • RAM: <code>{sys_stats['memory']['percent']:.1f}%</code> "
        message += f"(<code>{sys_stats['memory']['used_gb']:.1f}/{sys_stats['memory']['total_gb']:.1f} GB</code>)\n"
        message += f"   • Disk: <code>{sys_stats['disk']['percent']:.1f}%</code>\n\n"
    
    # Component statuses
    message += "🔌 <b>وضعیت اجزا:</b>\n"
    for component, status in health['components'].items():
        icon = "✅" if status['status'] == 'healthy' else "❌" if status['status'] == 'unhealthy' else "⚠️"
        comp_name = status.get('name', component).replace('_', ' ').title()
        message += f"   {icon} {comp_name}: <code>{status['status']}</code>\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━"
    
    keyboard = [
        [
            InlineKeyboardButton("📊 جزئیات عملکرد", callback_data='admin_perf_details'),
            InlineKeyboardButton("❌ لاگ خطاها", callback_data='admin_error_logs')
        ],
        [
            InlineKeyboardButton("🔌 بررسی پنل‌ها", callback_data='admin_check_panels'),
            InlineKeyboardButton("💾 وضعیت Cache", callback_data='admin_cache_stats')
        ],
        [
            InlineKeyboardButton("🔄 بروزرسانی", callback_data='admin_monitoring_menu'),
            InlineKeyboardButton("🔙 بازگشت", callback_data='admin_main')
        ]
    ]
    
    await query.message.edit_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def admin_perf_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed performance stats"""
    query = update.callback_query
    await query.answer()
    
    monitor = get_monitor()
    perf = monitor.get_performance_stats()
    
    message = "📊 <b>جزئیات عملکرد</b>\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += f"⏱ <b>Uptime:</b> <code>{perf['uptime_formatted']}</code>\n"
    message += f"   (<code>{perf['uptime_seconds']:.0f}</code> ثانیه)\n\n"
    message += f"📈 <b>درخواست‌ها:</b>\n"
    message += f"   • کل: <code>{perf['total_requests']:,}</code>\n"
    message += f"   • در دقیقه: <code>{perf['requests_per_minute']:.1f}</code>\n"
    message += f"   • کند (>2s): <code>{perf['slow_requests_count']}</code>\n\n"
    message += f"❌ <b>خطاها:</b>\n"
    message += f"   • کل: <code>{perf['total_errors']:,}</code>\n"
    message += f"   • نرخ: <code>{perf['error_rate']:.2f}%</code>\n\n"
    
    # Show slow requests
    if monitor.slow_requests:
        message += "🐌 <b>آخرین درخواست‌های کند:</b>\n"
        for req in monitor.slow_requests[-5:]:
            message += f"   • {req['handler']}: <code>{req['duration']:.2f}s</code>\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_monitoring_menu')]]
    
    await query.message.edit_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def admin_error_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent error logs"""
    query = update.callback_query
    await query.answer()
    
    monitor = get_monitor()
    errors = monitor.get_recent_errors(limit=10)
    
    if not errors:
        message = "✅ <b>هیچ خطایی ثبت نشده!</b>\n\nسیستم به درستی کار می‌کند."
    else:
        message = "❌ <b>آخرین خطاها</b>\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, error in enumerate(errors[:5], 1):
            timestamp = error['timestamp'].split('T')[1][:8]  # Just time
            message += f"<b>{i}. {error['error_type']}</b>\n"
            message += f"   ⏰ {timestamp}\n"
            message += f"   📝 {error['error_message'][:50]}...\n"
            if error['handler_name']:
                message += f"   🔧 Handler: <code>{error['handler_name']}</code>\n"
            message += "\n"
        
        message += f"<i>نمایش {len(errors[:5])} خطای اخیر</i>\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_monitoring_menu')]]
    
    await query.message.edit_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def admin_check_panels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check all panel health statuses"""
    query = update.callback_query
    await query.answer("در حال بررسی پنل‌ها...")
    
    try:
        from ..db import query_db
        panels = query_db("SELECT id, name FROM panels WHERE enabled = 1")
        
        if not panels:
            await query.message.reply_text("❌ هیچ پنل فعالی یافت نشد.")
            return
        
        monitor = get_monitor()
        message = "🔌 <b>وضعیت پنل‌ها</b>\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for panel in panels:
            health = await monitor.check_panel_health(panel['id'])
            
            icon = "✅" if health['status'] == 'healthy' else "❌"
            message += f"{icon} <b>{panel['name']}</b>\n"
            message += f"   • وضعیت: <code>{health['status']}</code>\n"
            message += f"   • زمان پاسخ: <code>{health['response_time']:.3f}s</code>\n"
            if health['message']:
                message += f"   • پیام: <code>{health['message'][:50]}</code>\n"
            message += "\n"
        
        message += "━━━━━━━━━━━━━━━━━━━━━━━━"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_monitoring_menu')]]
        
        await query.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Check panels error: {e}")
        await query.message.reply_text(f"❌ خطا: {str(e)}")

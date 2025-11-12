"""
Advanced Analytics Handlers for Admin
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from ..analytics import AdvancedAnalytics, format_stats_message
from ..cache_manager import get_cache
from ..config import logger
from ..helpers.back_buttons import BackButtons


async def admin_advanced_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show advanced statistics dashboard"""
    query = update.callback_query
    await query.answer()
    
    try:
        await query.message.edit_text("⏳ در حال تولید آمار پیشرفته...", parse_mode=ParseMode.HTML)
    except Exception:
        pass
    
    analytics = AdvancedAnalytics()
    stats = analytics.get_overview_stats()
    
    if not stats:
        await query.message.edit_text(
            "❌ خطا در دریافت آمار",
            reply_markup=InlineKeyboardMarkup([[BackButtons.to_admin_main()]])
        )
        return
    
    message_text = format_stats_message(stats)
    
    keyboard = [
        [
            InlineKeyboardButton("📈 نمودار رشد کاربران", callback_data='admin_chart_users'),
            InlineKeyboardButton("💰 نمودار درآمد", callback_data='admin_chart_revenue')
        ],
        [
            InlineKeyboardButton("👥 تحلیل Cohort", callback_data='admin_cohort_analysis'),
            InlineKeyboardButton("📊 منابع ترافیک", callback_data='admin_traffic_sources')
        ],
        [
            InlineKeyboardButton("🔮 پیش‌بینی درآمد", callback_data='admin_revenue_prediction'),
            InlineKeyboardButton("💾 وضعیت Cache", callback_data='admin_cache_stats')
        ],
        [
            InlineKeyboardButton("🧠 یادگیری ماشین", callback_data='ml_pipeline'),
            InlineKeyboardButton("💡 قیمت‌گذاری هوشمند", callback_data='smart_pricing')
        ],
        [
            InlineKeyboardButton("🔗 مدیریت Webhook", callback_data='webhook_management'),
            InlineKeyboardButton("📱 اپ موبایل", callback_data='mobile_app_management')
        ],
        [
            InlineKeyboardButton("☁️ زیرساخت ابری", callback_data='cloud_infrastructure'),
            InlineKeyboardButton("🔒 مرکز امنیت", callback_data='cyber_security_center')
        ],
        [
            BackButtons.refresh('admin_advanced_stats'),
            BackButtons.to_admin_main()
        ]
    ]
    
    await query.message.edit_text(
        message_text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def admin_chart_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send user growth chart"""
    query = update.callback_query
    await query.answer("در حال تولید نمودار...")
    
    try:
        analytics = AdvancedAnalytics()
        data = analytics.get_growth_chart_data(days=30)
        
        chart_buffer = analytics.generate_chart(data, chart_type='user_growth')
        
        if chart_buffer:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=chart_buffer,
                caption="📈 <b>نمودار رشد کاربران (30 روز اخیر)</b>",
                parse_mode=ParseMode.HTML
            )
        else:
            await query.message.reply_text("❌ خطا در تولید نمودار")
            
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        await query.message.reply_text(f"❌ خطا: {str(e)}")


async def admin_chart_revenue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send revenue chart"""
    query = update.callback_query
    await query.answer("در حال تولید نمودار...")
    
    try:
        analytics = AdvancedAnalytics()
        data = analytics.get_growth_chart_data(days=30)
        
        chart_buffer = analytics.generate_chart(data, chart_type='revenue')
        
        if chart_buffer:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=chart_buffer,
                caption="💰 <b>نمودار درآمد روزانه (30 روز اخیر)</b>",
                parse_mode=ParseMode.HTML
            )
        else:
            await query.message.reply_text("❌ خطا در تولید نمودار")
            
    except Exception as e:
        logger.error(f"Revenue chart error: {e}")
        await query.message.reply_text(f"❌ خطا: {str(e)}")


async def admin_cohort_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cohort analysis"""
    query = update.callback_query
    await query.answer()
    
    try:
        analytics = AdvancedAnalytics()
        cohorts = analytics.get_user_cohort_analysis()
        
        if not cohorts:
            await query.message.reply_text("❌ داده‌ای برای نمایش وجود ندارد")
            return
        
        message = "👥 <b>تحلیل Cohort (نرخ تبدیل ماهانه)</b>\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for cohort in cohorts:
            month = cohort['cohort_month']
            users = cohort['users']
            converted = cohort['converted']
            rate = cohort['conversion_rate']
            
            message += f"📅 <b>{month}</b>\n"
            message += f"   • کاربران: <code>{users}</code>\n"
            message += f"   • خرید کرده: <code>{converted}</code>\n"
            message += f"   • نرخ تبدیل: <code>{rate}%</code>\n\n"
        
        message += "━━━━━━━━━━━━━━━━━━━━━━━━"
        
        keyboard = [[BackButtons.to_advanced_stats()]]
        
        await query.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Cohort analysis error: {e}")
        await query.message.reply_text(f"❌ خطا: {str(e)}")


async def admin_traffic_sources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show traffic sources"""
    query = update.callback_query
    await query.answer()
    
    try:
        analytics = AdvancedAnalytics()
        sources = analytics.get_traffic_sources()
        
        if not sources:
            await query.message.reply_text("❌ داده‌ای برای نمایش وجود ندارد")
            return
        
        message = "📊 <b>منابع ترافیک</b>\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        total = sum(s['count'] for s in sources)
        
        for source in sources:
            count = source['count']
            percentage = (count / total * 100) if total > 0 else 0
            icon = "🔗" if source['source'] == 'Referral' else "🌐"
            
            message += f"{icon} <b>{source['source']}</b>\n"
            message += f"   • تعداد: <code>{count}</code> (<code>{percentage:.1f}%</code>)\n\n"
        
        message += f"📦 <b>جمع کل:</b> <code>{total}</code> کاربر\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━"
        
        keyboard = [[BackButtons.to_advanced_stats()]]
        
        await query.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Traffic sources error: {e}")
        await query.message.reply_text(f"❌ خطا: {str(e)}")


async def admin_revenue_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show revenue prediction"""
    query = update.callback_query
    await query.answer()
    
    try:
        analytics = AdvancedAnalytics()
        prediction = analytics.predict_revenue_next_month()
        stats = analytics.get_overview_stats()
        
        current_month = stats['revenue']['month']
        growth = ((prediction - current_month) / current_month * 100) if current_month > 0 else 0
        
        message = "🔮 <b>پیش‌بینی درآمد ماه آینده</b>\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += f"📊 <b>درآمد ماه جاری:</b>\n"
        message += f"   <code>{current_month:,.0f}</code> تومان\n\n"
        message += f"🔮 <b>پیش‌بینی ماه آینده:</b>\n"
        message += f"   <code>{prediction:,.0f}</code> تومان\n\n"
        message += f"📈 <b>نرخ رشد پیش‌بینی شده:</b>\n"
        message += f"   <code>{growth:+.1f}%</code>\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += "⚠️ <i>این پیش‌بینی بر اساس روند فعلی است</i>"
        
        keyboard = [[BackButtons.to_advanced_stats()]]
        
        await query.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Revenue prediction error: {e}")
        await query.message.reply_text(f"❌ خطا: {str(e)}")


async def admin_cache_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cache statistics"""
    query = update.callback_query
    await query.answer()
    
    try:
        cache = get_cache()
        stats = cache.get_stats()
        
        message = "💾 <b>وضعیت Cache</b>\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += f"🔧 <b>نوع:</b> <code>{stats['type'].upper()}</code>\n"
        message += f"🔑 <b>تعداد کلیدها:</b> <code>{stats['total_keys']}</code>\n"
        
        if stats['type'] == 'redis':
            message += f"✅ <b>Hits:</b> <code>{stats['hits']}</code>\n"
            message += f"❌ <b>Misses:</b> <code>{stats['misses']}</code>\n"
            message += f"💽 <b>حافظه استفاده شده:</b> <code>{stats['memory_used']}</code>\n"
            
            if stats['hits'] + stats['misses'] > 0:
                hit_rate = stats['hits'] / (stats['hits'] + stats['misses']) * 100
                message += f"📊 <b>نرخ Hit:</b> <code>{hit_rate:.1f}%</code>\n"
        
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━"
        
        keyboard = [
            [InlineKeyboardButton("🗑️ پاک کردن Cache", callback_data='admin_clear_cache')],
            [BackButtons.to_advanced_stats()]
        ]
        
        await query.message.edit_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        await query.message.reply_text(f"❌ خطا: {str(e)}")


async def admin_clear_cache(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all cache"""
    query = update.callback_query
    await query.answer()
    
    try:
        cache = get_cache()
        cache.clear_pattern('*')
        
        await query.message.edit_text(
            "✅ <b>Cache پاک شد!</b>\n\n"
            "تمام داده‌های کش شده حذف شدند.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                BackButtons.custom("🔙 بازگشت", 'admin_cache_stats')
            ]])
        )
        
    except Exception as e:
        logger.error(f"Clear cache error: {e}")
        await query.message.reply_text(f"❌ خطا: {str(e)}")

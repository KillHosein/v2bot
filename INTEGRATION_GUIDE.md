# 🔗 راهنمای یکپارچه‌سازی قابلیت‌های پیشرفته

## مراحل اضافه کردن به bot/app.py

### 1. Import های جدید

در بالای فایل `bot/app.py` اضافه کنید:

```python
# Advanced features
from .handlers.admin_advanced_analytics import (
    admin_advanced_stats, admin_chart_users, admin_chart_revenue,
    admin_cohort_analysis, admin_traffic_sources, admin_revenue_prediction,
    admin_cache_stats, admin_clear_cache
)
from .handlers.admin_monitoring import (
    admin_monitoring_menu, admin_perf_details, admin_error_logs,
    admin_check_panels
)
from .handlers.user_language import (
    language_menu, set_language, preferences_menu
)
from .cache_manager import get_cache
from .monitoring import get_monitor
from .i18n import setup_i18n_tables
```

### 2. راه‌اندازی سیستم‌ها

در تابع `build_application()` بعد از ساخت `application`:

```python
def build_application():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Initialize advanced systems
    try:
        # Setup i18n tables
        setup_i18n_tables()
        logger.info("✅ i18n system initialized")
    except Exception as e:
        logger.warning(f"⚠️ i18n initialization failed: {e}")
    
    try:
        # Initialize cache
        cache = get_cache()
        logger.info(f"✅ Cache system initialized: {cache.get_stats()['type']}")
    except Exception as e:
        logger.warning(f"⚠️ Cache initialization failed: {e}")
    
    try:
        # Initialize monitoring
        monitor = get_monitor()
        logger.info("✅ Monitoring system initialized")
    except Exception as e:
        logger.warning(f"⚠️ Monitoring initialization failed: {e}")
    
    # ... ادامه کد
```

### 3. اضافه کردن Handler ها

قبل از `return application`:

```python
    # Advanced Analytics (Admin)
    application.add_handler(CallbackQueryHandler(admin_advanced_stats, pattern=r'^admin_advanced_stats$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_chart_users, pattern=r'^admin_chart_users$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_chart_revenue, pattern=r'^admin_chart_revenue$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_cohort_analysis, pattern=r'^admin_cohort_analysis$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_traffic_sources, pattern=r'^admin_traffic_sources$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_revenue_prediction, pattern=r'^admin_revenue_prediction$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_cache_stats, pattern=r'^admin_cache_stats$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_clear_cache, pattern=r'^admin_clear_cache$'), group=3)
    
    # Monitoring (Admin)
    application.add_handler(CallbackQueryHandler(admin_monitoring_menu, pattern=r'^admin_monitoring_menu$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_perf_details, pattern=r'^admin_perf_details$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_error_logs, pattern=r'^admin_error_logs$'), group=3)
    application.add_handler(CallbackQueryHandler(admin_check_panels, pattern=r'^admin_check_panels$'), group=3)
    
    # Language & Preferences (User)
    application.add_handler(CallbackQueryHandler(language_menu, pattern=r'^language_menu$'), group=3)
    application.add_handler(CallbackQueryHandler(set_language, pattern=r'^set_lang_\w+$'), group=3)
    application.add_handler(CallbackQueryHandler(preferences_menu, pattern=r'^preferences_menu$'), group=3)

    return application
```

### 4. بروزرسانی منوی ادمین

در `bot/helpers/admin_menu.py` یا جایی که منوی ادمین ساخته می‌شود:

```python
def get_admin_main_keyboard():
    return [
        [InlineKeyboardButton("👥 کاربران", callback_data='admin_users_menu'),
         InlineKeyboardButton("📦 سفارشات", callback_data='admin_orders_menu')],
        [InlineKeyboardButton("📊 آمار", callback_data='admin_stats_menu'),
         InlineKeyboardButton("💰 کیف پول‌ها", callback_data='admin_wallet_tx_menu')],
        [InlineKeyboardButton("🎯 آمار پیشرفته", callback_data='admin_advanced_stats'),  # جدید
         InlineKeyboardButton("📡 مانیتورینگ", callback_data='admin_monitoring_menu')],  # جدید
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data='admin_settings_menu'),
         InlineKeyboardButton("🎫 تیکت‌ها", callback_data='admin_tickets_menu')],
        [InlineKeyboardButton("🏠 بازگشت", callback_data='start_main')]
    ]
```

### 5. بروزرسانی منوی کاربر

برای اضافه کردن دکمه تنظیمات/زبان در `bot/helpers/keyboards.py`:

```python
def build_start_menu_keyboard(user_id: int = None):
    from ..i18n import t
    
    keyboard = [
        [InlineKeyboardButton(t('menu_services', user_id), callback_data='my_services'),
         InlineKeyboardButton(t('menu_buy', user_id), callback_data='buy_config_main')],
        [InlineKeyboardButton(t('menu_wallet', user_id), callback_data='wallet_menu'),
         InlineKeyboardButton(t('menu_support', user_id), callback_data='support_menu')],
        [InlineKeyboardButton(t('menu_tutorials', user_id), callback_data='tutorials_menu'),
         InlineKeyboardButton(t('menu_referral', user_id), callback_data='referral_menu')],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data='preferences_menu')]  # جدید
    ]
    return keyboard
```

### 6. اضافه کردن Job های خودکار

برای گزارش‌گیری و نظارت خودکار:

```python
from datetime import time as dt_time

async def daily_stats_report(context):
    """ارسال گزارش روزانه به ادمین"""
    from .analytics import AdvancedAnalytics, format_stats_message
    from .config import ADMIN_ID
    
    try:
        analytics = AdvancedAnalytics()
        stats = analytics.get_overview_stats()
        message = format_stats_message(stats)
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📊 <b>گزارش روزانه</b>\n\n{message}",
            parse_mode=ParseMode.HTML
        )
        
        # ارسال نمودار
        data = analytics.get_growth_chart_data(days=7)
        chart = analytics.generate_chart(data, 'revenue')
        if chart:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=chart,
                caption="💰 نمودار درآمد هفته اخیر"
            )
    except Exception as e:
        logger.error(f"Daily report error: {e}")

async def health_check_job(context):
    """بررسی سلامت سیستم"""
    from .monitoring import get_monitor
    from .config import ADMIN_ID
    
    try:
        monitor = get_monitor()
        health = await monitor.run_full_health_check()
        
        if health['overall_status'] != 'healthy':
            message = "⚠️ <b>هشدار سیستم!</b>\n\n"
            message += f"وضعیت: <code>{health['overall_status']}</code>\n\n"
            
            for comp, status in health['components'].items():
                if status['status'] != 'healthy':
                    message += f"❌ {comp}: {status['message']}\n"
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=message,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Health check error: {e}")

# اضافه کردن job ها به application
def setup_jobs(application):
    job_queue = application.job_queue
    
    # گزارش روزانه ساعت 9 صبح
    job_queue.run_daily(
        daily_stats_report,
        time=dt_time(hour=9, minute=0)
    )
    
    # بررسی سلامت هر 10 دقیقه
    job_queue.run_repeating(
        health_check_job,
        interval=600,  # 10 minutes
        first=10
    )

# در تابع build_application
def build_application():
    # ... کد قبلی
    
    setup_jobs(application)
    
    return application
```

---

## 🧪 تست قابلیت‌های جدید

### 1. تست Cache

```python
python -c "
from bot.cache_manager import get_cache
cache = get_cache()
cache.set('test', 'value', ttl=60)
print('Cache test:', cache.get('test'))
print('Cache stats:', cache.get_stats())
"
```

### 2. تست Analytics

```python
python -c "
from bot.analytics import AdvancedAnalytics
analytics = AdvancedAnalytics()
stats = analytics.get_overview_stats()
print('Total users:', stats['users']['total'])
print('Active orders:', stats['orders']['active'])
"
```

### 3. تست i18n

```python
python -c "
from bot.i18n import get_i18n
i18n = get_i18n()
print('Languages:', i18n.get_available_languages())
print('Welcome FA:', i18n.t('welcome', 'fa', name='علی'))
print('Welcome EN:', i18n.t('welcome', 'en', name='Ali'))
"
```

### 4. تست Monitoring

```python
python -c "
import asyncio
from bot.monitoring import get_monitor

async def test():
    monitor = get_monitor()
    health = await monitor.run_full_health_check()
    print('Overall status:', health['overall_status'])
    print('Components:', list(health['components'].keys()))

asyncio.run(test())
"
```

---

## 📝 Checklist نصب

- [ ] نصب Redis
- [ ] بروزرسانی requirements.txt
- [ ] اضافه کردن imports به app.py
- [ ] راه‌اندازی سیستم‌ها در build_application
- [ ] اضافه کردن handler های جدید
- [ ] بروزرسانی منوی ادمین
- [ ] بروزرسانی منوی کاربر
- [ ] اضافه کردن job های خودکار
- [ ] تست همه قابلیت‌ها
- [ ] بررسی لاگ‌ها

---

## 🚀 راه‌اندازی نهایی

```bash
# 1. نصب Redis
sudo apt install redis-server
sudo systemctl start redis

# 2. نصب پکیج‌ها
cd v2bot
pip install -r requirements.txt

# 3. تست
python -m pytest tests/  # اگر تست دارید

# 4. اجرا
python -m bot.run

# 5. بررسی لاگ
# باید این پیام‌ها را ببینید:
# ✅ i18n system initialized
# ✅ Cache system initialized: redis
# ✅ Monitoring system initialized
```

---

## 🎯 دستورات مفید

### پاک کردن Cache
```bash
redis-cli FLUSHDB
```

### مشاهده لاگ‌های خطا
```bash
tail -f bot.log | grep ERROR
```

### بررسی استفاده از حافظه
```bash
redis-cli INFO memory | grep used_memory_human
```

### Backup دیتابیس
```bash
sqlite3 bot.db ".backup bot_backup.db"
```

---

**نکته:** همه این تغییرات backward-compatible هستند و ربات بدون آنها هم کار می‌کند.

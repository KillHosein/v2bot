# Wings Bot - بهینه‌سازی عملکرد

این فایل شامل راهنمای بهینه‌سازی عملکرد ربات برای کاهش کندی است.

## تغییرات اعمال شده

### 1. بهبود دیتابیس
- ✅ اضافه شدن ایندکس‌های جدید برای جداول پرتردد:
  - `idx_orders_panel_status` - برای کوئری‌های سفارشات بر اساس پنل و وضعیت
  - `idx_orders_username` - برای جستجوی سریع نام کاربری
  - `idx_tickets_status` - برای فیلتر تیکت‌ها بر اساس وضعیت
  - `idx_tickets_user` - برای جستجوی تیکت‌های کاربر
  - `idx_users_banned` - برای فیلتر کاربران مسدود
  - `idx_referrals_referrer` - برای کوئری‌های ارجاع

### 2. بهبود فایل بکاپ
- ✅ اضافه شدن تمام جداول مهم به فایل بکاپ:
  - کاربران (users)
  - سفارشات (orders)
  - پلن‌ها (plans)
  - پنل‌ها (panels)
  - تراکنش‌های کیف پول (wallet_transactions)
  - تیکت‌ها (tickets)
  - کدهای تخفیف (discount_codes)
  - کارت‌ها (cards)
  - ارجاعات (referrals)
  - ادمین‌ها (admins)

### 3. بهینه‌سازی‌های کدی
- ✅ رفع مشکل دکمه خاموش/روشن ربات
- ✅ اضافه کردن handler برای سفارشات در انتظار
- ✅ حذف دکمه غیرضروری "تغییر کلید اتصال" از یادآوری تمدید
- ✅ اضافه کردن handler برای دکمه "یادآوری فردا"

## توصیه‌های بیشتر برای بهبود عملکرد

### 1. تنظیمات دیتابیس
اگر دیتابیس شما بزرگ است (بیش از 10,000 رکورد)، این تنظیمات را در ابتدای `db.py` اضافه کنید:

```python
# در تابع db_setup، بعد از ایجاد connection:
cursor.execute("PRAGMA cache_size = -64000")  # 64MB cache
cursor.execute("PRAGMA temp_store = MEMORY")
cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB memory-mapped I/O
```

### 2. کاهش لاگ‌های غیرضروری
در محیط production، سطح لاگ را به WARNING تغییر دهید:
```python
# در config.py
logging.basicConfig(
    level=logging.WARNING,  # به جای INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 3. استفاده از Connection Pool
برای کاربردهای با بار بالا، از connection pooling استفاده کنید.

### 4. کش کردن نتایج
برای داده‌هایی که کمتر تغییر می‌کنند (مثل پلن‌ها، تنظیمات)، از کش استفاده کنید:

```python
from functools import lru_cache
from datetime import datetime, timedelta

_settings_cache = {}
_cache_time = {}

def get_setting_cached(key, max_age_seconds=60):
    """Get setting with cache"""
    now = datetime.now()
    if key in _settings_cache:
        if (now - _cache_time[key]).seconds < max_age_seconds:
            return _settings_cache[key]
    
    value = query_db("SELECT value FROM settings WHERE key=?", (key,), one=True)
    _settings_cache[key] = value
    _cache_time[key] = now
    return value
```

### 5. بهینه‌سازی کوئری‌های سنگین
کوئری‌های زیر را بهینه کنید:

**قبل:**
```sql
SELECT * FROM orders WHERE user_id = ?
```

**بعد:**
```sql
SELECT id, status, plan_id, timestamp FROM orders WHERE user_id = ? LIMIT 50
```

### 6. استفاده از Batch Processing
برای عملیات دسته‌ای، از executemany استفاده کنید:

```python
# به جای loop
data = [(val1, val2), (val3, val4), ...]
cursor.executemany("INSERT INTO table VALUES (?, ?)", data)
```

### 7. تنظیمات Telegram Bot
در `app.py`:
```python
# اضافه کردن timeout بیشتر
application = Application.builder().token(BOT_TOKEN).read_timeout(30).write_timeout(30).build()
```

### 8. پاکسازی دوره‌ای
یک job برای پاکسازی داده‌های قدیمی اضافه کنید:
- سفارشات رد شده قدیمی‌تر از 30 روز
- تیکت‌های بسته شده قدیمی‌تر از 90 روز
- لاگ‌های قدیمی

### 9. مانیتورینگ
برای شناسایی نقاط کند، زمان‌سنجی اضافه کنید:

```python
import time

def timing_decorator(func):
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        if duration > 2:  # بیش از 2 ثانیه
            logger.warning(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

### 10. استفاده از Async I/O
مطمئن شوید تمام عملیات شبکه (API calls به پنل) async هستند.

## بررسی عملکرد

برای بررسی عملکرد دیتابیس:
```sql
ANALYZE;
PRAGMA optimize;
```

برای مشاهده آمار:
```sql
SELECT * FROM sqlite_stat1;
```

## نتیجه‌گیری

با اعمال این تغییرات، عملکرد ربات باید به طور قابل توجهی بهبود یابد. اگر همچنان مشکل کندی دارید:
1. حجم دیتابیس را بررسی کنید
2. سرعت اتصال به پنل‌ها را چک کنید  
3. منابع سرور (CPU, RAM, Disk I/O) را مانیتور کنید
4. تعداد کاربران همزمان را در نظر بگیرید

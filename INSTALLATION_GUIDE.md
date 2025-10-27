# Wings Bot - راهنمای نصب و اعمال تغییرات

این راهنما برای اعمال تغییرات و رفع مشکلات جدید Wings Bot است.

## 📋 فهرست مطالب
1. [پیش‌نیازها](#پیش-نیازها)
2. [نحوه اعمال تغییرات](#نحوه-اعمال-تغییرات)
3. [تست عملکرد](#تست-عملکرد)
4. [رفع مشکلات احتمالی](#رفع-مشکلات-احتمالی)

---

## پیش‌نیازها

✅ Python 3.8 یا بالاتر  
✅ python-telegram-bot 20.x  
✅ دسترسی به سرور و فایل‌های ربات  
✅ بکاپ از دیتابیس فعلی  

---

## نحوه اعمال تغییرات

### روش 1: اعمال خودکار (توصیه می‌شود)

#### مرحله 1: متوقف کردن ربات
```bash
# اگر با systemd اجرا می‌کنید:
sudo systemctl stop v2bot

# اگر با screen اجرا می‌کنید:
screen -r v2bot
# سپس Ctrl+C برای متوقف کردن
```

#### مرحله 2: بکاپ گیری
```bash
cd /path/to/v2bot-master

# بکاپ دستی دیتابیس
cp bot.db bot.db.backup_$(date +%Y%m%d)

# بکاپ کل پروژه (اختیاری)
cd ..
tar -czf v2bot-backup-$(date +%Y%m%d).tar.gz v2bot-master/
```

#### مرحله 3: اجرای اسکریپت بهینه‌سازی
```bash
cd /path/to/v2bot-master

# اعطای مجوز اجرا
chmod +x apply_performance_fixes.py

# اجرای اسکریپت
python3 apply_performance_fixes.py
```

اسکریپت به صورت خودکار:
- بکاپ از دیتابیس می‌گیرد
- ایندکس‌های جدید را اضافه می‌کند
- دیتابیس را بهینه‌سازی می‌کند
- گزارش نهایی نمایش می‌دهد

#### مرحله 4: راه‌اندازی مجدد ربات
```bash
# اگر با systemd:
sudo systemctl start v2bot
sudo systemctl status v2bot

# اگر با screen:
screen -S v2bot
cd /path/to/v2bot-master
python3 main.py
# سپس Ctrl+A+D برای detach
```

---

### روش 2: اعمال دستی

اگر ترجیح می‌دهید تغییرات را دستی اعمال کنید:

#### 1. بروزرسانی فایل‌ها

فایل‌هایی که تغییر کرده‌اند:
```
bot/handlers/admin.py
bot/handlers/__init__.py
bot/handlers/user.py
bot/app.py
bot/db.py
bot/jobs/check_expiration.py
bot/jobs.py
```

#### 2. اجرای SQL برای ایندکس‌ها

```bash
sqlite3 bot.db
```

```sql
-- اضافه کردن ایندکس‌های جدید
CREATE INDEX IF NOT EXISTS idx_orders_panel_status ON orders(panel_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_username ON orders(marzban_username);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_users_banned ON users(banned);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);

-- بهینه‌سازی
ANALYZE;
PRAGMA optimize;

-- خروج
.exit
```

#### 3. راه‌اندازی مجدد
```bash
sudo systemctl restart v2bot
```

---

## تست عملکرد

بعد از اعمال تغییرات، این موارد را تست کنید:

### ✅ تست 1: دکمه خاموش/روشن ربات
1. وارد پنل ادمین شوید (`/admin`)
2. روی دکمه "🟢 ربات روشن (خاموش کردن)" کلیک کنید
3. باید وضعیت تغییر کند و منو refresh شود

### ✅ تست 2: سفارشات در انتظار
1. در پنل ادمین، گزینه "📦 سفارشات" را انتخاب کنید
2. روی "⏳ سفارشات در انتظار" کلیک کنید
3. باید لیست سفارشات pending نمایش داده شود

### ✅ تست 3: یادآوری فردا
1. منتظر یک پیام یادآوری تمدید باشید (یا با دستکاری دیتابیس تست کنید)
2. روی دکمه "🕘 یادآوری فردا" کلیک کنید
3. باید پیام "یادآوری به فردا موکول شد" نمایش داده شود

### ✅ تست 4: بکاپ
1. در تنظیمات پنل ادمین، بکاپ خودکار را فعال کنید
2. یا دستی بکاپ ایجاد کنید
3. فایل ZIP باید شامل فایل‌های JSON متعدد باشد

### ✅ تست 5: عملکرد
```bash
# بررسی زمان پاسخ‌دهی
time python3 -c "from bot.db import query_db; print(query_db('SELECT COUNT(*) FROM orders'))"

# مشاهده لاگ‌ها
tail -f logs/bot.log  # یا مسیر لاگ شما
```

---

## رفع مشکلات احتمالی

### مشکل 1: خطا در ایجاد ایندکس
```
Error: duplicate column name
```

**راه‌حل:** ایندکس از قبل وجود دارد. مشکلی نیست، ادامه دهید.

---

### مشکل 2: ربات استارت نمی‌شود
```
ModuleNotFoundError: No module named 'telegram'
```

**راه‌حل:**
```bash
pip3 install -r requirements.txt --upgrade
```

---

### مشکل 3: دیتابیس قفل است
```
database is locked
```

**راه‌حل:**
```bash
# متوقف کردن کامل ربات
sudo systemctl stop v2bot
pkill -f "python.*main.py"

# سپس دوباره اسکریپت را اجرا کنید
```

---

### مشکل 4: handler یافت نشد
```
KeyError: 'admin_orders_pending'
```

**راه‌حل:**
```bash
# مطمئن شوید تمام فایل‌ها بروز هستند
git pull  # اگر از git استفاده می‌کنید

# یا فایل‌های تغییر یافته را دستی کپی کنید
```

---

### مشکل 5: عملکرد بهبود نیافت

**بررسی‌های لازم:**

1. **بررسی ایندکس‌ها:**
```bash
sqlite3 bot.db "SELECT name FROM sqlite_master WHERE type='index';"
```

2. **بررسی حجم دیتابیس:**
```bash
ls -lh bot.db
```

اگر بیش از 500MB است، vacuum انجام دهید:
```bash
sqlite3 bot.db "VACUUM;"
```

3. **بررسی منابع سرور:**
```bash
top
free -h
df -h
```

4. **بررسی سرعت پنل:**
```bash
curl -w "@curl-format.txt" -o /dev/null -s "https://your-panel.com"
```

---

## مشاهده لاگ‌ها

برای بررسی عملکرد و مشکلات:

```bash
# لاگ‌های ربات
tail -f logs/bot.log

# لاگ‌های systemd (اگر با systemd اجرا می‌کنید)
sudo journalctl -u v2bot -f

# جستجو در لاگ‌ها
grep "Error" logs/bot.log
grep "admin_toggle_bot_active" logs/bot.log
```

---

## بررسی نهایی

بعد از اعمال تمام تغییرات:

```bash
# 1. بررسی وضعیت ربات
sudo systemctl status v2bot

# 2. بررسی ایندکس‌ها
python3 apply_performance_fixes.py  # گزینه check را انتخاب کنید

# 3. تست سرعت
time python3 -c "
from bot.db import query_db
import time
start = time.time()
query_db('SELECT * FROM orders WHERE status=\\"pending\\"')
print(f'Query time: {time.time()-start:.3f}s')
"
```

---

## پشتیبانی

در صورت بروز مشکل:

1. **لاگ‌ها را بررسی کنید**
2. **دیتابیس را با integrity check بررسی کنید:**
   ```bash
   sqlite3 bot.db "PRAGMA integrity_check;"
   ```
3. **بکاپ را بازگردانی کنید:**
   ```bash
   cp bot.db.backup_YYYYMMDD bot.db
   sudo systemctl restart v2bot
   ```

---

## چک‌لیست نهایی

قبل از راه‌اندازی نهایی:

- [ ] بکاپ از دیتابیس گرفته شده
- [ ] ایندکس‌های جدید اضافه شده
- [ ] تمام فایل‌های تغییر یافته بروز شده
- [ ] ربات restart شده
- [ ] تست‌های اساسی انجام شده
- [ ] لاگ‌ها بررسی شده
- [ ] عملکرد بهبود یافته

---

## اطلاعات بیشتر

- `CHANGELOG_FIXES.md` - لیست کامل تغییرات
- `PERFORMANCE_IMPROVEMENTS.md` - راهنمای بهینه‌سازی پیشرفته
- `README.md` - مستندات اصلی پروژه

---

**تاریخ:** 27 اکتبر 2025  
**نسخه:** 2.0  
**وضعیت:** تست شده و آماده استفاده

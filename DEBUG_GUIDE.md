# 🔍 راهنمای کامل Debug

## 🎯 ابزارهای Debug

شما 3 ابزار قدرتمند برای debug دارید:

### 1️⃣ CHECK_AND_FIX.py
بررسی سریع و هدفمند

### 2️⃣ FULL_DEBUG.py
بررسی کامل و جامع (10 تست)

### 3️⃣ FIX_ALL.py
رفع خودکار مشکلات رایج

---

## 🚀 نحوه استفاده

### مرحله 1: بررسی اولیه

```bash
python CHECK_AND_FIX.py
```

**خروجی مورد انتظار:**
```
✅ موفق: 7/7
```

---

### مرحله 2: Debug کامل

```bash
python FULL_DEBUG.py
```

**این اسکریپت بررسی می‌کند:**

1. ✅ **Syntax Errors** - خطاهای نحوی
2. ✅ **Import Check** - import های گم شده
3. ✅ **Handler Registration** - ثبت handler ها
4. ✅ **Database Systems** - سیستم‌های database
5. ✅ **Circular Imports** - import های دایره‌ای
6. ✅ **Indentation** - مشکلات تورفتگی
7. ✅ **State Count** - تعداد state ها
8. ✅ **Required Files** - فایل‌های ضروری
9. ✅ **Unused Imports** - import های استفاده نشده
10. ✅ **Logger Usage** - استفاده از logger

**خروجی مورد انتظار:**
```
✅ موفق: 10/10
🎉 عالی! همه تست‌ها موفق بودند!
✨ کد شما آماده production است!
```

---

### مرحله 3: رفع خودکار

اگر مشکلی یافت شد:

```bash
python FIX_ALL.py
```

**این اسکریپت رفع می‌کند:**

1. 🔧 **Indentation** - تبدیل tab به space
2. 🔧 **Line Endings** - تبدیل CRLF به LF
3. 🔧 **Trailing Whitespace** - حذف فضای خالی انتهای خط
4. 🔧 **Encoding** - اضافه کردن UTF-8 encoding
5. 🔧 **__init__.py** - ساخت فایل‌های init

---

## 🐛 مشکلات رایج و راه حل

### مشکل 1: Import های گم شده

**علامت:**
```
❌ app.py (imports & handlers)
Missing import: user_wallet
```

**راه حل:**
```bash
python AUTO_FIX.py
```

---

### مشکل 2: Syntax Error

**علامت:**
```
❌ bot/handlers/user.py: SyntaxError
```

**راه حل:**
1. فایل را باز کنید
2. خط خطا را پیدا کنید
3. syntax را اصلاح کنید

**مشکلات رایج syntax:**
- فراموشی `:` در انتهای def, if, for
- کاما های گم شده
- پرانتز باز نشده

---

### مشکل 3: IndentationError

**علامت:**
```
IndentationError: unexpected indent
```

**راه حل:**
```bash
python FIX_ALL.py
```

این خودکار tab ها را به space تبدیل می‌کند.

---

### مشکل 4: Circular Import

**علامت:**
```
ImportError: cannot import name 'X' from 'Y'
```

**راه حل:**
1. import را به انتهای فایل منتقل کنید
2. از `from typing import TYPE_CHECKING` استفاده کنید
3. ساختار کد را بازنگری کنید

---

### مشکل 5: Handler ثبت نشده

**علامت:**
```
❌ Not registered: wallet_charge_menu
```

**راه حل:**
در `bot/app.py` اضافه کنید:
```python
application.add_handler(
    CallbackQueryHandler(wallet_charge_menu, pattern=r'^wallet_charge_menu$'), 
    group=3
)
```

---

### مشکل 6: Database Error

**علامت:**
```
sqlite3.OperationalError: no such table
```

**راه حل:**
```bash
python -c "from bot.wallet_system import WalletSystem; WalletSystem.setup_tables()"
python -c "from bot.loyalty_system import LoyaltySystem; LoyaltySystem.setup_tables()"
```

---

### مشکل 7: State Count Mismatch

**علامت:**
```
❌ State Count: Expected 90, got 89
```

**راه حل:**
در `bot/states.py`:
```python
) = range(90)  # تعداد را اصلاح کنید
```

---

## 🔬 تست های پیشرفته

### تست با pyflakes

```bash
pip install pyflakes
pyflakes bot/
```

### تست با pylint

```bash
pip install pylint
pylint bot/ --disable=C,R
```

### تست با mypy (type checking)

```bash
pip install mypy
mypy bot/ --ignore-missing-imports
```

---

## 📊 تفسیر نتایج

### ✅ موفقیت کامل (10/10)

```
🎉 عالی! همه تست‌ها موفق بودند!
✨ کد شما آماده production است!
```

**اقدام:** هیچ! ادامه دهید

---

### ⚠️ خوب اما نیاز به بهبود (8-9/10)

```
⚠️ خوب! اما نیاز به بهبود دارد
💡 لطفاً موارد ناموفق را بررسی کنید
```

**اقدام:** مشکلات جزئی را برطرف کنید

---

### ❌ نیاز به توجه جدی (<8/10)

```
❌ مشکلات جدی یافت شد
🔧 لطفاً خطاها را برطرف کنید
```

**اقدام:** 
1. `FIX_ALL.py` را اجرا کنید
2. خطاهای syntax را برطرف کنید
3. دوباره تست کنید

---

## 🛠️ ابزارهای کمکی

### لیست تمام handler ها

```python
python -c "import bot.app; import inspect; [print(h) for h in dir(bot.app) if 'handler' in h.lower()]"
```

### بررسی import ها

```python
python -c "import sys; sys.path.insert(0, '.'); import bot.app; print('✅ Imports OK')"
```

### تست database

```python
python -c "from bot.db import query_db; print(query_db('SELECT COUNT(*) as c FROM users', one=True))"
```

---

## 📝 Checklist قبل از Production

```
□ همه تست‌های FULL_DEBUG.py موفق
□ هیچ syntax error نیست
□ تمام import ها کار می‌کنند
□ تمام handler ها ثبت شده‌اند
□ Database tables ساخته شده‌اند
□ Migration اجرا شده
□ Logger ها فعال هستند
□ .env پیکربندی شده
□ install.sh تست شده
□ ربات بدون خطا start می‌شود
```

---

## 🚨 خطاهای اضطراری

### ربات start نمی‌شود

```bash
# 1. بررسی لاگ
sudo journalctl -u v2bot -n 50 --no-pager

# 2. تست مستقیم
source .venv/bin/activate
python -m bot.run

# 3. بررسی imports
python -c "import bot.app"
```

### Database خراب شد

```bash
# بکاپ
cp bot.db bot.db.backup

# بازسازی
python -c "from bot.db import db_setup; db_setup()"
```

### Handler کار نمی‌کند

```python
# اضافه کردن debug log
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📚 منابع بیشتر

- [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md) - راهنمای کامل
- [IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md) - خلاصه بهبودها
- [UPGRADE_V3.md](UPGRADE_V3.md) - راهنمای v3.0

---

## 🎓 Best Practices

### 1. Debug منظم

هر روز یکبار:
```bash
python FULL_DEBUG.py
```

### 2. Commit های کوچک

```bash
git add -A
git commit -m "fix: description"
git push
```

### 3. تست قبل از Deploy

```bash
python FULL_DEBUG.py
python CHECK_AND_FIX.py
python -m bot.run  # تست 1 دقیقه
```

### 4. Backup منظم

```bash
cp bot.db backups/bot_$(date +%Y%m%d).db
```

---

## 🎉 نتیجه‌گیری

با این ابزارها می‌توانید:

✅ **مشکلات را سریع پیدا کنید**
✅ **خودکار رفع کنید**
✅ **از کیفیت کد اطمینان داشته باشید**
✅ **آماده production باشید**

**موفق باشید! 🚀**

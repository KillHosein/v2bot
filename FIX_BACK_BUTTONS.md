# 🔧 راهنمای رفع دکمه‌های بازگشت ادمین

## ❌ مشکل فعلی

دکمه‌های بازگشت در handlers مختلف به callback_data های مختلف اشاره می‌کنند که برخی وجود ندارند یا در ConversationHandler register نشده‌اند.

## ✅ راه‌حل

از کلاس `BackButtons` استفاده کنید که در `bot/helpers/back_buttons.py` قرار دارد.

---

## 📚 نحوه استفاده

### 1. Import کردن

```python
from ..helpers.back_buttons import BackButtons
```

### 2. استفاده در Keyboard

```python
# قبلاً (اشتباه)
keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_stats_menu')]]  # وجود ندارد!

# حالا (صحیح)
keyboard = [[BackButtons.to_admin_main()]]
```

---

## 🎯 دکمه‌های استاندارد

### برای پنل ادمین:

```python
# بازگشت به پنل اصلی ادمین
BackButtons.to_admin_main()
BackButtons.to_admin_main("🏠 پنل ادمین")  # با متن سفارشی

# بازگشت به منوهای مختلف
BackButtons.to_users()           # منوی کاربران
BackButtons.to_settings()        # منوی تنظیمات
BackButtons.to_panels()          # منوی پنل‌ها
BackButtons.to_plans()           # منوی پلن‌ها
BackButtons.to_tickets()         # منوی تیکت‌ها
BackButtons.to_tutorials()       # منوی آموزش‌ها
BackButtons.to_messages()        # منوی پیام‌ها
BackButtons.to_wallets()         # منوی کیف پول‌ها
BackButtons.to_cards()           # منوی کارت‌ها
BackButtons.to_advanced_stats()  # آمار پیشرفته
BackButtons.to_monitoring()      # مانیتورینگ
```

### برای کاربران:

```python
# بازگشت به منوی اصلی کاربر
BackButtons.to_start()
BackButtons.to_start("🏠 منوی اصلی")
```

### دکمه‌های اضافی:

```python
# دکمه بروزرسانی
BackButtons.refresh('admin_advanced_stats')
BackButtons.refresh('admin_monitoring_menu', "♻️ رفرش")

# دکمه لغو
BackButtons.cancel()
BackButtons.cancel("❌ انصراف")

# دکمه سفارشی
BackButtons.custom("🔙 بازگشت", 'custom_callback_data')
```

---

## 🔍 لیست کامل callback_data های معتبر

### ✅ Register شده در app.py:

```python
# منوهای اصلی
'admin_main'              # پنل اصلی ادمین ✅
'start_main'              # منوی اصلی کاربر ✅

# منوهای ادمین
'admin_users_menu'        # کاربران ✅
'admin_settings_manage'   # تنظیمات ✅
'admin_panels_menu'       # پنل‌ها ✅
'admin_plan_manage'       # پلن‌ها ✅
'admin_discount_menu'     # تخفیف‌ها ✅
'admin_messages_menu'     # پیام‌ها ✅
'admin_tickets_menu'      # تیکت‌ها ✅
'admin_tutorials_menu'    # آموزش‌ها ✅
'admin_wallets_menu'      # کیف پول‌ها ✅
'admin_cards_menu'        # کارت‌ها ✅
'admin_stats'             # آمار ✅
'admin_broadcast_menu'    # ارسال همگانی ✅
'admin_cron_menu'         # کرون جاب ✅
'admin_reseller_menu'     # نمایندگی ✅

# قابلیت‌های پیشرفته v2.0
'admin_advanced_stats'    # آمار پیشرفته ✅
'admin_monitoring_menu'   # مانیتورینگ ✅
'preferences_menu'        # تنظیمات کاربر ✅
'language_menu'           # تغییر زبان ✅
```

### ❌ وجود ندارند (استفاده نکنید):

```python
'admin_stats_menu'        # ❌ وجود ندارد! باید admin_main باشد
'admin_menu'              # ❌ وجود ندارد! باید admin_main باشد
'back_to_admin'           # ❌ وجود ندارد! باید admin_main باشد
```

---

## 🛠️ نمونه کد برای رفع مشکل

### مثال 1: Handler آمار پیشرفته

```python
from ..helpers.back_buttons import BackButtons

async def admin_advanced_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... کد شما
    
    keyboard = [
        [
            InlineKeyboardButton("📈 نمودار کاربران", callback_data='admin_chart_users'),
            InlineKeyboardButton("💰 نمودار درآمد", callback_data='admin_chart_revenue')
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
```

### مثال 2: Sub-menu با بازگشت به parent

```python
async def admin_chart_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... کد شما
    
    keyboard = [[BackButtons.to_advanced_stats()]]  # بازگشت به آمار پیشرفته
    
    await query.message.reply_text(
        chart_message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
```

### مثال 3: منوی تنظیمات

```python
async def admin_wallets_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... کد شما
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن ولت", callback_data='wallet_add_start')],
        [BackButtons.to_settings()]  # بازگشت به تنظیمات
    ]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
```

---

## 🔄 مراحل رفع یک Handler

### گام 1: پیدا کردن دکمه‌های بازگشت

```bash
# در IDE خود جستجو کنید
grep -r "بازگشت" bot/handlers/admin_*.py
```

### گام 2: Import کردن BackButtons

```python
from ..helpers.back_buttons import BackButtons
```

### گام 3: جایگزینی دکمه‌ها

```python
# قبل
InlineKeyboardButton("🔙 بازگشت", callback_data='admin_stats_menu')

# بعد
BackButtons.to_admin_main()
```

### گام 4: تست کردن

```bash
# در سرور
cd /root/v2bot
git pull
sudo systemctl restart wingsbot
sudo journalctl -u wingsbot -f
```

---

## 📋 Checklist برای هر Handler

برای هر فایل در `bot/handlers/admin_*.py`:

- [ ] Import کردن `BackButtons`
- [ ] جایگزینی دکمه بازگشت به پنل اصلی با `BackButtons.to_admin_main()`
- [ ] جایگزینی دکمه بازگشت به منوی والد با method مناسب
- [ ] اضافه کردن دکمه refresh در صورت نیاز با `BackButtons.refresh()`
- [ ] تست کردن در تلگرام

---

## 🚀 Quick Fix برای همه Handler ها

اگر می‌خواهید سریع همه را درست کنید:

```python
# در همه handler های admin که دکمه بازگشت دارند:

# 1. Import اضافه کنید
from ..helpers.back_buttons import BackButtons

# 2. دکمه‌های بازگشت را جایگزین کنید:

# بازگشت به پنل اصلی
"callback_data='admin_main'" → BackButtons.to_admin_main()

# بازگشت به تنظیمات
"callback_data='admin_settings_manage'" → BackButtons.to_settings()

# بازگشت به کاربران
"callback_data='admin_users_menu'" → BackButtons.to_users()

# و غیره...
```

---

## 💡 نکات مهم

1. **همیشه از BackButtons استفاده کنید** - از hardcode کردن callback_data خودداری کنید
2. **callback_data باید در app.py register باشد** - در ConversationHandler یا global handlers
3. **برای sub-menu ها** - از parent menu استفاده کنید نه admin_main
4. **متن دکمه را سفارشی کنید** - با پارامتر اول

---

## 🐛 Debug مشکلات

### مشکل: دکمه کار نمی‌کند

```bash
# 1. بررسی لاگ
sudo journalctl -u wingsbot -f | grep callback

# 2. بررسی callback_data در app.py
grep "pattern=.*admin_" bot/app.py

# 3. مطمئن شوید در state صحیح است
# اگر در ConversationHandler هستید، باید در state مناسب باشد
```

### مشکل: "No handler found"

این یعنی callback_data در هیچ handler ای register نشده.

**راه‌حل:**
- از `BackButtons` استفاده کنید که callback_data های معتبر دارد
- یا handler را در app.py اضافه کنید

---

## ✅ بعد از رفع مشکلات

همه دکمه‌های بازگشت باید:
1. کار کنند ✅
2. متن یکسان داشته باشند ✅
3. قابل نگهداری باشند ✅
4. از یک منبع مرکزی استفاده کنند ✅

---

**نکته نهایی:** این helper را در تمام handler های جدید نیز استفاده کنید!

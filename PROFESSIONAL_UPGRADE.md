# 🎯 راهنمای کامل ارتقاء حرفه‌ای ربات

## ✅ تغییرات انجام شده

### 1. حذف تنظیمات زبان کاربر
- ✅ دکمه "تنظیمات" از منوی کاربر حذف شد
- ✅ Handler های `language_menu`, `set_language`, `preferences_menu` حذف شدند
- ✅ کاربران دیگر نمی‌توانند زبان را تغییر دهند
- ✅ فقط فارسی استفاده می‌شود

### 2. سیستم متن‌های حرفه‌ای فارسی
- ✅ فایل `bot/helpers/persian_texts.py` ساخته شد
- ✅ تمام متن‌ها با ایموجی‌های زیبا و حرفه‌ای
- ✅ قالب‌بندی یکپارچه در تمام پیام‌ها
- ✅ استفاده از border های زیبا (╔═╗ ║ ╚═╝)

### 3. سیستم دکمه‌های استاندارد
- ✅ فایل `bot/helpers/back_buttons.py` ساخته شد
- ✅ تمام callback_data ها در یک جا
- ✅ دکمه‌های یکپارچه در تمام handlers

---

## 📚 استفاده از متن‌های حرفه‌ای

### Import کردن

```python
from ..helpers.persian_texts import (
    WelcomeTexts, ServiceTexts, WalletTexts, 
    PurchaseTexts, SupportTexts, AdminTexts,
    ErrorTexts, SuccessTexts
)
```

### یا استفاده سریع:

```python
from ..helpers.persian_texts import welcome, admin_welcome, error, success_payment
```

---

## 🎨 نمونه کدها

### 1. پیام خوش‌آمدگوئی

```python
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "کاربر"
    
    # استفاده از متن حرفه‌ای
    text = WelcomeTexts.main_welcome(user_name)
    
    keyboard = build_start_menu_keyboard()
    
    await update.message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
```

### 2. نمایش سرویس‌های کاربر

```python
async def my_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    services = query_db("SELECT * FROM services WHERE user_id = ?", (user_id,))
    
    if not services:
        # متن حرفه‌ای برای حالت بدون سرویس
        text = ServiceTexts.no_services()
    else:
        service = services[0]
        # متن حرفه‌ای برای سرویس فعال
        text = ServiceTexts.service_active(
            name=service['name'],
            days_left=service['days_left'],
            traffic_left=service['traffic']
        )
    
    await update.callback_query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
```

### 3. نمایش کیف پول

```python
async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = get_user_balance(user_id)
    
    # متن حرفه‌ای کیف پول
    text = WalletTexts.wallet_balance(balance)
    
    keyboard = [
        [InlineKeyboardButton("💳 افزایش موجودی", callback_data='charge_wallet')],
        [InlineKeyboardButton("📊 تاریخچه", callback_data='wallet_history')],
        [BackButtons.to_start()]
    ]
    
    await update.callback_query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
```

### 4. خرید سرویس

```python
async def purchase_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # انتخاب پلن
    text = PurchaseTexts.select_plan()
    
    # نمایش پلن انتخاب شده
    text = PurchaseTexts.plan_selected(
        name="پلن ویژه",
        price=50000,
        days=30,
        traffic="50 GB"
    )
    
    # در انتظار تأیید
    text = PurchaseTexts.payment_pending()
```

### 5. پشتیبانی

```python
async def support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # متن حرفه‌ای منوی پشتیبانی
    text = SupportTexts.support_menu()
    
    keyboard = [
        [InlineKeyboardButton("🎫 تیکت جدید", callback_data='ticket_create_start')],
        [InlineKeyboardButton("📚 سوالات متداول", callback_data='faq')],
        [BackButtons.to_start()]
    ]
    
    await update.callback_query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
```

### 6. پنل ادمین

```python
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_name = update.effective_user.first_name or "ادمین"
    
    # متن حرفه‌ای خوش‌آمدگوئی ادمین
    text = WelcomeTexts.admin_welcome(admin_name)
    
    # یا متن آمار سیستم
    stats = get_system_stats()
    text = AdminTexts.stats_overview(
        users=stats['total_users'],
        active=stats['active_users'],
        revenue_today=stats['revenue_today'],
        revenue_month=stats['revenue_month']
    )
    
    keyboard = get_admin_keyboard()
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
```

### 7. مدیریت خطاها

```python
async def some_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # عملیات
        pass
    except InsufficientBalance as e:
        # خطای موجودی کافی نیست
        text = ErrorTexts.insufficient_balance(
            balance=user_balance,
            required=required_amount
        )
        await update.callback_query.message.edit_text(
            text,
            parse_mode=ParseMode.HTML
        )
    except ServiceNotFound:
        # خطای سرویس یافت نشد
        text = ErrorTexts.service_not_found()
        await update.callback_query.message.edit_text(
            text,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        # خطای عمومی
        text = ErrorTexts.general_error()
        await update.callback_query.message.edit_text(
            text,
            parse_mode=ParseMode.HTML
        )
```

### 8. پیام‌های موفقیت

```python
async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # پرداخت تأیید شد
    text = SuccessTexts.payment_approved()
    
    await context.bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode=ParseMode.HTML
    )

async def renew_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # سرویس تمدید شد
    text = SuccessTexts.service_renewed()
    
    await update.callback_query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML
    )
```

---

## 🎯 Checklist برای هر Handler

- [ ] Import کردن `persian_texts`
- [ ] استفاده از متن‌های حرفه‌ای به جای hardcode
- [ ] Import کردن `BackButtons`
- [ ] استفاده از دکمه‌های استاندارد
- [ ] استفاده از `parse_mode=ParseMode.HTML`
- [ ] تست در تلگرام

---

## 📝 کلاس‌های موجود

### WelcomeTexts
- `main_welcome(name)` - پیام خوش‌آمدگوئی کاربر
- `admin_welcome(name)` - پیام خوش‌آمدگوئی ادمین

### ServiceTexts
- `no_services()` - بدون سرویس
- `service_active(name, days_left, traffic_left)` - سرویس فعال
- `service_expired()` - سرویس منقضی شده

### WalletTexts
- `wallet_balance(balance)` - موجودی کیف پول
- `wallet_low_balance(balance)` - موجودی کم

### PurchaseTexts
- `select_plan()` - انتخاب پلن
- `plan_selected(name, price, days, traffic)` - پلن انتخاب شده
- `payment_pending()` - در انتظار تأیید

### SupportTexts
- `support_menu()` - منوی پشتیبانی
- `ticket_created()` - تیکت ثبت شد

### AdminTexts
- `stats_overview(users, active, revenue_today, revenue_month)` - آمار سیستم
- `user_banned(user_id)` - کاربر مسدود شد
- `user_unbanned(user_id)` - کاربر آزاد شد

### ErrorTexts
- `general_error()` - خطای عمومی
- `insufficient_balance(balance, required)` - موجودی کافی نیست
- `service_not_found()` - سرویس یافت نشد

### SuccessTexts
- `payment_approved()` - پرداخت تأیید شد
- `service_renewed()` - سرویس تمدید شد

---

## 🚀 مراحل بعدی

### 1. بروزرسانی Handler ها

لیست handler هایی که باید بروز شوند:

#### کاربران:
- [ ] `common.py` - start_command
- [ ] `user.py` - my_services, wallet_menu
- [ ] `purchase.py` - purchase flow
- [ ] `renewal.py` - renewal flow

#### ادمین:
- [ ] `admin.py` - admin_command
- [ ] `admin_users.py` - user management
- [ ] `admin_stats_broadcast.py` - stats display
- [ ] `admin_tickets.py` - ticket management

### 2. تست

```bash
# در سرور
cd /root/v2bot
git pull origin main
sudo systemctl restart wingsbot
sudo journalctl -u wingsbot -f
```

### 3. بررسی در تلگرام

- [ ] /start - پیام خوش‌آمدگوئی زیبا نمایش داده می‌شود
- [ ] سرویس‌های من - متن حرفه‌ای نمایش داده می‌شود
- [ ] کیف پول - قالب‌بندی زیبا
- [ ] خرید - مراحل با متن واضح
- [ ] پشتیبانی - متن راهنما
- [ ] ادمین - آمار حرفه‌ای

---

## 💡 نکات مهم

1. **همیشه از persian_texts استفاده کنید** - نه hardcode متن
2. **parse_mode را HTML بگذارید** - برای پشتیبانی از `<b>`, `<code>`, `<i>`
3. **دکمه‌ها را از BackButtons بگیرید** - نه hardcode callback_data
4. **متن‌ها را سفارشی کنید** - با پارامترهای مناسب
5. **consistent باشید** - از یک سبک در همه جا استفاده کنید

---

## 🎨 سبک طراحی

### Border ها:
```
╔══════════════════════════════╗
║  متن هدر                     ║
╚══════════════════════════════╝
```

### جداکننده:
```
━━━━━━━━━━━━━━━━━━━━━━━━
```

### Box برای اطلاعات:
```
┌─────────────────────────┐
│  اطلاعات                │
├─────────────────────────┤
│  • مورد 1               │
│  • مورد 2               │
└─────────────────────────┘
```

### ایموجی‌های استاندارد:
- ✅ - موفقیت
- ❌ - خطا
- ⚠️ - هشدار
- ℹ️ - اطلاعات
- 🎯 - هدف/انتخاب
- 💰 - پول/پرداخت
- 📊 - آمار/نمودار
- 🔹 - نقطه لیست
- 🔽 - فلش پایین (انتخاب)
- 👇 - اشاره به پایین

---

## ✅ نتیجه نهایی

بعد از اعمال تغییرات:
1. ✨ ربات حرفه‌ای‌تر به نظر می‌رسد
2. 📱 کاربران تجربه بهتری دارند
3. 🎯 متن‌ها واضح‌تر و زیباتر هستند
4. 🔧 نگهداری آسان‌تر است
5. 🚀 توسعه سریع‌تر است

**ربات شما آماده جذب کاربران بیشتر است!** 🎉

# راهنمای مهاجرت پیام‌ها (Messages Migration)

## مرحله ۱: اجرای Migration

برای اضافه کردن تمام پیام‌های پیش‌فرض به دیتابیس:

```bash
cd /path/to/v2bot
python3 add_default_messages.py
```

این اسکریپت ۳۰+ پیام مهم سیستم را به جدول `messages` اضافه می‌کند.

## مرحله ۲: به‌روزرسانی کدها

### قبل (Hard-coded):
```python
await update.message.reply_text("پلن موردنظر خود را انتخاب کنید:")
```

### بعد (از دیتابیس):
```python
from ..db import get_message_text

text = get_message_text('purchase_plan_selection', 'پلن موردنظر خود را انتخاب کنید:')
await update.message.reply_text(text)
```

### با متغیرها (format):
```python
text = get_message_text('purchase_plan_confirm', '✅ تایید خرید...')
text = text.format(
    plan_name=plan['name'],
    price=f"{plan['price']:,}",
    duration=plan['duration']
)
await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
```

## لیست پیام‌های اضافه‌شده

### خرید و پرداخت
- `purchase_plan_selection` - انتخاب پلن
- `purchase_plan_confirm` - تایید خرید
- `purchase_payment_methods` - انتخاب روش پرداخت
- `purchase_payment_pending` - در انتظار پرداخت
- `purchase_payment_received` - رسید دریافت شد
- `purchase_cancelled` - خرید لغو شد
- `purchase_success` - خرید موفق

### سرویس‌ها
- `services_list_header` - هدر لیست سرویس‌ها
- `services_empty` - هیچ سرویسی وجود ندارد
- `service_detail` - جزئیات سرویس
- `service_link_refreshed` - لینک به‌روزرسانی شد
- `service_renewal_confirm` - تایید تمدید
- `service_renewed` - تمدید موفق

### کیف پول
- `wallet_balance` - موجودی کیف پول
- `wallet_deposit_request` - درخواست شارژ
- `wallet_deposit_pending` - در انتظار واریز
- `wallet_deposit_approved` - واریز تایید شد
- `wallet_insufficient` - موجودی ناکافی

### پشتیبانی
- `support_menu` - منوی پشتیبانی
- `support_ticket_created` - تیکت ایجاد شد
- `support_ticket_replied` - پاسخ به تیکت
- `support_ticket_closed` - تیکت بسته شد

### دعوت دوستان
- `referral_info` - اطلاعات دعوت
- `referral_bonus` - پاداش دعوت

### آموزش‌ها
- `tutorials_list` - لیست آموزش‌ها

### خطاها
- `error_generic` - خطای عمومی
- `error_invalid_input` - ورودی نامعتبر
- `error_session_expired` - جلسه منقضی شد

### تخفیف
- `discount_applied` - تخفیف اعمال شد
- `discount_invalid` - کد تخفیف نامعتبر
- `discount_prompt` - درخواست کد تخفیف

### تست رایگان
- `trial_available` - تست رایگان در دسترس
- `trial_already_used` - تست قبلاً استفاده شده
- `trial_activated` - تست فعال شد

## مثال کامل: به‌روزرسانی یک handler

### قبل:
```python
async def show_plan_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan = context.user_data.get('selected_plan')
    text = f"✅ **تایید خرید**\n\n📦 پلن: {plan['name']}\n💰 قیمت: {plan['price']}\n⏱ مدت: {plan['duration']} روز\n\nآیا مطمئن هستید؟"
    await update.callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
```

### بعد:
```python
from ..db import get_message_text

async def show_plan_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan = context.user_data.get('selected_plan')
    
    text = get_message_text(
        'purchase_plan_confirm',
        '✅ **تایید خرید**\n\n📦 پلن: {plan_name}\n💰 قیمت: {price}\n⏱ مدت: {duration} روز\n\nآیا مطمئن هستید؟'
    )
    text = text.format(
        plan_name=plan['name'],
        price=f"{plan['price']:,}",
        duration=plan['duration']
    )
    
    await update.callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
```

## مزایا

✅ **ادمین می‌تواند تمام متن‌ها را از پنل تغییر دهد**
✅ **نیاز به restart یا deploy مجدد نیست**
✅ **پشتیبانی از چند زبانه در آینده**
✅ **تست A/B روی متن‌ها**
✅ **تغییرات سریع بدون دسترسی به کد**

## نکات مهم

⚠️ **placeholder ها را حفظ کنید**: وقتی ادمین متن را تغییر می‌دهد، باید placeholder هایی مثل `{plan_name}` یا `{price}` را حفظ کند.

⚠️ **پیام‌های admin_* را تغییر ندهید**: این پیام‌ها برای پنل ادمین هستند و نباید توسط سیستم مدیریت پیام‌ها تغییر کنند.

💡 **Fallback**: همیشه یک متن پیش‌فرض به `get_message_text()` بدهید تا اگر پیام از دیتابیس حذف شد، ربات کار کند.

## به‌روزرسانی تدریجی

می‌توانید به‌صورت تدریجی کدها را به‌روز کنید:
1. ابتدا بخش‌های پرترافیک (خرید، سرویس‌ها)
2. سپس بخش‌های کم‌تر استفاده‌شده (پشتیبانی، آموزش)
3. در نهایت خطاها و پیام‌های کمکی

## تست

بعد از migration:
1. از پنل ادمین > مدیریت پیام‌ها وارد شوید
2. پیام‌های جدید را ببینید و تست کنید
3. یک پیام را تغییر دهید و بررسی کنید که در ربات اعمال شده است

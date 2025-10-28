# 📝 چگونه یک متن را قابل ویرایش کنیم

## وضعیت فعلی

✅ **این متن‌ها الان قابل ویرایش هستند:**
- `start_main` - صفحه اصلی
- `buy_config_main` - صفحه خرید
- `support_menu` - منوی پشتیبانی
- `support_ticket_create` - ثبت تیکت

❌ **بقیه هنوز hard-coded هستند**

## راه‌حل: تبدیل دستی (مطمئن 100%)

### مثال: تبدیل "تیکت ثبت شد"

#### قبل (hard-coded):
```python
await update.message.reply_text(
    "✅ تیکت ثبت شد!\n\n"
    f"🎫 شماره: #{ticket_id}\n"
    "پاسخ به زودی..."
)
```

#### بعد (قابل ویرایش):
```python
text = get_message_text(
    'support_ticket_created',
    "✅ تیکت ثبت شد!\n\n🎫 شماره: {ticket_id}\n پاسخ به زودی..."
)
text = text.format(ticket_id=ticket_id)
await update.message.reply_text(text)
```

### مراحل:

#### 1️⃣ پیدا کردن متن
```bash
grep -r "تیکت ثبت شد" bot/handlers/
```

#### 2️⃣ Import اضافه کردن
```python
from ..db import query_db, execute_db, get_message_text
```

#### 3️⃣ تبدیل متن
قبل:
```python
text = "سلام {name}"
```

بعد:
```python
text = get_message_text('message_name', 'سلام {name}')
text = text.format(name=username)
```

#### 4️⃣ نام پیام را اضافه کنید به `db.py`
فایل: `bot/db.py` خط ~45

```python
default_messages = {
    ...
    'support_ticket_created': ('✅ تیکت ثبت شد!\n\n...', None, None),
    ...
}
```

## 🎯 پیام‌هایی که بیشتر درخواست می‌شوند:

### پشتیبانی (4 پیام):
- ✅ `support_menu` - منوی پشتیبانی (انجام شده)
- ✅ `support_ticket_create` - ثبت تیکت (انجام شده)
- ❌ `support_ticket_created` - تیکت ثبت شد
- ❌ `support_ticket_replied` - پاسخ تیکت
- ❌ `support_ticket_closed` - تیکت بسته شد

### سرویس‌ها (4 پیام):
- ❌ `services_empty` - هیچ سرویسی ندارید
- ❌ `services_list_header` - لیست سرویس‌ها
- ❌ `service_detail` - جزئیات سرویس
- ❌ `service_renewed` - تمدید موفق

### کیف پول (4 پیام):
- ❌ `wallet_balance` - موجودی
- ❌ `wallet_deposit_pending` - در انتظار
- ❌ `wallet_deposit_approved` - تایید شد
- ❌ `wallet_insufficient` - ناکافی

### خرید (3 پیام):
- ❌ `purchase_success` - خرید موفق
- ❌ `purchase_cancelled` - لغو شد
- ❌ `purchase_payment_received` - رسید دریافت شد

## 💡 نکات مهم:

### ✅ درست:
```python
# با placeholder
text = get_message_text('msg', 'سلام {name}')
text = text.format(name=user.first_name)
```

### ❌ غلط:
```python
# بدون format
text = get_message_text('msg', f'سلام {user.first_name}')
# این کار نمی‌کند چون ادمین نمی‌تواند {name} را ویرایش کند
```

### Placeholder ها:
- `{name}` - نام
- `{price}` - قیمت
- `{ticket_id}` - شماره تیکت
- `{balance}` - موجودی
- `{service_name}` - نام سرویس

## 🚀 درخواست تبدیل سریع

اگر می‌خواهید **یک** متن خاص را سریع تبدیل کنیم:

1. بگویید کدام متن (مثلاً "تیکت ثبت شد")
2. من کد آن را می‌نویسم
3. شما فقط copy/paste می‌کنید
4. تمام! ✅

## 📊 پیشرفت

- ✅ تبدیل شده: 4/35 (11%)
- ⏳ درخواست شده: 0
- 📝 باقیمانده: 31

---

**سوال دارید؟** فقط بگویید کدام متن را می‌خواهید!

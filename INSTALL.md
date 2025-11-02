# 🚀 نصب و راه‌اندازی با یک دستور

## ✅ نصب سریع (در سرور)

فقط **یک دستور**:

```bash
cd /root/v2bot && git pull origin main && bash COMPLETE_SETUP.sh && sudo systemctl restart wingsbot && sudo journalctl -u wingsbot -n 50 --no-pager
```

این دستور:
1. ✅ آخرین نسخه را دانلود می‌کند
2. ✅ همه handler ها را یکسان می‌کند  
3. ✅ ربات را ریستارت می‌کند
4. ✅ لاگ را نمایش می‌دهد

---

## 📋 روش گام به گام

اگر می‌خواهید مرحله به مرحله ببینید:

### گام 1: دریافت کد

```bash
cd /root/v2bot
git pull origin main
```

### گام 2: اجرای اسکریپت همگام‌سازی

```bash
bash COMPLETE_SETUP.sh
```

### گام 3: ریستارت ربات

```bash
sudo systemctl restart wingsbot
```

### گام 4: بررسی لاگ

```bash
sudo journalctl -u wingsbot -f --no-pager
```

---

## ✅ انتظارات

بعد از نصب باید این پیام‌ها را ببینید:

```
✅ i18n system initialized
✅ Cache system initialized: memory  
✅ Advanced features initialized (v2.0)
🤖 Bot started successfully!
```

---

## 🎯 تست در تلگرام

```
/admin

همه دکمه‌های بازگشت باید کار کنند:
✅ وضعیت سیستم → بازگشت
✅ تنظیمات → بازگشت
✅ آمار پیشرفته → بازگشت
✅ مانیتورینگ → بازگشت
✅ کاربران → بازگشت
✅ پنل‌ها → بازگشت
✅ پلن‌ها → بازگشت
```

---

## 🔧 عیب‌یابی

### اگر خطا دیدید:

```bash
# مشاهده لاگ کامل
sudo journalctl -u wingsbot -n 100 --no-pager

# چک کردن وضعیت
sudo systemctl status wingsbot

# ریستارت مجدد
sudo systemctl restart wingsbot
```

### اگر ربات start نشد:

```bash
# بررسی فایل‌ها
cd /root/v2bot
ls -la bot/helpers/

# باید این فایل‌ها وجود داشته باشند:
# back_buttons.py
# persian_texts.py
```

---

## 📞 پشتیبانی

اگر مشکلی داشتید:
1. لاگ را بررسی کنید
2. مطمئن شوید git pull کار کرده
3. مطمئن شوید COMPLETE_SETUP.sh اجرا شده

---

**ربات شما آماده است! 🎉**

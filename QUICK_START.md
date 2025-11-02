# 🚀 نصب سریع V2Bot

## نصب با سه دستور:

```bash
sudo apt update && sudo apt install -y git curl python3 python3-venv python3-pip
git clone https://github.com/KillHosein/v2bot
cd v2bot
bash install.sh
```

این همه! ربات شما نصب می‌شود.

---

## راه‌اندازی به عنوان سرویس:

```bash
sudo cp v2bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now v2bot
```

---

## مشاهده لاگ:

```bash
sudo journalctl -u v2bot -f
```

---

## ویژگی‌های نسخه 2.0:

- ✅ نصب خودکار
- ✅ Redis caching (سریع‌تر)
- ✅ آمار پیشرفته با نمودار
- ✅ مانیتورینگ سیستم
- ✅ چند زبانه (فارسی/انگلیسی/عربی)
- ✅ پنل ادمین حرفه‌ای
- ✅ دکمه‌های استاندارد
- ✅ متن‌های زیبا

---

## دسترسی به پنل ادمین:

```
/start در تلگرام
→ پنل ادمین
→ 🎯 آمار پیشرفته
→ 📡 مانیتورینگ
```

---

**موفق باشید! 🎉**

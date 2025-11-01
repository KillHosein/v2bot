## 🚀 نصب و راه‌اندازی سریع

### ⚡ نصب یک‌خطی (توصیه می‌شود)

**فقط کافیست این دستورات را اجرا کنید:**

```bash
sudo apt update && sudo apt install -y git curl python3 python3-venv python3-pip
git clone https://github.com/KillHosein/v2bot
cd v2bot
bash install.sh
```

اسکریپت نصب **خودکار** همه چیز را برای شما انجام می‌دهد:
- ✅ نصب Redis برای cache (10x سریع‌تر)
- ✅ نصب فونت‌ها برای نمودارها
- ✅ نصب تمام dependencies
- ✅ راه‌اندازی دیتابیس
- ✅ تنظیم سیستم چند زبانه
- ✅ تست همه قابلیت‌ها

### 📝 اطلاعات مورد نیاز

هنگام اجرای install.sh از شما سوال می‌شود:
- 🤖 **BOT_TOKEN**: توکن ربات از [@BotFather](https://t.me/BotFather)
- 👤 **ADMIN_ID**: آیدی عددی شما از [@userinfobot](https://t.me/userinfobot)
- 📢 **CHANNEL_ID**: آیدی کانال (اختیاری، Enter بزنید برای رد شدن)

### 🎯 اجرای ربات

**حالت توسعه:**
```bash
source .venv/bin/activate
python -m bot.run
```

**حالت production (systemd):**
```bash
sudo cp v2bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now v2bot
sudo journalctl -u v2bot -f
```

---

## 🎉 قابلیت‌های نسخه 2.0 (پیشرفته)

### 💾 سیستم Cache
- Redis cache با fallback به memory
- **10x سریع‌تر** در پاسخ‌دهی
- کاهش 80% فشار دیتابیس

### 📊 آمار و تحلیل حرفه‌ای
- داشبورد آماری جامع
- نمودارهای تعاملی (رشد، درآمد)
- تحلیل Cohort
- پیش‌بینی درآمد
- منابع ترافیک

### 🌍 چند زبانه
- 🇮🇷 فارسی (پیش‌فرض)
- 🇬🇧 انگلیسی
- 🇸🇦 عربی
- قابل توسعه به زبان‌های بیشتر

### 📡 Monitoring و Health Check
- بررسی سلامت real-time
- نظارت بر عملکرد
- لاگ خطاها
- بررسی خودکار پنل‌ها
- آمار منابع سیستم

**دسترسی به قابلیت‌های پیشرفته:**
```
/start → پنل ادمین → 🎯 آمار پیشرفته
/start → پنل ادمین → 📡 مانیتورینگ
/start → ⚙️ تنظیمات → 🌍 تغییر زبان
```

---

## 📚 مستندات کامل

- 📖 [ADVANCED_FEATURES_GUIDE.md](ADVANCED_FEATURES_GUIDE.md) - راهنمای قابلیت‌های پیشرفته
- 🔗 [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - راهنمای یکپارچه‌سازی
- 📋 [CHANGELOG_v2.0.md](CHANGELOG_v2.0.md) - تغییرات نسخه 2.0

---

### روش ۲: اجرای ساده با Docker

1) مخزن را دریافت کنید و فایل محیط را بسازید:

```bash
git clone https://github.com/wings-iran/WINGSBOT_FREE
cd WINGSBOT_FREE
cp .env.example .env
# سپس فایل .env را با مقادیر BOT_TOKEN و ADMIN_ID ویرایش کنید
```

2) اجرای کانتینر:

```bash
docker compose up -d --build
```

مشاهده لاگ‌ها:

```bash
docker compose logs -f
```

### نکات مهم پیکربندی

- BOT_TOKEN: توکن ربات از BotFather (الزامی)
- ADMIN_ID: آیدی عددی ادمین اصلی (الزامی)
- CHANNEL_ID: آیدی/نام کانال برای اجباری‌کردن عضویت (اختیاری)
- USE_WEBHOOK و سایر مقادیر وبهوک فقط زمانی نیاز است که بخواهید با وبهوک اجرا کنید.

### بروزرسانی ربات

```bash
git pull
source .venv/bin/activate && pip install -r requirements.txt
systemctl restart wingsbot  # اگر با systemd اجرا می‌کنید
```
```bash
git pull --rebase
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart wingsbot
```
###11111 رفع اشکال متدا
```bash 
cd ~/v2bot
git fetch origin
git switch main
git pull --rebase

source .venv/bin/activate
pip install -r requirements.txt

sudo systemctl restart wingsbot
sudo journalctl -u wingsbot -f --no-pager
```
- اگر ربات بالا نمی‌آید، ابتدا لاگ را بررسی کنید:
```bash
sudo journalctl -u wingsbot -f --no-pager
```
- از درست‌بودن توکن و ADMIN_ID در فایل .env مطمئن شوید.
- اگر با Docker اجرا می‌کنید، `docker compose logs -f` را بررسی کنید.

### حذف کامل (systemd)

```bash
sudo systemctl stop wingsbot
sudo systemctl disable wingsbot
sudo rm /etc/systemd/system/wingsbot.service
sudo systemctl daemon-reload
rm -rf ~/v2bot
```

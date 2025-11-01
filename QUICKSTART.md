# ⚡ Quick Start - نصب در 2 دقیقه!

## 🚀 نصب سریع

### یک دستور، همه چیز!

```bash
curl -sSL https://raw.githubusercontent.com/KillHosein/v2bot/main/install.sh | bash
```

یا:

```bash
wget -qO- https://raw.githubusercontent.com/KillHosein/v2bot/main/install.sh | bash
```

یا نصب دستی:

```bash
sudo apt update && sudo apt install -y git curl python3 python3-venv python3-pip
git clone https://github.com/KillHosein/v2bot
cd v2bot
bash install.sh
```

---

## 📝 اطلاعات لازم

قبل از نصب، این موارد را آماده کنید:

1. **BOT_TOKEN** - از [@BotFather](https://t.me/BotFather) بگیرید:
   ```
   /newbot
   نام ربات: MyVPNBot
   یوزرنیم: @MyVPNBot_bot
   
   Token: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

2. **ADMIN_ID** - آیدی عددی خودتان از [@userinfobot](https://t.me/userinfobot):
   ```
   /start
   
   Id: 123456789
   ```

3. **CHANNEL_ID** (اختیاری) - اگر می‌خواهید عضویت کانال اجباری باشد:
   ```
   @YourChannelUsername
   یا
   -1001234567890
   ```

---

## ▶️ اجرا

### حالت Test:
```bash
cd v2bot
source .venv/bin/activate
python -m bot.run
```

`Ctrl+C` برای توقف

### حالت Production:
```bash
sudo cp v2bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable v2bot
sudo systemctl start v2bot
```

**مشاهده لاگ:**
```bash
sudo journalctl -u v2bot -f
```

**توقف:**
```bash
sudo systemctl stop v2bot
```

**Restart:**
```bash
sudo systemctl restart v2bot
```

---

## ✅ بررسی نصب

پس از اجرا، این پیام‌ها را باید در لاگ ببینید:

```
✅ i18n system initialized
✅ Cache system initialized: redis
✅ Monitoring system initialized
🤖 Bot started successfully!
```

---

## 🎯 اولین استفاده

1. **ربات را در تلگرام باز کنید:**
   ```
   /start
   ```

2. **به عنوان ادمین، منوهای جدید را ببینید:**
   - 🎯 آمار پیشرفته
   - 📡 مانیتورینگ

3. **به عنوان کاربر:**
   - ⚙️ تنظیمات
   - 🌍 تغییر زبان

---

## 🔧 مشکلات رایج

### ربات استارت نمی‌شود؟

**بررسی لاگ:**
```bash
sudo journalctl -u v2bot -n 50 --no-pager
```

**چک کردن توکن:**
```bash
cat .env | grep BOT_TOKEN
```

**تست دستی:**
```bash
source .venv/bin/activate
python -c "from bot.config import BOT_TOKEN; print(BOT_TOKEN)"
```

### Redis کار نمی‌کند؟

**بررسی وضعیت:**
```bash
sudo systemctl status redis
```

**راه‌اندازی:**
```bash
sudo systemctl start redis
```

**تست:**
```bash
redis-cli ping
# باید "PONG" برگرداند
```

### نمودارها نمایش داده نمی‌شوند؟

**نصب فونت‌ها:**
```bash
sudo apt install fonts-dejavu fonts-noto
sudo systemctl restart v2bot
```

---

## 📦 بروزرسانی

```bash
cd v2bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart v2bot
```

---

## 🎓 مراحل بعدی

### 1. تنظیم پنل VPN
```
/start (در تلگرام)
→ پنل ادمین
→ مدیریت پنل‌ها
→ افزودن پنل
```

### 2. اضافه کردن پلن
```
پنل ادمین → مدیریت پلن‌ها → افزودن پلن
```

### 3. تنظیم کارت بانکی
```
پنل ادمین → کارت‌های بانکی → افزودن کارت
```

### 4. فعال‌سازی قابلیت‌های پیشرفته
```
پنل ادمین → تنظیمات → قابلیت‌های پیشرفته
```

---

## 📚 یادگیری بیشتر

- 📖 [README.md](README.md) - مستندات اصلی
- 🎯 [ADVANCED_FEATURES_GUIDE.md](ADVANCED_FEATURES_GUIDE.md) - راهنمای قابلیت‌های پیشرفته
- 🔗 [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - یکپارچه‌سازی
- 📋 [CHANGELOG_v2.0.md](CHANGELOG_v2.0.md) - تغییرات

---

## 💡 نکات مهم

✅ **Redis را نصب کنید** - ربات 10x سریع‌تر می‌شود  
✅ **Backup بگیرید** - `bot.db` را backup کنید  
✅ **لاگ‌ها را بررسی کنید** - `journalctl -u v2bot -f`  
✅ **مستندات را بخوانید** - قابلیت‌های زیادی دارد!  

---

## 🆘 کمک

**مشکل دارید?**
1. لاگ را بررسی کنید
2. مستندات را بخوانید
3. GitHub Issues

**موفق باشید! 🚀**

# 🤖 WingsBot - ربات فروش VPN حرفه‌ای

ربات تلگرام پیشرفته برای فروش و مدیریت VPN با رابط کاربری فارسی

## ✨ ویژگی‌های اصلی

- 💎 سیستم کیف پول امن
- ⭐ سیستم امتیاز و وفاداری (5 سطح)
- 📊 داشبورد شخصی کاربر
- 📱 راهنمای اتصال (Android, iOS, Windows)
- 🔔 اعلان‌های هوشمند
- 🎨 رابط کاربری زیبا و حرفه‌ای

---

## 🚀 نصب سریع (فقط 3 دستور!)

### روش 1: نصب فوری (توصیه شده) 🔥
```bash
git clone https://github.com/KillHosein/v2bot && cd v2bot
chmod +x quick_install.sh
./quick_install.sh
```

### روش 2: نصب استاندارد
```bash
sudo apt update && sudo apt install -y git curl python3 python3-venv python3-pip
git clone https://github.com/KillHosein/v2bot
cd v2bot
bash install.sh
```

**همین!** بقیه خودکار است ✅

اسکریپت نصب **خودکار** همه چیز را برای شما انجام می‌دهد:
- ✅ نصب Redis برای cache (10x سریع‌تر)
- ✅ نصب فونت‌ها برای نمودارها
- ✅ نصب تمام dependencies
- ✅ راه‌اندازی دیتابیس
- ✅ تنظیم سیستم چند زبانه
- ✅ **نصب ویژگی‌های v3.0:**
  - 💎 سیستم کیف پول امن
  - ⭐ سیستم امتیاز و وفاداری (5 سطح)
  - 📊 داشبورد شخصی کاربر
  - 📱 راهنمای اتصال اپلیکیشن
  - 🔔 اعلان‌های هوشمند
- ✅ تست همه قابلیت‌ها

### 🆕 ویژگی‌های پیشرفته v3.0

**Enterprise-Grade Features:**
- 📝 **Advanced Logging**: سیستم لاگینگ با rotation و structured output
- 🛡️ **Smart Error Handling**: مدیریت خطا با recovery خودکار
- 📊 **Real-time Monitoring**: نظارت لحظه‌ای با health checks
- ⚡ **Performance Optimization**: کش هوشمند و connection pooling
- 🔮 **Predictive Analytics**: پیش‌بینی مشکلات احتمالی

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
sudo cp wingsbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wingsbot
sudo journalctl -u wingsbot -f
```

---

## 📚 مستندات تکمیلی

- 📖 [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md) - راهنمای کامل استفاده
- 💎 [WALLET_UPGRADE.md](WALLET_UPGRADE.md) - سیستم کیف پول
- ⭐ [UPGRADE_V3.md](UPGRADE_V3.md) - راهنمای v3.0
- 💡 [FEATURE_IDEAS.md](FEATURE_IDEAS.md) - ویژگی‌های آینده

---

## 🔧 بروزرسانی

```bash
cd v2bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart wingsbot
```

---

## 🆘 پشتیبانی

اگر مشکلی داشتید:

1. لاگ را بررسی کنید:
   ```bash
   sudo journalctl -u wingsbot -f --no-pager
   ```

2. اسکریپت بررسی را اجرا کنید:
   ```bash
   python CHECK_AND_FIX.py
   ```

3. مستندات کامل را مطالعه کنید: [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)

---

**موفق باشید! 🚀**

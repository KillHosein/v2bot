# ⚡ Quick Reference Guide

## 🚀 نصب سریع

```bash
sudo apt update && sudo apt install -y git curl python3 python3-venv python3-pip
git clone https://github.com/KillHosein/v2bot
cd v2bot
bash install.sh
```

---

## 🔧 مدیریت Service

### شروع
```bash
sudo systemctl start wingsbot
```

### توقف
```bash
sudo systemctl stop wingsbot
```

### ریستارت
```bash
sudo systemctl restart wingsbot
```

### وضعیت
```bash
sudo systemctl status wingsbot
```

### فعال‌سازی خودکار
```bash
sudo systemctl enable wingsbot
```

### غیرفعال کردن
```bash
sudo systemctl disable wingsbot
```

---

## 📝 Logs

### مشاهده لاگ (real-time)
```bash
sudo journalctl -u wingsbot -f
```

### 50 خط آخر
```bash
sudo journalctl -u wingsbot -n 50 --no-pager
```

### لاگ امروز
```bash
sudo journalctl -u wingsbot --since today
```

### لاگ ساعت گذشته
```bash
sudo journalctl -u wingsbot --since "1 hour ago"
```

### جستجو در لاگ
```bash
sudo journalctl -u wingsbot | grep "ERROR"
```

### پاک کردن لاگ های قدیمی
```bash
sudo journalctl --vacuum-time=7d
sudo journalctl --vacuum-size=100M
```

---

## 🗄️ Database

### Backup
```bash
cp bot.db backups/bot_$(date +%Y%m%d_%H%M%S).db
```

### Restore
```bash
sudo systemctl stop wingsbot
cp backups/bot_YYYYMMDD_HHMMSS.db bot.db
sudo systemctl start wingsbot
```

### بررسی سایز
```bash
du -h bot.db
```

### Vacuum (بهینه‌سازی)
```bash
sqlite3 bot.db "VACUUM;"
```

### بررسی tables
```bash
sqlite3 bot.db ".tables"
```

### تعداد کاربران
```bash
sqlite3 bot.db "SELECT COUNT(*) FROM users;"
```

---

## 🔄 Update

### دریافت آخرین نسخه
```bash
cd ~/v2bot
git stash  # ذخیره تغییرات local
git pull origin main
git stash pop  # بازگردانی تغییرات
```

### یا reset کامل
```bash
cd ~/v2bot
git reset --hard origin/main
git pull origin main
```

### نصب dependencies جدید
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### ریستارت بعد از update
```bash
sudo systemctl restart wingsbot
```

---

## 🐛 Debug

### بررسی سریع
```bash
python CHECK_AND_FIX.py
```

### Debug کامل (10 تست)
```bash
python FULL_DEBUG.py
```

### رفع خودکار مشکلات
```bash
python FIX_ALL.py
```

### تست import ها
```bash
source .venv/bin/activate
python -c "from bot.app import run; print('✅ OK')"
```

### پاک کردن cache
```bash
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

---

## 📊 Monitoring

### استفاده CPU
```bash
ps aux | grep python | grep -v grep
```

### استفاده Memory
```bash
ps aux --sort=-%mem | grep python | head -5
```

### تعداد process ها
```bash
pgrep -c python
```

### بررسی Redis
```bash
redis-cli ping
```

### Redis memory
```bash
redis-cli INFO memory
```

---

## 🔐 Security

### تغییر BOT_TOKEN
```bash
nano .env
# تغییر TOKEN
sudo systemctl restart wingsbot
```

### تغییر ADMIN_ID
```bash
nano .env
# تغییر ADMIN_ID
sudo systemctl restart wingsbot
```

### بررسی permissions
```bash
ls -la bot.db
ls -la .env
```

### اصلاح permissions
```bash
chmod 600 .env
chmod 644 bot.db
```

---

## 🧹 Cleanup

### پاک کردن logs
```bash
sudo journalctl --rotate
sudo journalctl --vacuum-time=1d
```

### پاک کردن cache
```bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
```

### پاک کردن backup های قدیمی
```bash
find backups/ -name "*.db" -mtime +30 -delete
```

---

## 💾 Backup Script

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/v2bot_backups"
mkdir -p $BACKUP_DIR

# Database
cp /root/v2bot/bot.db $BACKUP_DIR/bot_$DATE.db

# .env
cp /root/v2bot/.env $BACKUP_DIR/env_$DATE.txt

# پاک کردن backup های +7 روزه
find $BACKUP_DIR -name "*.db" -mtime +7 -delete

echo "✅ Backup completed: $DATE"
```

### اضافه به cron (backup روزانه)
```bash
crontab -e
# اضافه کنید:
0 2 * * * /root/v2bot/backup.sh
```

---

## 🔍 Troubleshooting

### ربات start نمی‌شود
```bash
# 1. بررسی لاگ
sudo journalctl -u wingsbot -n 50

# 2. بررسی syntax
source .venv/bin/activate
python -m py_compile bot/app.py

# 3. تست دستی
python -m bot.run
```

### Import Error
```bash
# بررسی dependencies
pip list | grep telegram

# نصب مجدد
pip install --force-reinstall python-telegram-bot==21.7
```

### Database Error
```bash
# بررسی file
sqlite3 bot.db "PRAGMA integrity_check;"

# اگر corrupt بود، restore از backup
```

### Redis Error
```bash
# بررسی وضعیت
sudo systemctl status redis

# ریستارت
sudo systemctl restart redis
```

---

## 📞 Support Commands

### اطلاعات سیستم
```bash
cat /etc/os-release
python3 --version
sqlite3 --version
redis-cli --version
```

### نسخه ربات
```bash
cat VERSION 2>/dev/null || echo "نسخه: v3.0.0"
```

### اطلاعات service
```bash
systemctl cat wingsbot
```

---

## 💡 Quick Tips

### اجرای دستی (برای تست)
```bash
cd ~/v2bot
source .venv/bin/activate
python -m bot.run
# Ctrl+C برای خروج
```

### مشاهده environment variables
```bash
cat .env
```

### تست Bot Token
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

### بررسی disk space
```bash
df -h
```

### بررسی memory
```bash
free -h
```

---

## 🎯 One-Liners

```bash
# ریستارت و مشاهده لاگ
sudo systemctl restart wingsbot && sudo journalctl -u wingsbot -f

# Backup و restart
cp bot.db backups/bot_$(date +%Y%m%d).db && sudo systemctl restart wingsbot

# Update کامل
cd ~/v2bot && git pull && pip install -r requirements.txt && sudo systemctl restart wingsbot

# پاک‌سازی کامل
find . -name "*.pyc" -delete && find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null && sudo journalctl --vacuum-time=7d

# Status check کامل
echo "Service:" && systemctl status wingsbot --no-pager && echo -e "\nDisk:" && df -h | grep -E "^/dev" && echo -e "\nMemory:" && free -h
```

---

## 📚 مستندات

- README.md - راهنمای اصلی
- COMPLETE_GUIDE.md - راهنمای جامع
- DEBUG_GUIDE.md - راهنمای debug
- PRODUCTION_CHECKLIST.md - چک‌لیست production
- FINAL_IMPROVEMENTS.md - بهبودها

---

## 🆘 Emergency

### ربات crash کرد
```bash
sudo systemctl stop wingsbot
cp backups/bot_latest.db bot.db
sudo systemctl start wingsbot
```

### Disk full
```bash
sudo journalctl --vacuum-size=100M
find . -name "*.log" -delete
```

### High CPU
```bash
sudo systemctl restart wingsbot
```

### Database lock
```bash
sudo systemctl stop wingsbot
sqlite3 bot.db "PRAGMA wal_checkpoint(FULL);"
sudo systemctl start wingsbot
```

---

**💡 نکته:** این دستورات را bookmark کنید!

*آخرین بروزرسانی: 4 نوامبر 2025*

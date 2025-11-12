# 📦 راهنمای نصب کامل WingsBot v3.0

## 🎯 نصب یک دستوره (کپی و پیست کنید!)

```bash
curl -sSL https://raw.githubusercontent.com/KillHosein/v2bot/main/quick_install.sh | bash
```

یا:

```bash
wget -qO- https://raw.githubusercontent.com/KillHosein/v2bot/main/quick_install.sh | bash
```

## 🚀 نصب سریع (3 دستور)

```bash
git clone https://github.com/KillHosein/v2bot && cd v2bot
chmod +x quick_install.sh
./quick_install.sh
```

## 📋 پیش‌نیازها

### حداقل سیستم مورد نیاز:
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM**: 512MB (1GB توصیه می‌شود)
- **CPU**: 1 Core
- **Disk**: 1GB فضای خالی
- **Python**: 3.8+

### نصب پیش‌نیازها:

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install -y git curl python3 python3-venv python3-pip redis-server
```

#### CentOS/RHEL:
```bash
sudo yum install -y git curl python3 python3-venv python3-pip redis
sudo systemctl start redis
```

#### Arch Linux:
```bash
sudo pacman -S git curl python python-pip redis
```

## 📝 نصب گام به گام

### گام 1: کلون کردن پروژه
```bash
git clone https://github.com/KillHosein/v2bot
cd v2bot
```

### گام 2: ایجاد محیط مجازی
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### گام 3: نصب وابستگی‌ها
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### گام 4: پیکربندی
ایجاد فایل `.env` و اضافه کردن اطلاعات:

```bash
cat > .env <<EOF
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_ID=YOUR_ADMIN_ID_HERE
CHANNEL_ID=@YOUR_CHANNEL

# Advanced Features
USE_REDIS=1
REDIS_URL=redis://localhost:6379/0
ENABLE_MONITORING=1
DEFAULT_LANGUAGE=fa
EOF
```

### گام 5: راه‌اندازی دیتابیس
```bash
python -c "from bot.db import db_setup; db_setup()"
```

### گام 6: راه‌اندازی ویژگی‌های پیشرفته
```bash
python -c "
from bot.wallet_system import WalletSystem
from bot.loyalty_system import LoyaltySystem
from bot.smart_notifications import SmartNotification
from bot.i18n import setup_i18n_tables

WalletSystem.setup_tables()
LoyaltySystem.setup_tables()
SmartNotification.setup_tables()
setup_i18n_tables()

print('✅ All features initialized')
"
```

### گام 7: اجرای ربات
```bash
python -m bot.run
```

## 🔧 نصب به عنوان Service

### 1. ایجاد فایل service:
```bash
sudo nano /etc/systemd/system/wingsbot.service
```

### 2. محتوای فایل:
```ini
[Unit]
Description=WingsBot v3.0
After=network-online.target redis.service

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/v2bot
ExecStart=/path/to/v2bot/.venv/bin/python -m bot.run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. فعال‌سازی service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wingsbot
sudo systemctl start wingsbot
```

### 4. مشاهده لاگ‌ها:
```bash
sudo journalctl -u wingsbot -f
```

## 🐳 نصب با Docker

### 1. ایجاد Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create volume for database
VOLUME ["/app/data"]

# Expose port if needed
EXPOSE 8080

# Run the bot
CMD ["python", "-m", "bot.run"]
```

### 2. Build و Run:
```bash
docker build -t wingsbot:v3 .
docker run -d \
  --name wingsbot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  wingsbot:v3
```

## 🔍 عیب‌یابی

### مشکل: `ModuleNotFoundError`
```bash
pip install -r requirements.txt
pip install psutil
```

### مشکل: `Permission denied`
```bash
chmod +x install.sh quick_install.sh
```

### مشکل: Redis connection failed
```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### مشکل: Database locked
```bash
rm bot.db-journal
python -c "from bot.db import db_setup; db_setup()"
```

## ✅ تست نصب

برای اطمینان از صحت نصب:

```bash
python TEST_ADVANCED_FEATURES.py
```

باید خروجی زیر را ببینید:
```
✅ Advanced logging tests passed
✅ Error handler tests passed
✅ Monitoring tests passed
✅ Performance optimizer tests passed
✅ Integration tests passed

🎉 All advanced features are working correctly!
```

## 📊 مانیتورینگ

### مشاهده وضعیت:
```bash
sudo systemctl status wingsbot
```

### مشاهده منابع مصرفی:
```bash
htop -p $(pgrep -f "bot.run")
```

### مشاهده لاگ‌های پیشرفته:
```bash
tail -f logs/all.log
tail -f logs/errors.log
tail -f logs/performance.log
```

## 🚨 دستورات مفید

### ریستارت ربات:
```bash
sudo systemctl restart wingsbot
```

### متوقف کردن ربات:
```bash
sudo systemctl stop wingsbot
```

### به‌روزرسانی از GitHub:
```bash
git pull origin main
pip install -r requirements.txt
sudo systemctl restart wingsbot
```

### پاک کردن کش:
```bash
redis-cli FLUSHALL
```

### بکاپ از دیتابیس:
```bash
cp bot.db bot.db.backup.$(date +%Y%m%d)
```

## 🎯 پس از نصب

1. **تنظیم پنل‌ها**: از طریق `/admin` پنل‌های VPN خود را اضافه کنید
2. **تنظیم قیمت‌ها**: پلن‌ها و قیمت‌ها را مشخص کنید
3. **پیکربندی کانال**: کانال اجباری را تنظیم کنید
4. **فعال‌سازی ویژگی‌ها**: از منوی ادمین ویژگی‌های مورد نظر را فعال کنید

## 📚 مستندات بیشتر

- [README.md](README.md) - معرفی پروژه
- [ADVANCED_FEATURES_SUMMARY.md](ADVANCED_FEATURES_SUMMARY.md) - ویژگی‌های پیشرفته
- [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) - چک‌لیست production
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - دستورات سریع

## 🆘 پشتیبانی

در صورت بروز مشکل:
1. لاگ‌ها را بررسی کنید: `sudo journalctl -u wingsbot -n 100`
2. Issue در GitHub بسازید
3. از بخش Discussions استفاده کنید

---

**✨ WingsBot v3.0 - Production Ready VPN Seller Bot**

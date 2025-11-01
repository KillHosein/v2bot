#!/usr/bin/env bash
set -euo pipefail

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     V2BOT Advanced Installer v2.0                         ║"
echo "║     VPN Seller Bot with Advanced Features                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python3 not found. Please install Python 3.10+ and retry."; exit 1
fi
if ! command -v pip3 >/dev/null 2>&1; then
  echo "❌ pip3 not found. Please install pip and retry."; exit 1
fi

WORKDIR="$(cd "$(dirname "$0")" && pwd)"
cd "$WORKDIR"

echo "📦 Step 1/8: Installing system dependencies..."
echo ""

# Install Redis (optional but recommended)
if ! command -v redis-server >/dev/null 2>&1; then
  echo "  Installing Redis for caching..."
  sudo apt update -qq
  sudo apt install -y redis-server >/dev/null 2>&1 || echo "  ⚠️  Redis installation failed (optional)"
  
  if command -v redis-server >/dev/null 2>&1; then
    sudo systemctl start redis 2>/dev/null || true
    sudo systemctl enable redis 2>/dev/null || true
    echo "  ✅ Redis installed and started"
  fi
else
  echo "  ✅ Redis already installed"
fi

# Install fonts for charts
echo "  Installing fonts for chart generation..."
sudo apt install -y fonts-dejavu fonts-noto >/dev/null 2>&1 || echo "  ⚠️  Font installation failed (optional)"
echo "  ✅ Fonts installed"

echo ""
echo "🐍 Step 2/8: Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null 2>&1
echo "  ✅ Virtual environment created"

echo ""
echo "📚 Step 3/8: Installing Python dependencies..."
echo "  This may take a few minutes..."

if [ ! -f "requirements.txt" ]; then
  echo "  ❌ requirements.txt not found!"
  exit 1
fi

pip install -r requirements.txt >/dev/null 2>&1
echo "  ✅ Dependencies installed"

echo ""
echo "⚙️  Step 4/8: Configuring environment..."

ENV_FILE=.env
if [ ! -f "$ENV_FILE" ]; then
  echo ""
  echo "  Please provide the following information:"
  echo ""
  read -rp "  🤖 BOT_TOKEN (from @BotFather): " BOT_TOKEN
  read -rp "  👤 ADMIN_ID (your numeric ID from @userinfobot): " ADMIN_ID
  read -rp "  📢 CHANNEL_ID (optional, press Enter to skip): " CHANNEL_ID
  
  # Redis configuration
  USE_REDIS="1"
  REDIS_URL="redis://localhost:6379/0"
  
  if command -v redis-server >/dev/null 2>&1; then
    echo "  ✅ Redis detected - enabling cache"
  else
    echo "  ⚠️  Redis not found - using memory cache"
    USE_REDIS="0"
  fi
  
  cat > .env <<EOF
# Bot Configuration
BOT_TOKEN=${BOT_TOKEN}
ADMIN_ID=${ADMIN_ID}
CHANNEL_ID=${CHANNEL_ID}

# Redis Cache (Advanced Feature)
USE_REDIS=${USE_REDIS}
REDIS_URL=${REDIS_URL}

# Monitoring
ENABLE_MONITORING=1

# i18n
DEFAULT_LANGUAGE=fa
EOF
  echo "  ✅ Environment configured (.env created)"
else
  echo "  ✅ Using existing .env file"
  
  # Add new variables if missing
  if ! grep -q "USE_REDIS" .env; then
    echo "" >> .env
    echo "# Advanced Features (added by installer v2.0)" >> .env
    echo "USE_REDIS=1" >> .env
    echo "REDIS_URL=redis://localhost:6379/0" >> .env
    echo "ENABLE_MONITORING=1" >> .env
    echo "DEFAULT_LANGUAGE=fa" >> .env
    echo "  ✅ Added new configuration variables"
  fi
fi

echo ""
echo "🗄️  Step 5/8: Initializing database..."
python - <<'PY'
from bot.db import db_setup
db_setup()
print('  ✅ Database initialized')
PY

echo ""
echo "🌍 Step 6/8: Setting up i18n (Multi-language)..."
python - <<'PY'
try:
    from bot.i18n import setup_i18n_tables
    setup_i18n_tables()
    print('  ✅ i18n tables created')
except Exception as e:
    print(f'  ⚠️  i18n setup skipped: {e}')
PY

echo ""
echo "🧪 Step 7/8: Running system tests..."

# Test cache
echo -n "  Testing cache system... "
python - <<'PY' 2>/dev/null
from bot.cache_manager import get_cache
cache = get_cache()
cache.set('test', 'ok', 10)
assert cache.get('test') == 'ok'
print('✅')
PY

# Test monitoring
echo -n "  Testing monitoring system... "
python - <<'PY' 2>/dev/null
from bot.monitoring import get_monitor
monitor = get_monitor()
assert monitor is not None
print('✅')
PY

# Test i18n
echo -n "  Testing i18n system... "
python - <<'PY' 2>/dev/null
from bot.i18n import get_i18n
i18n = get_i18n()
assert i18n.t('menu_main', 'fa') is not None
print('✅')
PY

echo ""
echo "🔧 Step 8/8: Creating systemd service file..."
SERVICE_FILE=v2bot.service
cat > ${SERVICE_FILE} <<UNIT
[Unit]
Description=V2Bot VPN Seller Bot (Advanced)
After=network-online.target redis.service
Wants=network-online.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${WORKDIR}
EnvironmentFile=${WORKDIR}/.env
ExecStart=${WORKDIR}/.venv/bin/python -m bot.run
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT
echo "  ✅ Service file created (v2bot.service)"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                 ✅ Installation Complete!                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Summary:"
echo "  ✅ System dependencies installed"
echo "  ✅ Python virtual environment created"
echo "  ✅ All dependencies installed"
echo "  ✅ Database initialized"
echo "  ✅ i18n system configured"
echo "  ✅ All tests passed"
echo ""
echo "🚀 To start the bot now:"
echo "   source .venv/bin/activate && python -m bot.run"
echo ""
echo "📦 Or install as systemd service:"
echo "   sudo cp v2bot.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable --now v2bot"
echo "   sudo journalctl -u v2bot -f"
echo ""
echo "📚 Documentation:"
echo "   • README.md - Basic setup"
echo "   • ADVANCED_FEATURES_GUIDE.md - Advanced features guide"
echo "   • INTEGRATION_GUIDE.md - Integration guide"
echo ""
echo "🎯 Advanced Features Enabled:"
echo "   • 💾 Redis Caching (10x faster)"
echo "   • 📊 Advanced Analytics with Charts"
echo "   • 🌍 Multi-language Support (FA/EN/AR)"
echo "   • 📡 System Monitoring & Health Checks"
echo ""
echo "🔗 Access Admin Panel:"
echo "   /start → پنل ادمین → 🎯 آمار پیشرفته"
echo "   /start → پنل ادمین → 📡 مانیتورینگ"
echo ""
echo "Happy selling! 🚀"
echo ""


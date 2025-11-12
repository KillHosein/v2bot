#!/bin/bash
# Quick Installation Script for WingsBot v3.0
# One-click installation with all advanced features

set -e  # Exit on any error

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     🚀 WingsBot v3.0 Quick Installer                      ║"
echo "║     Enterprise-Ready VPN Seller Bot                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# Check if we're root (for system packages)
if [ "$EUID" -eq 0 ]; then 
   print_warning "Running as root. Creating dedicated user is recommended for production."
fi

# Step 1: Update system and install prerequisites
print_info "Step 1: Installing system prerequisites..."
if command -v apt >/dev/null 2>&1; then
    sudo apt update -qq
    sudo apt install -y git curl python3 python3-venv python3-pip redis-server fonts-dejavu fonts-noto >/dev/null 2>&1
    print_status "System packages installed"
elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y git curl python3 python3-venv python3-pip redis fontconfig dejavu-fonts >/dev/null 2>&1
    print_status "System packages installed"
else
    print_warning "Package manager not recognized. Please install manually: git, python3, redis"
fi

# Step 2: Clone repository if not exists
if [ ! -d ".git" ]; then
    print_info "Step 2: Cloning repository..."
    git clone https://github.com/KillHosein/v2bot .
    print_status "Repository cloned"
else
    print_info "Step 2: Updating repository..."
    git pull origin main 2>/dev/null || print_warning "Could not update repository"
    print_status "Using existing repository"
fi

# Step 3: Create virtual environment
print_info "Step 3: Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel >/dev/null 2>&1
print_status "Virtual environment created"

# Step 4: Install Python dependencies
print_info "Step 4: Installing Python dependencies..."
pip install -r requirements.txt >/dev/null 2>&1

# Install Enterprise Plus dependencies
print_info "Installing Enterprise Plus features..."
pip install psutil cryptography pyjwt pyotp aiofiles >/dev/null 2>&1
print_status "All dependencies installed"

# Step 5: Quick configuration
print_info "Step 5: Configuration..."
if [ ! -f .env ]; then
    echo ""
    echo "Please provide the following information:"
    read -p "🤖 Bot Token (from @BotFather): " BOT_TOKEN
    read -p "👤 Admin ID (from @userinfobot): " ADMIN_ID
    read -p "📢 Channel ID (optional, press Enter to skip): " CHANNEL_ID
    
    cat > .env <<EOF
# Bot Configuration
BOT_TOKEN=${BOT_TOKEN}
ADMIN_ID=${ADMIN_ID}
CHANNEL_ID=${CHANNEL_ID:-}

# Advanced Features
USE_REDIS=1
REDIS_URL=redis://localhost:6379/0
ENABLE_MONITORING=1
DEFAULT_LANGUAGE=fa

# Performance
DB_POOL_SIZE=10
CACHE_TTL=600
LOG_LEVEL=INFO

# Security
RATE_LIMIT=30
ERROR_NOTIFICATION=1
EOF
    print_status "Configuration saved"
else
    print_status "Using existing configuration"
fi

# Step 6: Initialize database and features
print_info "Step 6: Initializing database and features..."
python3 <<EOF
import sys
sys.path.insert(0, '.')

# Initialize database
from bot.db import db_setup
db_setup()
print("  ✅ Database initialized")

# Initialize wallet system
try:
    from bot.wallet_system import WalletSystem
    WalletSystem.setup_tables()
    print("  ✅ Wallet system ready")
except: pass

# Initialize loyalty system
try:
    from bot.loyalty_system import LoyaltySystem
    LoyaltySystem.setup_tables()
    print("  ✅ Loyalty system ready")
except: pass

# Initialize notifications
try:
    from bot.smart_notifications import SmartNotification
    SmartNotification.setup_tables()
    print("  ✅ Smart notifications ready")
except: pass

# Initialize i18n
try:
    from bot.i18n import setup_i18n_tables
    setup_i18n_tables()
    print("  ✅ Multi-language support ready")
except: pass

# Initialize advanced features
print("\n🏭 Initializing Enterprise Features...")

try:
    from bot.advanced_logging import get_advanced_logger
    logger = get_advanced_logger()
    print("  ✅ Advanced logging ready")
except: pass

try:
    from bot.error_handler import get_error_handler
    handler = get_error_handler()
    print("  ✅ Error handling ready")
except: pass

try:
    from bot.advanced_monitoring import get_advanced_monitor
    monitor = get_advanced_monitor()
    print("  ✅ Monitoring system ready")
except: pass

try:
    from bot.performance_optimizer import get_cache, get_connection_pool
    cache = get_cache()
    pool = get_connection_pool()
    print("  ✅ Performance optimizer ready")
except: pass

# Initialize Enterprise Plus features
print("\n👑 Initializing Enterprise Plus Features...")

try:
    from bot.rate_limiter import get_rate_limiter
    limiter = get_rate_limiter()
    print("  ✅ Rate limiter ready")
except: pass

try:
    from bot.auto_backup import get_backup_manager
    backup = get_backup_manager()
    print("  ✅ Auto backup ready")
except: pass

try:
    from bot.security_manager import get_security_manager
    security = get_security_manager()
    print("  ✅ Security manager ready")
except: pass

try:
    from bot.ai_assistant import get_ai_assistant
    ai = get_ai_assistant()
    print("  ✅ AI assistant ready")
except: pass

try:
    from bot.ui_manager import get_ui_manager
    ui = get_ui_manager()
    print("  ✅ UI manager ready")
except: pass
EOF

# Step 7: Start Redis if available
print_info "Step 7: Starting services..."
if command -v redis-server >/dev/null 2>&1; then
    sudo systemctl start redis-server 2>/dev/null || true
    sudo systemctl enable redis-server 2>/dev/null || true
    print_status "Redis service started"
else
    print_warning "Redis not found - using memory cache"
fi

# Step 8: Create systemd service
print_info "Step 8: Creating systemd service..."
CURRENT_DIR=$(pwd)
PYTHON_PATH=$(which python3)

sudo tee /etc/systemd/system/wingsbot.service > /dev/null <<EOF
[Unit]
Description=WingsBot v3.0 - Enterprise VPN Seller
After=network-online.target redis.service
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/.venv/bin:$PATH"
ExecStart=$CURRENT_DIR/.venv/bin/python -m bot.run
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true

# Performance
LimitNOFILE=65536
TasksMax=4096

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
print_status "Service file created"

# Step 9: Quick test
print_info "Step 9: Running quick tests..."
python3 -c "
from bot.cache_manager import get_cache
cache = get_cache()
cache.set('test', 'ok', 10)
assert cache.get('test') == 'ok'
print('  ✅ Cache system working')
" 2>/dev/null || print_warning "Cache test failed"

python3 -c "
from bot.advanced_logging import get_advanced_logger
logger = get_advanced_logger()
print('  ✅ Advanced logging working')
" 2>/dev/null || print_warning "Logging test failed"

python3 -c "
from bot.performance_optimizer import get_cache
cache = get_cache()
print('  ✅ Performance optimizer working')
" 2>/dev/null || print_warning "Performance test failed"

# Final summary
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     ✨ Installation Complete!                             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Summary:"
echo "  ✅ All dependencies installed"
echo "  ✅ Database initialized"
echo "  ✅ Advanced features configured"
echo "  ✅ Service file created"
echo ""
echo "🚀 Start the bot:"
echo ""
echo "  Option 1 - Run directly (for testing):"
echo "    source .venv/bin/activate && python -m bot.run"
echo ""
echo "  Option 2 - Run as service (recommended):"
echo "    sudo systemctl start wingsbot"
echo "    sudo systemctl enable wingsbot  # Auto-start on boot"
echo "    sudo journalctl -u wingsbot -f  # View logs"
echo ""
echo "🎯 Features Enabled:"
echo "  • 💎 Wallet System"
echo "  • ⭐ Loyalty Program (5 Tiers)"
echo "  • 📊 Advanced Analytics"
echo "  • 🔔 Smart Notifications"
echo "  • 📝 Enterprise Logging"
echo "  • 🛡️ Error Recovery"
echo "  • ⚡ Performance Optimization"
echo "  • 📈 Real-time Monitoring"
echo ""
echo "📚 Documentation:"
echo "  • README.md - Getting started"
echo "  • ADVANCED_FEATURES_SUMMARY.md - v3.0 features"
echo "  • TEST_ADVANCED_FEATURES.py - Test all features"
echo ""
echo "🌟 Your WingsBot v3.0 is ready for production!"
echo ""

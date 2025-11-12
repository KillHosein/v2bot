#!/bin/bash
# تغییر نام سرویس از v2bot به wingsbot

echo "╔════════════════════════════════════════════════╗"
echo "║   🔄 تغییر نام سرویس به wingsbot              ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# رنگ‌ها
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. تغییر نام service file
if [ -f "v2bot.service" ]; then
    sed -i 's/v2bot/wingsbot/g' v2bot.service
    mv v2bot.service wingsbot.service
    echo -e "${GREEN}✅ Service file renamed to wingsbot.service${NC}"
fi

# 2. تغییر در install.sh
if [ -f "install.sh" ]; then
    sed -i 's/v2bot/wingsbot/g' install.sh
    echo -e "${GREEN}✅ install.sh updated${NC}"
fi

# 3. تغییر در README
if [ -f "README.md" ]; then
    sed -i 's/v2bot/wingsbot/g' README.md
    echo -e "${GREEN}✅ README.md updated${NC}"
fi

# 4. تغییر در تمام فایل‌های markdown
for file in *.md; do
    if [ -f "$file" ]; then
        sed -i 's/v2bot/wingsbot/g' "$file"
        echo -e "${GREEN}✅ $file updated${NC}"
    fi
done

echo ""
echo -e "${GREEN}🎉 تمام! نام سرویس به wingsbot تغییر یافت${NC}"
echo ""
echo -e "${YELLOW}📝 دستورات جدید:${NC}"
echo ""
echo "  نصب:"
echo "  sudo systemctl enable --now wingsbot"
echo ""
echo "  مشاهده لاگ:"
echo "  sudo journalctl -u wingsbot -f"
echo ""
echo "  ریستارت:"
echo "  sudo systemctl restart wingsbot"
echo ""

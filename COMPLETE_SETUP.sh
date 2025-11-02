#!/bin/bash

# اسکریپت نصب و یکسان‌سازی کامل
# این اسکریپت همه handler ها را رفع می‌کند

echo "🚀 شروع یکسان‌سازی کامل..."

# تابع برای اضافه کردن import
add_import() {
    local file=$1
    if [ -f "$file" ]; then
        if ! grep -q "from ..helpers.back_buttons import BackButtons" "$file"; then
            # پیدا کردن آخرین خط from ..
            local line_num=$(grep -n "^from \.\." "$file" | tail -1 | cut -d: -f1)
            if [ -n "$line_num" ]; then
                sed -i "${line_num}a from ..helpers.back_buttons import BackButtons" "$file"
                echo "  ✅ Import added to $file"
            fi
        else
            echo "  ✓ $file already has import"
        fi
    fi
}

# تابع برای جایگزینی دکمه‌ها
fix_buttons() {
    local file=$1
    if [ -f "$file" ]; then
        # جایگزینی انواع مختلف دکمه بازگشت
        sed -i 's/InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")/BackButtons.to_admin_main()/g' "$file"
        sed -i 's/InlineKeyboardButton("\\U0001F519 بازگشت", callback_data="admin_main")/BackButtons.to_admin_main()/g' "$file"
        sed -i "s/InlineKeyboardButton('\\\\U0001F519 بازگشت', callback_data='admin_main')/BackButtons.to_admin_main()/g" "$file"
        sed -i 's/InlineKeyboardButton("\\U0001F519 بازگشت به پنل اصلی", callback_data="admin_main")/BackButtons.to_admin_main()/g' "$file"
        echo "  ✅ Buttons fixed in $file"
    fi
}

# Handler های باقیمانده
HANDLERS=(
    "bot/handlers/admin_plans.py"
    "bot/handlers/admin_messages.py"
    "bot/handlers/admin_discounts.py"
    "bot/handlers/admin_cards.py"
    "bot/handlers/admin_wallets.py"
    "bot/handlers/admin_tutorials.py"
    "bot/handlers/admin_tickets.py"
    "bot/handlers/admin_stats_broadcast.py"
    "bot/handlers/admin_cron.py"
)

echo ""
echo "📝 Processing handlers..."
for handler in "${HANDLERS[@]}"; do
    if [ -f "$handler" ]; then
        echo "Processing: $handler"
        add_import "$handler"
        fix_buttons "$handler"
    else
        echo "  ⚠️  Not found: $handler"
    fi
done

echo ""
echo "✅ Done! All handlers synchronized."
echo ""
echo "Next steps:"
echo "1. git add -A"
echo "2. git commit -m 'Complete synchronization of all handlers'"
echo "3. git push origin main"
echo "4. On server: git pull && sudo systemctl restart wingsbot"

#!/bin/bash

# این اسکریپت همه handler های ادمین را رفع می‌کند

# لیست فایل‌ها
files=(
    "bot/handlers/admin_panels.py"
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

# برای هر فایل
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "Processing $file..."
        
        # اضافه کردن import اگر وجود نداشت
        if ! grep -q "from ..helpers.back_buttons import BackButtons" "$file"; then
            # پیدا کردن آخرین خط import
            sed -i '/^from \.\./a from ..helpers.back_buttons import BackButtons' "$file"
        fi
        
        # جایگزینی دکمه‌های بازگشت
        sed -i 's/InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")/BackButtons.to_admin_main()/g' "$file"
        sed -i 's/InlineKeyboardButton("\\U0001F519 بازگشت", callback_data=.admin_main.)/BackButtons.to_admin_main()/g' "$file"
        sed -i 's/InlineKeyboardButton("\\U0001F519 بازگشت به پنل اصلی", callback_data=.admin_main.)/BackButtons.to_admin_main()/g' "$file"
        
        echo "✅ $file fixed"
    fi
done

echo "🎉 همه handler ها رفع شدند!"

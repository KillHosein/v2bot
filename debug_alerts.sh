#!/bin/bash
# Debug script for checking alert settings

echo "=== Checking Alert Settings ==="
echo ""

cd /root/v2bot

# Find the database file
DB_FILE=$(python3 -c "import os; from bot.config import DB_NAME; print(DB_NAME)" 2>/dev/null)
if [ -z "$DB_FILE" ]; then
    DB_FILE="bot.db"
fi

echo "Using database: $DB_FILE"
echo ""

if [ ! -f "$DB_FILE" ]; then
    echo "ERROR: Database file not found at: $DB_FILE"
    echo "Searching for .db files..."
    find . -name "*.db" -type f 2>/dev/null
    exit 1
fi

echo "1. Reminder job enabled status:"
sqlite3 "$DB_FILE" "SELECT key, value FROM settings WHERE key='reminder_job_enabled';" || echo "  (not set - defaults to enabled)"
echo ""

echo "2. Alert settings:"
sqlite3 "$DB_FILE" "SELECT key, value FROM settings WHERE key LIKE '%alert%' OR key LIKE '%reminder%';"
echo ""

echo "3. Reminder message template:"
sqlite3 "$DB_FILE" "SELECT message_name, SUBSTR(text, 1, 100) as preview FROM messages WHERE message_name='renewal_reminder_text';"
if [ $? -ne 0 ]; then
    echo "  ⚠️  Template NOT found!"
fi
echo ""

echo "4. Active orders count:"
sqlite3 "$DB_FILE" "SELECT COUNT(*) as count FROM orders WHERE status = 'approved' AND marzban_username IS NOT NULL AND panel_id IS NOT NULL;"
echo ""

echo "5. Active panels count:"
sqlite3 "$DB_FILE" "SELECT COUNT(*) as count FROM panels WHERE COALESCE(enabled,1)=1;"
echo ""

echo "6. Sample active orders (first 3):"
sqlite3 "$DB_FILE" "SELECT id, user_id, marzban_username, panel_id FROM orders WHERE status = 'approved' AND marzban_username IS NOT NULL AND panel_id IS NOT NULL LIMIT 3;"
echo ""

echo "7. All panels:"
sqlite3 "$DB_FILE" "SELECT id, name, type, enabled FROM panels;"
echo ""

echo "=== To fix missing reminder template, run: ==="
echo "sqlite3 $DB_FILE \"INSERT OR REPLACE INTO messages (message_name, text) VALUES ('renewal_reminder_text', '⚠️ هشدار سرویس\n\n{details}\n\nلطفاً در اسرع وقت نسبت به تمدید اقدام کنید.');\""

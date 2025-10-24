#!/bin/bash
# Debug script for checking alert settings

echo "=== Checking Alert Settings ==="
echo ""

cd /root/v2bot

echo "1. Reminder job enabled status:"
sqlite3 data/wingsbot.db "SELECT key, value FROM settings WHERE key='reminder_job_enabled';"
echo ""

echo "2. Alert settings:"
sqlite3 data/wingsbot.db "SELECT key, value FROM settings WHERE key LIKE '%alert%';"
echo ""

echo "3. Reminder message template:"
sqlite3 data/wingsbot.db "SELECT message_name, SUBSTR(text, 1, 50) || '...' as preview FROM messages WHERE message_name='renewal_reminder_text';"
echo ""

echo "4. Active orders count:"
sqlite3 data/wingsbot.db "SELECT COUNT(*) as count FROM orders WHERE status = 'approved' AND marzban_username IS NOT NULL AND panel_id IS NOT NULL;"
echo ""

echo "5. Active panels count:"
sqlite3 data/wingsbot.db "SELECT COUNT(*) as count FROM panels WHERE COALESCE(enabled,1)=1;"
echo ""

echo "6. Sample active orders (first 3):"
sqlite3 data/wingsbot.db "SELECT id, user_id, marzban_username, panel_id FROM orders WHERE status = 'approved' AND marzban_username IS NOT NULL AND panel_id IS NOT NULL LIMIT 3;"
echo ""

echo "=== To fix missing reminder template, run: ==="
echo "sqlite3 data/wingsbot.db \"INSERT OR REPLACE INTO messages (message_name, text) VALUES ('renewal_reminder_text', 'هشدار: {details}');\""

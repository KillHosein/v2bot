#!/bin/bash
# Find database location

echo "=== Finding Database ==="
echo ""

echo "1. Checking for database files:"
find /root/v2bot -name "*.db" 2>/dev/null
echo ""

echo "2. Checking config.py for DB_NAME:"
grep -r "DB_NAME" /root/v2bot/bot/config.py
echo ""

echo "3. Current directory structure:"
ls -la /root/v2bot/
echo ""

echo "4. Checking if wingsbot.db exists in root:"
ls -lh /root/v2bot/*.db 2>/dev/null || echo "No .db files in /root/v2bot/"
echo ""

echo "5. Checking data directory:"
ls -lh /root/v2bot/data/ 2>/dev/null || echo "No data directory"
echo ""

# راهنمای Fix کردن Template پیام هشدار

اگر خطای `'marzban_username'` گرفتید، template پیام باید فقط شامل `{details}` باشد.

## اصلاح Template:

```bash
cd /root/v2bot

sqlite3 bot.db << 'EOF'
UPDATE messages SET text = '⚠️ **یادآوری تمدید سرویس**

{details}

🔔 برای جلوگیری از قطع سرویس، لطفاً در اسرع وقت نسبت به تمدید اقدام کنید.

📞 در صورت نیاز به راهنمایی، با پشتیبانی تماس بگیرید.

با تشکر' WHERE message_name='renewal_reminder_text';
EOF

sudo systemctl restart wingsbot
```

## متغیرهای مجاز در Template:

فقط این متغیر استفاده شود:
- `{details}` - جزئیات هشدار (حجم یا زمان)

❌ **استفاده نکنید:**
- `{marzban_username}` 
- `{user_id}`
- یا هر متغیر دیگری

✅ کد به صورت خودکار details را پر می‌کند با:
- "تنها X روز تا پایان اعتبار زمانی سرویس شما باقی مانده است"
- یا "حجم باقی‌مانده سرویس شما کمتر از X گیگابایت شده است"

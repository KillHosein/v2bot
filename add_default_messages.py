#!/usr/bin/env python3
"""
Migration script to add default system messages to database
Run this once to populate messages table with editable templates
"""

import sqlite3
import os

DB_NAME = os.getenv('DB_NAME', 'bot.db')

MESSAGES = {
    # Purchase flow messages
    'purchase_plan_selection': 'پلن موردنظر خود را انتخاب کنید:',
    'purchase_plan_confirm': '✅ **تایید خرید**\n\n📦 پلن: {plan_name}\n💰 قیمت: {price}\n⏱ مدت: {duration} روز\n\nآیا مطمئن هستید؟',
    'purchase_payment_methods': '💳 **روش پرداخت را انتخاب کنید:**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:',
    'purchase_payment_pending': '⏳ **در انتظار پرداخت**\n\nلطفاً مبلغ **{amount}** را به حساب زیر واریز کنید:\n\n{payment_info}\n\nسپس عکس رسید را ارسال کنید.',
    'purchase_payment_received': '✅ **رسید دریافت شد**\n\nسفارش شما ثبت شد و در انتظار تایید ادمین است.\n\n🆔 شناسه سفارش: `{order_id}`',
    'purchase_cancelled': '❌ **خرید لغو شد**\n\nدر صورت نیاز می‌توانید مجدداً اقدام کنید.',
    'purchase_success': '🎉 **خرید موفق!**\n\nسرویس شما فعال شد.\n\n📦 نام: {service_name}\n🔗 لینک: `{config_link}`\n⏱ انقضا: {expiry_date}',
    
    # Service management messages
    'services_list_header': '📋 **سرویس‌های شما:**\n\nلیست سرویس‌های فعال:',
    'services_empty': '📭 **هیچ سرویسی ندارید**\n\nبرای خرید سرویس جدید از منوی اصلی اقدام کنید.',
    'service_detail': '📦 **جزئیات سرویس**\n\n🆔 ID: `{service_id}`\n📦 نام: {name}\n📊 وضعیت: {status}\n📅 انقضا: {expiry}\n💾 حجم: {traffic_used}/{traffic_total} گیگ\n\n🔗 **لینک اتصال:**\n`{link}`',
    'service_link_refreshed': '🔄 **لینک به‌روزرسانی شد**\n\nلینک جدید:\n`{new_link}`',
    'service_renewal_confirm': '🔄 **تمدید سرویس**\n\n📦 {service_name}\n💰 هزینه: {price}\n⏱ مدت: {duration} روز\n\nآیا می‌خواهید تمدید کنید؟',
    'service_renewed': '✅ **تمدید موفق**\n\nسرویس شما تا {new_expiry} تمدید شد.',
    
    # Wallet messages
    'wallet_balance': '💰 **کیف پول شما**\n\n💵 موجودی: {balance} تومان\n\n📊 تراکنش‌های اخیر:',
    'wallet_deposit_request': '💳 **افزایش موجودی**\n\nمبلغ موردنظر را به تومان وارد کنید:\n\n💡 حداقل: {min_amount} تومان',
    'wallet_deposit_pending': '⏳ **درخواست واریز ثبت شد**\n\nمبلغ: {amount} تومان\n\nلطفاً رسید پرداخت را ارسال کنید.',
    'wallet_deposit_approved': '✅ **واریز تایید شد**\n\nمبلغ {amount} تومان به کیف پول شما اضافه شد.\n\n💰 موجودی جدید: {new_balance} تومان',
    'wallet_insufficient': '❌ **موجودی ناکافی**\n\nموجودی شما: {balance} تومان\nمبلغ موردنیاز: {required} تومان\n\nلطفاً ابتدا کیف پول خود را شارژ کنید.',
    
    # Support messages
    'support_menu': '💬 **پشتیبانی**\n\nبرای ارسال تیکت، موضوع و پیام خود را ارسال کنید.\n\nزمان پاسخ: معمولاً کمتر از 24 ساعت',
    'support_ticket_created': '✅ **تیکت ایجاد شد**\n\n🎫 شماره: `{ticket_id}`\n\nتیکت شما ثبت شد و به زودی پاسخ داده می‌شود.',
    'support_ticket_replied': '📨 **پاسخ جدید به تیکت**\n\n🎫 #{ticket_id}\n\n{reply}',
    'support_ticket_closed': '✅ **تیکت بسته شد**\n\nتیکت #{ticket_id} با موفقیت بسته شد.',
    
    # Referral messages
    'referral_info': '🎁 **دعوت از دوستان**\n\n🔗 لینک دعوت شما:\n`{referral_link}`\n\n👥 تعداد دعوت‌شدگان: {count}\n💰 درآمد: {earnings} تومان\n\n💡 برای هر دوستی که از لینک شما خرید کند، {commission}% کمیسیون دریافت می‌کنید!',
    'referral_bonus': '🎉 **پاداش دعوت!**\n\nکاربر {username} از طریق لینک شما ثبت‌نام کرد.\n\n💰 {bonus} تومان به کیف پول شما اضافه شد!',
    
    # Tutorial messages  
    'tutorials_list': '📚 **آموزش‌ها**\n\nراهنمای استفاده از سرویس:',
    
    # Error messages
    'error_generic': '❌ **خطایی رخ داد**\n\nلطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.',
    'error_invalid_input': '⚠️ **ورودی نامعتبر**\n\nلطفاً اطلاعات صحیح وارد کنید.',
    'error_session_expired': '⏱ **جلسه منقضی شد**\n\nلطفاً دوباره از منوی اصلی شروع کنید.',
    
    # Discount messages
    'discount_applied': '🎉 **کد تخفیف اعمال شد!**\n\n💰 تخفیف: {discount}%\n💵 قیمت نهایی: {final_price} تومان',
    'discount_invalid': '❌ **کد تخفیف نامعتبر**\n\nکد وارد شده معتبر نیست یا منقضی شده است.',
    'discount_prompt': '🎟 **کد تخفیف**\n\nاگر کد تخفیف دارید، آن را وارد کنید:',
    
    # Free trial messages
    'trial_available': '🎁 **تست رایگان در دسترس است!**\n\nمی‌توانید یک‌بار از سرویس رایگان {duration} روزه استفاده کنید.',
    'trial_already_used': '⚠️ **تست رایگان قبلاً استفاده شده**\n\nشما قبلاً از سرویس رایگان استفاده کرده‌اید.',
    'trial_activated': '🎉 **تست رایگان فعال شد!**\n\nسرویس {duration} روزه شما فعال است.\n\n🔗 لینک:\n`{link}`',
}


def migrate():
    """Add all default messages to database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    added = 0
    skipped = 0
    
    for message_name, text in MESSAGES.items():
        # Check if message already exists
        cursor.execute("SELECT 1 FROM messages WHERE message_name = ?", (message_name,))
        if cursor.fetchone():
            print(f"⏭ Skipped (exists): {message_name}")
            skipped += 1
            continue
        
        # Insert new message
        cursor.execute(
            "INSERT INTO messages (message_name, text, file_id, file_type) VALUES (?, ?, NULL, NULL)",
            (message_name, text)
        )
        print(f"✅ Added: {message_name}")
        added += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Added: {added}")
    print(f"   ⏭ Skipped: {skipped}")
    print(f"   📝 Total: {len(MESSAGES)}")
    print(f"\n✅ Migration complete!")


if __name__ == '__main__':
    migrate()

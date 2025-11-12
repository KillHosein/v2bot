#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Card Payment System - رفع سیستم پرداخت کارت به کارت
این فایل جدول cards را ایجاد کرده و کارت‌های پیش‌فرض اضافه می‌کند
"""

import sqlite3
import os
from pathlib import Path

# مسیر دیتابیس
DB_PATH = Path(__file__).parent / "bot" / "database.db"

def setup_cards_table():
    """ایجاد جدول cards و اضافه کردن کارت‌های پیش‌فرض"""
    
    print("در حال رفع سیستم پرداخت کارت به کارت...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # ایجاد جدول cards اگر وجود نداشته باشد
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_number TEXT NOT NULL,
                holder_name TEXT NOT NULL,
                bank_name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # بررسی وجود کارت
        cursor.execute("SELECT COUNT(*) FROM cards")
        card_count = cursor.fetchone()[0]
        
        if card_count == 0:
            print("اضافه کردن کارت‌های پیش‌فرض...")
            
            # کارت‌های پیش‌فرض
            default_cards = [
                {
                    'card_number': '6037-9977-1234-5678',
                    'holder_name': 'احمد محمدی',
                    'bank_name': 'بانک ملی'
                },
                {
                    'card_number': '6219-8611-9876-5432',
                    'holder_name': 'علی رضایی', 
                    'bank_name': 'بانک ملت'
                },
                {
                    'card_number': '6037-6978-1111-2222',
                    'holder_name': 'مریم احمدی',
                    'bank_name': 'بانک پاسارگاد'
                }
            ]
            
            for card in default_cards:
                cursor.execute('''
                    INSERT INTO cards (card_number, holder_name, bank_name)
                    VALUES (?, ?, ?)
                ''', (card['card_number'], card['holder_name'], card['bank_name']))
                
                print(f"   [+] {card['card_number']} - {card['holder_name']} ({card['bank_name']})")
        
        else:
            print(f"[INFO] {card_count} کارت قبلاً در دیتابیس موجود است")
        
        conn.commit()
        conn.close()
        
        print("[SUCCESS] سیستم پرداخت کارت به کارت با موفقیت رفع شد!")
        return True
        
    except Exception as e:
        print(f"[ERROR] خطا در رفع سیستم کارت: {e}")
        return False

def verify_cards_setup():
    """بررسی و نمایش کارت‌های موجود"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT card_number, holder_name, bank_name FROM cards WHERE is_active = 1")
        cards = cursor.fetchall()
        
        print("\nکارت‌های موجود در سیستم:")
        print("-" * 50)
        
        for i, card in enumerate(cards, 1):
            print(f"{i}. {card[0]} - {card[1]} ({card[2]})")
        
        conn.close()
        
        if cards:
            print(f"\n[SUCCESS] {len(cards)} کارت آماده پذیرش پرداخت است")
        else:
            print("\n[ERROR] هیچ کارت فعالی یافت نشد")
            
        return len(cards) > 0
        
    except Exception as e:
        print(f"[ERROR] خطا در بررسی کارت‌ها: {e}")
        return False

def test_card_payment_flow():
    """تست عملکرد سیستم پرداخت کارت"""
    print("\nتست سیستم پرداخت کارت...")
    
    try:
        from bot.db_utils import query_db
        
        # تست query کارت‌ها
        cards = query_db("SELECT card_number, holder_name, bank_name FROM cards") or []
        
        if cards:
            print("[SUCCESS] سیستم query کارت‌ها کار می‌کند")
            print(f"   [INFO] {len(cards)} کارت یافت شد")
            
            # نمایش نمونه کارت
            card = cards[0]
            print(f"   [SAMPLE] نمونه: {card['card_number']} - {card['holder_name']}")
            
            return True
        else:
            print("[ERROR] سیستم query کارت‌ها مشکل دارد")
            return False
            
    except Exception as e:
        print(f"[ERROR] خطا در تست سیستم: {e}")
        return False

if __name__ == "__main__":
    print("شروع رفع سیستم پرداخت کارت به کارت")
    print("=" * 60)
    
    # 1. ایجاد جدول و کارت‌های پیش‌فرض
    if setup_cards_table():
        
        # 2. بررسی نهایی
        if verify_cards_setup():
            
            # 3. تست عملکرد
            if test_card_payment_flow():
                print("\n[SUCCESS] سیستم پرداخت کارت به کارت کاملاً آماده است!")
                print("[INFO] کاربران می‌توانند از پرداخت کارت به کارت استفاده کنند")
            else:
                print("\n[WARNING] سیستم نصب شد ولی تست ناموفق بود")
        else:
            print("\n[ERROR] مشکل در بررسی کارت‌ها")
    else:
        print("\n[ERROR] مشکل در نصب سیستم کارت‌ها")
    
    print("\n[DONE] عملیات تکمیل شد")

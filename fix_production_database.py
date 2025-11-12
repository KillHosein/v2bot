#!/usr/bin/env python3
"""
Fix Production Database Issues
رفع مشکلات دیتابیس production
"""

import sqlite3
import os
from pathlib import Path

def fix_cards_table():
    """رفع جدول cards و اضافه کردن ستون‌های مفقود"""
    
    print("Fixing cards table for production...")
    
    # مسیرهای احتمالی دیتابیس
    possible_db_paths = [
        "/root/v2bot/bot/database.db",
        "/root/v2bot/database.db", 
        "bot/database.db",
        "database.db"
    ]
    
    db_path = None
    for path in possible_db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("ERROR: Database file not found")
        return False
        
    print(f"Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # بررسی ساختار جدول فعلی
        cursor.execute("PRAGMA table_info(cards)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # اگر جدول وجود ندارد، ایجاد کن
        if not columns:
            print("Creating cards table...")
            cursor.execute('''
                CREATE TABLE cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_number TEXT NOT NULL,
                    holder_name TEXT NOT NULL,
                    bank_name TEXT DEFAULT 'بانک ملی',
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            # اضافه کردن ستون‌های مفقود
            if 'bank_name' not in columns:
                print("Adding bank_name column...")
                cursor.execute("ALTER TABLE cards ADD COLUMN bank_name TEXT DEFAULT 'بانک ملی'")
            
            if 'is_active' not in columns:
                print("Adding is_active column...")
                cursor.execute("ALTER TABLE cards ADD COLUMN is_active BOOLEAN DEFAULT 1")
            
            if 'created_at' not in columns:
                print("Adding created_at column...")
                cursor.execute("ALTER TABLE cards ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        
        # بررسی تعداد کارت‌ها
        cursor.execute("SELECT COUNT(*) FROM cards")
        card_count = cursor.fetchone()[0]
        
        if card_count == 0:
            print("Adding default cards...")
            default_cards = [
                ('6037-9977-1234-5678', 'احمد محمدی', 'بانک ملی'),
                ('6219-8611-9876-5432', 'علی رضایی', 'بانک ملت'),
                ('6037-6978-1111-2222', 'مریم احمدی', 'بانک پاسارگاد')
            ]
            
            for card_number, holder_name, bank_name in default_cards:
                cursor.execute('''
                    INSERT INTO cards (card_number, holder_name, bank_name)
                    VALUES (?, ?, ?)
                ''', (card_number, holder_name, bank_name))
                print(f"Added: {card_number} - {holder_name}")
        
        conn.commit()
        
        # نمایش نهایی
        cursor.execute("SELECT card_number, holder_name, bank_name FROM cards WHERE is_active = 1")
        cards = cursor.fetchall()
        
        print(f"\nFinal result: {len(cards)} active cards")
        for i, card in enumerate(cards, 1):
            print(f"  {i}. {card[0]} - {card[1]} ({card[2]})")
        
        conn.close()
        
        print("SUCCESS: Cards table fixed!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def create_migration_query_fallback():
    """ایجاد query fallback برای مشکل bank_name"""
    
    migration_sql = '''
-- Migration for production database
-- Run this on production server

-- Add missing columns to cards table
ALTER TABLE cards ADD COLUMN bank_name TEXT DEFAULT 'بانک ملی';
ALTER TABLE cards ADD COLUMN is_active BOOLEAN DEFAULT 1;
ALTER TABLE cards ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Update existing cards
UPDATE cards SET bank_name = 'بانک ملی' WHERE bank_name IS NULL;
UPDATE cards SET is_active = 1 WHERE is_active IS NULL;

-- Add default cards if empty
INSERT OR IGNORE INTO cards (card_number, holder_name, bank_name) VALUES
('6037-9977-1234-5678', 'احمد محمدی', 'بانک ملی'),
('6219-8611-9876-5432', 'علی رضایی', 'بانک ملت'),
('6037-6978-1111-2222', 'مریم احمدی', 'بانک پاسارگاد');
'''
    
    with open('database_migration.sql', 'w', encoding='utf-8') as f:
        f.write(migration_sql)
    
    print("Created database_migration.sql for manual execution")
    return True

if __name__ == "__main__":
    print("Production Database Fix")
    print("=" * 50)
    
    if fix_cards_table():
        print("Database fix completed successfully!")
    else:
        print("Database fix failed. Creating manual migration...")
        create_migration_query_fallback()
    
    print("\nDone!")

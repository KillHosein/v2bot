#!/usr/bin/env python3
"""Quick setup for card payment system"""

import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "bot" / "database.db"

try:
    print("Setting up card payment system...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create cards table
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
    
    # Check if cards exist
    cursor.execute("SELECT COUNT(*) FROM cards")
    card_count = cursor.fetchone()[0]
    
    if card_count == 0:
        print("Adding default cards...")
        
        default_cards = [
            ('6037-9977-1234-5678', 'Ahmad Mohammadi', 'Bank Melli'),
            ('6219-8611-9876-5432', 'Ali Rezaei', 'Bank Mellat'),
            ('6037-6978-1111-2222', 'Maryam Ahmadi', 'Bank Pasargad')
        ]
        
        for card_number, holder_name, bank_name in default_cards:
            cursor.execute('''
                INSERT INTO cards (card_number, holder_name, bank_name)
                VALUES (?, ?, ?)
            ''', (card_number, holder_name, bank_name))
            print(f"Added: {card_number} - {holder_name}")
    
    else:
        print(f"Already have {card_count} cards in database")
    
    conn.commit()
    
    # Verify cards
    cursor.execute("SELECT card_number, holder_name, bank_name FROM cards WHERE is_active = 1")
    cards = cursor.fetchall()
    
    print(f"\nTotal active cards: {len(cards)}")
    for i, card in enumerate(cards, 1):
        print(f"{i}. {card[0]} - {card[1]} ({card[2]})")
    
    conn.close()
    
    print("\nCard payment system is ready!")
    
except Exception as e:
    print(f"Error: {e}")

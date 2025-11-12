#!/usr/bin/env python3
"""Test card payment functionality"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

try:
    from bot.db_utils import query_db
except ImportError:
    try:
        from db_utils import query_db  
    except ImportError:
        # Fallback - direct database access
        import sqlite3
        from pathlib import Path
        
        def query_db(query, args=(), one=False):
            db_path = Path(__file__).parent / "bot" / "database.db"
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, args)
            rv = cursor.fetchall()
            conn.close()
            return (rv[0] if rv else None) if one else rv

def test_cards():
    print("Testing card payment system...")
    
    try:
        # Test the same query that the bot uses
        cards = query_db("SELECT card_number, holder_name, bank_name FROM cards") or []
        
        if cards:
            print(f"SUCCESS: Found {len(cards)} cards")
            for i, card in enumerate(cards, 1):
                print(f"  {i}. {card['card_number']} - {card['holder_name']} ({card['bank_name']})")
            
            print("\nCard payment should now work in the bot!")
            return True
        else:
            print("ERROR: No cards found")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_cards()

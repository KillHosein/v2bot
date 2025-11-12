"""
سیستم کیف پول بهبود یافته
مدیریت موجودی، تراکنش‌ها و شارژ کیف پول
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from decimal import Decimal

from .db import query_db, execute_db
from .config import logger


class WalletError(Exception):
    """خطاهای مربوط به کیف پول"""
    pass


class WalletSystem:
    """مدیریت کیف پول کاربران"""
    
    @staticmethod
    def setup_tables():
        """ساخت جداول کیف پول"""
        try:
            # جدول کیف پول کاربران
            execute_db("""
                CREATE TABLE IF NOT EXISTS user_wallets (
                    user_id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    total_deposited INTEGER DEFAULT 0,
                    total_spent INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # ایندکس برای کارایی بهتر
            execute_db("""
                CREATE INDEX IF NOT EXISTS idx_wallet_balance 
                ON user_wallets(balance)
            """)
            
            # جدول تراکنش‌ها
            execute_db("""
                CREATE TABLE IF NOT EXISTS wallet_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    direction TEXT NOT NULL CHECK(direction IN ('credit', 'debit')),
                    method TEXT,
                    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'cancelled')),
                    reference TEXT,
                    description TEXT,
                    admin_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # ایندکس‌های تراکنش
            execute_db("""
                CREATE INDEX IF NOT EXISTS idx_tx_user 
                ON wallet_transactions(user_id, created_at DESC)
            """)
            execute_db("""
                CREATE INDEX IF NOT EXISTS idx_tx_status 
                ON wallet_transactions(status, created_at DESC)
            """)
            
            logger.info("✅ Wallet system tables created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating wallet tables: {e}")
            return False
    
    @staticmethod
    def get_or_create_wallet(user_id: int) -> Dict:
        """دریافت یا ساخت کیف پول کاربر"""
        wallet = query_db(
            "SELECT * FROM user_wallets WHERE user_id = ?",
            (user_id,),
            one=True
        )
        
        if not wallet:
            execute_db(
                "INSERT INTO user_wallets (user_id, balance) VALUES (?, 0)",
                (user_id,)
            )
            wallet = {
                'user_id': user_id,
                'balance': 0,
                'total_deposited': 0,
                'total_spent': 0
            }
        
        return wallet
    
    @staticmethod
    def get_balance(user_id: int) -> int:
        """دریافت موجودی کاربر"""
        wallet = WalletSystem.get_or_create_wallet(user_id)
        return int(wallet.get('balance', 0))
    
    @staticmethod
    def add_credit(
        user_id: int,
        amount: int,
        method: str = 'manual',
        reference: str = '',
        description: str = '',
        admin_id: Optional[int] = None,
        auto_approve: bool = False
    ) -> Tuple[bool, int, str]:
        """
        اضافه کردن اعتبار به کیف پول
        
        Returns:
            (success, transaction_id, message)
        """
        try:
            if amount <= 0:
                return False, 0, "مبلغ باید مثبت باشد"
            
            # ساخت تراکنش
            status = 'approved' if auto_approve else 'pending'
            
            tx_id = execute_db("""
                INSERT INTO wallet_transactions 
                (user_id, amount, direction, method, status, reference, description, admin_id, created_at)
                VALUES (?, ?, 'credit', ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                amount,
                method,
                status,
                reference,
                description,
                admin_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            # اگر تایید خودکار باشد، موجودی را بروز کن
            if auto_approve:
                WalletSystem._update_balance(user_id, amount, 'credit')
                
                execute_db("""
                    UPDATE wallet_transactions 
                    SET processed_at = ?
                    WHERE id = ?
                """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tx_id))
            
            logger.info(f"Credit transaction created: user={user_id}, amount={amount}, tx={tx_id}, status={status}")
            return True, tx_id, "تراکنش با موفقیت ثبت شد"
            
        except Exception as e:
            logger.error(f"Error adding credit: {e}")
            return False, 0, f"خطا در ثبت تراکنش: {str(e)}"
    
    @staticmethod
    def deduct_balance(
        user_id: int,
        amount: int,
        description: str = '',
        reference: str = ''
    ) -> Tuple[bool, str]:
        """
        کسر از موجودی کیف پول
        
        Returns:
            (success, message)
        """
        try:
            if amount <= 0:
                return False, "مبلغ باید مثبت باشد"
            
            # بررسی موجودی
            current_balance = WalletSystem.get_balance(user_id)
            if current_balance < amount:
                return False, f"موجودی کافی نیست (موجودی: {current_balance:,} تومان)"
            
            # کسر از موجودی
            WalletSystem._update_balance(user_id, amount, 'debit')
            
            # ثبت تراکنش
            execute_db("""
                INSERT INTO wallet_transactions 
                (user_id, amount, direction, method, status, reference, description, created_at, processed_at)
                VALUES (?, ?, 'debit', 'purchase', 'approved', ?, ?, ?, ?)
            """, (
                user_id,
                amount,
                reference,
                description,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            logger.info(f"Balance deducted: user={user_id}, amount={amount}")
            return True, "موجودی با موفقیت کسر شد"
            
        except Exception as e:
            logger.error(f"Error deducting balance: {e}")
            return False, f"خطا در کسر موجودی: {str(e)}"
    
    @staticmethod
    def _update_balance(user_id: int, amount: int, direction: str):
        """بروزرسانی موجودی داخلی"""
        if direction == 'credit':
            execute_db("""
                UPDATE user_wallets 
                SET balance = balance + ?,
                    total_deposited = total_deposited + ?,
                    updated_at = ?
                WHERE user_id = ?
            """, (amount, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
        else:  # debit
            execute_db("""
                UPDATE user_wallets 
                SET balance = balance - ?,
                    total_spent = total_spent + ?,
                    updated_at = ?
                WHERE user_id = ?
            """, (amount, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
    
    @staticmethod
    def approve_transaction(tx_id: int, admin_id: int) -> Tuple[bool, str]:
        """تایید تراکنش توسط ادمین"""
        try:
            # دریافت اطلاعات تراکنش
            tx = query_db(
                "SELECT * FROM wallet_transactions WHERE id = ?",
                (tx_id,),
                one=True
            )
            
            if not tx:
                return False, "تراکنش یافت نشد"
            
            if tx['status'] != 'pending':
                return False, f"تراکنش قبلاً {tx['status']} شده است"
            
            if tx['direction'] != 'credit':
                return False, "فقط تراکنش‌های واریز قابل تایید هستند"
            
            # بروزرسانی موجودی
            WalletSystem._update_balance(tx['user_id'], tx['amount'], 'credit')
            
            # بروزرسانی وضعیت تراکنش
            execute_db("""
                UPDATE wallet_transactions 
                SET status = 'approved',
                    admin_id = ?,
                    processed_at = ?
                WHERE id = ?
            """, (admin_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tx_id))
            
            logger.info(f"Transaction approved: tx={tx_id}, admin={admin_id}")
            return True, "تراکنش تایید شد"
            
        except Exception as e:
            logger.error(f"Error approving transaction: {e}")
            return False, f"خطا در تایید: {str(e)}"
    
    @staticmethod
    def reject_transaction(tx_id: int, admin_id: int) -> Tuple[bool, str]:
        """رد تراکنش توسط ادمین"""
        try:
            tx = query_db(
                "SELECT * FROM wallet_transactions WHERE id = ?",
                (tx_id,),
                one=True
            )
            
            if not tx:
                return False, "تراکنش یافت نشد"
            
            if tx['status'] != 'pending':
                return False, f"تراکنش قبلاً {tx['status']} شده است"
            
            # بروزرسانی وضعیت
            execute_db("""
                UPDATE wallet_transactions 
                SET status = 'rejected',
                    admin_id = ?,
                    processed_at = ?
                WHERE id = ?
            """, (admin_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tx_id))
            
            logger.info(f"Transaction rejected: tx={tx_id}, admin={admin_id}")
            return True, "تراکنش رد شد"
            
        except Exception as e:
            logger.error(f"Error rejecting transaction: {e}")
            return False, f"خطا در رد تراکنش: {str(e)}"
    
    @staticmethod
    def get_transactions(
        user_id: int,
        limit: int = 20,
        status: Optional[str] = None
    ) -> List[Dict]:
        """دریافت تاریخچه تراکنش‌های کاربر"""
        if status:
            return query_db("""
                SELECT * FROM wallet_transactions 
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, status, limit)) or []
        else:
            return query_db("""
                SELECT * FROM wallet_transactions 
                WHERE user_id = ?
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, limit)) or []
    
    @staticmethod
    def get_pending_transactions() -> List[Dict]:
        """دریافت تراکنش‌های در انتظار تایید"""
        return query_db("""
            SELECT wt.*, u.first_name, u.username
            FROM wallet_transactions wt
            LEFT JOIN users u ON wt.user_id = u.user_id
            WHERE wt.status = 'pending'
            ORDER BY wt.created_at ASC
        """) or []
    
    @staticmethod
    def get_wallet_stats(user_id: int) -> Dict:
        """دریافت آمار کیف پول کاربر"""
        wallet = WalletSystem.get_or_create_wallet(user_id)
        
        # تعداد تراکنش‌ها در 30 روز اخیر
        recent_tx = query_db("""
            SELECT COUNT(*) as count
            FROM wallet_transactions
            WHERE user_id = ?
            AND created_at >= datetime('now', '-30 days')
            AND status = 'approved'
        """, (user_id,), one=True)
        
        # آخرین شارژ
        last_deposit = query_db("""
            SELECT amount, created_at
            FROM wallet_transactions
            WHERE user_id = ?
            AND direction = 'credit'
            AND status = 'approved'
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,), one=True)
        
        return {
            'balance': wallet['balance'],
            'total_deposited': wallet.get('total_deposited', 0),
            'total_spent': wallet.get('total_spent', 0),
            'recent_tx_count': recent_tx['count'] if recent_tx else 0,
            'last_deposit_amount': last_deposit['amount'] if last_deposit else 0,
            'last_deposit_date': last_deposit['created_at'] if last_deposit else None
        }
    
    @staticmethod
    def format_transaction_text(tx: Dict, show_user: bool = False) -> str:
        """فرمت کردن متن تراکنش"""
        direction_emoji = "➕" if tx['direction'] == 'credit' else "➖"
        direction_text = "واریز" if tx['direction'] == 'credit' else "برداشت"
        
        status_emoji = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌',
            'cancelled': '🚫'
        }.get(tx['status'], '❓')
        
        status_text = {
            'pending': 'در انتظار تایید',
            'approved': 'تایید شده',
            'rejected': 'رد شده',
            'cancelled': 'لغو شده'
        }.get(tx['status'], 'نامشخص')
        
        text = f"{direction_emoji} <b>{direction_text}</b> - {status_emoji} {status_text}\n"
        text += f"💰 مبلغ: {tx['amount']:,} تومان\n"
        
        if show_user:
            user_name = tx.get('first_name', 'کاربر') + (f" (@{tx['username']})" if tx.get('username') else '')
            text += f"👤 کاربر: {user_name}\n"
            text += f"🆔 ID: <code>{tx['user_id']}</code>\n"
        
        if tx.get('method'):
            method_text = {
                'card': 'کارت به کارت',
                'gateway': 'درگاه پرداخت',
                'crypto': 'ارز دیجیتال',
                'manual': 'دستی',
                'purchase': 'خرید'
            }.get(tx['method'], tx['method'])
            text += f"💳 روش: {method_text}\n"
        
        if tx.get('reference'):
            text += f"🔑 مرجع: <code>{tx['reference']}</code>\n"
        
        if tx.get('description'):
            text += f"📝 توضیحات: {tx['description']}\n"
        
        text += f"📅 تاریخ: {tx['created_at'][:16]}\n"
        
        if tx.get('processed_at'):
            text += f"✅ پردازش: {tx['processed_at'][:16]}\n"
        
        return text

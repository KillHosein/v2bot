"""
Advanced Error Handling System
Provides graceful error recovery, user-friendly messages, and admin notifications
"""
import asyncio
import traceback
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from telegram import Update, Bot
from telegram.ext import ContextTypes
from telegram.error import NetworkError, BadRequest, TimedOut, ChatMigrated, RetryAfter, Forbidden
from .db import execute_db, query_db
from .config import ADMIN_ID, logger
from .advanced_logging import get_advanced_logger


class ErrorHandler:
    """Centralized error handling system"""
    
    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot
        self.logger = get_advanced_logger()
        self.error_counts: Dict[str, int] = {}
        self.last_notification: Dict[str, datetime] = {}
        self._create_tables()
    
    def _create_tables(self):
        """Create error tracking tables"""
        try:
            execute_db("""
                CREATE TABLE IF NOT EXISTS error_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT,
                    user_id INTEGER,
                    handler_name TEXT,
                    stack_trace TEXT,
                    resolved BOOLEAN DEFAULT 0,
                    resolution_notes TEXT
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL UNIQUE,
                    count INTEGER DEFAULT 1,
                    last_seen TEXT,
                    auto_response TEXT,
                    priority TEXT DEFAULT 'low'
                )
            """)
        except Exception as e:
            logger.error(f"Failed to create error tables: {e}")
    
    async def handle_error(self, 
                          update: Update, 
                          context: ContextTypes.DEFAULT_TYPE,
                          error: Exception,
                          handler_name: str = "") -> bool:
        """
        Main error handler
        Returns: True if error was handled gracefully, False if it needs to bubble up
        """
        user_id = update.effective_user.id if update and update.effective_user else None
        
        # Log the error
        self.logger.log_error(
            error,
            handler_name=handler_name,
            user_id=user_id,
            context={'update': str(update) if update else None}
        )
        
        # Track error in database
        self._track_error(error, user_id, handler_name)
        
        # Determine error type and response
        error_type = type(error).__name__
        
        # Handle specific error types
        if isinstance(error, NetworkError):
            return await self._handle_network_error(update, context, error)
        elif isinstance(error, BadRequest):
            return await self._handle_bad_request(update, context, error)
        elif isinstance(error, TimedOut):
            return await self._handle_timeout(update, context, error)
        elif isinstance(error, ChatMigrated):
            return await self._handle_chat_migrated(update, context, error)
        elif isinstance(error, RetryAfter):
            return await self._handle_retry_after(update, context, error)
        elif isinstance(error, Forbidden):
            return await self._handle_forbidden(update, context, error)
        else:
            return await self._handle_generic_error(update, context, error)
    
    def _track_error(self, error: Exception, user_id: Optional[int], handler_name: str):
        """Track error in database"""
        try:
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = traceback.format_exc()
            
            # Store in database
            execute_db("""
                INSERT INTO error_tracking 
                (timestamp, error_type, error_message, user_id, handler_name, stack_trace)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                error_type,
                error_message,
                user_id,
                handler_name,
                stack_trace
            ))
            
            # Update error patterns
            pattern = f"{error_type}:{error_message[:50]}"
            existing = query_db(
                "SELECT id, count FROM error_patterns WHERE pattern = ?",
                (pattern,),
                one=True
            )
            
            if existing:
                execute_db(
                    "UPDATE error_patterns SET count = count + 1, last_seen = ? WHERE id = ?",
                    (datetime.now().isoformat(), existing['id'])
                )
            else:
                execute_db(
                    "INSERT INTO error_patterns (pattern, last_seen) VALUES (?, ?)",
                    (pattern, datetime.now().isoformat())
                )
            
            # Increment error count for rate limiting
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
            
            # Notify admin if critical
            if self._is_critical_error(error):
                asyncio.create_task(self._notify_admin(error, user_id, handler_name))
                
        except Exception as e:
            logger.error(f"Failed to track error: {e}")
    
    def _is_critical_error(self, error: Exception) -> bool:
        """Determine if error is critical and needs immediate attention"""
        critical_types = [
            'DatabaseError',
            'PanelConnectionError',
            'PaymentProcessingError',
            'SecurityException'
        ]
        
        error_type = type(error).__name__
        return error_type in critical_types or self.error_counts.get(error_type, 0) > 10
    
    async def _notify_admin(self, error: Exception, user_id: Optional[int], handler_name: str):
        """Send notification to admin about critical error"""
        if not self.bot or not ADMIN_ID:
            return
        
        error_type = type(error).__name__
        
        # Rate limit notifications (max 1 per hour per error type)
        last_notif = self.last_notification.get(error_type)
        if last_notif and (datetime.now() - last_notif).total_seconds() < 3600:
            return
        
        self.last_notification[error_type] = datetime.now()
        
        message = (
            "🚨 <b>Critical Error Alert</b>\n\n"
            f"Type: <code>{error_type}</code>\n"
            f"Handler: <code>{handler_name}</code>\n"
            f"User: <code>{user_id}</code>\n"
            f"Message: {str(error)[:200]}\n"
            f"Count: {self.error_counts.get(error_type, 1)}\n\n"
            "Check /admin_errors for details"
        )
        
        try:
            await self.bot.send_message(
                chat_id=ADMIN_ID,
                text=message,
                parse_mode='HTML'
            )
        except Exception:
            pass
    
    async def _handle_network_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: NetworkError) -> bool:
        """Handle network-related errors"""
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⚠️ مشکلی در اتصال شبکه پیش آمده. لطفا دوباره تلاش کنید.",
                )
            except:
                pass
        return True
    
    async def _handle_bad_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: BadRequest) -> bool:
        """Handle bad request errors"""
        error_msg = str(error).lower()
        
        if "message is not modified" in error_msg:
            # Ignore this common non-critical error
            return True
        elif "message to delete not found" in error_msg:
            return True
        elif "message can't be deleted" in error_msg:
            return True
        else:
            if update and update.effective_chat:
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="⚠️ درخواست نامعتبر. لطفا دوباره تلاش کنید.",
                    )
                except:
                    pass
        return True
    
    async def _handle_timeout(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: TimedOut) -> bool:
        """Handle timeout errors"""
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⏱ زمان درخواست به پایان رسید. لطفا دوباره تلاش کنید.",
                )
            except:
                pass
        return True
    
    async def _handle_chat_migrated(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: ChatMigrated) -> bool:
        """Handle chat migration errors"""
        # Update chat ID in database
        try:
            new_chat_id = error.new_chat_id
            old_chat_id = update.effective_chat.id if update and update.effective_chat else None
            
            if old_chat_id and new_chat_id:
                execute_db(
                    "UPDATE users SET chat_id = ? WHERE chat_id = ?",
                    (new_chat_id, old_chat_id)
                )
        except:
            pass
        return True
    
    async def _handle_retry_after(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: RetryAfter) -> bool:
        """Handle rate limiting errors"""
        retry_after = error.retry_after
        
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⏳ محدودیت زمانی! لطفا {retry_after} ثانیه صبر کنید.",
                )
            except:
                pass
        
        # Sleep for the required duration
        await asyncio.sleep(retry_after)
        return True
    
    async def _handle_forbidden(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: Forbidden) -> bool:
        """Handle forbidden errors (bot blocked by user)"""
        if update and update.effective_user:
            # Mark user as blocked in database
            try:
                execute_db(
                    "UPDATE users SET bot_blocked = 1, blocked_at = ? WHERE user_id = ?",
                    (datetime.now().isoformat(), update.effective_user.id)
                )
            except:
                pass
        return True
    
    async def _handle_generic_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception) -> bool:
        """Handle any other error"""
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "❌ متاسفانه خطایی رخ داد.\n"
                        "لطفا دوباره تلاش کنید و در صورت تکرار با پشتیبانی تماس بگیرید.\n"
                        f"کد خطا: <code>{type(error).__name__}</code>"
                    ),
                    parse_mode='HTML'
                )
            except:
                pass
        return False
    
    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the last N hours"""
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        stats = {
            'total_errors': 0,
            'unique_errors': 0,
            'affected_users': set(),
            'top_errors': [],
            'critical_errors': 0
        }
        
        try:
            # Get all errors in timeframe
            errors = query_db(
                "SELECT * FROM error_tracking WHERE timestamp > ?",
                (since,)
            )
            
            stats['total_errors'] = len(errors)
            
            # Count unique error types
            error_types = {}
            for error in errors:
                error_type = error['error_type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
                if error['user_id']:
                    stats['affected_users'].add(error['user_id'])
            
            stats['unique_errors'] = len(error_types)
            stats['affected_users'] = len(stats['affected_users'])
            
            # Get top errors
            stats['top_errors'] = sorted(
                error_types.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Count critical errors
            patterns = query_db(
                "SELECT COUNT(*) as count FROM error_patterns WHERE priority = 'high' AND last_seen > ?",
                (since,),
                one=True
            )
            stats['critical_errors'] = patterns['count'] if patterns else 0
            
        except Exception as e:
            logger.error(f"Failed to get error stats: {e}")
        
        return stats


# Global error handler instance
_error_handler = None

def get_error_handler(bot: Optional[Bot] = None) -> ErrorHandler:
    """Get or create global error handler"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler(bot)
    elif bot and not _error_handler.bot:
        _error_handler.bot = bot
    return _error_handler


# Error handling decorator
def handle_errors(handler_name: Optional[str] = None):
    """Decorator to automatically handle errors in handlers"""
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            name = handler_name or func.__name__
            error_handler = get_error_handler(context.bot)
            
            try:
                return await func(update, context)
            except Exception as e:
                handled = await error_handler.handle_error(update, context, e, name)
                if not handled:
                    raise
        
        return wrapper
    return decorator

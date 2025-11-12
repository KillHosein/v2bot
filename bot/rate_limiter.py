"""
Advanced Rate Limiting and Anti-Spam System
Protects bot from abuse and ensures fair usage
"""
import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from .db import execute_db, query_db
from .advanced_logging import get_advanced_logger


class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self):
        self.logger = get_advanced_logger()
        self.user_requests: Dict[int, deque] = defaultdict(lambda: deque(maxlen=100))
        self.user_warnings: Dict[int, int] = defaultdict(int)
        self.banned_users: set = set()
        self.global_requests = deque(maxlen=1000)
        self._create_tables()
        self._load_banned_users()
    
    def _create_tables(self):
        """Create rate limiting tables"""
        try:
            execute_db("""
                CREATE TABLE IF NOT EXISTS rate_limit_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    violation_type TEXT,
                    endpoint TEXT,
                    severity TEXT,
                    action_taken TEXT
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS spam_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL,
                    pattern_type TEXT,
                    confidence REAL,
                    last_seen TEXT,
                    occurrences INTEGER DEFAULT 1
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS rate_limit_config (
                    endpoint TEXT PRIMARY KEY,
                    requests_per_minute INTEGER DEFAULT 30,
                    burst_limit INTEGER DEFAULT 5,
                    cooldown_seconds INTEGER DEFAULT 60,
                    auto_ban_threshold INTEGER DEFAULT 3
                )
            """)
            
            # Default configurations
            self._init_default_limits()
            
        except Exception as e:
            self.logger.log_error(e, "rate_limiter_init")
    
    def _init_default_limits(self):
        """Initialize default rate limits for different endpoints"""
        defaults = [
            ('start', 10, 3, 30, 5),
            ('admin', 60, 10, 10, 10),
            ('purchase', 5, 2, 120, 3),
            ('wallet', 20, 5, 60, 5),
            ('support', 10, 3, 60, 5),
            ('default', 30, 5, 30, 5)
        ]
        
        for endpoint, rpm, burst, cooldown, ban_threshold in defaults:
            execute_db("""
                INSERT OR IGNORE INTO rate_limit_config 
                (endpoint, requests_per_minute, burst_limit, cooldown_seconds, auto_ban_threshold)
                VALUES (?, ?, ?, ?, ?)
            """, (endpoint, rpm, burst, cooldown, ban_threshold))
    
    def _load_banned_users(self):
        """Load banned users from database"""
        try:
            banned = query_db("SELECT user_id FROM users WHERE banned = 1")
            self.banned_users = {user['user_id'] for user in banned} if banned else set()
        except:
            pass
    
    def check_rate_limit(self, 
                         user_id: int, 
                         endpoint: str = 'default',
                         check_global: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Check if user has exceeded rate limit
        Returns: (is_allowed, error_message)
        """
        # Check if user is banned
        if user_id in self.banned_users:
            return False, "شما به دلیل نقض قوانین مسدود شده‌اید."
        
        # Get rate limit config
        config = query_db(
            "SELECT * FROM rate_limit_config WHERE endpoint = ?",
            (endpoint,),
            one=True
        )
        
        if not config:
            config = query_db(
                "SELECT * FROM rate_limit_config WHERE endpoint = 'default'",
                one=True
            )
        
        now = time.time()
        
        # Check user-specific rate limit
        user_reqs = self.user_requests[user_id]
        
        # Clean old requests (older than 1 minute)
        while user_reqs and user_reqs[0] < now - 60:
            user_reqs.popleft()
        
        # Check burst limit (requests in last 5 seconds)
        recent_reqs = [r for r in user_reqs if r > now - 5]
        if len(recent_reqs) >= config['burst_limit']:
            self._record_violation(user_id, endpoint, 'burst_limit')
            return False, f"تعداد درخواست‌های شما بیش از حد است. لطفاً {config['cooldown_seconds']} ثانیه صبر کنید."
        
        # Check rate limit (requests per minute)
        if len(user_reqs) >= config['requests_per_minute']:
            self._record_violation(user_id, endpoint, 'rate_limit')
            return False, "محدودیت تعداد درخواست. لطفاً کمی صبر کنید."
        
        # Check global rate limit
        if check_global:
            self.global_requests.append(now)
            while self.global_requests and self.global_requests[0] < now - 60:
                self.global_requests.popleft()
            
            if len(self.global_requests) > 500:  # Global limit
                return False, "سرور شلوغ است. لطفاً بعداً تلاش کنید."
        
        # Record the request
        user_reqs.append(now)
        
        return True, None
    
    def _record_violation(self, user_id: int, endpoint: str, violation_type: str):
        """Record a rate limit violation"""
        self.user_warnings[user_id] += 1
        
        severity = 'low'
        action = 'warning'
        
        if self.user_warnings[user_id] >= 10:
            severity = 'critical'
            action = 'ban'
            self.ban_user(user_id, "Excessive rate limit violations")
        elif self.user_warnings[user_id] >= 5:
            severity = 'high'
            action = 'throttle'
        elif self.user_warnings[user_id] >= 3:
            severity = 'medium'
            action = 'cooldown'
        
        execute_db("""
            INSERT INTO rate_limit_violations 
            (user_id, timestamp, violation_type, endpoint, severity, action_taken)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            datetime.now().isoformat(),
            violation_type,
            endpoint,
            severity,
            action
        ))
        
        self.logger.logger.warning(
            f"Rate limit violation: user={user_id}, endpoint={endpoint}, "
            f"type={violation_type}, warnings={self.user_warnings[user_id]}"
        )
    
    def ban_user(self, user_id: int, reason: str):
        """Ban a user"""
        self.banned_users.add(user_id)
        execute_db(
            "UPDATE users SET banned = 1, ban_reason = ?, banned_at = ? WHERE user_id = ?",
            (reason, datetime.now().isoformat(), user_id)
        )
        self.logger.log_audit("user_banned", user_id, {'reason': reason})
    
    def unban_user(self, user_id: int):
        """Unban a user"""
        self.banned_users.discard(user_id)
        self.user_warnings[user_id] = 0
        execute_db(
            "UPDATE users SET banned = 0, ban_reason = NULL, banned_at = NULL WHERE user_id = ?",
            (user_id,)
        )
        self.logger.log_audit("user_unbanned", user_id)
    
    def check_spam_pattern(self, message: str, user_id: int) -> bool:
        """Check if message matches spam patterns"""
        spam_indicators = [
            # URLs and links
            (r'(https?://|www\.)\S+', 0.3),
            (r't\.me/\S+', 0.4),
            (r'@[a-zA-Z0-9_]{5,}', 0.2),
            
            # Repetitive patterns
            (r'(.)\1{5,}', 0.5),  # Same character repeated
            (r'(\b\w+\b)(\s+\1){3,}', 0.6),  # Same word repeated
            
            # Known spam keywords
            (r'(viagra|casino|lottery|winner|prize)', 0.8),
            (r'(click here|sign up now|limited offer)', 0.6),
            
            # Excessive caps
            (r'[A-Z]{10,}', 0.4),
            
            # Suspicious patterns
            (r'\d{10,}', 0.3),  # Long numbers (phone numbers, etc)
        ]
        
        import re
        total_score = 0.0
        
        for pattern, weight in spam_indicators:
            if re.search(pattern, message, re.IGNORECASE):
                total_score += weight
        
        # Check message frequency
        recent_messages = query_db(
            "SELECT COUNT(*) as count FROM messages WHERE user_id = ? AND timestamp > ?",
            (user_id, (datetime.now() - timedelta(minutes=1)).isoformat()),
            one=True
        )
        
        if recent_messages and recent_messages['count'] > 5:
            total_score += 0.5
        
        # If spam score is high, record it
        if total_score >= 1.0:
            execute_db("""
                INSERT INTO spam_patterns (pattern, pattern_type, confidence, last_seen)
                VALUES (?, 'message', ?, ?)
            """, (message[:100], total_score, datetime.now().isoformat()))
            
            self._record_violation(user_id, 'message', 'spam_detected')
            return True
        
        return False
    
    def get_user_status(self, user_id: int) -> Dict:
        """Get rate limit status for a user"""
        return {
            'banned': user_id in self.banned_users,
            'warnings': self.user_warnings.get(user_id, 0),
            'recent_requests': len(self.user_requests.get(user_id, [])),
            'can_request': user_id not in self.banned_users
        }
    
    def reset_user_limits(self, user_id: int):
        """Reset limits for a user"""
        self.user_requests[user_id].clear()
        self.user_warnings[user_id] = 0
    
    def get_statistics(self) -> Dict:
        """Get rate limiting statistics"""
        stats = {
            'total_banned': len(self.banned_users),
            'users_with_warnings': len([u for u, w in self.user_warnings.items() if w > 0]),
            'total_warnings': sum(self.user_warnings.values()),
            'global_rpm': len(self.global_requests),
            'recent_violations': []
        }
        
        # Get recent violations
        violations = query_db("""
            SELECT * FROM rate_limit_violations 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        """, ((datetime.now() - timedelta(hours=1)).isoformat(),))
        
        if violations:
            stats['recent_violations'] = violations
        
        return stats


# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# Decorator for rate limiting
def rate_limit(endpoint: str = 'default', check_spam: bool = False):
    """Decorator to apply rate limiting to handlers"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not update.effective_user:
                return await func(update, context)
            
            user_id = update.effective_user.id
            limiter = get_rate_limiter()
            
            # Check rate limit
            allowed, error_msg = limiter.check_rate_limit(user_id, endpoint)
            if not allowed:
                if update.callback_query:
                    await update.callback_query.answer(error_msg, show_alert=True)
                else:
                    await update.message.reply_text(f"⚠️ {error_msg}")
                return
            
            # Check spam if enabled
            if check_spam and update.message and update.message.text:
                if limiter.check_spam_pattern(update.message.text, user_id):
                    await update.message.reply_text(
                        "⛔ پیام شما حاوی محتوای نامناسب تشخیص داده شد."
                    )
                    return
            
            # Execute handler
            return await func(update, context)
        
        return wrapper
    return decorator

"""
سیستم Override خودکار برای جایگزینی متن‌های hard-coded با متن‌های دیتابیس
این ماژول به‌صورت خودکار تمام متن‌های ارسالی را چک می‌کند و اگر در دیتابیس یافت شد، جایگزین می‌کند
"""

from .db import query_db
from .config import logger
import re

# Cache برای متن‌ها (برای سرعت)
_message_cache = {}
_cache_ttl = 60  # 60 ثانیه
_last_cache_update = 0

def _update_cache():
    """به‌روزرسانی cache متن‌ها"""
    global _message_cache, _last_cache_update
    import time
    
    current_time = time.time()
    if current_time - _last_cache_update < _cache_ttl:
        return
    
    try:
        messages = query_db("SELECT message_name, text FROM messages WHERE message_name NOT LIKE 'admin_%'")
        _message_cache = {msg['text']: msg['message_name'] for msg in messages if msg.get('text')}
        _last_cache_update = current_time
        logger.debug(f"Message cache updated with {len(_message_cache)} messages")
    except Exception as e:
        logger.error(f"Failed to update message cache: {e}")

def find_and_replace_message(text: str) -> str:
    """
    پیدا کردن و جایگزینی متن با نسخه دیتابیس
    
    Args:
        text: متن اصلی hard-coded
        
    Returns:
        متن از دیتابیس یا همان متن اصلی
    """
    if not text or len(text) < 5:
        return text
    
    _update_cache()
    
    # اگر متن دقیقاً در دیتابیس است
    if text in _message_cache:
        message_name = _message_cache[text]
        try:
            from .db import get_message_text
            new_text = get_message_text(message_name, text)
            if new_text != text:
                logger.debug(f"Replaced text for {message_name}")
            return new_text
        except Exception as e:
            logger.error(f"Error getting message {message_name}: {e}")
            return text
    
    # جستجوی fuzzy برای متن‌های مشابه
    text_normalized = re.sub(r'\s+', ' ', text.strip())
    for cached_text, message_name in _message_cache.items():
        cached_normalized = re.sub(r'\s+', ' ', cached_text.strip())
        
        # اگر 80% شباهت داشت
        if _similarity(text_normalized, cached_normalized) > 0.8:
            try:
                from .db import get_message_text
                new_text = get_message_text(message_name, text)
                if new_text != text:
                    logger.debug(f"Fuzzy replaced text for {message_name}")
                return new_text
            except Exception as e:
                logger.error(f"Error getting message {message_name}: {e}")
                return text
    
    return text

def _similarity(s1: str, s2: str) -> float:
    """محاسبه شباهت دو متن"""
    if s1 == s2:
        return 1.0
    
    # اگر یکی در دیگری موجود است
    if s1 in s2 or s2 in s1:
        return 0.9
    
    # Levenshtein distance ساده
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0
    
    # فقط برای متن‌های کوتاه
    if len1 > 200 or len2 > 200:
        return 0.0
    
    distance = _levenshtein(s1, s2)
    max_len = max(len1, len2)
    return 1 - (distance / max_len)

def _levenshtein(s1: str, s2: str) -> int:
    """Levenshtein distance"""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

# Monkey patch برای reply_text و edit_text
original_reply_text = None
original_edit_text = None

def patch_telegram_methods():
    """Patch کردن متدهای Telegram برای override خودکار"""
    try:
        from telegram import Message
        
        global original_reply_text, original_edit_text
        
        # ذخیره متدهای اصلی
        original_reply_text = Message.reply_text
        original_edit_text = Message.edit_text
        
        # متد جدید reply_text
        async def new_reply_text(self, text, *args, **kwargs):
            # Override کردن text
            new_text = find_and_replace_message(text)
            return await original_reply_text(self, new_text, *args, **kwargs)
        
        # متد جدید edit_text
        async def new_edit_text(self, text, *args, **kwargs):
            # Override کردن text
            new_text = find_and_replace_message(text)
            return await original_edit_text(self, new_text, *args, **kwargs)
        
        # جایگزینی متدها
        Message.reply_text = new_reply_text
        Message.edit_text = new_edit_text
        
        logger.info("✅ Message override system activated!")
        return True
    except Exception as e:
        logger.error(f"Failed to patch Telegram methods: {e}")
        return False

def unpatch_telegram_methods():
    """برداشتن patch"""
    try:
        from telegram import Message
        
        if original_reply_text:
            Message.reply_text = original_reply_text
        if original_edit_text:
            Message.edit_text = original_edit_text
        
        logger.info("Message override system deactivated")
        return True
    except Exception as e:
        logger.error(f"Failed to unpatch Telegram methods: {e}")
        return False

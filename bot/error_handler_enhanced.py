# -*- coding: utf-8 -*-
"""
Enhanced Error Handler for Production Issues
مدیریت خطاهای پیشرفته برای مشکلات تولید
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest, NetworkError, RetryAfter, TimedOut

logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler for the bot"""
    
    # Log the error
    logger.error(f"Exception while handling update {update}: {context.error}")
    
    try:
        # Handle different types of errors
        if isinstance(context.error, BadRequest):
            await handle_bad_request_error(update, context)
        elif isinstance(context.error, NetworkError):
            await handle_network_error(update, context) 
        elif isinstance(context.error, RetryAfter):
            await handle_retry_after_error(update, context)
        elif isinstance(context.error, TimedOut):
            await handle_timeout_error(update, context)
        else:
            await handle_generic_error(update, context)
            
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

async def handle_bad_request_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle BadRequest errors"""
    error_msg = str(context.error)
    
    if "Message is not modified" in error_msg:
        # این خطا مهم نیست - پیام قبلاً همینطور بوده
        logger.info("Message not modified - ignoring")
        return
        
    elif "Message to edit not found" in error_msg:
        # پیام حذف شده یا منقضی شده
        logger.warning("Message to edit not found")
        return
        
    elif "Bad Request: message can't be edited" in error_msg:
        # پیام قابل ویرایش نیست
        logger.warning("Message can't be edited")
        return
        
    elif "no such column" in error_msg:
        # مشکل دیتابیس
        logger.error(f"Database schema issue: {error_msg}")
        await send_db_error_notification(update, context)
        
    else:
        logger.error(f"Unhandled BadRequest: {error_msg}")

async def handle_network_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle network-related errors"""
    logger.warning("Network error occurred - will retry")

async def handle_retry_after_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle rate limiting errors"""
    retry_after = context.error.retry_after
    logger.warning(f"Rate limited - retry after {retry_after} seconds")

async def handle_timeout_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle timeout errors"""
    logger.warning("Request timed out")

async def handle_generic_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle other errors"""
    logger.error(f"Unhandled error: {context.error}")

async def send_db_error_notification(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send notification about database errors to admin"""
    try:
        if isinstance(update, Update) and update.effective_user:
            # اگر امکان پاسخ دادن وجود دارد
            if update.effective_message:
                await update.effective_message.reply_text(
                    "⚠️ خطای موقت در سیستم. لطفاً چند لحظه دیگر تلاش کنید."
                )
    except Exception:
        # اگر نتوانست پاسخ دهد، مهم نیست
        pass

def setup_error_handling():
    """Setup enhanced error handling"""
    # تنظیم logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # تنظیم logger برای telegram
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logger.info("Enhanced error handling setup complete")
    
    return error_handler

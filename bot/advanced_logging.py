"""
Advanced Logging System with Rotation and Monitoring
Provides structured logging, log rotation, and performance tracking
"""
import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
import traceback
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Base log data
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if available
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'handler_name'):
            log_data['handler_name'] = record.handler_name
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
        if hasattr(record, 'error_type'):
            log_data['error_type'] = record.error_type
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False)


class AdvancedLogger:
    """Advanced logging manager with multiple outputs and rotation"""
    
    def __init__(self, name: str = 'wingsbot', log_dir: str = 'logs'):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        self.logger.handlers = []
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up various log handlers"""
        
        # 1. Console Handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 2. Rotating File Handler for all logs
        all_logs_path = self.log_dir / 'all.log'
        file_handler = logging.handlers.RotatingFileHandler(
            filename=all_logs_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(file_handler)
        
        # 3. Error File Handler (ERROR and above)
        error_logs_path = self.log_dir / 'errors.log'
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_logs_path,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(error_handler)
        
        # 4. Performance File Handler
        perf_logs_path = self.log_dir / 'performance.log'
        perf_handler = logging.handlers.RotatingFileHandler(
            filename=perf_logs_path,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.addFilter(lambda record: hasattr(record, 'duration'))
        perf_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(perf_handler)
    
    def log_performance(self, 
                       handler_name: str, 
                       duration: float, 
                       user_id: Optional[int] = None,
                       metadata: Optional[Dict] = None):
        """Log performance metrics"""
        extra = {
            'handler_name': handler_name,
            'duration': duration,
            'user_id': user_id
        }
        if metadata:
            extra.update(metadata)
        
        if duration > 5.0:
            self.logger.warning(f"Slow handler: {handler_name} took {duration:.2f}s", extra=extra)
        else:
            self.logger.info(f"Handler {handler_name} completed in {duration:.2f}s", extra=extra)
    
    def log_error(self,
                 error: Exception,
                 handler_name: str = "",
                 user_id: Optional[int] = None,
                 context: Optional[Dict] = None):
        """Log error with context"""
        extra = {
            'handler_name': handler_name,
            'user_id': user_id,
            'error_type': type(error).__name__
        }
        if context:
            extra.update(context)
        
        self.logger.error(
            f"Error in {handler_name}: {str(error)}",
            exc_info=True,
            extra=extra
        )
    
    def log_audit(self,
                 action: str,
                 user_id: int,
                 details: Optional[Dict] = None):
        """Log audit trail for important actions"""
        extra = {
            'user_id': user_id,
            'action': action,
            'audit': True
        }
        if details:
            extra['details'] = details
        
        self.logger.info(f"AUDIT: User {user_id} performed {action}", extra=extra)
    
    def get_logger(self) -> logging.Logger:
        """Get the underlying logger"""
        return self.logger


# Singleton instance
_advanced_logger = None

def get_advanced_logger() -> AdvancedLogger:
    """Get or create the advanced logger instance"""
    global _advanced_logger
    if _advanced_logger is None:
        _advanced_logger = AdvancedLogger()
    return _advanced_logger


# Performance logging decorator
def log_performance(handler_name: Optional[str] = None):
    """Decorator to automatically log handler performance"""
    def decorator(func):
        import time
        import asyncio
        from functools import wraps
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = handler_name or func.__name__
            logger = get_advanced_logger()
            start = time.time()
            
            # Try to extract user_id
            user_id = None
            try:
                if args and hasattr(args[0], 'effective_user'):
                    user_id = args[0].effective_user.id
            except:
                pass
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                logger.log_performance(name, duration, user_id)
                return result
            except Exception as e:
                duration = time.time() - start
                logger.log_error(e, name, user_id, {'duration': duration})
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = handler_name or func.__name__
            logger = get_advanced_logger()
            start = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.log_performance(name, duration)
                return result
            except Exception as e:
                duration = time.time() - start
                logger.log_error(e, name, context={'duration': duration})
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

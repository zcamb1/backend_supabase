#!/usr/bin/env python3
"""
Logging utility cho ElevenLabs Authentication System
Centralized logging với different levels và file rotation
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class AuthLogger:
    """Authentication system logger với custom formatting"""
    
    def __init__(self, name: str = "elevenlabs_auth"):
        self.name = name
        self.logger = None
        self._log_dir = self._get_log_directory()
        
    def _get_log_directory(self) -> str:
        """Lấy thư mục log"""
        if os.name == 'nt':  # Windows
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            log_dir = os.path.join(app_data, 'ElevenLabsTool', 'logs')
        else:  # Linux/macOS
            home_dir = os.path.expanduser('~')
            log_dir = os.path.join(home_dir, '.elevenlabs_tool', 'logs')
        
        # Tạo directory nếu chưa có
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    
    def setup(self, level: str = "INFO", enable_console: bool = True, enable_file: bool = True) -> logging.Logger:
        """
        Setup logger với configuration
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_console: Enable console output
            enable_file: Enable file output với rotation
        """
        # Tạo logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)  # Console chỉ show INFO+
            self.logger.addHandler(console_handler)
        
        # File handler với rotation
        if enable_file:
            log_file = os.path.join(self._log_dir, f"{self.name}.log")
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)  # File lưu tất cả
            self.logger.addHandler(file_handler)
        
        # Error file handler (riêng cho errors)
        if enable_file:
            error_log_file = os.path.join(self._log_dir, f"{self.name}_errors.log")
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3,
                encoding='utf-8'
            )
            error_handler.setFormatter(formatter)
            error_handler.setLevel(logging.ERROR)
            self.logger.addHandler(error_handler)
        
        # Log initial info
        self.logger.info(f"Logger initialized - Level: {level}")
        if enable_file:
            self.logger.info(f"Log directory: {self._log_dir}")
        
        return self.logger

# Global logger instance
_auth_logger = None

def setup_logger(name: str = "elevenlabs_auth", 
                level: str = "INFO", 
                enable_console: bool = True, 
                enable_file: bool = True) -> logging.Logger:
    """
    Setup global authentication logger
    
    Returns:
        Configured logger instance
    """
    global _auth_logger
    
    if _auth_logger is None:
        _auth_logger = AuthLogger(name)
    
    return _auth_logger.setup(level, enable_console, enable_file)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get logger instance
    
    Args:
        name: Logger name (optional, uses default if None)
    """
    global _auth_logger
    
    if _auth_logger is None:
        setup_logger()
    
    if name:
        return logging.getLogger(name)
    else:
        return _auth_logger.logger

# Logging decorators
def log_function_call(logger: Optional[logging.Logger] = None):
    """Decorator để log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or get_logger()
            log.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                log.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                log.error(f"{func.__name__} failed with error: {e}")
                raise
        return wrapper
    return decorator

def log_performance(logger: Optional[logging.Logger] = None):
    """Decorator để log performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            log = logger or get_logger()
            
            start_time = time.time()
            log.debug(f"Starting {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                log.debug(f"{func.__name__} completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                log.error(f"{func.__name__} failed after {execution_time:.3f}s with error: {e}")
                raise
        return wrapper
    return decorator

# Security logging helpers
def log_auth_event(event_type: str, username: str = None, device_id: str = None, 
                   success: bool = True, details: str = None, logger: Optional[logging.Logger] = None):
    """
    Log authentication events với security context
    
    Args:
        event_type: Type of event (LOGIN, LOGOUT, SESSION_VERIFY, etc.)
        username: Username involved
        device_id: Device fingerprint
        success: Whether event was successful
        details: Additional details
    """
    log = logger or get_logger()
    
    level = logging.INFO if success else logging.WARNING
    message = f"AUTH_EVENT: {event_type}"
    
    if username:
        message += f" | User: {username}"
    
    if device_id:
        # Mask device ID for security (show only first 8 chars)
        masked_device = f"{device_id[:8]}..." if len(device_id) > 8 else device_id
        message += f" | Device: {masked_device}"
    
    message += f" | Success: {success}"
    
    if details:
        message += f" | Details: {details}"
    
    log.log(level, message)

def log_security_event(event_type: str, severity: str = "MEDIUM", details: str = None, 
                      logger: Optional[logging.Logger] = None):
    """
    Log security events
    
    Args:
        event_type: Type of security event
        severity: LOW, MEDIUM, HIGH, CRITICAL
        details: Event details
    """
    log = logger or get_logger()
    
    level_map = {
        "LOW": logging.INFO,
        "MEDIUM": logging.WARNING, 
        "HIGH": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    level = level_map.get(severity, logging.WARNING)
    message = f"SECURITY_EVENT: {event_type} | Severity: {severity}"
    
    if details:
        message += f" | Details: {details}"
    
    log.log(level, message)

# Context manager for operation logging
class LoggedOperation:
    """Context manager để log operations"""
    
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        self.operation_name = operation_name
        self.logger = logger or get_logger()
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.info(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info(f"Operation completed: {self.operation_name} ({duration:.3f}s)")
        else:
            self.logger.error(f"Operation failed: {self.operation_name} ({duration:.3f}s) - {exc_val}")
        
        return False  # Don't suppress exceptions

# Test function
if __name__ == "__main__":
    # Test logging system
    logger = setup_logger(level="DEBUG")
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test security logging
    log_auth_event("LOGIN", "testuser", "abc123-device-id", True, "Successful login")
    log_auth_event("LOGIN", "baduser", "xyz789-device-id", False, "Invalid credentials")
    
    log_security_event("SUSPICIOUS_ACTIVITY", "HIGH", "Multiple failed login attempts")
    
    # Test context manager
    with LoggedOperation("Database Connection"):
        import time
        time.sleep(0.1)  # Simulate work
    
    # Test decorators
    @log_function_call()
    @log_performance()
    def test_function(x, y):
        import time
        time.sleep(0.05)
        return x + y
    
    result = test_function(1, 2)
    logger.info(f"Test function result: {result}")
    
    print(f"✅ Logging test completed. Check logs in: {_auth_logger._log_dir}") 
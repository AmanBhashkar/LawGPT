import logging
import os
from logging.handlers import RotatingFileHandler
import asyncio
from functools import wraps
import re
from datetime import datetime, timezone
from pythonjsonlogger import jsonlogger

# Create logs directory if it doesn't exist
LOGS_DIR = "autogen_logs"
os.makedirs(LOGS_DIR, exist_ok=True)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that adds timestamps and uppercases log levels."""

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # Add timestamp in UTC if not present
        if not log_record.get("timestamp"):
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now

        # Ensure log level is uppercase
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname.upper()


def setup_logger(module_name: str) -> logging.Logger:
    """
    Setup a logger for a specific module with both file and console handlers
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times
    if not logger.handlers:
        from logging.handlers import RotatingFileHandler

        # File handler with rotation
        file_handler = RotatingFileHandler(
            os.path.join(LOGS_DIR, f"{module_name}.log"), maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create JSON formatter
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


def mask_sensitive_data(data: str) -> str:
    """
    Mask sensitive data in logs
    """
    if not isinstance(data, str):
        return str(data)

    patterns = {
        r'"user_id":\s*"[^"]*"': '"user_id": "***"',
        r'"email":\s*"[^"]*"': '"email": "***"',
        r'"password":\s*"[^"]*"': '"password": "***"',
        r'"token":\s*"[^"]*"': '"token": "***"',
        r'"api_key":\s*"[^"]*"': '"api_key": "***"',
        r'"connection_string":\s*"[^"]*"': '"connection_string": "***"',
    }

    masked_data = data
    for pattern, replacement in patterns.items():
        masked_data = re.sub(pattern, replacement, masked_data)

    return masked_data


def log_function_call(logger):
    """
    Decorator to log function entry, exit, and parameters.
    Supports both synchronous and asynchronous functions.
    """

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                func_name = func.__name__
                masked_args = [mask_sensitive_data(str(arg)) for arg in args]
                masked_kwargs = {k: mask_sensitive_data(str(v)) for k, v in kwargs.items()}

                logger.debug(f"Entering {func_name} - Args: {masked_args}, Kwargs: {masked_kwargs}")
                try:
                    result = await func(*args, **kwargs)
                    logger.debug(f"Exiting {func_name} - Success")
                    return result
                except Exception as e:
                    logger.error(f"Error in {func_name}: {str(e)}", exc_info=True)
                    raise

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                func_name = func.__name__
                masked_args = [mask_sensitive_data(str(arg)) for arg in args]
                masked_kwargs = {k: mask_sensitive_data(str(v)) for k, v in kwargs.items()}

                logger.debug(f"Entering {func_name} - Args: {masked_args}, Kwargs: {masked_kwargs}")
                try:
                    result = func(*args, **kwargs)
                    logger.debug(f"Exiting {func_name} - Success")
                    return result
                except Exception as e:
                    logger.error(f"Error in {func_name}: {str(e)}", exc_info=True)
                    raise

            return sync_wrapper

    return decorator

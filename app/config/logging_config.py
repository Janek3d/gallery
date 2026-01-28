"""
Logging configuration helper for structured logging.

This module provides a convenient way to get loggers configured with JSON formatting.
Use this instead of importing logging directly for better structured logging.
"""

import logging


def get_logger(name: str = None):
    """
    Get a logger instance configured with JSON formatting.
    
    Args:
        name: Logger name (typically __name__). If None, uses 'root'.
    
    Returns:
        A logging.Logger instance configured with JSON formatting.
    
    Example:
        from config.logging_config import get_logger
        
        logger = get_logger(__name__)
        logger.info("User logged in", extra={'user_id': 123, 'ip_address': '192.168.1.1'})
    """
    return logging.getLogger(name)

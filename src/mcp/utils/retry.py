"""
Single consolidated retry implementation - no duplicates
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: str = 'exponential',
    exceptions: Tuple = (Exception,)
) -> Callable:
    """
    Decorator for retrying operations with backoff
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: 'exponential', 'linear', or 'constant'
        exceptions: Tuple of exceptions to catch
    
    Usage:
        @retry(max_attempts=3, backoff='exponential')
        def flaky_operation():
            # operation that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
                    
                    logger.warning(f"{func.__name__} attempt {attempt} failed: {e}")
                    time.sleep(current_delay)
                    
                    # Calculate next delay
                    if backoff == 'exponential':
                        current_delay *= 2
                    elif backoff == 'linear':
                        current_delay += delay
                    # else constant - no change
                    
                    attempt += 1
            
            return None  # Should never reach here
        
        return wrapper
    return decorator


def retry_operation(
    operation: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: str = 'exponential'
) -> Tuple[bool, Any]:
    """
    Function-based retry for operations
    
    Args:
        operation: Callable to retry
        max_attempts: Maximum attempts
        delay: Initial delay
        backoff: Backoff strategy
    
    Returns:
        (success, result) tuple
    """
    attempt = 1
    current_delay = delay
    last_error = None
    
    while attempt <= max_attempts:
        try:
            result = operation()
            return True, result
        except Exception as e:
            last_error = e
            if attempt == max_attempts:
                logger.error(f"Operation failed after {max_attempts} attempts: {e}")
                return False, last_error
            
            logger.debug(f"Attempt {attempt} failed, retrying...")
            time.sleep(current_delay)
            
            if backoff == 'exponential':
                current_delay *= 2
            elif backoff == 'linear':
                current_delay += delay
            
            attempt += 1
    
    return False, last_error
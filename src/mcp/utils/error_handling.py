"""
Enhanced error handling for Computer Use MCP
Provides robust error handling, retry logic, and recovery mechanisms
"""

from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
from typing import Dict, Any, Optional, Callable, Type, Union, List
import logging
import time

import secrets
import traceback

from ..core.constants import CIRCUIT_BREAKER_RECOVERY_TIMEOUT

#!/usr/bin/env python3

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"          # Can be ignored
    MEDIUM = "medium"    # Should be logged
    HIGH = "high"        # Requires attention
    CRITICAL = "critical"  # System failure


class MCPError(Exception):
    """Base exception for all MCP errors"""


    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 details: Optional[Dict[str, Any]] = None, retry_after: Optional[float] = None):
        super().__init__(message)
        self.severity = severity
        self.details = details or {}
        self.retry_after = retry_after
        self.timestamp = time.time()


class ScreenshotError(MCPError):
    """Screenshot-related errors"""
    pass


class InputError(MCPError):
    """Input operation errors"""
    pass


class SafetyError(MCPError):
    """Safety validation errors"""


    def __init__(self, message: str, blocked_action: str, reason: str) -> None:
        super().__init__(message, severity=ErrorSeverity.HIGH)
        self.blocked_action = blocked_action
        self.reason = reason
        self.details = {
            'blocked_action': blocked_action,
            'reason': reason
        }


class DisplayError(MCPError):
    """Display-related errors"""
    pass


class TimeoutError(MCPError):
    """Operation timeout errors"""
    pass


class TransientError(MCPError):
    """Transient errors that can be retried"""


    def __init__(self, message: str, retry_after: float = 1.0) -> None:
        super().__init__(message, severity=ErrorSeverity.LOW, retry_after=retry_after)


class PermanentError(MCPError):
    """Permanent errors that should not be retried"""


    def __init__(self, message: str) -> None:
        super().__init__(message, severity=ErrorSeverity.HIGH)


class RetryStrategy(ABC):
    """Base retry strategy"""

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Get delay before next retry"""
        pass

    @abstractmethod
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if should retry"""
        pass


class ExponentialBackoff(RetryStrategy):
    """Exponential backoff retry strategy"""


    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0,
                 max_attempts: int = 3, jitter: bool = True):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)

        if self.jitter:
            # Add random jitter to prevent thundering herd
            delay *= (0.5 + secrets.randbelow(1000) / 1000)

        return delay

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Check if should retry"""
        if attempt >= self.max_attempts:
            return False

        # Don't retry permanent errors
        if isinstance(error, PermanentError):
            return False

        # Don't retry safety errors
        if isinstance(error, SafetyError):
            return False

        # Retry transient errors and general exceptions
        return isinstance(error, (TransientError, TimeoutError)) or \
               not isinstance(error, MCPError)


class LinearBackoff(RetryStrategy):
    """Linear backoff retry strategy"""


    def __init__(self, delay: float = 1.0, max_attempts: int = 3) -> None:
        self.delay = delay
        self.max_attempts = max_attempts

    def get_delay(self, attempt: int) -> float:
        """Fixed delay between retries"""
        return self.delay

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Check if should retry"""
        if attempt >= self.max_attempts:
            return False

        return not isinstance(error, (PermanentError, SafetyError))


def retry(strategy: Optional[RetryStrategy] = None,
          exceptions: tuple = (Exception,),
          on_retry: Optional[Callable] = None):
    """
    Decorator for automatic retry with configurable strategy

    Args:
        strategy: Retry strategy (default: ExponentialBackoff)
        exceptions: Tuple of exceptions to catch
        on_retry: Callback function called before retry
    """
    if strategy is None:
        strategy = ExponentialBackoff()

    def decorator(func) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            last_error = None

            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e

                    if not strategy.should_retry(e, attempt):
                        raise

                    delay = strategy.get_delay(attempt)

                    # Call retry callback
                    if on_retry:
                        on_retry(func.__name__, attempt, e, delay)

                    logger.warning(
                        f"Retry {attempt + 1} for {func.__name__} after {delay:.2f}s: {str(e)}"
                    )

                    time.sleep(delay)
                    attempt += 1

            # Should never reach here
            raise last_error

        return wrapper

    return decorator


class ErrorHandler:
    """Centralized error handling and recovery"""


    def __init__(self) -> None:
        self.error_counts = {}
        self.error_handlers = {}
        self.recovery_strategies = {}
        self.circuit_breakers = {}

    def register_handler(self, error_type: Type[Exception],
                        handler: Callable[[Exception], Any]):
        """Register error handler for specific error type"""
        self.error_handlers[error_type] = handler

    def register_recovery(self, operation: str,
                         strategy: Callable[[], Any]):
        """Register recovery strategy for operation"""
        self.recovery_strategies[operation] = strategy

    def handle_error(self, error: Exception, operation: str = "unknown") -> Dict[str, Any]:
        """Handle error with appropriate strategy"""
        # Track error count
        error_key = f"{operation}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Check circuit breaker
        if self._is_circuit_open(operation):
            logger.error(f"Circuit breaker open for {operation}")
            return {
                'success': False,
                'error': 'Service temporarily unavailable',
                'circuit_breaker': True
            }

        # Find appropriate handler
        for error_type, handler in self.error_handlers.items():
            if isinstance(error, error_type):
                try:
                    return handler(error)
                except Exception as handler_error:
                    logger.error(f"Error handler failed: {handler_error}")

        # Default handling based on error type
        if isinstance(error, SafetyError):
            return {
                'success': False,
                'error': str(error),
                'severity': error.severity.value,
                'blocked_action': error.blocked_action,
                'reason': error.reason
            }

        if isinstance(error, TransientError):
            return {
                'success': False,
                'error': str(error),
                'severity': error.severity.value,
                'retry_after': error.retry_after,
                'transient': True
            }

        if isinstance(error, MCPError):
            return {
                'success': False,
                'error': str(error),
                'severity': error.severity.value,
                'details': error.details
            }

        # Generic error
        return {
            'success': False,
            'error': str(error),
            'error_type': type(error).__name__,
            'traceback': traceback.format_exc()
        }

    def _is_circuit_open(self, operation: str) -> bool:
        """Check if circuit breaker is open for operation"""
        if operation not in self.circuit_breakers:
            return False

        breaker = self.circuit_breakers[operation]
        return breaker.is_open()

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            'error_counts': self.error_counts,
            'top_errors': sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""


    def __init__(self, failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise MCPError("Circuit breaker is open", severity=ErrorSeverity.HIGH)

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if should attempt reset"""
        return (self.last_failure_time and
                time.time() - self.last_failure_time >= self.recovery_timeout)

    def _on_success(self) -> None:
        """Handle successful call"""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self) -> None:
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")

    def is_open(self) -> bool:
        """Check if circuit is open"""
        return self.state == "open" and not self._should_attempt_reset()

    def reset(self) -> None:
        """Manually reset circuit breaker"""
        self.failure_count = 0
        self.state = "closed"
        self.last_failure_time = None


class ErrorContext:
    """Context manager for error handling"""


    def __init__(self, operation: str, handler: Optional[ErrorHandler] = None,
                 fallback: Optional[Callable] = None):
        self.operation = operation
        self.handler = handler or ErrorHandler()
        self.fallback = fallback
        self.start_time = None

    def __enter__(self) -> 'ErrorContext':
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_val is None:
            return False

        # Log error with context
        duration = time.time() - self.start_time
        logger.error(
            f"Error in {self.operation} after {duration:.2f}s: {exc_val}",
            exc_info=True
        )

        # Handle error
        result = self.handler.handle_error(exc_val, self.operation)

        # Try fallback if available
        if self.fallback:
            try:
                self.fallback(exc_val, result)
            except Exception as fallback_error:
                logger.error(f"Fallback failed: {fallback_error}")

        # Suppress exception if it was handled
        return isinstance(exc_val, MCPError) and exc_val.severity != ErrorSeverity.CRITICAL


# Example usage
if __name__ == "__main__":
    # Example with retry decorator
    @retry(strategy=ExponentialBackoff(base_delay=0.5, max_attempts=3))
    def flaky_operation() -> str:
        if secrets.randbelow(1000) / 1000 < 0.7:
            raise TransientError("Network timeout")
        return "Success!"

    # Example with circuit breaker
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT)

    def protected_operation() -> Any:
        return breaker.call(flaky_operation)

    # Example with error context
    handler = ErrorHandler()

    with ErrorContext("screenshot_capture", handler):
        # This error will be handled gracefully
        raise ScreenshotError("Display not available")
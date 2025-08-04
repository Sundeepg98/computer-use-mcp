#!/usr/bin/env python3
"""
Enhanced Computer Use implementation
Combines all improvements: async, caching, error handling, middleware
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor

from .factory_refactored import create_computer_use, create_computer_use_for_testing
from .async_support import ComputerUseAsync, create_async_computer_use
from .caching import CachedScreenshotProvider, SmartCache
from .error_handling import (
    ErrorHandler, ErrorContext, retry, ExponentialBackoff,
    ScreenshotError, InputError, SafetyError, CircuitBreaker
)
from .middleware import (
    ComputerUseWithMiddleware, MiddlewareStack,
    LoggingMiddleware, RateLimitMiddleware, CachingMiddleware,
    ValidationMiddleware, MetricsMiddleware, RetryMiddleware
)

logger = logging.getLogger(__name__)


class EnhancedComputerUse:
    """
    Enhanced Computer Use with all improvements integrated
    
    Features:
    - Async/await support
    - Intelligent caching
    - Robust error handling
    - Middleware pipeline
    - Circuit breakers
    - Metrics collection
    """
    
    def __init__(
        self,
        enable_async: bool = True,
        enable_caching: bool = True,
        enable_middleware: bool = True,
        cache_ttl: float = 0.1,
        rate_limit: Optional[int] = 60,
        for_testing: bool = False
    ):
        """
        Initialize enhanced computer use
        
        Args:
            enable_async: Enable async operations
            enable_caching: Enable screenshot caching
            enable_middleware: Enable middleware pipeline
            cache_ttl: Cache time-to-live in seconds
            rate_limit: Max requests per minute (None = unlimited)
            for_testing: Use test implementations
        """
        # Create base instance
        if for_testing:
            self.base = create_computer_use_for_testing()
        else:
            self.base = create_computer_use()
        
        # Add caching if enabled
        if enable_caching:
            self.base.screenshot = CachedScreenshotProvider(
                self.base.screenshot,
                ttl=cache_ttl
            )
            self.smart_cache = SmartCache(initial_ttl=cache_ttl)
        
        # Create async version if enabled
        if enable_async:
            self.executor = ThreadPoolExecutor(max_workers=4)
            self.async_instance = ComputerUseAsync.from_sync(self.base, self.executor)
        else:
            self.async_instance = None
            self.executor = None
        
        # Setup middleware if enabled
        if enable_middleware:
            self.middleware_instance = ComputerUseWithMiddleware(self.base)
            self._setup_default_middleware(rate_limit)
        else:
            self.middleware_instance = None
        
        # Setup error handling
        self.error_handler = ErrorHandler()
        self._setup_error_handlers()
        
        # Setup circuit breakers
        self.circuit_breakers = {
            'screenshot': CircuitBreaker(failure_threshold=5, recovery_timeout=30),
            'input': CircuitBreaker(failure_threshold=10, recovery_timeout=60)
        }
        
        # Metrics
        self.metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def _setup_default_middleware(self, rate_limit: Optional[int]):
        """Setup default middleware stack"""
        # Logging
        self.middleware_instance.add_middleware(
            LoggingMiddleware(log_level="INFO", include_params=False)
        )
        
        # Rate limiting
        if rate_limit:
            self.middleware_instance.add_middleware(
                RateLimitMiddleware(max_requests=rate_limit, window_seconds=60)
            )
        
        # Caching for read operations
        self.middleware_instance.add_middleware(
            CachingMiddleware(ttl=60.0, cache_actions=['get_display_info'])
        )
        
        # Validation
        validators = {
            'click': self._validate_click_params,
            'type': self._validate_type_params
        }
        self.middleware_instance.add_middleware(
            ValidationMiddleware(validators=validators)
        )
        
        # Metrics
        self.metrics_middleware = MetricsMiddleware()
        self.middleware_instance.add_middleware(self.metrics_middleware)
        
        # Retry for transient failures
        self.middleware_instance.add_middleware(
            RetryMiddleware(max_retries=3, retry_delay=1.0)
        )
    
    def _setup_error_handlers(self):
        """Setup error recovery strategies"""
        # Screenshot error handler
        def handle_screenshot_error(error: ScreenshotError):
            logger.warning(f"Screenshot error: {error}, trying alternative method")
            # Could try alternative screenshot method here
            return {'success': False, 'error': str(error), 'fallback_attempted': True}
        
        self.error_handler.register_handler(ScreenshotError, handle_screenshot_error)
        
        # Safety error handler
        def handle_safety_error(error: SafetyError):
            logger.error(f"Safety violation: {error.blocked_action} - {error.reason}")
            return {
                'success': False,
                'error': str(error),
                'safety_violation': True,
                'details': error.details
            }
        
        self.error_handler.register_handler(SafetyError, handle_safety_error)
    
    def _validate_click_params(self, params: Dict[str, Any]):
        """Validate click parameters"""
        if 'x' not in params or 'y' not in params:
            raise ValueError("x and y coordinates required")
        
        x, y = params['x'], params['y']
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("Coordinates must be integers")
        
        if x < 0 or y < 0 or x > 10000 or y > 10000:
            raise ValueError("Coordinates out of reasonable bounds")
    
    def _validate_type_params(self, params: Dict[str, Any]):
        """Validate type parameters"""
        if 'text' not in params:
            raise ValueError("text parameter required")
        
        if not isinstance(params['text'], str):
            raise ValueError("text must be a string")
        
        if len(params['text']) > 10000:
            raise ValueError("text too long")
    
    # Synchronous API with enhancements
    @retry(strategy=ExponentialBackoff(max_attempts=3))
    def take_screenshot(self, analyze: Optional[str] = None) -> Dict[str, Any]:
        """Take screenshot with retry and caching"""
        self.metrics['total_operations'] += 1
        
        # Use circuit breaker
        breaker = self.circuit_breakers['screenshot']
        
        def _take_screenshot():
            with ErrorContext('screenshot', self.error_handler):
                if self.middleware_instance:
                    response = self.middleware_instance.execute(
                        'screenshot',
                        {'analyze': analyze} if analyze else {}
                    )
                    return response.data if response.success else {'success': False, 'error': response.error}
                else:
                    return self.base.take_screenshot(analyze)
        
        try:
            result = breaker.call(_take_screenshot)
            self.metrics['successful_operations'] += 1
            return result
        except Exception as e:
            self.metrics['failed_operations'] += 1
            return self.error_handler.handle_error(e, 'screenshot')
    
    def click(self, x: int, y: int, button: str = 'left') -> Dict[str, Any]:
        """Click with validation and error handling"""
        self.metrics['total_operations'] += 1
        
        # Use circuit breaker
        breaker = self.circuit_breakers['input']
        
        def _click():
            with ErrorContext('click', self.error_handler):
                if self.middleware_instance:
                    response = self.middleware_instance.execute(
                        'click',
                        {'x': x, 'y': y, 'button': button}
                    )
                    return response.data if response.success else {'success': False, 'error': response.error}
                else:
                    return self.base.click(x, y, button)
        
        try:
            result = breaker.call(_click)
            self.metrics['successful_operations'] += 1
            return result
        except Exception as e:
            self.metrics['failed_operations'] += 1
            return self.error_handler.handle_error(e, 'click')
    
    def type_text(self, text: str) -> Dict[str, Any]:
        """Type text with safety validation"""
        self.metrics['total_operations'] += 1
        
        breaker = self.circuit_breakers['input']
        
        def _type():
            with ErrorContext('type', self.error_handler):
                if self.middleware_instance:
                    response = self.middleware_instance.execute(
                        'type',
                        {'text': text}
                    )
                    return response.data if response.success else {'success': False, 'error': response.error}
                else:
                    return self.base.type_text(text)
        
        try:
            result = breaker.call(_type)
            self.metrics['successful_operations'] += 1
            return result
        except Exception as e:
            self.metrics['failed_operations'] += 1
            return self.error_handler.handle_error(e, 'type')
    
    # Async API
    async def take_screenshot_async(self, analyze: Optional[str] = None) -> Dict[str, Any]:
        """Async screenshot with all enhancements"""
        if not self.async_instance:
            # Fall back to sync in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.take_screenshot, analyze)
        
        self.metrics['total_operations'] += 1
        
        try:
            result = await self.async_instance.take_screenshot(analyze)
            self.metrics['successful_operations'] += 1
            return result
        except Exception as e:
            self.metrics['failed_operations'] += 1
            return self.error_handler.handle_error(e, 'screenshot_async')
    
    async def batch_operations_async(self, operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple operations concurrently"""
        if not self.async_instance:
            raise RuntimeError("Async not enabled")
        
        return await self.async_instance.batch_operations(operations)
    
    # Utility methods
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance and usage metrics"""
        metrics = self.metrics.copy()
        
        # Add middleware metrics if available
        if self.middleware_instance and hasattr(self.metrics_middleware, 'get_metrics'):
            metrics['middleware'] = self.metrics_middleware.get_metrics()
        
        # Add cache metrics
        if hasattr(self, 'smart_cache'):
            metrics['cache'] = self.smart_cache.get_insights()
        
        # Add error stats
        metrics['errors'] = self.error_handler.get_error_stats()
        
        # Add circuit breaker status
        metrics['circuit_breakers'] = {
            name: {
                'state': breaker.state,
                'failure_count': breaker.failure_count,
                'is_open': breaker.is_open()
            }
            for name, breaker in self.circuit_breakers.items()
        }
        
        return metrics
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers"""
        for breaker in self.circuit_breakers.values():
            breaker.reset()
    
    def clear_cache(self):
        """Clear all caches"""
        if hasattr(self.base.screenshot, 'invalidate_cache'):
            self.base.screenshot.invalidate_cache()
        
        if hasattr(self, 'smart_cache'):
            self.smart_cache.cache.clear()
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on exit"""
        if self.executor:
            self.executor.shutdown(wait=True)
        
        # Log final metrics
        logger.info(f"Session metrics: {self.get_metrics()}")
        
        return False


# Factory function
def create_enhanced_computer_use(**kwargs) -> EnhancedComputerUse:
    """
    Create enhanced computer use instance
    
    Keyword Args:
        enable_async: Enable async operations (default: True)
        enable_caching: Enable caching (default: True)
        enable_middleware: Enable middleware (default: True)
        cache_ttl: Cache TTL in seconds (default: 0.1)
        rate_limit: Rate limit per minute (default: 60)
        for_testing: Use test implementations (default: False)
    
    Returns:
        EnhancedComputerUse instance with all improvements
    """
    return EnhancedComputerUse(**kwargs)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        """Demonstrate enhanced features"""
        # Create enhanced instance
        with create_enhanced_computer_use(
            enable_async=True,
            enable_caching=True,
            enable_middleware=True,
            cache_ttl=1.0,
            rate_limit=100
        ) as computer:
            
            # Sync operations with all enhancements
            print("Taking screenshot...")
            result = computer.take_screenshot()
            print(f"Screenshot: {result['success']}")
            
            # Async operations
            print("\nAsync screenshot...")
            async_result = await computer.take_screenshot_async()
            print(f"Async screenshot: {async_result['success']}")
            
            # Batch operations
            print("\nBatch operations...")
            operations = [
                {'type': 'screenshot'},
                {'type': 'click', 'x': 100, 'y': 200},
                {'type': 'type', 'text': 'Hello, Enhanced World!'}
            ]
            results = await computer.batch_operations_async(operations)
            for i, res in enumerate(results):
                print(f"  Operation {i}: {res.get('success', False)}")
            
            # Show metrics
            print("\nMetrics:")
            metrics = computer.get_metrics()
            print(f"  Total operations: {metrics['total_operations']}")
            print(f"  Success rate: {metrics['successful_operations'] / max(metrics['total_operations'], 1):.2%}")
            print(f"  Circuit breakers: {metrics['circuit_breakers']}")
    
    # Run demo
    asyncio.run(demo())
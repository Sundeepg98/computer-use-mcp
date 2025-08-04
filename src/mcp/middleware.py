#!/usr/bin/env python3
"""
Middleware system for Computer Use MCP
Provides plugin architecture for extending functionality
"""

import time
import logging
from typing import Dict, Any, List, Optional, Callable, Protocol
from dataclasses import dataclass
from functools import wraps
import json

logger = logging.getLogger(__name__)


@dataclass
class Request:
    """Request object passed through middleware"""
    action: str
    params: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class Response:
    """Response object returned through middleware"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    duration: Optional[float] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Middleware(Protocol):
    """Protocol for middleware implementations"""
    
    def process_request(self, request: Request, next_handler: Callable) -> Response:
        """
        Process request and call next handler
        
        Args:
            request: The request to process
            next_handler: Function to call next middleware or final handler
            
        Returns:
            Response object
        """
        pass


class LoggingMiddleware:
    """Logs all requests and responses"""
    
    def __init__(self, log_level: str = "INFO", include_params: bool = True):
        self.log_level = getattr(logging, log_level.upper())
        self.include_params = include_params
    
    def process_request(self, request: Request, next_handler: Callable) -> Response:
        """Log request, execute, log response"""
        # Log request
        log_data = {
            'action': request.action,
            'timestamp': request.timestamp
        }
        if self.include_params:
            log_data['params'] = request.params
        
        logger.log(self.log_level, f"Request: {json.dumps(log_data)}")
        
        # Execute
        start_time = time.time()
        response = next_handler(request)
        duration = time.time() - start_time
        
        # Log response
        response_data = {
            'action': request.action,
            'success': response.success,
            'duration': duration
        }
        if response.error:
            response_data['error'] = response.error
        
        logger.log(self.log_level, f"Response: {json.dumps(response_data)}")
        
        # Add duration to response
        response.duration = duration
        return response


class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    def __init__(self, max_requests: int = 60, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    def process_request(self, request: Request, next_handler: Callable) -> Response:
        """Check rate limit before processing"""
        current_time = time.time()
        
        # Clean old requests
        self.requests = [
            t for t in self.requests 
            if current_time - t < self.window_seconds
        ]
        
        # Check limit
        if len(self.requests) >= self.max_requests:
            return Response(
                success=False,
                data=None,
                error=f"Rate limit exceeded: {self.max_requests} requests per {self.window_seconds}s",
                metadata={'rate_limit_reset': current_time + self.window_seconds}
            )
        
        # Track request
        self.requests.append(current_time)
        
        # Process
        return next_handler(request)


class CachingMiddleware:
    """Caching middleware for read operations"""
    
    def __init__(self, ttl: float = 60.0, cache_actions: List[str] = None):
        self.ttl = ttl
        self.cache_actions = cache_actions or ['screenshot', 'get_display_info']
        self.cache = {}
    
    def _get_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        return f"{request.action}:{json.dumps(request.params, sort_keys=True)}"
    
    def process_request(self, request: Request, next_handler: Callable) -> Response:
        """Cache responses for configured actions"""
        # Only cache specific actions
        if request.action not in self.cache_actions:
            return next_handler(request)
        
        # Check cache
        cache_key = self._get_cache_key(request)
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry['timestamp'] < self.ttl:
                response = entry['response']
                response.metadata['cache_hit'] = True
                return response
        
        # Execute and cache
        response = next_handler(request)
        
        if response.success:
            self.cache[cache_key] = {
                'response': response,
                'timestamp': time.time()
            }
        
        response.metadata['cache_hit'] = False
        return response


class ValidationMiddleware:
    """Validates requests before processing"""
    
    def __init__(self, validators: Dict[str, Callable] = None):
        self.validators = validators or {}
    
    def process_request(self, request: Request, next_handler: Callable) -> Response:
        """Validate request parameters"""
        # Check if validator exists for action
        if request.action in self.validators:
            validator = self.validators[request.action]
            try:
                validator(request.params)
            except Exception as e:
                return Response(
                    success=False,
                    data=None,
                    error=f"Validation failed: {str(e)}"
                )
        
        return next_handler(request)


class MetricsMiddleware:
    """Collects metrics about operations"""
    
    def __init__(self):
        self.metrics = {
            'requests': {},
            'errors': {},
            'durations': {}
        }
    
    def process_request(self, request: Request, next_handler: Callable) -> Response:
        """Collect metrics"""
        action = request.action
        
        # Track request count
        self.metrics['requests'][action] = self.metrics['requests'].get(action, 0) + 1
        
        # Execute and measure
        start_time = time.time()
        response = next_handler(request)
        duration = time.time() - start_time
        
        # Track duration
        if action not in self.metrics['durations']:
            self.metrics['durations'][action] = []
        self.metrics['durations'][action].append(duration)
        
        # Track errors
        if not response.success:
            self.metrics['errors'][action] = self.metrics['errors'].get(action, 0) + 1
        
        # Add metrics to response
        response.metadata['metrics'] = {
            'duration': duration,
            'request_count': self.metrics['requests'][action]
        }
        
        return response
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        # Calculate averages
        avg_durations = {}
        for action, durations in self.metrics['durations'].items():
            if durations:
                avg_durations[action] = sum(durations) / len(durations)
        
        return {
            'total_requests': sum(self.metrics['requests'].values()),
            'total_errors': sum(self.metrics['errors'].values()),
            'requests_by_action': self.metrics['requests'],
            'errors_by_action': self.metrics['errors'],
            'average_duration_by_action': avg_durations
        }


class RetryMiddleware:
    """Retry failed operations"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0,
                 retry_actions: List[str] = None):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_actions = retry_actions or ['screenshot']
    
    def process_request(self, request: Request, next_handler: Callable) -> Response:
        """Retry on failure for configured actions"""
        if request.action not in self.retry_actions:
            return next_handler(request)
        
        attempt = 0
        last_error = None
        
        while attempt <= self.max_retries:
            response = next_handler(request)
            
            if response.success:
                if attempt > 0:
                    response.metadata['retry_attempts'] = attempt
                return response
            
            last_error = response.error
            attempt += 1
            
            if attempt <= self.max_retries:
                logger.warning(f"Retrying {request.action} (attempt {attempt}/{self.max_retries})")
                time.sleep(self.retry_delay)
        
        # All retries failed
        response.metadata['retry_attempts'] = self.max_retries
        return response


class AuthMiddleware:
    """Authentication/authorization middleware"""
    
    def __init__(self, auth_token: Optional[str] = None, 
                 permissions: Dict[str, List[str]] = None):
        self.auth_token = auth_token
        self.permissions = permissions or {}
    
    def process_request(self, request: Request, next_handler: Callable) -> Response:
        """Check authentication and authorization"""
        # Check auth token if configured
        if self.auth_token:
            provided_token = request.metadata.get('auth_token')
            if provided_token != self.auth_token:
                return Response(
                    success=False,
                    data=None,
                    error="Unauthorized: Invalid auth token"
                )
        
        # Check permissions
        user = request.metadata.get('user', 'anonymous')
        if user in self.permissions:
            allowed_actions = self.permissions[user]
            if request.action not in allowed_actions:
                return Response(
                    success=False,
                    data=None,
                    error=f"Forbidden: User {user} cannot perform {request.action}"
                )
        
        return next_handler(request)


class MiddlewareStack:
    """Manages middleware execution order"""
    
    def __init__(self):
        self.middleware: List[Middleware] = []
    
    def add(self, middleware: Middleware):
        """Add middleware to stack"""
        self.middleware.append(middleware)
    
    def remove(self, middleware: Middleware):
        """Remove middleware from stack"""
        self.middleware.remove(middleware)
    
    def execute(self, request: Request, handler: Callable) -> Response:
        """Execute request through middleware stack"""
        def build_chain(middleware_list: List[Middleware], final_handler: Callable) -> Callable:
            """Build the middleware chain"""
            if not middleware_list:
                return lambda req: final_handler(req)
            
            def chain(req: Request) -> Response:
                current = middleware_list[0]
                remaining = middleware_list[1:]
                next_handler = build_chain(remaining, final_handler)
                return current.process_request(req, next_handler)
            
            return chain
        
        # Build and execute chain
        chain = build_chain(self.middleware, handler)
        return chain(request)


class ComputerUseWithMiddleware:
    """Computer use implementation with middleware support"""
    
    def __init__(self, computer_use):
        self.computer_use = computer_use
        self.middleware_stack = MiddlewareStack()
    
    def add_middleware(self, middleware: Middleware):
        """Add middleware to processing pipeline"""
        self.middleware_stack.add(middleware)
    
    def _execute_action(self, request: Request) -> Response:
        """Execute the actual action"""
        try:
            # Map action to method
            action_map = {
                'screenshot': self.computer_use.take_screenshot,
                'click': lambda: self.computer_use.click(**request.params),
                'type': lambda: self.computer_use.type_text(**request.params),
                'key': lambda: self.computer_use.key_press(**request.params),
                'scroll': lambda: self.computer_use.scroll(**request.params),
                'drag': lambda: self.computer_use.drag(**request.params),
            }
            
            if request.action not in action_map:
                return Response(
                    success=False,
                    data=None,
                    error=f"Unknown action: {request.action}"
                )
            
            # Execute action
            result = action_map[request.action]()
            
            return Response(
                success=result.get('success', True),
                data=result,
                error=result.get('error')
            )
            
        except Exception as e:
            return Response(
                success=False,
                data=None,
                error=str(e)
            )
    
    def execute(self, action: str, params: Dict[str, Any] = None, 
                metadata: Dict[str, Any] = None) -> Response:
        """Execute action through middleware pipeline"""
        request = Request(
            action=action,
            params=params or {},
            metadata=metadata or {}
        )
        
        return self.middleware_stack.execute(request, self._execute_action)


# Example middleware
class AuditMiddleware:
    """Audit trail middleware"""
    
    def __init__(self, audit_file: str = "audit.log"):
        self.audit_file = audit_file
    
    def process_request(self, request: Request, next_handler: Callable) -> Response:
        """Log audit trail"""
        response = next_handler(request)
        
        audit_entry = {
            'timestamp': request.timestamp,
            'action': request.action,
            'params': request.params,
            'user': request.metadata.get('user', 'system'),
            'success': response.success,
            'error': response.error,
            'duration': response.duration
        }
        
        # Append to audit file
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')
        
        return response


# Example usage
if __name__ == "__main__":
    from .factory_refactored import create_computer_use
    
    # Create computer use with middleware
    computer = ComputerUseWithMiddleware(create_computer_use())
    
    # Add middleware
    computer.add_middleware(LoggingMiddleware())
    computer.add_middleware(RateLimitMiddleware(max_requests=10, window_seconds=60))
    computer.add_middleware(CachingMiddleware(ttl=5.0))
    computer.add_middleware(MetricsMiddleware())
    computer.add_middleware(RetryMiddleware())
    
    # Execute actions
    response = computer.execute('screenshot')
    print(f"Screenshot result: {response.success}")
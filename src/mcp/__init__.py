"""
Computer Use MCP - Model Context Protocol Server for Computer Control
Provides safe and intelligent computer automation tools for Claude and other MCP clients
Developed with Test-Driven Development achieving 100% test coverage
"""

__version__ = "1.0.0"

# Import refactored components  
from .computer_use_refactored import ComputerUseRefactored
from .computer_use_core import ComputerUseCore  # Backward compatibility wrapper
from .factory_refactored import create_computer_use, create_computer_use_for_testing
from .safety_checks import SafetyChecker
from .visual_analyzer import VisualAnalyzer

# Import original components
try:
    from .visual_mode import VisualMode
    from .claude_integration import ClaudeComputerUse
    from .error_handler import ComputerUseErrorHandler
    from .config import ComputerUseConfig
except ImportError:
    # Some components might not be available
    VisualMode = None
    ClaudeComputerUse = None
    ComputerUseErrorHandler = None
    ComputerUseConfig = None

# Import enhanced functionality
try:
    from .enhanced_computer_use import EnhancedComputerUse, create_enhanced_computer_use
    from .async_support import (
        ComputerUseAsync, create_async_computer_use, 
        create_async_computer_use_for_testing
    )
    from .middleware import (
        ComputerUseWithMiddleware, Middleware,
        LoggingMiddleware, RateLimitMiddleware,
        CachingMiddleware, MetricsMiddleware
    )
    from .error_handling import (
        MCPError, ScreenshotError, InputError, SafetyError,
        ErrorHandler, retry, ExponentialBackoff, CircuitBreaker
    )
    from .caching import CachedScreenshotProvider, SmartCache
except ImportError:
    # Enhanced features not available
    pass

# Convenience aliases for cleaner imports - use refactored as primary
ComputerUse = ComputerUseRefactored  # Primary export is the refactored version
ComputerUseCompat = ComputerUseCore  # Backward compatibility wrapper
create = create_computer_use
create_for_testing = create_computer_use_for_testing
create_enhanced = create_enhanced_computer_use

# Re-export submodules with cleaner names
from . import middleware
from . import error_handling as errors
from . import caching as cache

__all__ = [
    # Core functionality - refactored version is primary
    'ComputerUse',  # Primary - ComputerUseRefactored
    'ComputerUseRefactored',  # Explicit refactored version
    'ComputerUseCore',  # Backward compatibility
    'ComputerUseCompat',  # Alias for backward compatibility
    'create_computer_use',
    'create',  # Alias
    'create_computer_use_for_testing',
    'create_for_testing',  # Alias
    
    # Enhanced functionality
    'EnhancedComputerUse',
    'create_enhanced_computer_use',
    'create_enhanced',  # Alias
    
    # Async support
    'ComputerUseAsync',
    'create_async_computer_use',
    'create_async_computer_use_for_testing',
    
    # Middleware
    'ComputerUseWithMiddleware',
    'Middleware',
    'LoggingMiddleware',
    'RateLimitMiddleware',
    'CachingMiddleware',
    'MetricsMiddleware',
    
    # Error handling
    'MCPError',
    'ScreenshotError',
    'InputError',
    'SafetyError',
    'ErrorHandler',
    'retry',
    'ExponentialBackoff',
    'CircuitBreaker',
    
    # Caching
    'CachedScreenshotProvider',
    'SmartCache',
    
    # Original exports
    'SafetyChecker',
    'VisualAnalyzer',
    'VisualMode',
    'ClaudeComputerUse',
    'ComputerUseErrorHandler',
    'ComputerUseConfig',
    
    # Submodules
    'middleware',
    'errors',
    'cache',
]

# Provide helpful error message for old imports
def _old_import_error():
    raise ImportError(
        "\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Import path has changed for cleaner imports!\n"
        "\n"
        "OLD WAY:  from mcp import ComputerUseCore\n"
        "NEW WAY:  from mcp import ComputerUse\n"
        "\n"
        "Please update your imports to use 'mcp' instead.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )

# Catch attempts to use old import path
import sys
if 'computer_use_mcp' in sys.modules:
    sys.modules['computer_use_mcp'].__getattr__ = lambda x: _old_import_error()

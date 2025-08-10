"""
Input module for computer-use-mcp lite
Provides essential input functionality
"""

from typing import Optional, Any
import logging

from .windows import WindowsInput, WSL2Input
from .x11 import X11Input
from ..platforms import detect_platform

logger = logging.getLogger(__name__)


class InputFactory:
    """Factory for creating appropriate input implementation"""
    
    @staticmethod
    def create() -> Any:
        """Create appropriate input handler for current platform"""
        platform_info = detect_platform()
        
        logger.info(f"Creating input handler for {platform_info['platform']} "
                   f"({platform_info['environment']})")
        
        if platform_info['platform'] == 'windows':
            return WindowsInput()
        elif platform_info['environment'] == 'wsl2':
            return X11Input()  # WSL2 uses X11
        elif platform_info['platform'] == 'linux':
            return X11Input()
        else:
            # Fallback to mock
            from ..core.test_mocks import MockInputProvider
            logger.warning("No input provider available, using mock")
            return MockInputProvider()


# Public API
__all__ = ['InputFactory', 'WindowsInput', 'X11Input']

# Aliases for compatibility
WindowsInputProvider = WindowsInput
X11InputProvider = X11Input
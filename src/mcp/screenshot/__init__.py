"""
Screenshot module for computer-use-mcp lite
Provides essential screenshot functionality
"""

from typing import Optional, Dict, Any
import logging

from .windows import WindowsScreenshot, WSL2Screenshot
from .x11 import X11Screenshot
from ..platforms import detect_platform

logger = logging.getLogger(__name__)


class ScreenshotFactory:
    """Factory for creating appropriate screenshot implementation"""
    
    @staticmethod
    def create(force: Optional[str] = None) -> Any:
        """
        Create appropriate screenshot implementation
        
        Args:
            force: Force specific implementation
            
        Returns:
            Screenshot provider instance
        """
        if force:
            if force == 'windows':
                return WindowsScreenshot()
            elif force == 'x11':
                return X11Screenshot()
            elif force == 'wsl2':
                return WSL2Screenshot()
            else:
                raise ValueError(f"Unknown implementation: {force}")
        
        # Auto-detect
        platform_info = detect_platform()
        
        if platform_info['platform'] == 'windows':
            return WindowsScreenshot()
        elif platform_info['environment'] == 'wsl2':
            return X11Screenshot()  # WSL2 uses X11
        elif platform_info['platform'] == 'linux':
            return X11Screenshot()
        else:
            # Fallback to mock
            from ..core.test_mocks import MockScreenshotProvider
            logger.warning("No screenshot provider available, using mock")
            return MockScreenshotProvider()


# Public API
__all__ = ['ScreenshotFactory', 'WindowsScreenshot', 'X11Screenshot', 'WSL2Screenshot']

# Aliases for compatibility
WindowsScreenshotProvider = WindowsScreenshot
X11ScreenshotProvider = X11Screenshot
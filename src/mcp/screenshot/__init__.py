"""
Screenshot module for computer-use-mcp
Provides cross-platform screenshot functionality
"""

from typing import Optional, Union, Dict, Any
import logging
import threading

# from .macos import MacOSScreenshot  # Not implemented yet
from .server_core import ServerCoreScreenshot
from .vcxsrv import VcXsrvScreenshot
from .windows import WindowsScreenshot
from .windows import WSL2Screenshot
from .windows_rdp import RDPScreenshot
from .x11 import X11Screenshot
from ..platforms.platform_utils import get_platform_info, get_recommended_screenshot_method


logger = logging.getLogger(__name__)

# Lazy imports to avoid loading unnecessary modules
_screenshot_instance: Optional['ScreenshotBase'] = None
_screenshot_instance_lock = threading.Lock()


class ScreenshotFactory:
    """Factory for creating appropriate screenshot implementation"""

    @staticmethod
    def create(force: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> 'ScreenshotBase':
        """
        Create appropriate screenshot implementation

        Args:
            force: Force specific implementation ('windows', 'x11', 'wsl2', etc.)
            config: Configuration options

        Returns:
            Screenshot implementation instance
        """

        if force:
            return ScreenshotFactory._create_forced(force, config)

        # Auto-detect best method
        platform_info = get_platform_info()
        method = get_recommended_screenshot_method()

        logger.info(f"Auto-detected platform: {platform_info['platform']} "
                   f"({platform_info['environment']}), using method: {method}")

        if method == 'windows_native':
            return WindowsScreenshot(config)
        elif method == 'windows_rdp_capture':
            return RDPScreenshot(config)
        elif method == 'not_available':
            return ServerCoreScreenshot(config)
        elif method == 'vcxsrv_x11':
            return VcXsrvScreenshot(config)
        elif method == 'wsl2_powershell':
            return WSL2Screenshot(config)
        elif method == 'x11':
            return X11Screenshot(config)
        elif method == 'macos_screencapture':
            raise NotImplementedError("MacOS screenshot not implemented yet")
        else:
            # Fallback
            return ScreenshotFactory._create_fallback(config)

    @staticmethod
    def _create_forced(implementation: str, config: Optional[Dict[str, Any]] = None) -> 'ScreenshotBase':
        """Create forced implementation"""
        if implementation == 'windows':
            return WindowsScreenshot(config)
        elif implementation == 'windows_rdp':
            return RDPScreenshot(config)
        elif implementation == 'server_core':
            return ServerCoreScreenshot(config)
        elif implementation == 'vcxsrv':
            return VcXsrvScreenshot(config)
        elif implementation == 'wsl2':
            return WSL2Screenshot(config)
        elif implementation == 'x11':
            return X11Screenshot(config)
        else:
            raise ValueError(f"Unknown implementation: {implementation}")

    @staticmethod
    def _create_fallback(config: Optional[Dict[str, Any]] = None) -> 'ScreenshotBase':
        """Create fallback implementation"""
        # Try implementations in order
        implementations = [
            ('x11', lambda: __import__('mcp.screenshot.x11', fromlist=['X11Screenshot']).X11Screenshot),
            ('windows', lambda: __import__(
                'mcp.screenshot.windows', fromlist=['WindowsScreenshot']
            ).WindowsScreenshot),
        ]

        for name, loader in implementations:
            try:
                cls = loader()
                instance = cls(config)
                if instance.is_available():
                    logger.info(f"Using fallback implementation: {name}")
                    return instance
            except Exception as e:
                logger.debug(f"Fallback {name} not available: {e}")
                continue

        raise RuntimeError("No screenshot implementation available")


def get_screenshot_handler() -> 'ScreenshotBase':
    """Get cached screenshot handler instance"""
    global _screenshot_instance

    if _screenshot_instance is None:
        with _screenshot_instance_lock:
            if _screenshot_instance is None:
                _screenshot_instance = ScreenshotFactory.create()

    return _screenshot_instance


# Public API
__all__ = ['ScreenshotFactory', 'get_screenshot_handler']
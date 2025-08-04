"""
Screenshot module for computer-use-mcp
Provides cross-platform screenshot functionality
"""

from typing import Optional, Union, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Lazy imports to avoid loading unnecessary modules
_screenshot_instance: Optional['ScreenshotBase'] = None


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
        from ..platform_utils import get_platform_info, get_recommended_screenshot_method
        
        if force:
            return ScreenshotFactory._create_forced(force, config)
        
        # Auto-detect best method
        platform_info = get_platform_info()
        method = get_recommended_screenshot_method()
        
        logger.info(f"Auto-detected platform: {platform_info['platform']} "
                   f"({platform_info['environment']}), using method: {method}")
        
        if method == 'windows_native':
            from .windows import WindowsScreenshot
            return WindowsScreenshot(config)
        elif method == 'windows_rdp_capture':
            from .windows_rdp import RDPScreenshot
            return RDPScreenshot(config)
        elif method == 'not_available':
            from .server_core import ServerCoreScreenshot
            return ServerCoreScreenshot(config)
        elif method == 'vcxsrv_x11':
            from .vcxsrv import VcXsrvScreenshot
            return VcXsrvScreenshot(config)
        elif method == 'wsl2_powershell':
            from .windows import WSL2Screenshot
            return WSL2Screenshot(config)
        elif method == 'x11':
            from .x11 import X11Screenshot
            return X11Screenshot(config)
        elif method == 'macos_screencapture':
            from .macos import MacOSScreenshot
            return MacOSScreenshot(config)
        else:
            # Fallback
            return ScreenshotFactory._create_fallback(config)
    
    @staticmethod
    def _create_forced(implementation: str, config: Optional[Dict[str, Any]] = None) -> 'ScreenshotBase':
        """Create forced implementation"""
        if implementation == 'windows':
            from .windows import WindowsScreenshot
            return WindowsScreenshot(config)
        elif implementation == 'windows_rdp':
            from .windows_rdp import RDPScreenshot
            return RDPScreenshot(config)
        elif implementation == 'server_core':
            from .server_core import ServerCoreScreenshot
            return ServerCoreScreenshot(config)
        elif implementation == 'vcxsrv':
            from .vcxsrv import VcXsrvScreenshot
            return VcXsrvScreenshot(config)
        elif implementation == 'wsl2':
            from .windows import WSL2Screenshot
            return WSL2Screenshot(config)
        elif implementation == 'x11':
            from .x11 import X11Screenshot
            return X11Screenshot(config)
        else:
            raise ValueError(f"Unknown implementation: {implementation}")
    
    @staticmethod
    def _create_fallback(config: Optional[Dict[str, Any]] = None) -> 'ScreenshotBase':
        """Create fallback implementation"""
        # Try implementations in order
        implementations = [
            ('x11', lambda: __import__('mcp.screenshot.x11', fromlist=['X11Screenshot']).X11Screenshot),
            ('windows', lambda: __import__('mcp.screenshot.windows', fromlist=['WindowsScreenshot']).WindowsScreenshot),
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
        _screenshot_instance = ScreenshotFactory.create()
    
    return _screenshot_instance


# Public API
__all__ = ['ScreenshotFactory', 'get_screenshot_handler']
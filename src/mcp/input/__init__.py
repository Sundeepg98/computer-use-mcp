"""
Input module for computer-use-mcp
Provides cross-platform mouse and keyboard functionality
"""

from typing import Optional, Dict, Any
import logging

from .windows import WSL2Input
from .x11 import X11Input
from .windows import WindowsInput
from ..platforms.platform_utils import get_platform_info, get_recommended_input_method


logger = logging.getLogger(__name__)


class InputFactory:
    """Factory for creating appropriate input implementation"""

    @staticmethod
    def create() -> 'InputHandler':
        """Create appropriate input handler for current platform"""
        platform_info = get_platform_info()
        method = get_recommended_input_method()

        logger.info(f"Creating input handler for {platform_info['platform']} "
                   f"({platform_info['environment']}), method: {method}")

        if method == 'windows_native':
            return WindowsInput()
        elif method == 'wsl2_powershell':
            return WSL2Input()
        elif method == 'x11_xdotool':
            try:
                return X11Input()
            except Exception as e:
                logger.warning(f"X11Input not available: {e}")
                # Fallback to WSL2 if available
                if platform_info.get('can_use_powershell'):
                    return WSL2Input()
                raise
        else:
            raise RuntimeError(f"No input handler available for method: {method}")


def get_input_handler() -> 'InputHandler':
    """Get input handler for current platform"""
    return InputFactory.create()


__all__ = ['InputFactory', 'get_input_handler']
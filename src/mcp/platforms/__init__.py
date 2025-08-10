"""
Streamlined Platform Detection and Provider Creation
Only 3 essential platforms: Windows, Linux/X11, WSL2
"""

import platform
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def detect_platform() -> Dict[str, str]:
    """
    Detect current platform and environment
    Returns platform info dict
    """
    system = platform.system().lower()
    
    # Check for WSL
    is_wsl = False
    if system == 'linux':
        try:
            with open('/proc/version', 'r') as f:
                is_wsl = 'microsoft' in f.read().lower()
        except:
            pass
    
    if is_wsl:
        return {
            'platform': 'linux',
            'environment': 'wsl2',
            'display': os.environ.get('DISPLAY', ':0')
        }
    elif system == 'windows':
        return {
            'platform': 'windows',
            'environment': 'native',
            'display': 'windows'
        }
    elif system == 'linux':
        return {
            'platform': 'linux',
            'environment': 'x11',
            'display': os.environ.get('DISPLAY', ':0')
        }
    elif system == 'darwin':
        return {
            'platform': 'macos',
            'environment': 'native',
            'display': 'macos'
        }
    else:
        return {
            'platform': 'unknown',
            'environment': 'unknown',
            'display': None
        }


def get_platform_providers() -> Dict[str, Any]:
    """
    Get platform-specific provider implementations
    Returns dict with screenshot, input, platform, and display providers
    """
    platform_info = detect_platform()
    
    # Import implementations
    from ..implementations.platform_info_impl import PlatformInfoImpl
    from ..implementations.display_manager_impl import DisplayManagerImpl
    
    # Platform-specific providers
    if platform_info['platform'] == 'windows':
        from ..screenshot.windows import WindowsScreenshot
        from ..input.windows import WindowsInput
        
        return {
            'screenshot': WindowsScreenshot(),
            'input': WindowsInput(),
            'platform': PlatformInfoImpl(),
            'display': DisplayManagerImpl()
        }
    
    elif platform_info['environment'] == 'wsl2':
        # WSL2 uses hybrid approach
        from ..screenshot.x11 import X11Screenshot
        from ..input.x11 import X11Input
        
        return {
            'screenshot': X11Screenshot(),
            'input': X11Input(),
            'platform': PlatformInfoImpl(),
            'display': DisplayManagerImpl()
        }
    
    elif platform_info['platform'] == 'linux':
        from ..screenshot.x11 import X11Screenshot
        from ..input.x11 import X11Input
        
        return {
            'screenshot': X11Screenshot(),
            'input': X11Input(),
            'platform': PlatformInfoImpl(),
            'display': DisplayManagerImpl()
        }
    
    else:
        # Fallback to mock providers
        from ..core.test_mocks import get_mock_providers
        logger.warning(f"Unsupported platform: {platform_info['platform']}, using mock providers")
        return get_mock_providers()

"""
Platform information implementation
"""

from typing import Dict

from ..abstractions import PlatformInfo
from ..platforms.platform_utils import get_platform_info as _get_platform_info


class PlatformInfoImpl:
    """Default implementation of PlatformInfo protocol"""


    def __init__(self):
        self._info = _get_platform_info()

    def get_platform(self) -> str:
        """Get platform name (windows, linux, macos)"""
        return self._info.get('platform', 'unknown')

    def get_environment(self) -> str:
        """Get environment details (native, wsl2, etc)"""
        # Derive environment from platform info
        if self._info.get('is_wsl'):
            return 'wsl'
        elif self._info.get('is_docker'):
            return 'docker'
        elif self._info.get('is_windows_server'):
            return 'windows_server'
        elif self._info.get('system') == 'windows':
            return 'windows'
        elif self._info.get('system') == 'darwin':
            return 'macos'
        elif self._info.get('system') == 'linux':
            return 'linux'
        else:
            return 'unknown'

    def get_capabilities(self) -> Dict[str, bool]:
        """Get platform capabilities"""
        return {
            'screenshot': True,
            'input': True,
            'gui': self._info.get('has_gui', False),
            'x11': self._info.get('can_use_x11', False),
            'rdp': self._info.get('is_rdp', False),
            'wsl2': self._info.get('wsl2', False),
            'display': self._info.get('display_available', False)
        }
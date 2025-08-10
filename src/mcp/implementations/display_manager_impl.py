"""
Display manager implementation
"""

from typing import Optional
import logging
import os

from ..abstractions import DisplayManager
from ..platforms.platform_utils import is_windows, is_wsl2, get_platform_info


logger = logging.getLogger(__name__)


class DisplayManagerImpl:
    """Default implementation of DisplayManager protocol"""


    def __init__(self):
        self._platform_info = get_platform_info()

    def is_display_available(self) -> bool:
        """Check if display is available"""
        # Windows and WSL2 always have display via PowerShell
        if is_windows() or is_wsl2():
            logger.debug("Display available: Windows/WSL2 detected")
            return True

        # macOS always has display
        if self._platform_info['platform'] == 'macos':
            logger.debug("Display available: macOS detected")
            return True

        # Linux - check for X11 or Wayland
        if self._platform_info['platform'] == 'linux':
            # Check DISPLAY environment variable
            display = os.environ.get('DISPLAY')
            if display:
                logger.debug(f"Display available: DISPLAY={display}")
                return True

            # Check Wayland
            wayland = os.environ.get('WAYLAND_DISPLAY')
            if wayland:
                logger.debug(f"Display available: WAYLAND_DISPLAY={wayland}")
                return True

            # Check if we can use X11
            can_use_x11 = self._platform_info.get('can_use_x11', False)
            logger.debug(f"Linux display check: DISPLAY=None, WAYLAND=None, can_use_x11={can_use_x11}")
            return can_use_x11

        logger.debug(f"Display not available: Unknown platform {self._platform_info['platform']}")
        return False

    def get_best_display(self) -> Optional[str]:
        """Get the best available display"""
        if is_windows():
            return 'windows_native'

        if is_wsl2():
            return 'wsl2_powershell'

        if self._platform_info['platform'] == 'macos':
            return 'macos_native'

        if self._platform_info['platform'] == 'linux':
            if os.environ.get('DISPLAY'):
                return os.environ['DISPLAY']
            if os.environ.get('WAYLAND_DISPLAY'):
                return 'wayland'

        return None

    def setup_display(self) -> bool:
        """Setup display if needed"""
        # Most platforms don't need setup
        if self.is_display_available():
            return True

        # Linux might need X server setup
        if self._platform_info['platform'] == 'linux':
            try:
                # Try to set DISPLAY if not set
                if not os.environ.get('DISPLAY'):
                    os.environ['DISPLAY'] = ':0'
                    logger.info("Set DISPLAY=:0")
                    return True
            except Exception as e:
                logger.error(f"Failed to setup display: {e}")
                return False

        return False
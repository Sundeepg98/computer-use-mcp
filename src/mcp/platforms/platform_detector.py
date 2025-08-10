"""
Unified Platform Detection - Single Source of Truth
Consolidates all platform detection logic from multiple files
"""

from functools import lru_cache
from typing import Dict, Any, Optional
import logging
import os
import platform
import subprocess
import threading

try:
    import winreg
except ImportError:
    # winreg is Windows-only
    winreg = None

from ..core.constants import SUBPROCESS_TIMEOUT_NORMAL, SUBPROCESS_TIMEOUT_SHORT

#!/usr/bin/env python3

logger = logging.getLogger(__name__)


class PlatformDetector:
    """
    Singleton platform detector that caches results
    Replaces duplicate implementations across:
    - auto_resolver.py
    - xserver_manager.py
    - platform_utils.py
    - utils/helpers.py
    - windows_server_detector.py
    """

    _instance = None
    _cache = None
    _lock = threading.Lock()

    def __new__(cls) -> 'PlatformDetector':
        """Thread-safe singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def detect(self) -> Dict[str, Any]:
        """
        Detect platform information - cached for performance

        Returns:
            Dict with platform info including:
            - system: Operating system name
            - is_wsl: Whether running in WSL
            - is_docker: Whether running in Docker
            - is_ssh: Whether in SSH session
            - is_windows_server: Whether on Windows Server
            - has_gui: Whether GUI is available
        """
        if self._cache is not None:
            return self._cache

        self._cache = {
            'system': platform.system().lower(),
            'version': platform.version(),
            'machine': platform.machine(),
            'is_wsl': self._detect_wsl(),
            'is_docker': self._detect_docker(),
            'is_ssh': self._detect_ssh(),
            'is_windows_server': self._detect_windows_server(),
            'has_gui': self._detect_gui(),
            'display_available': self._check_display()
        }

        logger.debug(f"Platform detected: {self._cache}")
        return self._cache

    def _detect_wsl(self) -> bool:
        """Detect if running in WSL"""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except (OSError, IOError, FileNotFoundError):
            return False

    def _detect_docker(self) -> bool:
        """Detect if running in Docker container"""
        return os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')

    def _detect_ssh(self) -> bool:
        """Detect if in SSH session"""
        return bool(os.environ.get('SSH_CONNECTION') or os.environ.get('SSH_CLIENT'))

    def _detect_windows_server(self) -> bool:
        """Detect if running on Windows Server"""
        if platform.system() != 'Windows':
            return False

        try:
            # Check using wmic
            result = subprocess.run(
                ['wmic', 'os', 'get', 'Caption', '/value'],
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT_NORMAL
            )
            if result.returncode == 0:
                return 'server' in result.stdout.lower()
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            pass

        # Fallback: Check registry
        if winreg is not None:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                  r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                    product_name = winreg.QueryValueEx(key, "ProductName")[0]
                    return 'server' in str(product_name).lower()
            except (ImportError, OSError, WindowsError):
                pass

        return False

    def _detect_gui(self) -> bool:
        """Detect if GUI is available"""
        system = platform.system().lower()

        if system == 'windows':
            # Windows always has GUI unless it's Server Core
            if self._detect_windows_server():
                # Check for Server Core
                if winreg is not None:
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                          r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                            install_type = winreg.QueryValueEx(key, "InstallationType")[0]
                            return install_type.lower() != 'server core'
                    except (ImportError, OSError, WindowsError):
                        return True
                else:
                    return True
            return True

        elif system == 'darwin':
            # macOS always has GUI
            return True

        else:  # Linux/Unix
            # Check for X11 or Wayland
            return bool(os.environ.get('DISPLAY') or
                       os.environ.get('WAYLAND_DISPLAY') or
                       self._detect_wsl())  # WSL can use Windows display

    def _check_display(self) -> bool:
        """Check if display is actually available and working"""
        if not self._detect_gui():
            return False

        system = platform.system().lower()

        if system in ['linux', 'freebsd', 'openbsd']:
            # Try xset to verify X11 connection
            if os.environ.get('DISPLAY'):
                try:
                    result = subprocess.run(['xset', 'q'],
                                          capture_output=True,
                                          timeout=SUBPROCESS_TIMEOUT_SHORT)
                    return result.returncode == 0
                except (subprocess.SubprocessError, OSError, FileNotFoundError):
                    pass

        return True

    @property
    def is_wsl(self) -> bool:
        """Quick access to WSL status"""
        return self.detect()['is_wsl']

    @property
    def is_docker(self) -> bool:
        """Quick access to Docker status"""
        return self.detect()['is_docker']

    @property
    def system(self) -> str:
        """Quick access to system name"""
        return self.detect()['system']

    @property
    def has_gui(self) -> bool:
        """Quick access to GUI availability"""
        return self.detect()['has_gui']

    def clear_cache(self) -> None:
        """Clear cached platform info (useful after system changes)"""
        self._cache = None

    def get_recommended_screenshot_method(self) -> str:
        """Get recommended screenshot method for current platform"""
        info = self.detect()

        if info['is_wsl']:
            return 'wsl2_powershell'
        elif info['system'] == 'windows':
            if info['is_windows_server'] and not info['has_gui']:
                return 'server_core'
            return 'windows_native'
        elif info['system'] == 'darwin':
            return 'macos_screencapture'
        elif info['system'] == 'linux':
            if info['display_available']:
                return 'x11'
            return 'none'
        else:
            return 'none'

    def get_recommended_input_method(self) -> str:
        """Get recommended input method for current platform"""
        info = self.detect()

        if info['system'] == 'windows':
            return 'windows'
        elif info['system'] == 'darwin':
            return 'macos'
        elif info['display_available']:
            return 'x11'
        else:
            return 'none'


# Global instance for easy access
_detector = PlatformDetector()


# Convenience functions for backward compatibility
def get_platform_info() -> Dict[str, Any]:
    """Get platform information"""
    return _detector.detect()


def detect_wsl() -> bool:
    """Check if running in WSL"""
    return _detector.is_wsl


def detect_docker() -> bool:
    """Check if running in Docker"""
    return _detector.is_docker


def get_recommended_screenshot_method() -> str:
    """Get recommended screenshot method"""
    return _detector.get_recommended_screenshot_method()


def get_recommended_input_method() -> str:
    """Get recommended input method"""
    return _detector.get_recommended_input_method()
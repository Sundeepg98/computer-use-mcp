"""
Platform detection utilities for computer-use-mcp
Detects Windows, WSL1, WSL2, Linux, macOS and available features
"""

from typing import Dict, Any, Optional
import logging
import os
import platform
import shutil
import subprocess

from .vcxsrv_detector import VcXsrvDetector
from .windows_server_detector import WindowsServerDetector
from .platform_detector import PlatformDetector as UnifiedPlatformDetector
from ..core.constants import SUBPROCESS_TIMEOUT_SHORT

#!/usr/bin/env python3

logger = logging.getLogger(__name__)


class ExtendedPlatformDetector:
    """Extended platform detection with additional feature checks"""


    def __init__(self):
        self._platform_cache: Optional[Dict[str, Any]] = None
        self._unified_detector = UnifiedPlatformDetector()

    def detect_platform(self) -> Dict[str, Any]:
        """
        Detect current platform and environment

        Returns:
            Dict with platform information:
            - platform: 'windows', 'linux', 'macos'
            - environment: 'native', 'wsl1', 'wsl2'
            - can_use_powershell: bool
            - can_use_dotnet: bool
            - can_use_x11: bool
            - can_use_screencapture: bool (macOS)
            - wsl_version: Optional[int]
        """
        if self._platform_cache is not None:
            return self._platform_cache

        # Start with unified detector results
        unified_info = self._unified_detector.detect()
        system = unified_info['system']

        result = {
            'platform': system,
            'environment': 'wsl2' if unified_info['is_wsl'] else 'native',
            'can_use_powershell': False,
            'can_use_dotnet': False,
            'can_use_x11': False,
            'can_use_screencapture': False,
            'wsl_version': 2 if unified_info['is_wsl'] else None,
            'is_docker': unified_info['is_docker'],
            'is_ssh': unified_info['is_ssh'],
            'display_available': unified_info['display_available']
        }

        if system == 'Windows':
            result['platform'] = 'windows'
            result['can_use_powershell'] = True
            result['can_use_dotnet'] = True

            # Import Windows Server detector
            try:
                detector = WindowsServerDetector()
                server_info = detector.detect_windows_environment()

                # Add server-specific information
                result['is_windows_server'] = server_info['is_server']
                result['server_version'] = server_info.get('server_version')
                result['has_gui'] = server_info['has_gui']
                result['is_server_core'] = server_info['is_server_core']
                result['is_rdp_session'] = server_info['is_rdp_session']
                result['display_available'] = server_info['display_available']

                # Override environment if server
                if server_info['is_server']:
                    if server_info['is_server_core']:
                        result['environment'] = 'windows_server_core'
                    elif server_info['is_rdp_session']:
                        result['environment'] = 'windows_rdp'
                    else:
                        result['environment'] = 'windows_server'

                # Check for VcXsrv X11 server
                try:
                    vcxsrv_detector = VcXsrvDetector()
                    vcxsrv_info = vcxsrv_detector.detect_vcxsrv()

                    result['vcxsrv_installed'] = vcxsrv_info['installed']
                    result['vcxsrv_running'] = vcxsrv_info['running']
                    result['vcxsrv_display_available'] = vcxsrv_info['xdisplay_available']

                    # If VcXsrv is available, we can potentially use X11
                    if vcxsrv_info['xdisplay_available']:
                        result['can_use_x11'] = True
                        result['vcxsrv_display'] = vcxsrv_info['recommended_display']

                except Exception as e:
                    logger.debug(f"VcXsrv detection failed: {e}")

            except Exception as e:
                logger.warning(f"Failed to detect Windows Server details: {e}")
                # Fallback to basic Windows detection

        elif system == 'Linux':
            result['platform'] = 'linux'

            # Check for WSL
            wsl_interop = os.environ.get('WSL_INTEROP')
            wsl_distro = os.environ.get('WSL_DISTRO_NAME')

            if wsl_interop and wsl_distro:
                # WSL2 has interop and /mnt/wslg
                result['environment'] = 'wsl2'
                result['wsl_version'] = 2
                result['can_use_powershell'] = True
                result['can_use_x11'] = True  # But won't capture Windows desktop
            elif wsl_distro:
                # WSL1 check - look for Microsoft in kernel release
                try:
                    with open('/proc/sys/kernel/osrelease', 'r') as f:
                        if 'Microsoft' in f.read():
                            result['environment'] = 'wsl1'
                            result['wsl_version'] = 1
                            result['can_use_x11'] = True
                except (OSError, IOError):
                    pass
            else:
                # Native Linux
                result['can_use_x11'] = self.check_x11_available()

        elif system == 'Darwin':
            result['platform'] = 'macos'
            result['can_use_screencapture'] = True

        self._platform_cache = result
        return result

    def check_x11_available(self) -> bool:
        """Check if X11 display is available"""
        if not os.environ.get('DISPLAY'):
            return False

        try:
            # Try xset to check X11 connection
            result = subprocess.run(
                ['xset', 'q'],
                capture_output=True,
                timeout=SUBPROCESS_TIMEOUT_SHORT
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, OSError):
            return False

    def check_powershell_available(self) -> bool:
        """Check if PowerShell is available (for WSL2)"""
        return shutil.which('powershell.exe') is not None

    def get_recommended_screenshot_method(self) -> str:
        """Get recommended screenshot method for current platform"""
        info = self.detect_platform()

        if info['platform'] == 'windows':
            # Check if VcXsrv X11 is available as alternative
            if info.get('vcxsrv_display_available'):
                # VcXsrv provides X11 capability on Windows
                # Useful for Linux applications or alternative screenshot method
                pass  # Consider as secondary option

            # Handle Windows Server scenarios
            if info['environment'] == 'windows_server_core':
                # Server Core with VcXsrv could enable some GUI via X11
                if info.get('vcxsrv_display_available'):
                    return 'vcxsrv_x11'
                return 'not_available'  # No GUI at all
            elif info['environment'] == 'windows_rdp':
                return 'windows_rdp_capture'
            elif info['environment'] == 'windows_server':
                return 'windows_native'  # Server with GUI
            else:
                return 'windows_native'  # Regular Windows
        elif info['platform'] == 'linux' and info['environment'] == 'wsl2':
            return 'wsl2_powershell'
        elif info['platform'] == 'linux' and info['can_use_x11']:
            return 'x11'
        elif info['platform'] == 'macos':
            return 'macos_screencapture'
        else:
            return 'fallback'

    def get_recommended_input_method(self) -> str:
        """Get recommended input method for current platform"""
        info = self.detect_platform()

        if info['platform'] == 'windows' and info['environment'] == 'native':
            return 'windows_native'
        elif info['platform'] == 'linux' and info['environment'] == 'wsl2':
            return 'wsl2_powershell'
        elif info['platform'] == 'linux' and info['can_use_x11']:
            return 'x11_xdotool'
        elif info['platform'] == 'macos':
            return 'macos_native'
        else:
            return 'fallback'


# Global instance for convenience
_detector = ExtendedPlatformDetector()

def get_platform_info() -> Dict[str, Any]:
    """Get platform information"""
    return _detector.detect_platform()

def is_wsl2() -> bool:
    """Check if running in WSL2"""
    info = _detector.detect_platform()
    return info['environment'] == 'wsl2'

def is_windows() -> bool:
    """Check if running on Windows (native or WSL)"""
    info = _detector.detect_platform()
    return info['platform'] == 'windows' or info['environment'] in ['wsl1', 'wsl2']

def is_linux() -> bool:
    """Check if running on Linux (native, not WSL)"""
    info = _detector.detect_platform()
    return info['platform'] == 'linux' and info['environment'] == 'native'

def can_use_powershell() -> bool:
    """Check if PowerShell is available"""
    info = _detector.detect_platform()
    return info['can_use_powershell']

def get_recommended_input_method() -> str:
    """Get recommended input method for current platform"""
    return _detector.get_recommended_input_method()

def get_recommended_screenshot_method() -> str:
    """Get recommended screenshot method for current platform"""
    return _detector.get_recommended_screenshot_method()

def is_windows_server() -> bool:
    """Check if running on Windows Server"""
    info = _detector.detect_platform()
    return info.get('is_windows_server', False)

def is_server_core() -> bool:
    """Check if running on Windows Server Core (no GUI)"""
    info = _detector.detect_platform()
    return info.get('is_server_core', False)

def is_rdp_session() -> bool:
    """Check if running in RDP/Terminal Services session"""
    info = _detector.detect_platform()
    return info.get('is_rdp_session', False)

def get_windows_server_info() -> Dict[str, Any]:
    """Get detailed Windows Server information"""
    info = _detector.detect_platform()
    return {
        'is_server': info.get('is_windows_server', False),
        'version': info.get('server_version'),
        'has_gui': info.get('has_gui', True),
        'is_core': info.get('is_server_core', False),
        'is_rdp': info.get('is_rdp_session', False),
        'environment': info.get('environment', 'native'),
        'display_available': info.get('display_available', True),
        'vcxsrv_installed': info.get('vcxsrv_installed', False),
        'vcxsrv_running': info.get('vcxsrv_running', False),
        'vcxsrv_display_available': info.get('vcxsrv_display_available', False)
    }

def has_vcxsrv() -> bool:
    """Check if VcXsrv is installed"""
    info = _detector.detect_platform()
    return info.get('vcxsrv_installed', False)

def is_vcxsrv_running() -> bool:
    """Check if VcXsrv is running"""
    info = _detector.detect_platform()
    return info.get('vcxsrv_running', False)

def get_vcxsrv_status() -> Dict[str, Any]:
    """Get detailed VcXsrv status"""
    if platform.system() != 'Windows':
        return {'available': False, 'reason': 'Not Windows'}

    try:
        detector = VcXsrvDetector()
        return detector.detect_vcxsrv()
    except Exception as e:
        return {'available': False, 'error': str(e)}
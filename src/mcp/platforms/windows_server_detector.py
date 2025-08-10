"""
Windows Server detection and capability assessment
Handles Server Core, RDP, Terminal Services, and VDI environments
"""

from typing import Dict, Any, Optional
import logging
import os
import platform
import re
import subprocess

try:
    import psutil
except ImportError:
    # psutil not installed
    psutil = None
try:
    import winreg
except ImportError:
    # winreg is Windows-only
    winreg = None
try:
    import ctypes
except ImportError:
    # ctypes might not be available
    ctypes = None

from ..core.constants import SUBPROCESS_TIMEOUT_NORMAL

#!/usr/bin/env python3

logger = logging.getLogger(__name__)


class WindowsServerDetector:
    """Detects Windows Server environments and capabilities"""


    def __init__(self):
        self._cache: Optional[Dict[str, Any]] = None

    def detect_windows_environment(self) -> Dict[str, Any]:
        """
        Comprehensive Windows environment detection

        Returns:
            Dict containing:
            - is_server: bool - Running on Windows Server
            - server_version: str - Server version (2019, 2022, etc.)
            - has_gui: bool - GUI is available
            - is_server_core: bool - Running Server Core (no GUI)
            - is_rdp_session: bool - Running in RDP session
            - is_terminal_services: bool - Terminal Services enabled
            - session_id: int - Windows session ID
            - is_console_session: bool - Running on console (not remote)
            - display_available: bool - Can capture screenshots
            - recommended_method: str - Best screenshot method
        """
        if self._cache is not None:
            return self._cache

        result = {
            'is_server': False,
            'server_version': None,
            'has_gui': True,
            'is_server_core': False,
            'is_rdp_session': False,
            'is_terminal_services': False,
            'session_id': 0,
            'is_console_session': True,
            'display_available': True,
            'recommended_method': 'windows_native',
            'environment_details': {}
        }

        if platform.system() != 'Windows':
            self._cache = result
            return result

        # Detect Windows Server
        try:
            # Use wmic to get OS information
            output = subprocess.check_output(
                ['wmic', 'os', 'get', 'Caption,Version', '/value'],
                text=True,
                timeout=SUBPROCESS_TIMEOUT_NORMAL
            )

            caption = ""
            version = ""
            for line in output.split('\n'):
                if line.startswith('Caption='):
                    caption = line.split('=', 1)[1].strip()
                elif line.startswith('Version='):
                    version = line.split('=', 1)[1].strip()

            # Check if it's Windows Server
            if 'Server' in caption:
                result['is_server'] = True

                # Extract server version
                if '2022' in caption:
                    result['server_version'] = '2022'
                elif '2019' in caption:
                    result['server_version'] = '2019'
                elif '2016' in caption:
                    result['server_version'] = '2016'
                elif '2012' in caption:
                    result['server_version'] = '2012R2' if 'R2' in caption else '2012'
                else:
                    result['server_version'] = 'Unknown'

                # Check for Server Core
                if 'Core' in caption or self._is_server_core():
                    result['is_server_core'] = True
                    result['has_gui'] = False
                    result['display_available'] = False

            result['environment_details']['os_caption'] = caption
            result['environment_details']['os_version'] = version

        except Exception as e:
            logger.warning(f"Failed to detect Windows version via wmic: {e}")

        # Detect RDP/Terminal Services session
        try:
            # Check session name - RDP sessions typically have 'RDP-Tcp#' format
            session_name = os.environ.get('SESSIONNAME', '')
            if session_name and (session_name.startswith('RDP-') or 'RDP' in session_name):
                result['is_rdp_session'] = True
                result['is_console_session'] = False

            # Alternative: Check if running in remote session
            try:
                output = subprocess.check_output(
                    ['query', 'session'],
                    text=True,
                    timeout=SUBPROCESS_TIMEOUT_NORMAL
                )

                # Parse current session
                for line in output.split('\n'):
                    if '>' in line:  # Current session marked with >
                        parts = line.split()
                        if len(parts) > 2:
                            session_name = parts[1]
                            session_id = parts[2] if parts[2].isdigit() else parts[3]

                            result['session_id'] = int(session_id) if session_id.isdigit() else 0

                            if 'rdp' in session_name.lower():
                                result['is_rdp_session'] = True
                                result['is_console_session'] = False
                            elif session_name.lower() == 'console':
                                result['is_console_session'] = True

            except Exception as e:
                logger.debug(f"Failed to query session: {e}")

            # Check if Terminal Services is running
            try:
                output = subprocess.check_output(
                    ['sc', 'query', 'TermService'],
                    text=True,
                    timeout=SUBPROCESS_TIMEOUT_NORMAL
                )
                if 'RUNNING' in output:
                    result['is_terminal_services'] = True
            except (subprocess.SubprocessError, subprocess.TimeoutExpired, OSError) as e:
                logger.debug(f"Failed to query TermService: {e}")
                # Terminal services status unknown, continue with detection

        except Exception as e:
            logger.warning(f"Failed to detect RDP/TS session: {e}")

        # Determine screenshot capability and recommended method
        if result['is_server_core']:
            result['display_available'] = False
            result['recommended_method'] = 'not_available'
        elif result['is_rdp_session']:
            result['display_available'] = True
            result['recommended_method'] = 'rdp_capture'
        else:
            # Check if desktop is available
            try:
                user32 = ctypes.windll.user32
                # Try to get desktop window
                hwnd = user32.GetDesktopWindow()
                if hwnd:
                    result['display_available'] = True
                    result['recommended_method'] = 'windows_native'
                else:
                    result['display_available'] = False
                    result['recommended_method'] = 'not_available'
            except (ImportError, AttributeError, OSError) as e:
                # ctypes not available or Windows API call failed
                logger.debug(f"Failed to check desktop availability: {e}")
                # For non-server core Windows, display is likely available
                # but we can't confirm via API
                result['display_available'] = not result.get('is_server_core', False)
                result['recommended_method'] = 'windows_native' if result['display_available'] else 'not_available'

        self._cache = result
        return result

    def _is_server_core(self) -> bool:
        """Check if running Windows Server Core (no GUI)"""
        try:
            # Server Core doesn't have explorer.exe as shell
            output = subprocess.check_output(
                ['reg', 'query', 'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon',
                 '/v', 'Shell'],
                text=True,
                timeout=SUBPROCESS_TIMEOUT_NORMAL
            )

            # Server Core uses cmd.exe as shell instead of explorer.exe
            if 'cmd.exe' in output.lower() and 'explorer.exe' not in output.lower():
                return True

            # Alternative check: Server Core doesn't have certain GUI components
            try:
                # Try to query a GUI-only service
                output = subprocess.check_output(
                    ['sc', 'query', 'Themes'],  # Themes service only on GUI
                    text=True,
                    timeout=SUBPROCESS_TIMEOUT_NORMAL,
                    stderr=subprocess.DEVNULL
                )
                return 'FAILED' in output or 'service does not exist' in output.lower()
            except subprocess.CalledProcessError:
                return True  # Service doesn't exist = Server Core

        except Exception as e:
            logger.debug(f"Server Core detection failed: {e}")

        return False

    def get_display_capabilities(self) -> Dict[str, Any]:
        """Get detailed display capabilities for current environment"""
        env = self.detect_windows_environment()

        capabilities = {
            'can_screenshot': env['display_available'],
            'screenshot_method': env['recommended_method'],
            'limitations': [],
            'alternatives': []
        }

        if env['is_server_core']:
            capabilities['limitations'].append('Server Core has no GUI - screenshots not possible')
            capabilities['alternatives'].append('Use Windows Admin Center for remote management')
            capabilities['alternatives'].append('Use PowerShell remoting for automation')

        elif env['is_rdp_session']:
            capabilities['limitations'].append('RDP session - captures RDP window only')
            capabilities['alternatives'].append('Use native tools on RDP client machine')

        if env['is_server'] and not env['has_gui']:
            capabilities['limitations'].append('No desktop environment available')

        return capabilities

    def get_recommended_tools(self) -> Dict[str, Any]:
        """Get recommended tools for current Windows environment"""
        env = self.detect_windows_environment()

        tools = {
            'screenshot': [],
            'input': [],
            'automation': []
        }

        if env['display_available']:
            if env['is_rdp_session']:
                tools['screenshot'].append({
                    'name': 'RDP Screenshot',
                    'method': 'windows_rdp_capture',
                    'description': 'Captures RDP session window'
                })
            else:
                tools['screenshot'].append({
                    'name': 'Windows Native',
                    'method': 'windows_native',
                    'description': 'Uses Windows GDI+ APIs'
                })

            tools['input'].append({
                'name': 'SendInput API',
                'method': 'windows_sendinput',
                'description': 'Native Windows input injection'
            })

        # Always available tools
        tools['automation'].append({
            'name': 'PowerShell',
            'method': 'powershell',
            'description': 'PowerShell automation and scripting'
        })

        if env['is_server']:
            tools['automation'].append({
                'name': 'Windows Admin Center',
                'method': 'wac',
                'description': 'Web-based server management'
            })

            if env['is_server_core']:
                tools['automation'].append({
                    'name': 'Server Core App Compatibility',
                    'method': 'appcompat',
                    'description': 'Limited GUI app support on Server Core'
                })

        return tools


def is_windows_server() -> bool:
    """Quick check if running on Windows Server"""
    if platform.system() != 'Windows':
        return False

    detector = WindowsServerDetector()
    return detector.detect_windows_environment()['is_server']


def can_capture_screenshot() -> bool:
    """Check if screenshot capture is possible in current environment"""
    if platform.system() != 'Windows':
        return True  # Assume other platforms can

    detector = WindowsServerDetector()
    return detector.detect_windows_environment()['display_available']


def get_screenshot_method() -> str:
    """Get recommended screenshot method for current environment"""
    if platform.system() != 'Windows':
        return 'default'

    detector = WindowsServerDetector()
    return detector.detect_windows_environment()['recommended_method']
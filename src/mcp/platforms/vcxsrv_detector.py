"""
VcXsrv X11 Server detection and integration for Windows
Enables X11 application support on Windows environments
"""

import time
from typing import Dict, Any, Optional, List
import logging
import os
import platform
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

from ..utils.config import ComputerUseConfig
from ..core.constants import (
    SUBPROCESS_TIMEOUT_NORMAL, SUBPROCESS_TIMEOUT_SHORT,
    SUBPROCESS_TIMEOUT_QUICK, WAIT_DELAY_LONG
)
from ..core.paths import VCXSRV_PATHS, get_vcxsrv_search_paths

logger = logging.getLogger(__name__)


class VcXsrvDetector:
    """Detects and manages VcXsrv X11 server on Windows"""


    def __init__(self):
        self._cache: Optional[Dict[str, Any]] = None
        self._managed_processes: Dict[int, subprocess.Popen] = {}  # Track started processes
        # Use centralized paths configuration
        if platform.system() == "Windows" and winreg is not None:
            self.common_paths = get_vcxsrv_search_paths()
        else:
            self.common_paths = []

    def detect_vcxsrv(self) -> Dict[str, Any]:
        """
        Comprehensive VcXsrv detection

        Returns:
            Dict containing:
            - installed: bool - VcXsrv is installed
            - running: bool - VcXsrv is currently running
            - version: str - VcXsrv version
            - executable_path: str - Path to vcxsrv.exe
            - display_numbers: List[int] - Active display numbers
            - xdisplay_available: bool - X11 display is available
            - recommended_display: str - Best display to use (e.g., ":0")
            - capabilities: Dict - What X11 features are available
        """
        if self._cache is not None:
            return self._cache

        if platform.system() != 'Windows':
            self._cache = self._get_empty_result()
            return self._cache

        result = {
            'installed': False,
            'running': False,
            'version': None,
            'executable_path': None,
            'display_numbers': [],
            'xdisplay_available': False,
            'recommended_display': None,
            'capabilities': {
                'screenshot': False,
                'input': False,
                'window_management': False,
                'clipboard': False
            },
            'processes': [],
            'installation_method': None
        }

        # Check if VcXsrv is installed
        install_info = self._detect_installation()
        result.update(install_info)

        if result['installed']:
            # Check if VcXsrv is running
            running_info = self._detect_running_instances()
            result.update(running_info)

            # Test X11 display availability
            if result['running']:
                display_info = self._test_x11_displays()
                result.update(display_info)

        self._cache = result
        return result

    def _get_empty_result(self) -> Dict[str, Any]:
        """Get empty result for non-Windows systems"""
        return {
            'installed': False,
            'running': False,
            'version': None,
            'executable_path': None,
            'display_numbers': [],
            'xdisplay_available': False,
            'recommended_display': None,
            'capabilities': {},
            'processes': []
        }

    def _detect_installation(self) -> Dict[str, Any]:
        """Detect VcXsrv installation"""
        result = {
            'installed': False,
            'executable_path': None,
            'version': None,
            'installation_method': None
        }

        # Method 1: Check common installation paths
        for path in self.common_paths:
            if os.path.isfile(path):
                result['installed'] = True
                result['executable_path'] = path
                result['installation_method'] = 'standard_install'

                # Try to get version
                try:
                    version_result = subprocess.run(
                        [path, '-version'],
                        capture_output=True,
                        text=True,
                        timeout=SUBPROCESS_TIMEOUT_NORMAL
                    )
                    if version_result.returncode == 0:
                        # Parse version from output
                        for line in version_result.stdout.split('\n'):
                            if 'VcXsrv' in line and ('version' in line.lower() or 'v' in line):
                                result['version'] = line.strip()
                                break
                except Exception as e:
                    logger.debug(f"Failed to get VcXsrv version: {e}")

                break

        # Method 2: Check Windows Registry
        if not result['installed']:
            reg_info = self._check_registry()
            if reg_info['found']:
                result.update(reg_info)
                result['installation_method'] = 'registry'

        # Method 3: Check PATH
        if not result['installed']:
            try:
                path_result = subprocess.run(
                    ['where', 'vcxsrv.exe'],
                    capture_output=True,
                    text=True,
                    timeout=SUBPROCESS_TIMEOUT_NORMAL
                )
                if path_result.returncode == 0:
                    executable_path = path_result.stdout.strip().split('\n')[0]
                    result['installed'] = True
                    result['executable_path'] = executable_path
                    result['installation_method'] = 'path'
            except Exception as e:
                logger.debug(f"PATH check failed: {e}")

        return result

    def _check_registry(self) -> Dict[str, Any]:
        """Check Windows Registry for VcXsrv"""
        result = {'found': False}

        try:
            # Check common registry locations
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\VcXsrv"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\VcXsrv"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\VcXsrv")
            ]

            for hkey, path in registry_paths:
                try:
                    with winreg.OpenKey(hkey, path) as key:
                        # Try to get installation path
                        try:
                            install_path, _ = winreg.QueryValueEx(key, "InstallLocation")
                            executable = os.path.join(install_path, "vcxsrv.exe")
                            if os.path.isfile(executable):
                                result['found'] = True
                                result['installed'] = True
                                result['executable_path'] = executable
                        except FileNotFoundError:
                            pass

                        # Try to get version
                        try:
                            version, _ = winreg.QueryValueEx(key, "Version")
                            result['version'] = version
                        except FileNotFoundError:
                            pass

                        if result['found']:
                            break

                except FileNotFoundError:
                    continue

        except Exception as e:
            logger.debug(f"Registry check failed: {e}")

        return result

    def _detect_running_instances(self) -> Dict[str, Any]:
        """Detect running VcXsrv instances"""
        result = {
            'running': False,
            'processes': [],
            'display_numbers': []
        }

        try:
            # Find VcXsrv processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'vcxsrv' in proc.info['name'].lower():
                        process_info = {
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': proc.info['cmdline'] or []
                        }

                        # Extract display number from command line
                        display_num = self._extract_display_number(process_info['cmdline'])
                        if display_num is not None:
                            process_info['display'] = display_num
                            result['display_numbers'].append(display_num)

                        result['processes'].append(process_info)
                        result['running'] = True

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            logger.debug(f"Process detection failed: {e}")

        # Sort display numbers
        result['display_numbers'] = sorted(set(result['display_numbers']))

        return result

    def _extract_display_number(self, cmdline: List[str]) -> Optional[int]:
        """Extract display number from VcXsrv command line"""
        for arg in cmdline:
            if arg.startswith(':'):
                try:
                    return int(arg[1:])
                except ValueError:
                    continue
            elif '-display' in arg.lower():
                # Next argument might be display number
                try:
                    idx = cmdline.index(arg)
                    if idx + 1 < len(cmdline):
                        display_arg = cmdline[idx + 1]
                        if display_arg.startswith(':'):
                            return int(display_arg[1:])
                except (ValueError, IndexError):
                    continue
        return None

    def _test_x11_displays(self) -> Dict[str, Any]:
        """Test X11 display availability"""
        result = {
            'xdisplay_available': False,
            'recommended_display': None,
            'capabilities': {
                'screenshot': False,
                'input': False,
                'window_management': False,
                'clipboard': False
            }
        }

        for display_num in self.display_numbers:
            display = f":{display_num}"

            # Test display connectivity
            if self._test_display_connection(display):
                result['xdisplay_available'] = True
                result['recommended_display'] = display

                # Test specific capabilities
                result['capabilities'] = self._test_x11_capabilities(display)
                break

        return result

    def _test_display_connection(self, display: str) -> bool:
        """Test connection to X11 display"""
        try:
            # Set DISPLAY environment variable
            env = os.environ.copy()
            env['DISPLAY'] = display

            # Try xset query (basic X11 connectivity test)
            result = subprocess.run(
                ['xset', 'q'],
                capture_output=True,
                env=env,
                timeout=SUBPROCESS_TIMEOUT_QUICK
            )

            return result.returncode == 0

        except Exception as e:
            logger.debug(f"Display connection test failed for {display}: {e}")
            return False

    def _test_x11_capabilities(self, display: str) -> Dict[str, bool]:
        """Test specific X11 capabilities"""
        capabilities = {
            'screenshot': False,
            'input': False,
            'window_management': False,
            'clipboard': False
        }

        env = os.environ.copy()
        env['DISPLAY'] = display

        # Test screenshot capability (xwd, import, or scrot)
        for tool in ['import', 'scrot', 'xwd']:
            try:
                result = subprocess.run(
                    ['which', tool],
                    capture_output=True,
                    timeout=SUBPROCESS_TIMEOUT_SHORT
                )
                if result.returncode == 0:
                    capabilities['screenshot'] = True
                    break
            except (subprocess.SubprocessError, subprocess.TimeoutExpired, OSError):
                continue

        # Test input capability (xdotool)
        try:
            result = subprocess.run(
                ['which', 'xdotool'],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                capabilities['input'] = True
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, OSError):
            pass

        # Test window management (wmctrl or xwininfo)
        for tool in ['wmctrl', 'xwininfo']:
            try:
                result = subprocess.run(
                    ['which', tool],
                    capture_output=True,
                    timeout=SUBPROCESS_TIMEOUT_SHORT
                )
                if result.returncode == 0:
                    capabilities['window_management'] = True
                    break
            except (subprocess.SubprocessError, subprocess.TimeoutExpired, OSError):
                continue

        # Test clipboard (xclip or xsel)
        for tool in ['xclip', 'xsel']:
            try:
                result = subprocess.run(
                    ['which', tool],
                    capture_output=True,
                    timeout=SUBPROCESS_TIMEOUT_SHORT
                )
                if result.returncode == 0:
                    capabilities['clipboard'] = True
                    break
            except (subprocess.SubprocessError, subprocess.TimeoutExpired, OSError):
                continue

        return capabilities

    @property
    def display_numbers(self) -> List[int]:
        """Get list of active display numbers"""
        info = self.detect_vcxsrv()
        return info.get('display_numbers', [])

    def start_vcxsrv(self, display: int = 0, **kwargs) -> Dict[str, Any]:
        """Start VcXsrv server if not running"""
        info = self.detect_vcxsrv()

        if not info['installed']:
            return {
                'success': False,
                'error': 'VcXsrv is not installed',
                'suggestion': 'Install VcXsrv from https://sourceforge.net/projects/vcxsrv/'
            }

        if display in info['display_numbers']:
            return {
                'success': True,
                'message': f'VcXsrv already running on display :{display}',
                'display': f':{display}'
            }

        # Build command line arguments
        cmd = [info['executable_path']]
        cmd.extend([f':{display}'])

        # Add common useful arguments
        args = kwargs.get('args', [])
        if not args:
            args = [
                '-multiwindow',  # Multiple windows mode
                '-clipboard',    # Enable clipboard
                '-wgl',          # Use Windows OpenGL
                '-ac'            # Disable access control
            ]

        cmd.extend(args)

        proc = None
        try:
            # Start VcXsrv
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Wait a moment for startup
            time.sleep(WAIT_DELAY_LONG)

            # Clear cache to get updated info
            self._cache = None

            # Verify it's running
            updated_info = self.detect_vcxsrv()
            if display in updated_info['display_numbers']:
                # Store the process for later cleanup
                self._managed_processes[display] = proc
                return {
                    'success': True,
                    'message': f'VcXsrv started on display :{display}',
                    'display': f':{display}',
                    'pid': proc.pid
                }
            else:
                # Failed to start properly, terminate the process
                proc.terminate()
                return {
                    'success': False,
                    'error': 'VcXsrv started but display not available',
                    'pid': proc.pid
                }

        except Exception as e:
            # Clean up process if it was started
            if proc is not None:
                try:
                    proc.terminate()
                    proc.wait(timeout=SUBPROCESS_TIMEOUT_NORMAL)
                except (subprocess.TimeoutExpired, OSError) as e:
                    logger.warning(f"Failed to terminate process: {e}")
            return {
                'success': False,
                'error': f'Failed to start VcXsrv: {e}'
            }

    def stop_vcxsrv(self, display: int) -> bool:
        """Stop a managed VcXsrv instance"""
        if display in self._managed_processes:
            proc = self._managed_processes[display]
            try:
                proc.terminate()
                proc.wait(timeout=5)
                del self._managed_processes[display]
                logger.info(f"Stopped VcXsrv on display {display}")
                return True
            except Exception as e:
                logger.error(f"Failed to stop VcXsrv on display {display}: {e}")
                return False
        return False

    def __del__(self):
        """Cleanup all managed processes on deletion"""
        for display in list(self._managed_processes.keys()):
            self.stop_vcxsrv(display)

    def get_installation_guide(self) -> Dict[str, Any]:
        """Get VcXsrv installation guide"""
        return {
            'name': 'VcXsrv Windows X Server',
            'description': 'X11 server for Windows enabling Linux GUI applications',
            'download_url': 'https://sourceforge.net/projects/vcxsrv/',
            'installation_steps': [
                '1. Download VcXsrv from SourceForge',
                '2. Run the installer as Administrator',
                '3. Follow installation wizard (default settings work)',
                '4. Launch XLaunch to configure and start server',
                '5. Configure Windows Firewall if prompted'
            ],
            'configuration_tips': [
                'Use "Multiple windows" mode for better integration',
                'Enable clipboard sharing for copy/paste',
                'Disable access control (-ac) for easier connectivity',
                'Consider "Disable WGL" if OpenGL causes issues'
            ],
            'wsl2_setup': [
                '1. Install VcXsrv on Windows',
                '2. Start VcXsrv with "-ac" (disable access control)',
                '3. In WSL2, set DISPLAY environment variable',
                '4. Export DISPLAY=<Windows_IP>:0.0',
                '5. Test with: xeyes or xclock'
            ]
        }
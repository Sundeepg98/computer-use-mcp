"""
X Server Management for Computer Use MCP
Handles X server installation, startup, and management for WSL2/Linux environments
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
import os
import subprocess
import sys
import time

from ..platforms.platform_detector import PlatformDetector
from .config import ComputerUseConfig
from ..core.constants import (

#!/usr/bin/env python3

    SUBPROCESS_TIMEOUT_SHORT, SUBPROCESS_TIMEOUT_NORMAL,
    SUBPROCESS_TIMEOUT_LONG, SUBPROCESS_TIMEOUT_EXTREME,
    XSERVER_START_DELAY
)

logger = logging.getLogger(__name__)


class XServerManager:
    """Manages X server installation and lifecycle for computer use operations"""


    def __init__(self):
        """Initialize X server manager"""
        self.xserver_processes = {}
        self.display_ports = {}
        self.detector = PlatformDetector()
        self.config = ComputerUseConfig()
        self.wsl_mode = self.detector.is_wsl
        self.host_ip = self._get_host_ip() if self.wsl_mode else None
    def _get_host_ip(self) -> Optional[str]:
        """Get Windows host IP for WSL2 X forwarding"""
        try:
            result = subprocess.run(
                ['cat', self.config.get_path('etc_resolv_conf')],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if 'nameserver' in line:
                    return line.split()[1]
        except (subprocess.SubprocessError, OSError, IndexError):
            pass
        return None

    def check_xserver_available(self, display: str = None) -> Dict[str, Any]:
        """Check if X server is available and responsive"""
        display = display or os.environ.get('DISPLAY', ':0')

        try:
            # Test X server connection
            result = subprocess.run(
                ['xset', 'q'],
                env={**os.environ, 'DISPLAY': display},
                capture_output=True,
                timeout=SUBPROCESS_TIMEOUT_NORMAL
            )

            if result.returncode == 0:
                return {
                    'available': True,
                    'display': display,
                    'method': 'native_x11',
                    'info': result.stdout.decode()
                }
        except Exception as e:
            logger.debug(f"X server test failed: {e}")

        return {
            'available': False,
            'display': display,
            'method': None,
            'error': 'X server not responsive'
        }

    def install_xserver_packages(self) -> Dict[str, Any]:
        """Install necessary X server packages"""
        packages = [
            'xorg',
            'xserver-xorg',
            'xvfb',  # Virtual framebuffer X server
            'x11-apps',  # X11 client applications
            'x11-utils',  # X11 utilities
            'xdotool',  # X11 automation tool
            'scrot',  # Screenshot utility
            'imagemagick'  # Image manipulation
        ]

        results = {
            'installed': [],
            'failed': [],
            'already_installed': []
        }

        for package in packages:
            try:
                # Check if already installed
                check_result = subprocess.run(
                    ['dpkg', '-l', package],
                    capture_output=True,
                    timeout=SUBPROCESS_TIMEOUT_LONG
                )

                if check_result.returncode == 0:
                    results['already_installed'].append(package)
                    continue

                # Install package
                install_result = subprocess.run(
                    ['sudo', 'apt-get', 'install', '-y', package],
                    capture_output=True,
                    timeout=SUBPROCESS_TIMEOUT_EXTREME
                )

                if install_result.returncode == 0:
                    results['installed'].append(package)
                else:
                    results['failed'].append({
                        'package': package,
                        'error': install_result.stderr.decode()
                    })

            except Exception as e:
                results['failed'].append({
                    'package': package,
                    'error': str(e)
                })

        return results

    def start_virtual_display(self, display_num: int = 99,
                            width: int = 1920, height: int = 1080) -> Dict[str, Any]:
        """Start virtual X server using Xvfb"""
        display = f":{display_num}"

        process = None
        try:
            # Check if display already in use
            if display in self.xserver_processes:
                return {
                    'success': True,
                    'display': display,
                    'status': 'already_running',
                    'pid': self.xserver_processes[display].pid
                }

            # Start Xvfb
            cmd = [
                'Xvfb', display,
                '-screen', '0', f'{width}x{height}x24',
                '-ac',  # Allow all connections
                '+extension', 'GLX',
                '+render',
                '-noreset'
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait a moment for server to start
            time.sleep(XSERVER_START_DELAY)

            # Test if server started successfully
            test_result = self.check_xserver_available(display)

            if test_result['available']:
                self.xserver_processes[display] = process
                self.display_ports[display] = {
                    'width': width,
                    'height': height,
                    'pid': process.pid
                }

                return {
                    'success': True,
                    'display': display,
                    'status': 'started',
                    'pid': process.pid,
                    'resolution': f'{width}x{height}'
                }
            else:
                process.terminate()
                return {
                    'success': False,
                    'display': display,
                    'error': 'Failed to start X server',
                    'details': test_result
                }

        except Exception as e:
            # Clean up process if it was started
            if process is not None:
                try:
                    process.terminate()
                    process.wait(timeout=SUBPROCESS_TIMEOUT_NORMAL)
                except (subprocess.TimeoutExpired, OSError) as e:
                    logger.warning(f"Failed to terminate X server process: {e}")
            return {
                'success': False,
                'display': display,
                'error': str(e)
            }

    def setup_wsl_xforwarding(self) -> Dict[str, Any]:
        """Setup X11 forwarding for WSL2 to Windows host"""
        if not self.wsl_mode:
            return {
                'success': False,
                'error': 'Not running in WSL environment'
            }

        if not self.host_ip:
            return {
                'success': False,
                'error': 'Could not determine Windows host IP'
            }

        # Set DISPLAY environment variable
        display = f"{self.host_ip}:0.0"
        os.environ['DISPLAY'] = display

        # Test connection
        test_result = self.check_xserver_available(display)

        if test_result['available']:
            return {
                'success': True,
                'display': display,
                'host_ip': self.host_ip,
                'method': 'wsl_xforwarding'
            }
        else:
            return {
                'success': False,
                'display': display,
                'host_ip': self.host_ip,
                'error': 'Windows X server not accessible',
                'suggestion': 'Install VcXsrv or X410 on Windows and allow connections'
            }

    def get_best_display(self) -> Dict[str, Any]:
        """Get the best available display configuration"""
        # Priority order:
        # 1. Existing DISPLAY environment variable
        # 2. WSL X forwarding
        # 3. Virtual display
        # 4. Native X server

        # Check existing DISPLAY
        existing_display = os.environ.get('DISPLAY')
        if existing_display:
            test_result = self.check_xserver_available(existing_display)
            if test_result['available']:
                return {
                    **test_result,
                    'method': 'existing_display'
                }

        # Try WSL X forwarding
        if self.wsl_mode:
            wsl_result = self.setup_wsl_xforwarding()
            if wsl_result['success']:
                return {
                    'available': True,
                    'display': wsl_result['display'],
                    'method': 'wsl_xforwarding',
                    'host_ip': wsl_result['host_ip']
                }

        # Try starting virtual display
        virtual_result = self.start_virtual_display()
        if virtual_result['success']:
            # Set environment variable
            os.environ['DISPLAY'] = virtual_result['display']
            return {
                'available': True,
                'display': virtual_result['display'],
                'method': 'virtual_display',
                'pid': virtual_result['pid']
            }

        # Last resort: try native X server
        native_result = self.check_xserver_available(':0')
        if native_result['available']:
            return native_result

        return {
            'available': False,
            'error': 'No X server available',
            'suggestions': [
                'Install X server packages',
                'Start virtual display server',
                'Setup X11 forwarding (WSL2)',
                'Install Windows X server (VcXsrv/X410)'
            ]
        }

    def stop_xserver(self, display: str) -> Dict[str, Any]:
        """Stop X server process"""
        if display not in self.xserver_processes:
            return {
                'success': False,
                'error': f'No X server process found for display {display}'
            }

        try:
            process = self.xserver_processes[display]
            process.terminate()
            process.wait(timeout=SUBPROCESS_TIMEOUT_LONG)

            del self.xserver_processes[display]
            if display in self.display_ports:
                del self.display_ports[display]

            return {
                'success': True,
                'display': display,
                'status': 'stopped'
            }

        except Exception as e:
            return {
                'success': False,
                'display': display,
                'error': str(e)
            }

    def cleanup_all(self) -> Dict[str, Any]:
        """Stop all managed X server processes"""
        results = []

        for display in list(self.xserver_processes.keys()):
            result = self.stop_xserver(display)
            results.append(result)

        return {
            'stopped_servers': len(results),
            'results': results
        }

    def __del__(self):
        """Cleanup all X server processes on deletion"""
        try:
            self.cleanup_all()
        except Exception as e:
            logger.error(f"Failed to cleanup X server resources: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get status of all X server processes"""
        return {
            'wsl_mode': self.wsl_mode,
            'host_ip': self.host_ip,
            'current_display': os.environ.get('DISPLAY'),
            'managed_servers': {
                display: {
                    'pid': info['pid'],
                    'resolution': f"{info['width']}x{info['height']}"
                }
                for display, info in self.display_ports.items()
            },
            'active_processes': len(self.xserver_processes)
        }

    def test_display(self, display: str = None) -> Dict[str, Any]:
        """Test if display is working"""
        if not display:
            display = os.environ.get('DISPLAY', ':0')

        try:
            # Try to run xdpyinfo to test display
            result = subprocess.run(
                ['xdpyinfo', '-display', display],
                capture_output=True,
                timeout=SUBPROCESS_TIMEOUT_NORMAL
            )

            if result.returncode == 0:
                return {
                    'success': True,
                    'display': display,
                    'status': 'working',
                    'info': result.stdout.decode()[:200]  # First 200 chars
                }
            else:
                return {
                    'success': False,
                    'display': display,
                    'error': result.stderr.decode()
                }
        except Exception as e:
            return {
                'success': False,
                'display': display,
                'error': str(e)
            }

    def setup_wsl_forwarding(self) -> Dict[str, Any]:
        """Setup WSL2 X11 forwarding"""
        if not self.wsl_mode:
            return {
                'success': False,
                'error': 'Not in WSL mode'
            }

        try:
            # Set DISPLAY to point to Windows host
            display = f"{self.host_ip}:0.0"
            os.environ['DISPLAY'] = display

            # Test the connection
            test_result = self.test_display(display)

            return {
                'success': test_result['success'],
                'display': display,
                'host_ip': self.host_ip,
                'message': (
                    'WSL2 X11 forwarding configured'
                    if test_result['success']
                    else 'Failed to connect to Windows X server'
                )
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def stop_virtual_display(self, display: str = None) -> Dict[str, Any]:
        """Stop virtual display (alias for stop_xserver)"""
        return self.stop_xserver(display)

    def cleanup_all_servers(self) -> Dict[str, Any]:
        """Cleanup all servers (alias for cleanup_all)"""
        return self.cleanup_all()
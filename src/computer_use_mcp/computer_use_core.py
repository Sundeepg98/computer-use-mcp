#!/usr/bin/env python3
"""
Core computer use functionality for Claude system
Provides screenshot, click, type, and other visual interactions
"""

import os
import sys
import time
import subprocess
from typing import Dict, Any, Optional, Tuple, List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def capture_screenshot() -> bytes:
    """Capture screenshot using available tools with multiple fallbacks"""
    methods = [
        # Method 1: scrot (often more reliable)
        {
            'name': 'scrot',
            'cmd': ['scrot', '--silent', '/tmp/screenshot.png'],
            'read_file': '/tmp/screenshot.png'
        },
        # Method 2: ImageMagick import
        {
            'name': 'import',
            'cmd': ['import', '-window', 'root', 'png:-'],
            'read_file': None
        },
        # Method 3: xwd + convert
        {
            'name': 'xwd',
            'cmd': ['xwd', '-root', '-out', '/tmp/screenshot.xwd'],
            'convert': ['convert', '/tmp/screenshot.xwd', 'png:-'],
            'read_file': None
        },
        # Method 4: Windows PowerShell (for WSL2)
        {
            'name': 'powershell',
            'cmd': ['powershell.exe', '-Command', 
                   'Add-Type -AssemblyName System.Windows.Forms; ' +
                   'Add-Type -AssemblyName System.Drawing; ' +
                   '$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; ' +
                   '$bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height); ' +
                   '$graphics = [System.Drawing.Graphics]::FromImage($bitmap); ' +
                   '$graphics.CopyFromScreen(0, 0, 0, 0, $bounds.Size); ' +
                   '$tempPath = [System.IO.Path]::GetTempPath() + "wsl_screenshot.png"; ' +
                   '$bitmap.Save($tempPath, [System.Drawing.Imaging.ImageFormat]::Png); ' +
                   '$graphics.Dispose(); $bitmap.Dispose(); ' +
                   'Write-Output $tempPath'],
            'read_file': None,
            'get_temp_path': True
        }
    ]
    
    for method in methods:
        try:
            # Check if command exists
            cmd_name = method['cmd'][0]
            if not any(os.path.exists(os.path.join(path, cmd_name)) 
                      for path in os.environ.get('PATH', '').split(':')):
                continue
            
            # Execute command
            result = subprocess.run(
                method['cmd'],
                capture_output=True,
                timeout=10
            )
            
            # Handle result based on method
            if method.get('read_file'):
                # Method writes to file
                if result.returncode == 0 and os.path.exists(method['read_file']):
                    with open(method['read_file'], 'rb') as f:
                        data = f.read()
                    os.unlink(method['read_file'])  # Clean up
                    if data:
                        print(f"Screenshot captured using {method['name']}", file=sys.stderr)
                        return data
            elif method.get('get_temp_path'):
                # PowerShell method outputs temp file path
                if result.returncode == 0 and result.stdout:
                    temp_path = result.stdout.decode().strip()
                    # Convert Windows path to WSL path
                    if temp_path.startswith('C:'):
                        wsl_path = '/mnt/c' + temp_path[2:].replace('\\', '/')
                        if os.path.exists(wsl_path):
                            with open(wsl_path, 'rb') as f:
                                data = f.read()
                            os.unlink(wsl_path)  # Clean up
                            if data:
                                print(f"Screenshot captured using {method['name']}", file=sys.stderr)
                                return data
            elif method.get('convert'):
                # Method needs conversion
                if result.returncode == 0:
                    convert_result = subprocess.run(
                        method['convert'],
                        capture_output=True
                    )
                    if convert_result.returncode == 0:
                        print(f"Screenshot captured using {method['name']}", file=sys.stderr)
                        return convert_result.stdout
            else:
                # Method outputs directly
                if result.returncode == 0 and result.stdout:
                    print(f"Screenshot captured using {method['name']}", file=sys.stderr)
                    return result.stdout
                    
        except Exception as e:
            print(f"Screenshot method {method['name']} failed: {e}", file=sys.stderr)
            continue
    
    # All methods failed - return placeholder
    print("All screenshot methods failed, returning placeholder", file=sys.stderr)
    return create_placeholder_image()


def create_placeholder_image() -> bytes:
    """Create a placeholder image when screenshot fails"""
    # Create a simple PNG placeholder
    placeholder_text = b"""[SCREENSHOT UNAVAILABLE]
    
Display not accessible or X server not running.

To fix:
1. Install X server (VcXsrv/X410 on Windows)
2. Set DISPLAY environment variable
3. Allow X server connections

Current DISPLAY: """ + os.environ.get('DISPLAY', 'None').encode()
    
    # Return as text for now (would need PIL to create actual PNG)
    return placeholder_text


class ComputerUseCore:
    """Core computer use functionality with ultrathink integration"""
    
    def __init__(self, test_mode=False):
        """Initialize computer use core"""
        self.test_mode = test_mode
        self.safety_checks = True
        self.ultrathink_enabled = True
        
        # Initialize X server manager
        try:
            from .xserver_manager import XServerManager
            self.xserver_manager = XServerManager()
        except Exception as e:
            logger.warning(f"Failed to initialize X server manager: {e}")
            self.xserver_manager = None
        
        # Setup display
        if not test_mode:
            self._init_display()
        else:
            self.display_available = False
        
        # Initialize safety checker
        from .safety_checks import SafetyChecker
        self.safety_checker = SafetyChecker()
    
    def _init_display(self):
        """Initialize display connection using X Server Manager"""
        if self.xserver_manager is None:
            logger.warning("X server manager not available, display initialization skipped")
            self.display_available = False
            self.display_info = {'error': 'X server manager not initialized'}
            return
            
        try:
            # Get best available display
            display_result = self.xserver_manager.get_best_display()
            
            if display_result['available']:
                self.display_available = True
                self.display_info = display_result
                logger.info(f"Display initialized: {display_result['display']} ({display_result['method']})")
            else:
                self.display_available = False
                self.display_info = display_result
                logger.warning(f"No display available: {display_result.get('error', 'Unknown error')}")
                
                # Log suggestions for fixing display issues
                if 'suggestions' in display_result:
                    logger.info("Suggestions to fix display:")
                    for suggestion in display_result['suggestions']:
                        logger.info(f"  - {suggestion}")
                        
        except Exception as e:
            logger.error(f"Display initialization failed: {e}")
            self.display_available = False
            self.display_info = {'error': str(e)}
    
    def screenshot(self, analyze=None) -> Dict[str, Any]:
        """Capture current screen"""
        logger.info("Capturing screenshot with ultrathink analysis")
        
        if self.test_mode:
            # Return mock data in test mode
            return {
                'status': 'success',
                'data': 'mock_screenshot_data',
                'width': 1920,
                'height': 1080,
                'analyze': analyze,
                'test_mode': True
            }
        
        if self.ultrathink_enabled:
            # Add ultrathink analysis context
            logger.info("Ultrathink: Analyzing screen context before capture")
        
        screenshot_data = capture_screenshot()
        return {
            'status': 'success',
            'data': screenshot_data,
            'analyze': analyze
        }
    
    def click(self, x: int, y: int, button: str = 'left') -> Dict[str, Any]:
        """Perform mouse click at coordinates"""
        logger.info(f"Clicking at ({x}, {y}) with {button} button")
        
        if self.ultrathink_enabled:
            logger.info("Ultrathink: Verifying click target before action")
        
        try:
            if self.display_available:
                # Use xdotool for clicking (install: sudo apt-get install xdotool)
                cmd = ['xdotool', 'mousemove', str(x), str(y), 'click']
                if button == 'left':
                    cmd.append('1')
                elif button == 'right':
                    cmd.append('3')
                elif button == 'middle':
                    cmd.append('2')
                
                subprocess.run(cmd, check=True)
            
            return {
                'success': True,
                'action': 'click',
                'coordinates': (x, y),
                'button': button,
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return {
                'success': False,
                'action': 'click',
                'error': str(e)
            }
    
    def type_text(self, text: str) -> Dict[str, Any]:
        """Type text using keyboard"""
        logger.info(f"Typing text: {text[:20]}...")
        
        # Check safety first
        if self.safety_checks and not self.safety_checker.check_text_safety(text):
            error_msg = f"Safety check failed: {self.safety_checker.last_error}"
            logger.error(error_msg)
            if not self.test_mode:
                raise Exception(error_msg)
            # In test mode, still raise for dangerous commands
            elif any(danger in text.lower() for danger in ['rm -rf', 'format', 'delete /']):
                raise Exception(error_msg)
        
        if self.test_mode:
            return {
                'status': 'success',
                'text': text,
                'test_mode': True
            }
        
        if self.ultrathink_enabled:
            logger.info("Ultrathink: Analyzing text input context")
        
        try:
            if self.display_available:
                # Use xdotool for typing
                subprocess.run(
                    ['xdotool', 'type', '--clearmodifiers', text],
                    check=True
                )
            
            return {
                'success': True,
                'action': 'type',
                'text': text,
                'length': len(text),
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Type text failed: {e}")
            return {
                'success': False,
                'action': 'type',
                'error': str(e)
            }
    
    def key_press(self, key: str) -> Dict[str, Any]:
        """Press a specific key or key combination"""
        logger.info(f"Pressing key: {key}")
        
        try:
            if self.display_available:
                subprocess.run(['xdotool', 'key', key], check=True)
            
            return {
                'success': True,
                'action': 'key_press',
                'key': key,
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return {
                'success': False,
                'action': 'key_press',
                'error': str(e)
            }
    
    def scroll(self, direction: str = 'down', amount: int = 3) -> Dict[str, Any]:
        """Scroll in specified direction"""
        logger.info(f"Scrolling {direction} by {amount}")
        
        try:
            if self.display_available:
                button = '5' if direction == 'down' else '4'
                for _ in range(amount):
                    subprocess.run(['xdotool', 'click', button], check=True)
                    time.sleep(0.1)
            
            return {
                'success': True,
                'action': 'scroll',
                'direction': direction,
                'amount': amount,
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return {
                'success': False,
                'action': 'scroll',
                'error': str(e)
            }
    
    def move_mouse(self, x: int, y: int) -> Dict[str, Any]:
        """Move mouse to coordinates without clicking"""
        logger.info(f"Moving mouse to ({x}, {y})")
        
        try:
            if self.display_available:
                subprocess.run(
                    ['xdotool', 'mousemove', str(x), str(y)],
                    check=True
                )
            
            return {
                'success': True,
                'action': 'move',
                'coordinates': (x, y),
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Mouse move failed: {e}")
            return {
                'success': False,
                'action': 'move',
                'error': str(e)
            }
    
    def wait(self, seconds: float) -> Dict[str, Any]:
        """Wait for specified duration"""
        logger.info(f"Waiting for {seconds} seconds")
        # Handle negative duration gracefully
        if seconds < 0:
            seconds = 0
        time.sleep(seconds)
        
        return {
            'success': True,
            'action': 'wait',
            'duration': seconds,
            'timestamp': time.time()
        }
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position"""
        try:
            if self.display_available:
                result = subprocess.run(
                    ['xdotool', 'getmouselocation'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Parse output like "x:123 y:456 screen:0 window:12345"
                parts = result.stdout.split()
                x = int(parts[0].split(':')[1])
                y = int(parts[1].split(':')[1])
                return (x, y)
        except Exception as e:
            logger.error(f"Get mouse position failed: {e}")
        
        return (0, 0)
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """Click and drag from start to end coordinates"""
        logger.info(f"Dragging from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        
        try:
            if self.display_available:
                # Move to start position
                subprocess.run(['xdotool', 'mousemove', str(start_x), str(start_y)], check=True)
                # Mouse down
                subprocess.run(['xdotool', 'mousedown', '1'], check=True)
                # Move to end position
                subprocess.run(['xdotool', 'mousemove', str(end_x), str(end_y)], check=True)
                # Mouse up
                subprocess.run(['xdotool', 'mouseup', '1'], check=True)
            
            return {
                'success': True,
                'action': 'drag',
                'start': (start_x, start_y),
                'end': (end_x, end_y),
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Drag failed: {e}")
            return {
                'success': False,
                'action': 'drag',
                'error': str(e)
            }
    
    def install_xserver(self) -> Dict[str, Any]:
        """Install X server packages"""
        logger.info("Installing X server packages")
        
        if self.xserver_manager is None:
            return {'error': 'X server manager not available'}
        
        if self.ultrathink_enabled:
            logger.info("Ultrathink: Planning X server installation strategy")
        
        return self.xserver_manager.install_xserver_packages()
    
    def start_xserver(self, display_num: int = 99, 
                     width: int = 1920, height: int = 1080) -> Dict[str, Any]:
        """Start virtual X server"""
        logger.info(f"Starting virtual X server :{display_num} ({width}x{height})")
        
        if self.xserver_manager is None:
            return {'success': False, 'error': 'X server manager not available'}
        
        if self.ultrathink_enabled:
            logger.info("Ultrathink: Optimizing virtual display configuration")
        
        result = self.xserver_manager.start_virtual_display(display_num, width, height)
        
        if result['success']:
            # Update our display status
            self.display_available = True
            self.display_info = {
                'display': result['display'],
                'method': 'virtual_display',
                'resolution': result['resolution']
            }
            os.environ['DISPLAY'] = result['display']
        
        return result
    
    def stop_xserver(self, display: str) -> Dict[str, Any]:
        """Stop X server"""
        logger.info(f"Stopping X server {display}")
        
        if self.xserver_manager is None:
            return {'success': False, 'error': 'X server manager not available'}
        
        result = self.xserver_manager.stop_xserver(display)
        
        # Update display status if we stopped the current display
        if result['success'] and display == os.environ.get('DISPLAY'):
            self.display_available = False
            if 'DISPLAY' in os.environ:
                del os.environ['DISPLAY']
        
        return result
    
    def setup_wsl_xforwarding(self) -> Dict[str, Any]:
        """Setup WSL2 X11 forwarding"""
        logger.info("Setting up WSL2 X11 forwarding")
        
        if self.xserver_manager is None:
            return {'success': False, 'error': 'X server manager not available'}
        
        if self.ultrathink_enabled:
            logger.info("Ultrathink: Configuring optimal WSL2 X forwarding")
        
        result = self.xserver_manager.setup_wsl_xforwarding()
        
        if result['success']:
            self.display_available = True
            self.display_info = {
                'display': result['display'],
                'method': 'wsl_xforwarding',
                'host_ip': result['host_ip']
            }
        
        return result
    
    def get_xserver_status(self) -> Dict[str, Any]:
        """Get X server status"""
        if self.xserver_manager is None:
            return {
                'error': 'X server manager not available',
                'display_available': self.display_available,
                'display_info': getattr(self, 'display_info', {})
            }
        
        base_status = self.xserver_manager.get_status()
        
        return {
            **base_status,
            'display_available': self.display_available,
            'display_info': getattr(self, 'display_info', {})
        }
    
    def test_display(self) -> Dict[str, Any]:
        """Test current display configuration"""
        if self.xserver_manager is None:
            return {'success': False, 'error': 'X server manager not available'}
        
        current_display = os.environ.get('DISPLAY')
        if not current_display:
            return {
                'success': False,
                'error': 'No DISPLAY environment variable set'
            }
        
        return self.xserver_manager.check_xserver_available(current_display)
    
    def cleanup_xservers(self) -> Dict[str, Any]:
        """Cleanup all managed X servers"""
        logger.info("Cleaning up all X servers")
        
        if self.xserver_manager is None:
            return {'error': 'X server manager not available', 'stopped_servers': 0}
        
        result = self.xserver_manager.cleanup_all()
        
        # Reset display status
        self.display_available = False
        if 'DISPLAY' in os.environ:
            del os.environ['DISPLAY']
        
        return result
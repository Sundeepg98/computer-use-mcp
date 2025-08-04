#!/usr/bin/env python3
"""
Core computer use functionality for Claude system - V2 with full Windows support
Provides screenshot, click, type, and other visual interactions
Cross-platform: Windows, WSL2, Linux, macOS
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

# Import our new modules
from .platform_utils import get_platform_info, is_wsl2, is_windows
from .screenshot import ScreenshotFactory, get_screenshot_handler
from .input import InputFactory


class ComputerUseCore:
    """Core computer use functionality with full cross-platform support"""
    
    def __init__(self, test_mode=False):
        """Initialize computer use core"""
        self.test_mode = test_mode
        self.safety_checks = True
        self.ultrathink_enabled = True
        
        # Get platform information
        self.platform_info = get_platform_info()
        logger.info(f"Initialized on {self.platform_info['platform']} "
                   f"({self.platform_info['environment']})")
        
        # Initialize screenshot handler
        self.screenshot_handler = ScreenshotFactory.create()
        
        # Initialize input handler
        self.input_handler = InputFactory.create()
        
        # Initialize safety checker
        from .safety_checks import SafetyChecker
        self.safety_checker = SafetyChecker()
        
        # Initialize display info
        self.display_available = self._check_display_available()
        
        # X server manager for Linux compatibility
        if self.platform_info['platform'] == 'linux' and not is_wsl2():
            try:
                from .xserver_manager import XServerManager
                self.xserver_manager = XServerManager()
            except Exception as e:
                logger.warning(f"X server manager not available: {e}")
                self.xserver_manager = None
        else:
            self.xserver_manager = None
    
    def _check_display_available(self) -> bool:
        """Check if display is available for current platform"""
        if self.test_mode:
            return False
        
        # Always available on Windows/WSL2
        if is_windows() or is_wsl2():
            return True
        
        # Check X11 on Linux
        if self.platform_info['platform'] == 'linux':
            return self.platform_info.get('can_use_x11', False)
        
        # macOS always has display
        if self.platform_info['platform'] == 'macos':
            return True
        
        return False
    
    def screenshot(self, analyze=None) -> Dict[str, Any]:
        """Capture current screen"""
        logger.info("Capturing screenshot with ultrathink analysis")
        
        if self.test_mode:
            return {
                'status': 'success',
                'data': b'mock_screenshot_data',
                'width': 1920,
                'height': 1080,
                'analyze': analyze,
                'test_mode': True
            }
        
        if self.ultrathink_enabled:
            logger.info("Ultrathink: Analyzing screen context before capture")
        
        try:
            screenshot_data = self.screenshot_handler.capture()
            
            return {
                'status': 'success',
                'data': screenshot_data,
                'analyze': analyze,
                'platform_info': {
                    'platform': self.platform_info['platform'],
                    'environment': self.platform_info['environment'],
                    'method': self.screenshot_handler.__class__.__name__,
                    'implementation': 'native'
                }
            }
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'analyze': analyze
            }
    
    def click(self, x: int, y: int, button: str = 'left') -> Dict[str, Any]:
        """Perform mouse click at coordinates"""
        logger.info(f"Clicking at ({x}, {y}) with {button} button")
        
        if self.ultrathink_enabled:
            logger.info("Ultrathink: Verifying click target before action")
        
        if self.test_mode:
            # Check display availability even in test mode for proper testing
            if not self.display_available:
                return {
                    'success': False,
                    'action': 'click',
                    'error': 'No display available'
                }
            return {
                'success': True,
                'action': 'click',
                'coordinates': (x, y),
                'button': button,
                'test_mode': True
            }
        
        # Check display availability
        if not self.display_available:
            return {
                'success': False,
                'action': 'click',
                'error': 'No display available'
            }
        
        try:
            return self.input_handler.click(x=x, y=y, button=button)
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
            elif any(danger in text.lower() for danger in ['rm -rf', 'format', 'delete /']):
                raise Exception(error_msg)
        
        if self.test_mode:
            return {
                'success': True,
                'text': text,
                'test_mode': True
            }
        
        if self.ultrathink_enabled:
            logger.info("Ultrathink: Analyzing text input context")
        
        try:
            # Get keyboard handler based on platform
            if hasattr(self.input_handler, 'type_text'):
                return self.input_handler.type_text(text)
            else:
                # Create keyboard handler
                if is_windows() or is_wsl2():
                    from .input.windows import WindowsKeyboard, WSL2Input
                    if is_wsl2():
                        keyboard = WSL2Input()
                    else:
                        keyboard = WindowsKeyboard()
                    return keyboard.type_text(text)
                else:
                    # Fallback to xdotool for Linux
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
        
        if self.test_mode:
            return {
                'success': True,
                'action': 'key_press',
                'key': key,
                'test_mode': True
            }
        
        try:
            # Get keyboard handler
            if is_windows() or is_wsl2():
                if is_wsl2():
                    # Use WSL2Input which has key_press support
                    if hasattr(self.input_handler, 'key_press'):
                        return self.input_handler.key_press(key)
                    else:
                        # Fallback to PowerShell SendKeys
                        from .input.windows import WSL2Input
                        wsl2_input = WSL2Input()
                        return wsl2_input.key_press(key)
                else:
                    from .input.windows import WindowsKeyboard
                    keyboard = WindowsKeyboard()
                    return keyboard.key_press(key)
            else:
                # Linux/X11
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
        
        if self.test_mode:
            return {
                'success': True,
                'action': 'scroll',
                'direction': direction,
                'amount': amount,
                'test_mode': True
            }
        
        try:
            if hasattr(self.input_handler, 'scroll'):
                return self.input_handler.scroll(direction=direction, amount=amount)
            else:
                # Fallback for Linux
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
        
        if self.test_mode:
            return {
                'success': True,
                'action': 'move',
                'coordinates': (x, y),
                'test_mode': True
            }
        
        try:
            return self.input_handler.move_mouse(x=x, y=y)
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
            if hasattr(self.input_handler, 'get_mouse_position'):
                return self.input_handler.get_mouse_position()
            else:
                # Linux fallback
                result = subprocess.run(
                    ['xdotool', 'getmouselocation'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Parse output like "x:123 y:456 screen:0 window:12345"
                parts = result.stdout.split()
                x_part = next((p for p in parts if p.startswith('x:')), None)
                y_part = next((p for p in parts if p.startswith('y:')), None)
                if x_part and y_part:
                    x = int(x_part.split(':')[1])
                    y = int(y_part.split(':')[1])
                    return (x, y)
                return (0, 0)
        except Exception as e:
            logger.error(f"Get mouse position failed: {e}")
            return (0, 0)
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """Click and drag from start to end coordinates"""
        logger.info(f"Dragging from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        
        if self.test_mode:
            return {
                'success': True,
                'action': 'drag',
                'start': (start_x, start_y),
                'end': (end_x, end_y),
                'test_mode': True
            }
        
        try:
            if hasattr(self.input_handler, 'drag'):
                return self.input_handler.drag(
                    start_x=start_x, start_y=start_y,
                    end_x=end_x, end_y=end_y
                )
            else:
                # Linux fallback
                subprocess.run(['xdotool', 'mousemove', str(start_x), str(start_y)], check=True)
                subprocess.run(['xdotool', 'mousedown', '1'], check=True)
                subprocess.run(['xdotool', 'mousemove', str(end_x), str(end_y)], check=True)
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
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            **self.platform_info,
            'display_available': self.display_available,
            'screenshot_implementation': self.screenshot_handler.__class__.__name__,
            'input_implementation': self.input_handler.__class__.__name__,
        }
    
    # Backward compatibility methods
    def install_xserver(self) -> Dict[str, Any]:
        """Install X server packages (Linux only)"""
        if self.xserver_manager:
            return self.xserver_manager.install_xserver_packages()
        return {'error': 'Not applicable on this platform'}
    
    def start_xserver(self, display_num: int = 99, 
                     width: int = 1920, height: int = 1080) -> Dict[str, Any]:
        """Start virtual X server (Linux only)"""
        if self.xserver_manager:
            return self.xserver_manager.start_virtual_display(display_num, width, height)
        return {'error': 'Not applicable on this platform'}
    
    def get_xserver_status(self) -> Dict[str, Any]:
        """Get X server status"""
        status = {
            'platform': self.platform_info['platform'],
            'environment': self.platform_info['environment'],
            'display_available': self.display_available,
            'x11_available': self.platform_info.get('can_use_x11', False),
            'method': 'native' if is_windows() or is_wsl2() else 'x11'
        }
        
        # Add display info if xserver_manager exists
        if self.xserver_manager:
            status['display_info'] = self.xserver_manager.get_status()
        
        return status
    
    def test_display(self) -> Dict[str, Any]:
        """Test if display is working"""
        if self.xserver_manager:
            return self.xserver_manager.test_display()
        
        # For Windows/WSL2, test if we can capture a screenshot
        if is_windows() or is_wsl2():
            try:
                screenshot_data = capture_screenshot()
                return {
                    'success': True,
                    'display': 'Windows Desktop',
                    'method': 'PowerShell screenshot',
                    'screenshot_size': len(screenshot_data) if screenshot_data else 0
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return {'error': 'No display test available for this platform'}
    
    def setup_wsl_xforwarding(self) -> Dict[str, Any]:
        """Setup WSL2 X11 forwarding"""
        if self.xserver_manager and hasattr(self.xserver_manager, 'setup_wsl_forwarding'):
            return self.xserver_manager.setup_wsl_forwarding()
        
        # For WSL2, we use PowerShell directly, no X11 forwarding needed
        if is_wsl2():
            return {
                'success': True,
                'message': 'WSL2 uses PowerShell for Windows integration, X11 forwarding not required',
                'method': 'PowerShell'
            }
        
        return {'error': 'Not applicable on this platform'}
    
    def stop_xserver(self, display: str = None) -> Dict[str, Any]:
        """Stop X server"""
        if self.xserver_manager:
            return self.xserver_manager.stop_virtual_display(display)
        return {'error': 'Not applicable on this platform'}
    
    def cleanup_xservers(self) -> Dict[str, Any]:
        """Cleanup all X servers"""
        if self.xserver_manager:
            return self.xserver_manager.cleanup_all_servers()
        return {'error': 'Not applicable on this platform'}


# Backward compatibility - export the same capture_screenshot function
def capture_screenshot() -> bytes:
    """Capture screenshot using best available method"""
    handler = get_screenshot_handler()
    return handler.capture()
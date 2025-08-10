"""
Streamlined Computer Use Core - Clean DI without bloat
"""

import time
from typing import Dict, Any, Optional
import logging

from ..abstractions import (
    ScreenshotProvider,
    InputProvider,
    PlatformInfo,
    DisplayManager
)
from .safety import get_safety_checker

logger = logging.getLogger(__name__)


class ComputerUse:
    """
    Streamlined Computer Use with dependency injection
    No test_mode, no bloat, just clean functionality
    """
    
    def __init__(
        self,
        screenshot_provider: ScreenshotProvider,
        input_provider: InputProvider,
        platform_info: PlatformInfo,
        display_manager: DisplayManager,
    ):
        """Initialize with injected dependencies"""
        self.screenshot = screenshot_provider
        self.input = input_provider
        self.platform = platform_info
        self.display = display_manager
        self.safety = get_safety_checker()  # Use singleton
        
        # Compatibility
        self.display_available = self.display.is_display_available()
        
        logger.info(f"Initialized on {self.platform.get_platform()}")
    
    def take_screenshot(self) -> Dict[str, Any]:
        """Take a screenshot"""
        try:
            # Debug: Log display check
            display_available = self.display.is_display_available()
            logger.info(f"Display check: available={display_available}")
            
            if not display_available:
                logger.warning("Display not available for screenshot")
                return {
                    'success': False,
                    'error': 'No display available',
                    'platform': self.platform.get_platform()
                }
            
            logger.info("Attempting screenshot capture...")
            screenshot_data = self.screenshot.capture()
            
            # Debug: Check data
            if screenshot_data:
                logger.info(f"Screenshot captured: {len(screenshot_data)} bytes")
            else:
                logger.warning("Screenshot capture returned no data")
            
            return {
                'success': True,
                'data': screenshot_data,
                'platform': self.platform.get_platform(),
                'method': self.screenshot.__class__.__name__
            }
            
        except Exception as e:
            logger.error(f"Screenshot failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'platform': self.platform.get_platform()
            }
    
    def click(self, x: int, y: int, button: str = 'left') -> Dict[str, Any]:
        """Perform a mouse click"""
        try:
            # Validate coordinates
            if not isinstance(x, int) or not isinstance(y, int):
                return {
                    'success': False,
                    'error': 'Coordinates must be integers'
                }
            
            # Safety check
            is_safe, error = self.safety.validate_action('click', {
                'x': x, 'y': y, 'button': button
            })
            if not is_safe:
                return {
                    'success': False,
                    'error': f'Safety check failed: {error}'
                }
            
            if not self.display.is_display_available():
                return {
                    'success': False,
                    'error': 'No display available'
                }
            
            # Perform click
            success = self.input.click(x, y, button)
            
            return {
                'success': success,
                'action': 'click',
                'coordinates': (x, y),
                'button': button
            }
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def type_text(self, text: str) -> Dict[str, Any]:
        """Type text"""
        try:
            # Safety check
            is_safe, error = self.safety.validate_text(text)
            if not is_safe:
                return {
                    'success': False,
                    'error': f'Safety check failed: {error}'
                }
            
            if not self.display.is_display_available():
                return {
                    'success': False,
                    'error': 'No display available'
                }
            
            success = self.input.type_text(text)
            
            return {
                'success': success,
                'action': 'type',
                'text_length': len(text)
            }
            
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def key_press(self, key: str) -> Dict[str, Any]:
        """Press a key or key combination"""
        try:
            # Safety check
            is_safe, error = self.safety.validate_action('key', {'key': key})
            if not is_safe:
                return {
                    'success': False,
                    'error': f'Safety check failed: {error}'
                }
            
            if not self.display.is_display_available():
                return {
                    'success': False,
                    'error': 'No display available'
                }
            
            success = self.input.key_press(key)
            
            return {
                'success': success,
                'action': 'key',
                'key': key
            }
            
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def scroll(self, direction: str = 'down', amount: int = 3) -> Dict[str, Any]:
        """Scroll in a direction"""
        try:
            if direction not in ['up', 'down']:
                return {
                    'success': False,
                    'error': f'Invalid direction: {direction}'
                }
            
            if not self.display.is_display_available():
                return {
                    'success': False,
                    'error': 'No display available'
                }
            
            success = self.input.scroll(direction, amount)
            
            return {
                'success': success,
                'action': 'scroll',
                'direction': direction,
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """Drag from one point to another"""
        try:
            # Validate all coordinates
            coords = [start_x, start_y, end_x, end_y]
            if not all(isinstance(c, int) for c in coords):
                return {
                    'success': False,
                    'error': 'All coordinates must be integers'
                }
            
            if not self.display.is_display_available():
                return {
                    'success': False,
                    'error': 'No display available'
                }
            
            success = self.input.drag(start_x, start_y, end_x, end_y)
            
            return {
                'success': success,
                'action': 'drag',
                'start': (start_x, start_y),
                'end': (end_x, end_y)
            }
            
        except Exception as e:
            logger.error(f"Drag failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def wait(self, seconds: float = 1.0) -> Dict[str, Any]:
        """Wait for specified seconds"""
        try:
            time.sleep(seconds)
            return {
                'success': True,
                'action': 'wait',
                'seconds': seconds
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
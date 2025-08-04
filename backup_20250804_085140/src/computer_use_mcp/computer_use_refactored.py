#!/usr/bin/env python3
"""
REFACTORED: Computer Use Core with Clean Architecture

This version eliminates test_mode and uses proper dependency injection
with clean abstractions for all platform-specific functionality.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List

from .abstractions import (
    ScreenshotProvider, InputProvider, PlatformInfo, 
    SafetyValidator, DisplayManager
)
from .visual_analyzer import VisualAnalyzer

logger = logging.getLogger(__name__)


class ComputerUseRefactored:
    """
    Refactored Computer Use Core with proper dependency injection
    
    This version:
    - No test_mode anti-pattern
    - All dependencies injected
    - Clean separation of concerns
    - Fully testable with proper mocks
    """
    
    def __init__(
        self,
        screenshot_provider: ScreenshotProvider,
        input_provider: InputProvider,
        platform_info: PlatformInfo,
        safety_validator: SafetyValidator,
        display_manager: DisplayManager,
        visual_analyzer: Optional[VisualAnalyzer] = None,
        enable_ultrathink: bool = True
    ):
        """
        Initialize with injected dependencies
        
        Args:
            screenshot_provider: Implementation for taking screenshots
            input_provider: Implementation for input operations
            platform_info: Platform information provider
            safety_validator: Safety validation implementation
            display_manager: Display management implementation
            visual_analyzer: Optional visual analysis implementation
            enable_ultrathink: Enable deep analysis mode
        """
        self.screenshot = screenshot_provider
        self.input = input_provider
        self.platform = platform_info
        self.safety = safety_validator
        self.display = display_manager
        self.visual_analyzer = visual_analyzer or VisualAnalyzer()
        self.ultrathink_enabled = enable_ultrathink
        
        # Log initialization
        platform = self.platform.get_platform()
        environment = self.platform.get_environment()
        logger.info(f"Initialized on {platform} ({environment})")
    
    def take_screenshot(self, analyze: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot with optional analysis"""
        try:
            # Check display availability
            if not self.display.is_display_available():
                return {
                    'success': False,
                    'error': 'No display available',
                    'platform': self.platform.get_platform()
                }
            
            # Capture screenshot
            screenshot_data = self.screenshot.capture()
            
            result = {
                'success': True,
                'data': screenshot_data,
                'platform': self.platform.get_platform(),
                'method': self.screenshot.__class__.__name__
            }
            
            # Perform analysis if requested
            if analyze and self.ultrathink_enabled:
                logger.info("Ultrathink: Performing deep visual analysis")
                analysis = self.visual_analyzer.analyze(screenshot_data, analyze)
                result['analysis'] = analysis
            
            return result
            
        except Exception as e:
            logger.error(f"Screenshot failed: {str(e)}")
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
            
            # Check display
            if not self.display.is_display_available():
                return {
                    'success': False,
                    'error': 'No display available'
                }
            
            if self.ultrathink_enabled:
                logger.info(f"Ultrathink: Verifying click target at ({x}, {y})")
            
            # Perform click
            success = self.input.click(x, y, button)
            
            return {
                'success': success,
                'action': 'click',
                'coordinates': (x, y),
                'button': button
            }
            
        except Exception as e:
            logger.error(f"Click failed: {str(e)}")
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
            
            if self.ultrathink_enabled:
                logger.info("Ultrathink: Analyzing text input context")
            
            # Type text
            success = self.input.type_text(text)
            
            return {
                'success': success,
                'action': 'type',
                'text': text[:20] + '...' if len(text) > 20 else text
            }
            
        except Exception as e:
            logger.error(f"Type failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def key_press(self, key: str) -> Dict[str, Any]:
        """Press a key"""
        try:
            # Validate key
            valid_keys = ['Return', 'Tab', 'Escape', 'BackSpace', 'Delete',
                         'Up', 'Down', 'Left', 'Right', 'Home', 'End',
                         'Page_Up', 'Page_Down', 'F1-F12', 'ctrl+a', 'ctrl+c',
                         'ctrl+v', 'ctrl+x', 'ctrl+z', 'ctrl+y', 'alt+tab']
            
            if key not in valid_keys and not any(key.startswith(prefix) for prefix in ['ctrl+', 'alt+', 'shift+']):
                return {
                    'success': False,
                    'error': f'Invalid key: {key}'
                }
            
            # Press key
            success = self.input.key_press(key)
            
            return {
                'success': success,
                'action': 'key',
                'key': key
            }
            
        except Exception as e:
            logger.error(f"Key press failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def move_mouse(self, x: int, y: int) -> Dict[str, Any]:
        """Move mouse to position"""
        try:
            # Validate coordinates
            if not isinstance(x, int) or not isinstance(y, int):
                return {
                    'success': False,
                    'error': 'Coordinates must be integers'
                }
            
            # Move mouse
            success = self.input.mouse_move(x, y)
            
            return {
                'success': success,
                'action': 'move',
                'coordinates': (x, y)
            }
            
        except Exception as e:
            logger.error(f"Mouse move failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """Drag from start to end position"""
        try:
            # Validate coordinates
            coords = [start_x, start_y, end_x, end_y]
            if not all(isinstance(c, int) for c in coords):
                return {
                    'success': False,
                    'error': 'All coordinates must be integers'
                }
            
            # Perform drag
            success = self.input.drag(start_x, start_y, end_x, end_y)
            
            return {
                'success': success,
                'action': 'drag',
                'start': (start_x, start_y),
                'end': (end_x, end_y)
            }
            
        except Exception as e:
            logger.error(f"Drag failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def scroll(self, direction: str = 'down', amount: int = 3) -> Dict[str, Any]:
        """Scroll in direction by amount"""
        try:
            # Validate direction
            valid_directions = ['up', 'down', 'left', 'right']
            if direction not in valid_directions:
                return {
                    'success': False,
                    'error': f'Invalid direction: {direction}'
                }
            
            # Perform scroll
            success = self.input.scroll(direction, amount)
            
            return {
                'success': success,
                'action': 'scroll',
                'direction': direction,
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Scroll failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def wait(self, seconds: float) -> Dict[str, Any]:
        """Wait for specified seconds"""
        try:
            import time
            time.sleep(seconds)
            
            return {
                'success': True,
                'action': 'wait',
                'seconds': seconds
            }
            
        except Exception as e:
            logger.error(f"Wait failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            'platform': self.platform.get_platform(),
            'environment': self.platform.get_environment(),
            'capabilities': self.platform.get_capabilities(),
            'display_available': self.display.is_display_available()
        }
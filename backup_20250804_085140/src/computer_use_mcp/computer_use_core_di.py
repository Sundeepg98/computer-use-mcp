#!/usr/bin/env python3
"""
REFACTORED: Core computer use functionality with Dependency Injection

This version removes test_mode and uses proper dependency injection,
allowing for real unit testing of all code paths.
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
from .safety_checks import SafetyChecker


class ComputerUseCoreWithDI:
    """
    Core computer use functionality with Dependency Injection
    
    This version allows injecting all dependencies, making it properly testable
    without the test_mode anti-pattern.
    """
    
    def __init__(
        self,
        screenshot_handler=None,
        input_handler=None,
        safety_checker=None,
        platform_info_provider=None,
        display_checker=None,
        xserver_manager=None
    ):
        """
        Initialize with injectable dependencies
        
        Args:
            screenshot_handler: Handler for taking screenshots (default: auto-detect)
            input_handler: Handler for input operations (default: auto-detect)
            safety_checker: Safety validation (default: SafetyChecker)
            platform_info_provider: Platform detection (default: get_platform_info)
            display_checker: Display availability checker (default: internal)
            xserver_manager: X server manager for Linux (default: auto-detect)
        """
        # NO MORE test_mode! Use dependency injection instead
        
        # Platform information
        self.platform_info_provider = platform_info_provider or get_platform_info
        self.platform_info = self.platform_info_provider()
        logger.info(f"Initialized on {self.platform_info['platform']} "
                   f"({self.platform_info['environment']})")
        
        # Screenshot handler - injectable for testing
        self.screenshot_handler = screenshot_handler or ScreenshotFactory.create()
        
        # Input handler - injectable for testing
        self.input_handler = input_handler or InputFactory.create()
        
        # Safety checker - injectable for testing
        self.safety_checker = safety_checker or SafetyChecker()
        self.safety_checks = True  # Can be disabled if needed
        
        # Display checker - injectable for testing
        self.display_checker = display_checker or self._default_display_checker
        self.display_available = self.display_checker()
        
        # X server manager - injectable for testing
        if xserver_manager is not None:
            self.xserver_manager = xserver_manager
        else:
            self._initialize_xserver_manager()
        
        # Features
        self.ultrathink_enabled = True
    
    def _default_display_checker(self) -> bool:
        """Default display availability checker"""
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
    
    def _initialize_xserver_manager(self):
        """Initialize X server manager if needed"""
        if self.platform_info['platform'] == 'linux' and not is_wsl2():
            try:
                from .xserver_manager import XServerManager
                self.xserver_manager = XServerManager()
            except Exception as e:
                logger.warning(f"X server manager not available: {e}")
                self.xserver_manager = None
        else:
            self.xserver_manager = None
    
    def screenshot(self, analyze=None) -> Dict[str, Any]:
        """
        Capture current screen
        
        NO MORE test_mode check! This always runs real logic.
        In tests, inject a mock screenshot_handler.
        """
        logger.info("Capturing screenshot with ultrathink analysis")
        
        if self.ultrathink_enabled:
            logger.info("Ultrathink: Analyzing screen context before capture")
        
        # Check display availability
        if not self.display_available:
            return {
                'status': 'error',
                'error': 'No display available',
                'suggestion': 'Start X server or use virtual display'
            }
        
        # Safety check
        if self.safety_checks and not self.safety_checker.is_safe('screenshot'):
            return {
                'status': 'error',
                'error': 'Operation blocked by safety check'
            }
        
        try:
            # Use injected handler - mockable in tests!
            screenshot_data = self.screenshot_handler.capture()
            
            result = {
                'status': 'success',
                'data': screenshot_data,
                'timestamp': time.time()
            }
            
            # Add metadata if available
            if hasattr(self.screenshot_handler, 'get_metadata'):
                result.update(self.screenshot_handler.get_metadata())
            
            # Analyze if requested
            if analyze and self.ultrathink_enabled:
                result['analysis'] = self._analyze_screenshot(screenshot_data, analyze)
            
            return result
            
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'suggestion': self._get_error_suggestion(e)
            }
    
    def click(self, x: int, y: int, button: str = 'left') -> Dict[str, Any]:
        """
        Click at coordinates
        
        Real logic always runs - inject mocks for testing
        """
        logger.info(f"Clicking at ({x}, {y}) with {button} button")
        
        # Validate coordinates
        if not self._validate_coordinates(x, y):
            return {
                'status': 'error',
                'error': f'Invalid coordinates: ({x}, {y})'
            }
        
        # Check display
        if not self.display_available:
            return {
                'status': 'error',
                'error': 'No display available for click operation'
            }
        
        # Safety check
        action = f"click at ({x}, {y}) with {button} button"
        if self.safety_checks and not self.safety_checker.is_safe(action):
            return {
                'status': 'error',
                'error': 'Click blocked by safety check'
            }
        
        try:
            # Use injected handler
            self.input_handler.click(x, y, button)
            
            return {
                'status': 'success',
                'coordinates': {'x': x, 'y': y},
                'button': button,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def type_text(self, text: str) -> Dict[str, Any]:
        """
        Type text
        
        Real logic always runs - inject mocks for testing
        """
        logger.info(f"Typing text: {text[:50]}...")
        
        # Check display
        if not self.display_available:
            return {
                'status': 'error',
                'error': 'No display available for typing'
            }
        
        # Safety check
        if self.safety_checks and not self.safety_checker.check_text_safety(text):
            return {
                'status': 'error',
                'error': 'Text blocked by safety check',
                'reason': 'Contains potentially dangerous content'
            }
        
        try:
            # Use injected handler
            self.input_handler.type_text(text)
            
            return {
                'status': 'success',
                'text_length': len(text),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Type text failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _validate_coordinates(self, x: int, y: int) -> bool:
        """Validate coordinates are reasonable"""
        if x < 0 or y < 0:
            return False
        
        # Check against reasonable maximums
        if x > 10000 or y > 10000:
            return False
        
        return True
    
    def _analyze_screenshot(self, data: bytes, analyze_request: str) -> Dict[str, Any]:
        """Analyze screenshot data based on request"""
        # This would integrate with vision analysis
        return {
            'request': analyze_request,
            'status': 'analysis_complete',
            'findings': 'Screenshot analysis would go here'
        }
    
    def _get_error_suggestion(self, error: Exception) -> str:
        """Get helpful suggestion for error"""
        error_str = str(error).lower()
        
        if 'display' in error_str:
            return 'Try starting X server or using virtual display'
        elif 'permission' in error_str:
            return 'Check file permissions and user access'
        elif 'not found' in error_str:
            return 'Ensure required tools are installed'
        else:
            return 'Check system logs for more details'


# Example factory for easy migration
class ComputerUseCoreFactory:
    """Factory to create ComputerUseCore instances"""
    
    @staticmethod
    def create_production():
        """Create production instance with real dependencies"""
        return ComputerUseCoreWithDI()
    
    @staticmethod
    def create_for_testing(
        screenshot_handler=None,
        input_handler=None,
        safety_checker=None
    ):
        """Create test instance with mock dependencies"""
        return ComputerUseCoreWithDI(
            screenshot_handler=screenshot_handler,
            input_handler=input_handler,
            safety_checker=safety_checker
        )


# Migration helper
def migrate_from_test_mode(old_core):
    """
    Helper to migrate from old test_mode core to new DI core
    
    Usage:
        old_core = ComputerUseCore(test_mode=True)
        new_core = migrate_from_test_mode(old_core)
    """
    if hasattr(old_core, 'test_mode') and old_core.test_mode:
        # Create mock handlers for test mode behavior
        from unittest.mock import Mock
        
        mock_screenshot = Mock()
        mock_screenshot.capture.return_value = b'mock_screenshot_data'
        
        mock_input = Mock()
        mock_safety = Mock()
        mock_safety.is_safe.return_value = True
        mock_safety.check_text_safety.return_value = True
        
        return ComputerUseCoreWithDI(
            screenshot_handler=mock_screenshot,
            input_handler=mock_input,
            safety_checker=mock_safety
        )
    else:
        # Production migration - use real handlers
        return ComputerUseCoreWithDI(
            screenshot_handler=old_core.screenshot_handler if hasattr(old_core, 'screenshot_handler') else None,
            input_handler=old_core.input_handler if hasattr(old_core, 'input_handler') else None,
            safety_checker=old_core.safety_checker if hasattr(old_core, 'safety_checker') else None
        )
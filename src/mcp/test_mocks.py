"""
Mock implementations for testing without test_mode
"""
from unittest.mock import Mock
from typing import Dict, Any, Optional


class MockScreenshotProvider:
    """Mock screenshot provider for testing"""
    def __init__(self, capture_data=None):
        self.capture_data = capture_data or b'mock_screenshot_data'
        self.capture_called = 0
        
    def capture(self):
        self.capture_called += 1
        return self.capture_data
    
    def is_available(self):
        return True
    
    def get_display_info(self):
        return {'width': 1920, 'height': 1080, 'mock': True}


class MockInputProvider:
    """Mock input provider for testing"""
    def __init__(self, default_success=True):
        self.default_success = default_success
        self.actions = []
        
    def click(self, x, y, button='left'):
        self.actions.append(('click', x, y, button))
        return self.default_success
    
    def type_text(self, text):
        self.actions.append(('type', text))
        return self.default_success
    
    def key_press(self, key):
        self.actions.append(('key', key))
        return self.default_success
    
    def mouse_move(self, x, y):
        self.actions.append(('move', x, y))
        return self.default_success
    
    def drag(self, start_x, start_y, end_x, end_y):
        self.actions.append(('drag', start_x, start_y, end_x, end_y))
        return self.default_success
    
    def scroll(self, direction, amount):
        self.actions.append(('scroll', direction, amount))
        return self.default_success


class MockPlatformInfo:
    """Mock platform info for testing"""
    def __init__(self, platform='test', environment='mock'):
        self._platform = platform
        self._environment = environment
        
    def get_platform(self):
        return self._platform
    
    def get_environment(self):
        return self._environment
    
    def get_capabilities(self):
        return {'test': True}


class MockSafetyValidator:
    """Mock safety validator for testing"""
    def __init__(self, default_safe=True):
        self.default_safe = default_safe
        self.validations = []
        
    def validate_action(self, action, params):
        self.validations.append(('action', action, params))
        return (self.default_safe, None if self.default_safe else "Blocked")
    
    def validate_text(self, text):
        self.validations.append(('text', text))
        return (self.default_safe, None if self.default_safe else "Blocked")
    
    def validate_command(self, command):
        self.validations.append(('command', command))
        return (self.default_safe, None if self.default_safe else "Blocked")


class MockDisplayManager:
    """Mock display manager for testing"""
    def __init__(self, available=True):
        self._available = available
        
    def is_display_available(self):
        return self._available
    
    def get_best_display(self):
        return 'mock_display' if self._available else None
    
    def setup_display(self):
        return self._available


def capture_screenshot():
    """Mock screenshot capture function for backward compatibility"""
    # This is a mock implementation that always returns test data
    return b'mock_screenshot_data'


class MockVisualAnalyzer:
    """Mock visual analyzer for testing"""
    def analyze(self, image_data, query):
        return {
            'analysis': f'Mock analysis of: {query}',
            'objects_detected': [],
            'text_found': '',
            'mock': True
        }


def create_test_computer_use(**overrides):
    """Helper to create ComputerUse instance for testing"""
    from .factory_refactored import create_computer_use_for_testing
    
    # Use proper dependency injection for testing
    return create_computer_use_for_testing(**overrides)

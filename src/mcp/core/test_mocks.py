"""
Mock implementations for testing without test_mode
"""

from typing import Dict, Any, Optional
from unittest.mock import Mock


class MockScreenshotProvider:
    """Mock screenshot provider for testing"""
    
    def __init__(self, capture_data: Optional[bytes] = None) -> None:
        self.capture_data = capture_data or b'mock_screenshot_data'
        self.capture_called = 0
        
    def capture(self) -> bytes:
        self.capture_called += 1
        return self.capture_data
    
    def is_available(self) -> bool:
        return True
    
    def get_display_info(self) -> Dict[str, Any]:
        return {'width': 1920, 'height': 1080, 'mock': True}


class MockInputProvider:
    """Mock input provider for testing"""
    def __init__(self, default_success: bool = True) -> None:
        self.default_success = default_success
        self.actions = []
        
    def click(self, x: int, y: int, button: str = 'left') -> bool:
        self.actions.append(('click', x, y, button))
        return self.default_success
    
    def type_text(self, text: str) -> bool:
        self.actions.append(('type', text))
        return self.default_success
    
    def key_press(self, key: str) -> bool:
        self.actions.append(('key', key))
        return self.default_success
    
    def mouse_move(self, x: int, y: int) -> bool:
        self.actions.append(('move', x, y))
        return self.default_success
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        self.actions.append(('drag', start_x, start_y, end_x, end_y))
        return self.default_success
    
    def scroll(self, direction: str, amount: int) -> bool:
        self.actions.append(('scroll', direction, amount))
        return self.default_success


class MockPlatformInfo:
    """Mock platform info for testing"""
    def __init__(self, platform: str = 'test', environment: str = 'mock') -> None:
        self._platform = platform
        self._environment = environment
        
    def get_platform(self) -> str:
        return self._platform
    
    def get_environment(self) -> str:
        return self._environment
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {'test': True}


class MockSafetyValidator:
    """Mock safety validator for testing"""
    def __init__(self, default_safe: bool = True) -> None:
        self.default_safe = default_safe
        self.validations = []
        
    def validate_action(self, action: str, params: Dict[str, Any]) -> tuple:
        self.validations.append(('action', action, params))
        return (self.default_safe, None if self.default_safe else "Blocked")
    
    def validate_text(self, text: str) -> tuple:
        self.validations.append(('text', text))
        return (self.default_safe, None if self.default_safe else "Blocked")
    
    def validate_command(self, command: str) -> tuple:
        self.validations.append(('command', command))
        return (self.default_safe, None if self.default_safe else "Blocked")


class MockDisplayManager:
    """Mock display manager for testing"""
    def __init__(self, available: bool = True) -> None:
        self._available = available
        
    def is_display_available(self) -> bool:
        return self._available
    
    def get_best_display(self) -> Optional[str]:
        return 'mock_display' if self._available else None
    
    def setup_display(self) -> bool:
        return self._available


def capture_screenshot() -> bytes:
    """Mock screenshot capture function for backward compatibility"""
    # This is a mock implementation that always returns test data
    return b'mock_screenshot_data'




def get_mock_providers() -> Dict[str, Any]:
    """Get all mock providers for testing"""
    return {
        'screenshot': MockScreenshotProvider(),
        'input': MockInputProvider(),
        'platform': MockPlatformInfo(),
        'display': MockDisplayManager(),
        'safety': MockSafetyValidator()
    }


def create_test_computer_use(**overrides) -> Any:
    """Helper to create ComputerUse instance for testing"""
    from .factory import create_computer_use_for_testing
    # Use proper dependency injection for testing
    return create_computer_use_for_testing(**overrides)

#!/usr/bin/env python3
"""
Example of proper testing without test_mode

This demonstrates how to test ComputerUseRefactored using dependency injection
and mock implementations instead of the test_mode anti-pattern.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
# Using bytes instead of numpy for test simplicity

from mcp.test_mocks import create_test_computer_use

from mcp.factory_refactored import create_computer_use_for_testing
from mcp.abstractions import (
    ScreenshotProvider, InputProvider, PlatformInfo,
    SafetyValidator, DisplayManager
)


class MockScreenshotProvider:
    """Mock implementation of ScreenshotProvider for testing"""
    
    def __init__(self, capture_data=None, is_available=True):
        self.capture_data = capture_data or b'mock_screenshot_data'
        self._is_available = is_available
        self.capture_called = 0
    
    def capture(self):
        self.capture_called += 1
        return self.capture_data
    
    def is_available(self) -> bool:
        return self._is_available
    
    def get_display_info(self) -> dict:
        return {'width': 100, 'height': 100, 'mock': True}


class MockInputProvider:
    """Mock implementation of InputProvider for testing"""
    
    def __init__(self, default_success=True):
        self.default_success = default_success
        self.clicks = []
        self.typed_text = []
        self.key_presses = []
        self.mouse_moves = []
        self.drags = []
        self.scrolls = []
    
    def click(self, x: int, y: int, button: str = 'left') -> bool:
        self.clicks.append({'x': x, 'y': y, 'button': button})
        return self.default_success
    
    def type_text(self, text: str) -> bool:
        self.typed_text.append(text)
        return self.default_success
    
    def key_press(self, key: str) -> bool:
        self.key_presses.append(key)
        return self.default_success
    
    def mouse_move(self, x: int, y: int) -> bool:
        self.mouse_moves.append({'x': x, 'y': y})
        return self.default_success
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        self.drags.append({
            'start': (start_x, start_y),
            'end': (end_x, end_y)
        })
        return self.default_success
    
    def scroll(self, direction: str, amount: int) -> bool:
        self.scrolls.append({'direction': direction, 'amount': amount})
        return self.default_success


class TestComputerUseRefactored(unittest.TestCase):
    """Test ComputerUseRefactored with proper mocking"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock implementations
        self.mock_screenshot = MockScreenshotProvider()
        self.mock_input = MockInputProvider()
        
        # Create simple mocks for other dependencies
        self.mock_platform = Mock()
        self.mock_platform.get_platform.return_value = 'test'
        self.mock_platform.get_environment.return_value = 'mock'
        self.mock_platform.get_capabilities.return_value = {'test': True}
        
        self.mock_safety = Mock()
        self.mock_safety.validate_action.return_value = (True, None)
        self.mock_safety.validate_text.return_value = (True, None)
        
        self.mock_display = Mock()
        self.mock_display.is_display_available.return_value = True
        
        # Create instance with mocks
        self.computer_use = create_computer_use_for_testing(
            screenshot_provider=self.mock_screenshot,
            input_provider=self.mock_input,
            platform_info=self.mock_platform,
            safety_validator=self.mock_safety,
            display_manager=self.mock_display,
            visual_analyzer=Mock(),
            enable_ultrathink=False  # Disable for faster tests
        )
    
    def test_screenshot_success(self):
        """Test successful screenshot capture"""
        result = self.computer_use.take_screenshot()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data'], b'mock_screenshot_data')
        self.assertEqual(self.mock_screenshot.capture_called, 1)
        self.assertEqual(result['platform'], 'test')
    
    def test_screenshot_no_display(self):
        """Test screenshot when display is not available"""
        self.mock_display.is_display_available.return_value = False
        
        result = self.computer_use.take_screenshot()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'No display available')
        self.assertEqual(self.mock_screenshot.capture_called, 0)
    
    def test_click_success(self):
        """Test successful click operation"""
        result = self.computer_use.click(100, 200, 'left')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['coordinates'], (100, 200))
        self.assertEqual(result['button'], 'left')
        self.assertEqual(len(self.mock_input.clicks), 1)
        self.assertEqual(self.mock_input.clicks[0], {
            'x': 100, 'y': 200, 'button': 'left'
        })
    
    def test_click_safety_check_fails(self):
        """Test click blocked by safety check"""
        self.mock_safety.validate_action.return_value = (False, 'Dangerous location')
        
        result = self.computer_use.click(100, 200)
        
        self.assertFalse(result['success'])
        self.assertIn('Safety check failed', result['error'])
        self.assertEqual(len(self.mock_input.clicks), 0)
    
    def test_type_text_success(self):
        """Test successful text typing"""
        result = self.computer_use.type_text("Hello World")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['text'], 'Hello World')
        self.assertEqual(self.mock_input.typed_text, ['Hello World'])
    
    def test_type_text_safety_block(self):
        """Test text typing blocked by safety"""
        self.mock_safety.validate_text.return_value = (False, 'Contains rm -rf')
        
        result = self.computer_use.type_text("rm -rf /")
        
        self.assertFalse(result['success'])
        self.assertIn('Safety check failed', result['error'])
        self.assertEqual(self.mock_input.typed_text, [])
    
    def test_key_press_valid(self):
        """Test valid key press"""
        result = self.computer_use.key_press('Return')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['key'], 'Return')
        self.assertEqual(self.mock_input.key_presses, ['Return'])
    
    def test_key_press_invalid(self):
        """Test invalid key press"""
        result = self.computer_use.key_press('InvalidKey')
        
        self.assertFalse(result['success'])
        self.assertIn('Invalid key', result['error'])
        self.assertEqual(self.mock_input.key_presses, [])
    
    def test_drag_operation(self):
        """Test drag operation"""
        result = self.computer_use.drag(10, 20, 100, 200)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['start'], (10, 20))
        self.assertEqual(result['end'], (100, 200))
        self.assertEqual(len(self.mock_input.drags), 1)
    
    def test_scroll_operation(self):
        """Test scroll operation"""
        result = self.computer_use.scroll('down', 5)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['direction'], 'down')
        self.assertEqual(result['amount'], 5)
        self.assertEqual(self.mock_input.scrolls, [
            {'direction': 'down', 'amount': 5}
        ])
    
    def test_platform_info(self):
        """Test getting platform information"""
        info = self.computer_use.get_platform_info()
        
        self.assertEqual(info['platform'], 'test')
        self.assertEqual(info['environment'], 'mock')
        self.assertEqual(info['capabilities'], {'test': True})
        self.assertTrue(info['display_available'])
    
    def test_input_failure_handling(self):
        """Test handling of input operation failures"""
        self.mock_input.default_success = False
        
        result = self.computer_use.click(50, 50)
        
        self.assertFalse(result['success'])
        # But the operation was still attempted
        self.assertEqual(len(self.mock_input.clicks), 1)
    
    def test_exception_handling(self):
        """Test exception handling in operations"""
        # Make capture raise an exception
        self.mock_screenshot.capture = Mock(side_effect=Exception("Hardware error"))
        
        result = self.computer_use.take_screenshot()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Hardware error')


class TestFactoryPattern(unittest.TestCase):
    """Test the factory pattern for creating instances"""
    
    @patch('mcp.factory_refactored.ScreenshotFactory')
    @patch('mcp.factory_refactored.InputFactory')
    def test_create_default(self, mock_input_factory, mock_screenshot_factory):
        """Test creating default instance"""
        # Mock the factories
        mock_screenshot = Mock()
        mock_input = Mock()
        mock_screenshot_factory.create.return_value = mock_screenshot
        mock_input_factory.create.return_value = mock_input
        
        from mcp.factory_refactored import create_computer_use
        
        instance = create_computer_use()
        
        # Verify instance was created
        self.assertIsNotNone(instance)
        
        # Verify factories were called
        mock_screenshot_factory.create.assert_called_once()
        mock_input_factory.create.assert_called_once()
    
    def test_create_for_testing_with_overrides(self):
        """Test creating instance with custom implementations"""
        from mcp.factory_refactored import create_computer_use_for_testing
        
        custom_screenshot = Mock()
        custom_input = Mock()
        
        instance = create_computer_use_for_testing(
            screenshot_provider=custom_screenshot,
            input_provider=custom_input
        )
        
        # Verify custom implementations were used
        self.assertIs(instance.screenshot, custom_screenshot)
        self.assertIs(instance.input, custom_input)


if __name__ == '__main__':
    unittest.main()
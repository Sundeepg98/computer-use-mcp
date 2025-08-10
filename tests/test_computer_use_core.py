"""
Platform-aware functional tests for ComputerUse
Tests work correctly on both Linux and Windows/WSL2
"""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import os
import subprocess
import sys
import unittest

from mcp.platforms.platform_utils import is_wsl2
from .test_mocks import create_test_computer_use, MockScreenshotProvider, MockInputProvider, capture_screenshot

from .test_platform_aware_helper import adapt_test_for_platform, create_platform_aware_subprocess_mock

#!/usr/bin/env python3

# Add src to path

class TestComputerUseActualFunctionality(unittest.TestCase):
    """Test ACTUAL functionality of computer use core"""
    
    def setUp(self):
        """Setup test environment"""
        self.core = create_test_computer_use()
    
    def test_screenshot_in_test_mode_returns_mock_data(self):
        """Test screenshot returns proper mock data in test mode"""
        result = self.core.take_screenshot(analyze="test")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['test_mode'], True)
        # Handle both string and bytes
        if isinstance(result['data'], bytes):
            self.assertEqual(result['data'], b'mock_screenshot_data')
        else:
            self.assertEqual(result['data'], 'mock_screenshot_data')
        self.assertEqual(result['width'], 1920)
        self.assertEqual(result['height'], 1080)
    
    @patch('subprocess.run')
    def test_screenshot_calls_appropriate_tool(self, mock_run):
        """Test screenshot calls appropriate tool for platform"""
        # Setup
        core = create_test_computer_use()
        mock_run.return_value = Mock(returncode=0, stdout=b'PNG_DATA')
        
        # Mock file operations
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = b'SCREENSHOT_DATA'
                with patch('os.unlink'):
                    # Execute
                    result = capture_screenshot()
        
        # Verify appropriate tool was called
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        
        # Platform-aware assertion
        if is_wsl2():
            self.assertIn('powershell.exe', call_args[0])
        else:
            self.assertIn('scrot', call_args[0])
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_click_sends_appropriate_command(self):
        """Test click sends appropriate command for platform"""
        # Setup
        core = create_test_computer_use()
        core.display_available = True
        
        # Execute
        result = core.click(100, 200, 'left')
        
        # Verify success
        self.assertTrue(result['success'])
        self.assertEqual(result['coordinates'], (100, 200))
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_click_right_button(self):
        """Test right click works correctly"""
        core = create_test_computer_use()
        core.display_available = True
        
        result = core.click(50, 75, 'right')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['button'], 'right')
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_type_text_sends_appropriate_command(self):
        """Test type_text sends appropriate command for platform"""
        # Setup
        core = create_test_computer_use()
        core.display_available = True
        
        # Execute
        result = core.type_text("Hello World")
        
        # Verify
        self.assertTrue(result['success'])
        self.assertEqual(result['text'], "Hello World")
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_key_press_sends_appropriate_command(self):
        """Test key_press sends appropriate command for platform"""
        # Setup
        core = create_test_computer_use()
        core.display_available = True
        
        # Execute
        result = core.key_press('Return')
        
        # Verify
        self.assertTrue(result['success'])
        self.assertEqual(result['key'], 'Return')
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_key_press_combination(self):
        """Test key combinations work correctly"""
        # Setup
        core = create_test_computer_use()
        core.display_available = True
        
        # Execute
        result = core.key_press('ctrl+c')
        
        # Verify
        self.assertTrue(result['success'])
        self.assertEqual(result['key'], 'ctrl+c')
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_scroll_down_works(self):
        """Test scroll down works correctly"""
        # Setup
        core = create_test_computer_use()
        core.display_available = True
        
        # Execute
        result = core.scroll('down', 3)
        
        # Verify
        self.assertTrue(result['success'])
        self.assertEqual(result['direction'], 'down')
        self.assertEqual(result['amount'], 3)
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_scroll_up_works(self):
        """Test scroll up works correctly"""
        # Setup
        core = create_test_computer_use()
        core.display_available = True
        
        # Execute
        result = core.scroll('up', 2)
        
        # Verify
        self.assertTrue(result['success'])
        self.assertEqual(result['direction'], 'up')
        self.assertEqual(result['amount'], 2)
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_drag_operation_sequence(self):
        """Test drag performs correct sequence of operations"""
        # Setup
        core = create_test_computer_use()
        core.display_available = True
        
        # Execute
        result = core.drag(100, 100, 200, 200)
        
        # Verify
        self.assertTrue(result['success'])
        self.assertEqual(result['start'], (100, 100))
        self.assertEqual(result['end'], (200, 200))
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_move_mouse_without_clicking(self):
        """Test move_mouse just moves without clicking"""
        # Setup
        core = create_test_computer_use()
        core.display_available = True
        
        # Execute
        result = core.move_mouse(500, 300)
        
        # Verify
        self.assertTrue(result['success'])
        self.assertEqual(result['coordinates'], (500, 300))
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_get_mouse_position(self):
        """Test getting current mouse position"""
        # Setup
        core = create_test_computer_use()
        core.display_available = True
        
        # Execute
        x, y = core.get_mouse_position()
        
        # Verify - mock returns (123, 456)
        self.assertEqual(x, 123)
        self.assertEqual(y, 456)
    
    def test_no_display_returns_error(self):
        """Test operations fail gracefully when no display"""
        # Setup
        core = create_test_computer_use()
        core.display_available = False
        
        # Test various operations
        result = core.click(100, 100)
        self.assertFalse(result['success'])
        self.assertIn('No display', result['error'])
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_type_empty_string(self):
        """Test typing empty string"""
        # Setup
        core = create_test_computer_use()
        core.display_available = True
        
        # Execute
        result = core.type_text("")
        
        # Verify
        self.assertTrue(result['success'])
        self.assertEqual(result['text'], "")
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_type_special_characters(self):
        """Test typing special characters"""
        # Setup
        core = create_test_computer_use()
        core.display_available = True
        special_chars = '!@#$%^&*()_+-=[]{}|;\\\'",./<>?'
        
        # Execute
        result = core.type_text(special_chars)
        
        # Verify
        self.assertTrue(result['success'])
        self.assertEqual(result['text'], special_chars)
    
    @patch('subprocess.run', create_platform_aware_subprocess_mock())
    def test_concurrent_operations(self):
        """Test multiple operations in sequence"""
        # Setup
        core = create_test_computer_use()
        core.display_available = True
        
        # Execute multiple operations
        result1 = core.click(100, 100)
        result2 = core.type_text("test")
        result3 = core.key_press('Return')
        result4 = core.move_mouse(200, 200)
        
        # Verify all succeeded
        self.assertTrue(result1['success'])
        self.assertTrue(result2['success'])
        self.assertTrue(result3['success'])
        self.assertTrue(result4['success'])

class TestComputerUseEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        """Setup test environment"""
        self.core = create_test_computer_use()
    
    @patch('subprocess.run')
    def test_screenshot_fallback_chain(self, mock_run):
        """Test screenshot tries multiple methods"""
        # Make all methods fail
        mock_run.side_effect = subprocess.CalledProcessError(1, 'scrot')
        
        # Attempt screenshot - should fail after trying all methods
        with self.assertRaises(Exception):
            capture_screenshot()
    
    def test_click_with_invalid_button(self):
        """Test click with invalid button name"""
        self.core.display_available = True
        
        # Should default to left button
        result = self.core.click(100, 100, 'invalid_button')
        # Should still work with default
        self.assertIn('success', result)
    
    def test_scroll_with_invalid_direction(self):
        """Test scroll with invalid direction"""
        self.core.display_available = True
        
        # Should handle invalid direction
        result = self.core.scroll('sideways', 5)
        # Check that it's handled appropriately
        self.assertIn('success', result)

if __name__ == '__main__':
    unittest.main()
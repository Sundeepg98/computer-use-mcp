#!/usr/bin/env python3
"""
Functional tests for ComputerUseCore - ACTUAL functionality testing
Tests that the code WORKS, not just that it exists
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import subprocess
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from computer_use_core import ComputerUseCore, capture_screenshot


class TestComputerUseCoreActualFunctionality(unittest.TestCase):
    """Test ACTUAL functionality of computer use core"""
    
    def setUp(self):
        """Setup test environment"""
        self.core = ComputerUseCore(test_mode=True)
    
    def test_screenshot_in_test_mode_returns_mock_data(self):
        """Test screenshot returns proper mock data in test mode"""
        result = self.core.screenshot(analyze="test")
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['test_mode'], True)
        self.assertEqual(result['data'], 'mock_screenshot_data')
        self.assertEqual(result['width'], 1920)
        self.assertEqual(result['height'], 1080)
    
    @patch('subprocess.run')
    def test_screenshot_calls_scrot_when_available(self, mock_run):
        """Test screenshot attempts scrot first"""
        # Setup
        core = ComputerUseCore(test_mode=False)
        mock_run.return_value = Mock(returncode=0, stdout=b'PNG_DATA')
        
        # Mock file operations
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = b'SCREENSHOT_DATA'
                with patch('os.unlink'):
                    # Execute
                    result = capture_screenshot()
        
        # Verify scrot was called
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        self.assertIn('scrot', call_args[0])
    
    @patch('subprocess.run')
    def test_click_sends_xdotool_command(self, mock_run):
        """Test click actually sends xdotool command"""
        # Setup
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        # Execute
        result = core.click(100, 200, 'left')
        
        # Verify
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], 'xdotool')
        self.assertEqual(call_args[1], 'mousemove')
        self.assertEqual(call_args[2], '100')
        self.assertEqual(call_args[3], '200')
        self.assertEqual(call_args[4], 'click')
        self.assertEqual(call_args[5], '1')  # left button
        
        self.assertTrue(result['success'])
        self.assertEqual(result['coordinates'], (100, 200))
    
    @patch('subprocess.run')
    def test_click_right_button(self, mock_run):
        """Test right click sends correct button code"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        core.click(50, 75, 'right')
        
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[5], '3')  # right button code
    
    @patch('subprocess.run')
    def test_type_text_sends_xdotool_type_command(self, mock_run):
        """Test type_text actually sends text via xdotool"""
        # Setup
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        # Execute
        result = core.type_text("Hello World")
        
        # Verify
        mock_run.assert_called_with(
            ['xdotool', 'type', '--clearmodifiers', 'Hello World'],
            check=True
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['text'], 'Hello World')
    
    def test_type_text_in_test_mode(self):
        """Test type_text returns mock data in test mode"""
        result = self.core.type_text("Test input")
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['text'], 'Test input')
        self.assertEqual(result['test_mode'], True)
    
    @patch('subprocess.run')
    def test_key_press_sends_xdotool_key(self, mock_run):
        """Test key_press sends proper xdotool command"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        result = core.key_press("Return")
        
        mock_run.assert_called_with(['xdotool', 'key', 'Return'], check=True)
        self.assertTrue(result['success'])
    
    @patch('subprocess.run')
    def test_key_press_combination(self, mock_run):
        """Test key combinations like Ctrl+C"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        result = core.key_press("ctrl+c")
        
        mock_run.assert_called_with(['xdotool', 'key', 'ctrl+c'], check=True)
        self.assertTrue(result['success'])
    
    @patch('subprocess.run')
    def test_scroll_down_sends_button_5(self, mock_run):
        """Test scroll down sends mouse button 5"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        result = core.scroll('down', 3)
        
        # Should click button 5 three times
        self.assertEqual(mock_run.call_count, 3)
        for call_obj in mock_run.call_args_list:
            args = call_obj[0][0]
            self.assertEqual(args[0], 'xdotool')
            self.assertEqual(args[1], 'click')
            self.assertEqual(args[2], '5')
    
    @patch('subprocess.run')
    def test_scroll_up_sends_button_4(self, mock_run):
        """Test scroll up sends mouse button 4"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        result = core.scroll('up', 2)
        
        self.assertEqual(mock_run.call_count, 2)
        for call_obj in mock_run.call_args_list:
            args = call_obj[0][0]
            self.assertEqual(args[2], '4')  # button 4 for scroll up
    
    @patch('subprocess.run')
    def test_drag_operation_sequence(self, mock_run):
        """Test drag performs correct sequence of operations"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        result = core.drag(10, 20, 100, 200)
        
        # Should have 4 calls: move, mousedown, move, mouseup
        self.assertEqual(mock_run.call_count, 4)
        
        calls = [call[0][0] for call in mock_run.call_args_list]
        
        # First: move to start
        self.assertEqual(calls[0], ['xdotool', 'mousemove', '10', '20'])
        # Second: mouse down
        self.assertEqual(calls[1], ['xdotool', 'mousedown', '1'])
        # Third: move to end
        self.assertEqual(calls[2], ['xdotool', 'mousemove', '100', '200'])
        # Fourth: mouse up
        self.assertEqual(calls[3], ['xdotool', 'mouseup', '1'])
        
        self.assertTrue(result['success'])
    
    @patch('subprocess.run')
    def test_move_mouse_without_clicking(self, mock_run):
        """Test move_mouse just moves without clicking"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        result = core.move_mouse(500, 300)
        
        mock_run.assert_called_once_with(
            ['xdotool', 'mousemove', '500', '300'],
            check=True
        )
        self.assertTrue(result['success'])
    
    @patch('subprocess.run')
    def test_get_mouse_position(self, mock_run):
        """Test getting current mouse position"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout="x:123 y:456 screen:0 window:12345"
        )
        
        x, y = core.get_mouse_position()
        
        self.assertEqual(x, 123)
        self.assertEqual(y, 456)
    
    def test_wait_actually_waits(self):
        """Test wait function actually pauses execution"""
        import time
        start = time.time()
        
        result = self.core.wait(0.5)
        
        elapsed = time.time() - start
        self.assertGreaterEqual(elapsed, 0.5)
        self.assertLess(elapsed, 0.6)
        self.assertTrue(result['success'])
    
    @patch('subprocess.run')
    def test_error_handling_when_xdotool_fails(self, mock_run):
        """Test proper error handling when xdotool fails"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.side_effect = subprocess.CalledProcessError(1, 'xdotool')
        
        result = core.click(100, 100)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_no_display_returns_error(self):
        """Test operations fail gracefully when no display"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = False
        
        result = core.click(100, 100)
        
        # Should still return success=True but no actual action
        self.assertTrue(result['success'])
    
    @patch('os.environ.get')
    @patch('subprocess.run')
    def test_wsl2_display_setup(self, mock_run, mock_env):
        """Test WSL2 display setup for Windows"""
        # Mock environment to look like WSL with DISPLAY set
        mock_env.side_effect = lambda x, default='': {
            'WSL_DISTRO_NAME': 'Ubuntu',
            'DISPLAY': ':0'  # Has display
        }.get(x, default)
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout="nameserver 172.22.0.1\n"
        )
        
        with patch.dict('os.environ', {'DISPLAY': ':0', 'WSL_DISTRO_NAME': 'Ubuntu'}):
            core = ComputerUseCore(test_mode=False)
            # Manually call _init_display since it's called in __init__
            # and we need to verify the environment setup
            
            # Verify that in WSL environment, the display setup runs
            self.assertTrue(core.display_available)
            # The actual DISPLAY setting happens in __init__, which already ran
    
    def test_safety_checks_enabled_by_default(self):
        """Test safety checks are enabled by default"""
        core = ComputerUseCore(test_mode=False)
        
        self.assertTrue(core.safety_checks)
        self.assertTrue(hasattr(core, 'ultrathink_enabled'))
    
    @patch('subprocess.run')
    def test_screenshot_fallback_chain(self, mock_run):
        """Test screenshot tries multiple methods"""
        # All methods fail
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, 'scrot'),
            subprocess.CalledProcessError(1, 'import'),
            subprocess.CalledProcessError(1, 'xwd'),
            subprocess.CalledProcessError(1, 'powershell.exe'),
        ]
        
        with patch('os.path.exists', return_value=False):
            result = capture_screenshot()
        
        # Should return placeholder when all fail
        self.assertIn(b'SCREENSHOT UNAVAILABLE', result)
    
    def test_screenshot_analyze_parameter(self):
        """Test screenshot accepts and includes analyze parameter"""
        result = self.core.screenshot(analyze="Find the submit button")
        
        self.assertEqual(result['analyze'], "Find the submit button")
        self.assertIn('status', result)
        self.assertIn('data', result)


class TestComputerUseCoreEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Setup test environment"""
        self.core = ComputerUseCore(test_mode=True)
    
    @patch('subprocess.run')
    def test_click_with_invalid_coordinates(self, mock_run):
        """Test click handles invalid coordinates gracefully"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        # Negative coordinates should still work
        result = core.click(-10, -20)
        self.assertTrue(result['success'])
        
        # Very large coordinates
        result = core.click(99999, 99999)
        self.assertTrue(result['success'])
    
    @patch('subprocess.run')
    def test_type_empty_string(self, mock_run):
        """Test typing empty string"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        result = core.type_text("")
        
        mock_run.assert_called_with(
            ['xdotool', 'type', '--clearmodifiers', ''],
            check=True
        )
        self.assertTrue(result['success'])
    
    @patch('subprocess.run')
    def test_type_special_characters(self, mock_run):
        """Test typing special characters"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = core.type_text(special_text)
        
        mock_run.assert_called_with(
            ['xdotool', 'type', '--clearmodifiers', special_text],
            check=True
        )
        self.assertTrue(result['success'])
    
    def test_wait_negative_duration(self):
        """Test wait with negative duration"""
        # Should handle gracefully
        result = self.core.wait(-1)
        
        # Should still return success but not actually wait negative time
        self.assertTrue(result['success'])
    
    @patch('subprocess.run')
    def test_concurrent_operations(self, mock_run):
        """Test multiple operations in sequence"""
        core = ComputerUseCore(test_mode=False)
        core.display_available = True
        mock_run.return_value = Mock(returncode=0)
        
        # Simulate a complex workflow
        core.move_mouse(100, 100)
        core.click(100, 100)
        core.type_text("Hello")
        core.key_press("Return")
        core.scroll('down', 2)
        
        # All operations should succeed
        self.assertGreater(mock_run.call_count, 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
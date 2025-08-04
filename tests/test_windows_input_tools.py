#!/usr/bin/env python3
"""
TDD Tests for Windows input tools (mouse, keyboard, etc.)
Ensures ALL MCP tools work on Windows/WSL2
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock, call

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestWindowsMouseOperations(unittest.TestCase):
    """Test mouse operations on Windows"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from mcp.input.windows import WindowsInput
            self.input = WindowsInput()
        except ImportError:
            self.skipTest("WindowsInput not implemented yet - TDD in progress")
    
    def test_mouse_click_native_windows(self):
        """Test mouse click on native Windows"""
        with patch('platform.system', return_value='Windows'):
            with patch('ctypes.windll') as mock_windll:
                # Test left click
                result = self.input.click(x=500, y=300, button='left')
                
                # Verify Windows API calls
                mock_windll.user32.SetCursorPos.assert_called_with(500, 300)
                mock_windll.user32.mouse_event.assert_called()
                
                self.assertTrue(result['success'])
                self.assertEqual(result['action'], 'click')
                self.assertEqual(result['coordinates'], (500, 300))
    
    def test_mouse_click_wsl2(self):
        """Test mouse click in WSL2 using PowerShell"""
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {'WSL_INTEROP': '/run/WSL/123'}):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    
                    result = self.input.click(x=500, y=300, button='right')
                    
                    # Verify PowerShell was called
                    mock_run.assert_called_once()
                    ps_command = mock_run.call_args[0][0]
                    self.assertEqual(ps_command[0], 'powershell.exe')
                    self.assertIn('[System.Windows.Forms.Cursor]::Position', ps_command[2])
                    self.assertIn('RightClick', ps_command[2])
                    
                    self.assertTrue(result['success'])
    
    def test_mouse_move(self):
        """Test mouse movement without clicking"""
        with patch('ctypes.windll') as mock_windll:
            result = self.input.move_mouse(x=800, y=600)
            
            mock_windll.user32.SetCursorPos.assert_called_with(800, 600)
            self.assertTrue(result['success'])
            self.assertEqual(result['action'], 'move')
    
    def test_mouse_drag(self):
        """Test click and drag operation"""
        with patch('ctypes.windll') as mock_windll:
            result = self.input.drag(
                start_x=100, start_y=100,
                end_x=500, end_y=500
            )
            
            # Verify sequence: move, mouse down, move, mouse up
            calls = mock_windll.user32.SetCursorPos.call_args_list
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0][0], (100, 100))
            self.assertEqual(calls[1][0], (500, 500))
            
            # Verify mouse button events
            mouse_events = mock_windll.user32.mouse_event.call_args_list
            self.assertGreaterEqual(len(mouse_events), 2)  # At least down and up
            
            self.assertTrue(result['success'])
    
    def test_mouse_scroll(self):
        """Test mouse scroll operation"""
        with patch('ctypes.windll') as mock_windll:
            # Test scroll down
            result = self.input.scroll(direction='down', amount=3)
            
            # Verify scroll events
            self.assertEqual(mock_windll.user32.mouse_event.call_count, 3)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['direction'], 'down')
            self.assertEqual(result['amount'], 3)
    
    def test_get_mouse_position(self):
        """Test getting current mouse position"""
        with patch('ctypes.windll') as mock_windll:
            # Mock cursor position
            mock_point = MagicMock()
            mock_point.x = 1024
            mock_point.y = 768
            mock_windll.user32.GetCursorPos.return_value = True
            
            with patch('ctypes.wintypes.POINT', return_value=mock_point):
                x, y = self.input.get_mouse_position()
                
                self.assertEqual(x, 1024)
                self.assertEqual(y, 768)


class TestWindowsKeyboardOperations(unittest.TestCase):
    """Test keyboard operations on Windows"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from mcp.input.windows import WindowsKeyboard
            self.keyboard = WindowsKeyboard()
        except ImportError:
            self.skipTest("WindowsKeyboard not implemented yet - TDD in progress")
    
    def test_type_text_native(self):
        """Test typing text on native Windows"""
        with patch('platform.system', return_value='Windows'):
            with patch('ctypes.windll') as mock_windll:
                result = self.keyboard.type_text("Hello Windows!")
                
                # Verify each character was sent
                self.assertGreater(mock_windll.user32.SendInput.call_count, 0)
                
                self.assertTrue(result['success'])
                self.assertEqual(result['text'], "Hello Windows!")
    
    def test_type_text_wsl2(self):
        """Test typing text in WSL2"""
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {'WSL_INTEROP': '/run/WSL/123'}):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    
                    result = self.keyboard.type_text("WSL2 typing test")
                    
                    # Verify PowerShell SendKeys was used
                    ps_command = mock_run.call_args[0][0]
                    self.assertIn('SendKeys', ps_command[2])
                    self.assertIn('WSL2 typing test', ps_command[2])
                    
                    self.assertTrue(result['success'])
    
    def test_key_press(self):
        """Test pressing special keys"""
        special_keys = ['Return', 'Tab', 'Escape', 'ctrl+a', 'alt+F4']
        
        with patch('ctypes.windll') as mock_windll:
            for key in special_keys:
                result = self.keyboard.key_press(key)
                
                self.assertTrue(result['success'])
                self.assertEqual(result['key'], key)
                
                # Verify key events were sent
                mock_windll.user32.SendInput.assert_called()
    
    def test_key_combinations(self):
        """Test complex key combinations"""
        with patch('ctypes.windll') as mock_windll:
            # Test Ctrl+C
            result = self.keyboard.key_press('ctrl+c')
            
            # Should send: Ctrl down, C down, C up, Ctrl up
            self.assertGreaterEqual(mock_windll.user32.SendInput.call_count, 4)
            self.assertTrue(result['success'])
    
    def test_unicode_support(self):
        """Test typing Unicode characters"""
        with patch('ctypes.windll') as mock_windll:
            result = self.keyboard.type_text("Hello 世界! 🌍")
            
            self.assertTrue(result['success'])
            # Verify Unicode was handled
            mock_windll.user32.SendInput.assert_called()


class TestWindowsWindowManagement(unittest.TestCase):
    """Test window management operations on Windows"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from mcp.window.windows import WindowsWindowManager
            self.window_mgr = WindowsWindowManager()
        except ImportError:
            self.skipTest("WindowsWindowManager not implemented yet - TDD in progress")
    
    def test_get_active_window(self):
        """Test getting active window information"""
        with patch('ctypes.windll') as mock_windll:
            mock_windll.user32.GetForegroundWindow.return_value = 12345
            mock_windll.user32.GetWindowTextW.return_value = 14
            
            result = self.window_mgr.get_active_window()
            
            self.assertIn('title', result)
            self.assertIn('handle', result)
            self.assertEqual(result['handle'], 12345)
    
    def test_list_windows(self):
        """Test listing all windows"""
        with patch('ctypes.windll') as mock_windll:
            # Mock EnumWindows behavior
            def mock_enum(callback, _):
                # Simulate finding 2 windows
                callback(111, None)
                callback(222, None)
                return True
            
            mock_windll.user32.EnumWindows.side_effect = mock_enum
            
            windows = self.window_mgr.list_windows()
            
            self.assertIsInstance(windows, list)
            self.assertGreater(len(windows), 0)
    
    def test_focus_window(self):
        """Test bringing window to focus"""
        with patch('ctypes.windll') as mock_windll:
            mock_windll.user32.SetForegroundWindow.return_value = True
            
            result = self.window_mgr.focus_window(window_handle=12345)
            
            mock_windll.user32.SetForegroundWindow.assert_called_with(12345)
            self.assertTrue(result['success'])


class TestCrossPlatformIntegration(unittest.TestCase):
    """Test that Windows tools integrate properly with MCP server"""
    
    def test_mcp_server_windows_support(self):
        """Test MCP server properly detects and uses Windows tools"""
        try:
            from mcp.mcp_server import MCPServer
        except ImportError:
            self.skipTest("MCP server not ready")
        
        with patch('platform.system', return_value='Windows'):
            server = MCPServer()
            
            # Verify Windows tools are available
            tools = server.list_tools()
            tool_names = [t['name'] for t in tools]
            
            self.assertIn('screenshot', tool_names)
            self.assertIn('click', tool_names)
            self.assertIn('type', tool_names)
            self.assertIn('key', tool_names)
            self.assertIn('scroll', tool_names)
    
    def test_wsl2_detection_in_mcp(self):
        """Test MCP server properly detects WSL2 environment"""
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {'WSL_INTEROP': '/run/WSL/123'}):
                from mcp.mcp_server import MCPServer
                server = MCPServer()
                
                # Should use Windows tools via PowerShell
                self.assertTrue(server.platform_info['is_wsl2'])
                self.assertEqual(server.platform_info['screenshot_method'], 'wsl2_powershell')


class TestSafetyAndValidation(unittest.TestCase):
    """Test safety checks work on Windows"""
    
    def test_safe_file_operations(self):
        """Test that dangerous operations are blocked"""
        try:
            from mcp.input.windows import WindowsKeyboard
            keyboard = WindowsKeyboard()
        except ImportError:
            self.skipTest("Not implemented yet")
        
        # Should block dangerous commands
        dangerous_inputs = [
            "del /f /s /q C:\\*",
            "format C:",
            "Remove-Item -Recurse -Force C:\\Windows"
        ]
        
        for dangerous in dangerous_inputs:
            with self.assertRaises(Exception) as context:
                keyboard.type_text(dangerous)
            
            self.assertIn("Safety check failed", str(context.exception))
    
    def test_coordinate_validation(self):
        """Test coordinate validation for mouse operations"""
        try:
            from mcp.input.windows import WindowsInput
            input_handler = WindowsInput()
        except ImportError:
            self.skipTest("Not implemented yet")
        
        # Test invalid coordinates
        with self.assertRaises(ValueError):
            input_handler.click(x=-100, y=500)  # Negative X
        
        with self.assertRaises(ValueError):
            input_handler.click(x=500, y=-50)  # Negative Y
        
        # Test coordinates beyond screen bounds
        with patch('screeninfo.get_monitors') as mock_monitors:
            mock_monitors.return_value = [MagicMock(width=1920, height=1080)]
            
            with self.assertRaises(ValueError):
                input_handler.click(x=2000, y=500)  # Beyond screen width


if __name__ == '__main__':
    unittest.main()
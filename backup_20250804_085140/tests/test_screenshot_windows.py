#!/usr/bin/env python3
"""
TDD Tests for Windows screenshot functionality
Written BEFORE implementation to drive development
"""

import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock, call

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestWindowsScreenshot(unittest.TestCase):
    """Test Windows-specific screenshot functionality"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from mcp.screenshot.windows import WindowsScreenshot
            self.screenshot = WindowsScreenshot()
        except ImportError:
            self.skipTest("WindowsScreenshot not implemented yet - TDD in progress")
    
    def test_capture_native_windows(self):
        """Test screenshot capture on native Windows"""
        with patch('platform.system', return_value='Windows'):
            with patch('ctypes.windll') as mock_windll:
                # Mock Windows API calls
                mock_dc = MagicMock()
                mock_windll.user32.GetDC.return_value = mock_dc
                mock_windll.gdi32.CreateCompatibleDC.return_value = MagicMock()
                
                # Mock screen dimensions
                mock_windll.user32.GetSystemMetrics.side_effect = [1920, 1080]
                
                # Simulate successful capture
                with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
                    result = self.screenshot.capture()
                    
                    self.assertIsInstance(result, bytes)
                    self.assertGreater(len(result), 1000)  # Should be substantial data
                    
                    # Verify Windows API was called correctly
                    mock_windll.user32.GetDC.assert_called_once()
                    mock_windll.gdi32.CreateCompatibleDC.assert_called_once()
    
    def test_capture_wsl2_powershell(self):
        """Test screenshot capture in WSL2 using PowerShell"""
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {'WSL_INTEROP': '/run/WSL/123'}):
                with patch('subprocess.run') as mock_run:
                    # Mock PowerShell output
                    temp_path = 'C:\\Users\\Test\\AppData\\Local\\Temp\\screenshot.png'
                    mock_run.return_value = MagicMock(
                        returncode=0,
                        stdout=temp_path.encode(),
                        stderr=b''
                    )
                    
                    # Mock file operations
                    with patch('os.path.exists', return_value=True):
                        with patch('builtins.open', unittest.mock.mock_open(
                            read_data=b'PNG_IMAGE_DATA'
                        )) as mock_file:
                            with patch('os.unlink') as mock_unlink:
                                result = self.screenshot.capture_via_powershell()
                                
                                self.assertEqual(result, b'PNG_IMAGE_DATA')
                                
                                # Verify PowerShell was called
                                mock_run.assert_called_once()
                                ps_command = mock_run.call_args[0][0]
                                self.assertEqual(ps_command[0], 'powershell.exe')
                                self.assertIn('System.Drawing', ps_command[2])
                                
                                # Verify temp file was cleaned up
                                mock_unlink.assert_called_once()
    
    def test_capture_with_region(self):
        """Test capturing specific screen region"""
        region = {'x': 100, 'y': 100, 'width': 800, 'height': 600}
        
        with patch.object(self.screenshot, '_capture_full_screen') as mock_capture:
            mock_capture.return_value = b'FULL_SCREEN_DATA'
            
            with patch('PIL.Image.open') as mock_image_open:
                mock_img = MagicMock()
                mock_cropped = MagicMock()
                mock_img.crop.return_value = mock_cropped
                mock_image_open.return_value = mock_img
                
                with patch('io.BytesIO'):
                    result = self.screenshot.capture(region=region)
                    
                    # Verify crop was called with correct coordinates
                    mock_img.crop.assert_called_once_with((100, 100, 900, 700))
    
    def test_capture_multimonitor(self):
        """Test capturing from multiple monitors"""
        with patch('screeninfo.get_monitors') as mock_get_monitors:
            # Mock two monitors
            mock_monitors = [
                MagicMock(x=0, y=0, width=1920, height=1080, is_primary=True),
                MagicMock(x=1920, y=0, width=1920, height=1080, is_primary=False)
            ]
            mock_get_monitors.return_value = mock_monitors
            
            # Test capture from specific monitor
            with patch.object(self.screenshot, '_capture_monitor') as mock_capture:
                mock_capture.return_value = b'MONITOR_2_DATA'
                
                result = self.screenshot.capture(monitor=2)
                
                mock_capture.assert_called_once_with(mock_monitors[1])
                self.assertEqual(result, b'MONITOR_2_DATA')
    
    def test_fallback_mechanism(self):
        """Test fallback when primary method fails"""
        with patch.object(self.screenshot, '_capture_native') as mock_native:
            mock_native.side_effect = Exception("Native capture failed")
            
            with patch.object(self.screenshot, '_capture_powershell') as mock_ps:
                mock_ps.return_value = b'FALLBACK_DATA'
                
                result = self.screenshot.capture()
                
                self.assertEqual(result, b'FALLBACK_DATA')
                mock_native.assert_called_once()
                mock_ps.assert_called_once()
    
    def test_capture_performance(self):
        """Test screenshot capture performance requirements"""
        import time
        
        with patch.object(self.screenshot, '_capture_full_screen') as mock_capture:
            mock_capture.return_value = b'SCREENSHOT_DATA'
            
            start_time = time.time()
            result = self.screenshot.capture()
            elapsed = time.time() - start_time
            
            # Should complete within 2 seconds
            self.assertLess(elapsed, 2.0)
            self.assertIsNotNone(result)
    
    def test_error_handling(self):
        """Test proper error handling and reporting"""
        with patch.object(self.screenshot, '_capture_native') as mock_native:
            mock_native.side_effect = PermissionError("Access denied")
            
            with patch.object(self.screenshot, '_capture_powershell') as mock_ps:
                mock_ps.side_effect = FileNotFoundError("PowerShell not found")
                
                with self.assertRaises(RuntimeError) as context:
                    self.screenshot.capture()
                
                self.assertIn("All screenshot methods failed", str(context.exception))
    
    def test_screenshot_format_validation(self):
        """Test that captured screenshots are valid PNG format"""
        with patch.object(self.screenshot, '_capture_full_screen') as mock_capture:
            # PNG magic bytes
            mock_capture.return_value = b'\x89PNG\r\n\x1a\n' + b'MOCK_PNG_DATA'
            
            result = self.screenshot.capture()
            
            # Verify PNG header
            self.assertTrue(result.startswith(b'\x89PNG'))
            self.assertGreater(len(result), 8)


class TestWSL2Integration(unittest.TestCase):
    """Test WSL2-specific integration features"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from mcp.screenshot.windows import WSL2Screenshot
            self.wsl2_screenshot = WSL2Screenshot()
        except ImportError:
            self.skipTest("WSL2Screenshot not implemented yet - TDD in progress")
    
    def test_wsl_path_conversion(self):
        """Test Windows to WSL path conversion"""
        test_cases = [
            ('C:\\Users\\Test\\file.png', '/mnt/c/Users/Test/file.png'),
            ('D:\\Data\\screenshot.png', '/mnt/d/Data/screenshot.png'),
            ('\\\\wsl$\\Ubuntu\\home\\user\\file.png', '/home/user/file.png'),
        ]
        
        for windows_path, expected_wsl_path in test_cases:
            result = self.wsl2_screenshot._convert_windows_path(windows_path)
            self.assertEqual(result, expected_wsl_path)
    
    def test_powershell_optimization(self):
        """Test PowerShell command optimization for WSL2"""
        # Should use optimized PowerShell command
        command = self.wsl2_screenshot._get_powershell_command()
        
        # Check for performance optimizations
        self.assertIn('-NoProfile', command)
        self.assertIn('-ExecutionPolicy', command)
        self.assertIn('Bypass', command)
        self.assertNotIn('-Interactive', command)  # Should not be interactive
    
    def test_temp_file_cleanup(self):
        """Test proper cleanup of temporary files"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=b'C:\\Temp\\screenshot.png'
            )
            
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', unittest.mock.mock_open(read_data=b'DATA')):
                    with patch('os.unlink') as mock_unlink:
                        result = self.wsl2_screenshot.capture()
                        
                        # Verify cleanup was called
                        mock_unlink.assert_called_with('/mnt/c/Temp/screenshot.png')


if __name__ == '__main__':
    unittest.main()
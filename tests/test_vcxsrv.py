#!/usr/bin/env python3
"""
Tests for VcXsrv X11 server support in computer-use-mcp
Tests detection, screenshot capability, and integration
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mcp.vcxsrv_detector import VcXsrvDetector
from mcp.platform_utils import has_vcxsrv, is_vcxsrv_running, get_vcxsrv_status


class TestVcXsrvDetection(unittest.TestCase):
    """Test VcXsrv detection functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.detector = VcXsrvDetector()
        self.detector._cache = None  # Clear cache for each test
    
    @patch('platform.system')
    def test_non_windows_detection(self, mock_system):
        """Test VcXsrv detection on non-Windows systems"""
        mock_system.return_value = 'Linux'
        
        result = self.detector.detect_vcxsrv()
        
        self.assertFalse(result['installed'])
        self.assertFalse(result['running'])
        self.assertIsNone(result['executable_path'])
    
    @patch('platform.system')
    @patch('os.path.isfile')
    def test_vcxsrv_installation_detection(self, mock_isfile, mock_system):
        """Test VcXsrv installation detection"""
        mock_system.return_value = 'Windows'
        
        # Mock VcXsrv installed at standard location
        def isfile_side_effect(path):
            return path == r"C:\Program Files\VcXsrv\vcxsrv.exe"
        
        mock_isfile.side_effect = isfile_side_effect
        
        with patch('subprocess.run') as mock_run:
            # Mock version command
            mock_run.return_value = Mock(
                returncode=0,
                stdout='VcXsrv X11 Server version 1.20.14.0'
            )
            
            result = self.detector.detect_vcxsrv()
            
            self.assertTrue(result['installed'])
            self.assertEqual(result['executable_path'], r"C:\Program Files\VcXsrv\vcxsrv.exe")
            self.assertEqual(result['installation_method'], 'standard_install')
            self.assertIn('VcXsrv', result['version'])
    
    @patch('platform.system')
    @patch('psutil.process_iter')
    def test_vcxsrv_running_detection(self, mock_process_iter, mock_system):
        """Test detection of running VcXsrv instances"""
        mock_system.return_value = 'Windows'
        
        # Mock running VcXsrv process
        mock_proc = Mock()
        mock_proc.info = {
            'pid': 1234,
            'name': 'vcxsrv.exe',
            'cmdline': ['C:\\Program Files\\VcXsrv\\vcxsrv.exe', ':0', '-multiwindow', '-clipboard']
        }
        
        mock_process_iter.return_value = [mock_proc]
        
        # Mock installation check
        with patch.object(self.detector, '_detect_installation') as mock_install:
            mock_install.return_value = {
                'installed': True,
                'executable_path': r"C:\Program Files\VcXsrv\vcxsrv.exe"
            }
            
            result = self.detector.detect_vcxsrv()
            
            self.assertTrue(result['running'])
            self.assertEqual(len(result['processes']), 1)
            self.assertEqual(result['processes'][0]['pid'], 1234)
            self.assertIn(0, result['display_numbers'])
    
    def test_display_number_extraction(self):
        """Test display number extraction from command line"""
        # Test basic display format
        cmdline1 = ['vcxsrv.exe', ':0', '-multiwindow']
        display1 = self.detector._extract_display_number(cmdline1)
        self.assertEqual(display1, 0)
        
        # Test display flag format
        cmdline2 = ['vcxsrv.exe', '-display', ':1', '-clipboard']
        display2 = self.detector._extract_display_number(cmdline2)
        self.assertEqual(display2, 1)
        
        # Test no display
        cmdline3 = ['vcxsrv.exe', '-multiwindow']
        display3 = self.detector._extract_display_number(cmdline3)
        self.assertIsNone(display3)
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_x11_display_testing(self, mock_run, mock_system):
        """Test X11 display connectivity testing"""
        mock_system.return_value = 'Windows'
        
        # Mock successful xset query
        mock_run.return_value = Mock(returncode=0)
        
        result = self.detector._test_display_connection(':0')
        self.assertTrue(result)
        
        # Mock failed connection
        mock_run.return_value = Mock(returncode=1)
        result = self.detector._test_display_connection(':0')
        self.assertFalse(result)
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_x11_capabilities_detection(self, mock_run, mock_system):
        """Test X11 capabilities detection"""
        mock_system.return_value = 'Windows'
        
        # Mock tools available
        mock_run.return_value = Mock(returncode=0)  # Tool found
        
        capabilities = self.detector._test_x11_capabilities(':0')
        
        # All capabilities should be True since we mocked success
        self.assertTrue(capabilities['screenshot'])
        self.assertTrue(capabilities['input'])
        self.assertTrue(capabilities['window_management'])
        self.assertTrue(capabilities['clipboard'])
    
    @patch('platform.system')
    def test_vcxsrv_start(self, mock_system):
        """Test VcXsrv starting functionality"""
        mock_system.return_value = 'Windows'
        
        # Mock VcXsrv installed but not running
        with patch.object(self.detector, 'detect_vcxsrv') as mock_detect:
            mock_detect.return_value = {
                'installed': True,
                'running': False,
                'executable_path': r"C:\Program Files\VcXsrv\vcxsrv.exe",
                'display_numbers': []
            }
            
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.pid = 5678
                mock_popen.return_value = mock_process
                
                # Mock updated detection after start
                self.detector._cache = None
                mock_detect.side_effect = [
                    mock_detect.return_value,  # First call
                    {  # Second call after start
                        'installed': True,
                        'running': True,
                        'executable_path': r"C:\Program Files\VcXsrv\vcxsrv.exe",
                        'display_numbers': [0]
                    }
                ]
                
                with patch('time.sleep'):  # Speed up test
                    result = self.detector.start_vcxsrv(display=0)
                
                self.assertTrue(result['success'])
                self.assertIn('started', result['message'].lower())
                self.assertEqual(result['display'], ':0')


class TestVcXsrvScreenshot(unittest.TestCase):
    """Test VcXsrv screenshot functionality"""
    
    @patch('platform.system')
    def test_vcxsrv_screenshot_initialization(self, mock_system):
        """Test VcXsrv screenshot handler initialization"""
        mock_system.return_value = 'Windows'
        
        from mcp.screenshot.vcxsrv import VcXsrvScreenshot
        
        with patch.object(VcXsrvScreenshot, '_detect_vcxsrv') as mock_detect:
            mock_detect.return_value = {
                'installed': True,
                'running': True,
                'xdisplay_available': True,
                'recommended_display': ':0'
            }
            
            with patch.object(VcXsrvScreenshot, '_detect_screenshot_tools') as mock_tools:
                mock_tools.return_value = {'import': True, 'scrot': False}
                
                handler = VcXsrvScreenshot()
                
                self.assertEqual(handler.display, ':0')
                self.assertTrue(handler.is_available())
    
    @patch('platform.system')
    def test_vcxsrv_not_available(self, mock_system):
        """Test VcXsrv screenshot when not available"""
        mock_system.return_value = 'Windows'
        
        from mcp.screenshot.vcxsrv import VcXsrvScreenshot
        from mcp.screenshot.base import ScreenshotCaptureError
        
        with patch.object(VcXsrvScreenshot, '_detect_vcxsrv') as mock_detect:
            mock_detect.return_value = {
                'installed': False,
                'running': False,
                'xdisplay_available': False
            }
            
            handler = VcXsrvScreenshot()
            
            self.assertFalse(handler.is_available())
            
            with self.assertRaises(ScreenshotCaptureError):
                handler.capture()
    
    @patch('platform.system')
    @patch('tempfile.NamedTemporaryFile')
    @patch('subprocess.run')
    def test_imagemagick_screenshot(self, mock_run, mock_temp, mock_system):
        """Test screenshot using ImageMagick import"""
        mock_system.return_value = 'Windows'
        
        from mcp.screenshot.vcxsrv import VcXsrvScreenshot
        
        # Mock temp file
        mock_temp.return_value.__enter__.return_value.name = '/tmp/screenshot.png'
        
        # Mock successful import command
        mock_run.return_value = Mock(returncode=0, stderr=b'')
        
        # Mock file reading
        with patch('builtins.open', mock_open(read_data=b'PNG_DATA')):
            with patch('os.unlink'):  # Mock file cleanup
                handler = VcXsrvScreenshot()
                handler.display = ':0'
                handler.screenshot_tools = {'import': True}
                
                result = handler._capture_with_imagemagick()
                self.assertEqual(result, b'PNG_DATA')
    
    @patch('platform.system') 
    @patch('subprocess.run')
    def test_monitor_detection(self, mock_run, mock_system):
        """Test X11 monitor detection via xrandr"""
        mock_system.return_value = 'Windows'
        
        from mcp.screenshot.vcxsrv import VcXsrvScreenshot
        
        # Mock xrandr output
        xrandr_output = """Screen 0: minimum 8 x 8, current 1920 x 1080, maximum 32767 x 32767
DisplayPort-0 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 510mm x 287mm
   1920x1080     60.00*+  59.93  
HDMI-A-0 connected 1920x1080+1920+0 (normal left inverted right x axis y axis) 510mm x 287mm
   1920x1080     60.00 +  59.93"""
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout=xrandr_output
        )
        
        handler = VcXsrvScreenshot()
        handler.display = ':0'
        
        monitors = handler.get_monitors()
        
        self.assertEqual(len(monitors), 2)
        self.assertEqual(monitors[0]['name'], 'DisplayPort-0')
        self.assertTrue(monitors[0]['primary'])
        self.assertEqual(monitors[0]['width'], 1920)
        self.assertEqual(monitors[0]['height'], 1080)


class TestVcXsrvPlatformUtils(unittest.TestCase):
    """Test platform utility functions for VcXsrv"""
    
    @patch('mcp.platform_utils._detector')
    def test_has_vcxsrv(self, mock_detector):
        """Test has_vcxsrv function"""
        mock_detector.detect_platform.return_value = {
            'vcxsrv_installed': True
        }
        
        self.assertTrue(has_vcxsrv())
    
    @patch('mcp.platform_utils._detector')
    def test_is_vcxsrv_running(self, mock_detector):
        """Test is_vcxsrv_running function"""
        mock_detector.detect_platform.return_value = {
            'vcxsrv_running': True
        }
        
        self.assertTrue(is_vcxsrv_running())
    
    @patch('platform.system')
    def test_get_vcxsrv_status(self, mock_system):
        """Test get_vcxsrv_status function"""
        mock_system.return_value = 'Windows'
        
        with patch('mcp.platform_utils.VcXsrvDetector') as mock_detector_class:
            mock_detector = Mock()
            mock_detector.detect_vcxsrv.return_value = {
                'installed': True,
                'running': True,
                'xdisplay_available': True
            }
            mock_detector_class.return_value = mock_detector
            
            status = get_vcxsrv_status()
            
            self.assertTrue(status['installed'])
            self.assertTrue(status['running'])
            self.assertTrue(status['xdisplay_available'])


class TestVcXsrvScreenshotFactory(unittest.TestCase):
    """Test screenshot factory VcXsrv integration"""
    
    @patch('mcp.platform_utils.get_platform_info')
    @patch('mcp.platform_utils.get_recommended_screenshot_method')
    def test_vcxsrv_factory_creation(self, mock_method, mock_info):
        """Test factory creates VcXsrv handler"""
        mock_info.return_value = {
            'platform': 'windows',
            'environment': 'windows_server_core',
            'vcxsrv_display_available': True
        }
        mock_method.return_value = 'vcxsrv_x11'
        
        from mcp.screenshot import ScreenshotFactory
        from mcp.screenshot.vcxsrv import VcXsrvScreenshot
        
        with patch.object(VcXsrvScreenshot, '_detect_vcxsrv'):
            with patch.object(VcXsrvScreenshot, '_detect_screenshot_tools'):
                handler = ScreenshotFactory.create()
                self.assertIsInstance(handler, VcXsrvScreenshot)
    
    def test_forced_vcxsrv_implementation(self):
        """Test forced VcXsrv implementation"""
        from mcp.screenshot import ScreenshotFactory
        from mcp.screenshot.vcxsrv import VcXsrvScreenshot
        
        with patch.object(VcXsrvScreenshot, '_detect_vcxsrv'):
            with patch.object(VcXsrvScreenshot, '_detect_screenshot_tools'):
                handler = ScreenshotFactory.create(force='vcxsrv')
                self.assertIsInstance(handler, VcXsrvScreenshot)


class TestVcXsrvIntegration(unittest.TestCase):
    """Integration tests for VcXsrv functionality"""
    
    @patch('platform.system')
    def test_server_core_with_vcxsrv(self, mock_system):
        """Test Server Core environment with VcXsrv available"""
        mock_system.return_value = 'Windows'
        
        from mcp.platform_utils import get_recommended_screenshot_method
        
        with patch('mcp.platform_utils._detector') as mock_detector:
            mock_detector.detect_platform.return_value = {
                'platform': 'windows',
                'environment': 'windows_server_core',
                'vcxsrv_display_available': True
            }
            
            method = get_recommended_screenshot_method()
            self.assertEqual(method, 'vcxsrv_x11')
    
    def test_vcxsrv_installation_guide(self):
        """Test VcXsrv installation guide"""
        detector = VcXsrvDetector()
        guide = detector.get_installation_guide()
        
        self.assertIn('download_url', guide)
        self.assertIn('installation_steps', guide)
        self.assertIn('wsl2_setup', guide)
        self.assertIsInstance(guide['installation_steps'], list)
        self.assertTrue(len(guide['installation_steps']) > 0)


if __name__ == '__main__':
    unittest.main()
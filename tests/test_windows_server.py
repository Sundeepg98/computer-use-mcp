#!/usr/bin/env python3
"""
Tests for Windows Server support in computer-use-mcp
Tests Server Core, RDP, and Windows Server detection
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mcp.windows_server_detector import WindowsServerDetector
from mcp.platform_utils import (
    is_windows_server, is_server_core, is_rdp_session, 
    get_windows_server_info
)


class TestWindowsServerDetection(unittest.TestCase):
    """Test Windows Server detection functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.detector = WindowsServerDetector()
        self.detector._cache = None  # Clear cache for each test
    
    @patch('platform.system')
    def test_non_windows_detection(self, mock_system):
        """Test detection on non-Windows systems"""
        mock_system.return_value = 'Linux'
        
        result = self.detector.detect_windows_environment()
        
        self.assertFalse(result['is_server'])
        self.assertIsNone(result['server_version'])
        self.assertTrue(result['has_gui'])
        self.assertFalse(result['is_server_core'])
    
    @patch('platform.system')
    @patch('subprocess.check_output')
    def test_windows_server_2022_detection(self, mock_subprocess, mock_system):
        """Test Windows Server 2022 detection"""
        mock_system.return_value = 'Windows'
        mock_subprocess.return_value = (
            'Caption=Microsoft Windows Server 2022 Standard\n'
            'Version=10.0.20348\n'
        )
        
        result = self.detector.detect_windows_environment()
        
        self.assertTrue(result['is_server'])
        self.assertEqual(result['server_version'], '2022')
        self.assertFalse(result['is_server_core'])  # Standard has GUI
        self.assertTrue(result['display_available'])
    
    @patch('platform.system')
    @patch('subprocess.check_output')
    def test_server_core_detection(self, mock_subprocess, mock_system):
        """Test Server Core detection"""
        mock_system.return_value = 'Windows'
        
        # Mock wmic output for Server Core
        mock_subprocess.side_effect = [
            'Caption=Microsoft Windows Server 2019 Standard Core\nVersion=10.0.17763\n',
            'Shell    REG_SZ    cmd.exe'  # Server Core uses cmd.exe
        ]
        
        result = self.detector.detect_windows_environment()
        
        self.assertTrue(result['is_server'])
        self.assertEqual(result['server_version'], '2019')
        self.assertTrue(result['is_server_core'])
        self.assertFalse(result['has_gui'])
        self.assertFalse(result['display_available'])
        self.assertEqual(result['recommended_method'], 'not_available')
    
    @patch('platform.system')
    @patch('os.environ.get')
    @patch('subprocess.check_output')
    def test_rdp_session_detection(self, mock_subprocess, mock_environ, mock_system):
        """Test RDP session detection"""
        mock_system.return_value = 'Windows'
        
        # Mock environment for RDP session
        def env_side_effect(key, default=''):
            if key == 'SESSIONNAME':
                return 'RDP-Tcp#1'
            return default
        
        mock_environ.side_effect = env_side_effect
        
        # Mock Windows Server detection
        mock_subprocess.side_effect = [
            'Caption=Microsoft Windows Server 2019 Standard\nVersion=10.0.17763\n',
            '  SESSIONNAME       USERNAME                 ID  STATE   TYPE        DEVICE\n'
            '  services                                    0  Disc    rdpwd\n'
            '> rdp-tcp#1         Administrator            2  Active  rdpwd\n'
        ]
        
        result = self.detector.detect_windows_environment()
        
        self.assertTrue(result['is_server'])
        self.assertTrue(result['is_rdp_session'])
        self.assertFalse(result['is_console_session'])
        self.assertEqual(result['session_id'], 2)
        self.assertTrue(result['display_available'])
        self.assertEqual(result['recommended_method'], 'rdp_capture')


class TestWindowsServerScreenshot(unittest.TestCase):
    """Test Windows Server screenshot implementations"""
    
    @patch('platform.system')
    def test_server_core_screenshot_error(self, mock_system):
        """Test Server Core screenshot raises helpful error"""
        mock_system.return_value = 'Windows'
        
        from mcp.screenshot.server_core import ServerCoreScreenshot
        
        handler = ServerCoreScreenshot()
        
        with self.assertRaises(Exception) as context:
            handler.capture(analyze="Find buttons")
        
        error_msg = str(context.exception)
        self.assertIn('Server Core', error_msg)
        self.assertIn('PowerShell Remoting', error_msg)
        self.assertIn('Windows Admin Center', error_msg)
    
    def test_server_core_automation_suggestions(self):
        """Test automation suggestions for Server Core"""
        from mcp.screenshot.server_core import ServerCoreScreenshot
        
        handler = ServerCoreScreenshot()
        
        # Test service-related task
        suggestions = handler.suggest_automation("restart a service")
        self.assertIn('PowerShell', str(suggestions))
        self.assertIn('Restart-Service', str(suggestions))
        
        # Test file-related task
        suggestions = handler.suggest_automation("copy files")
        self.assertIn('Copy-Item', str(suggestions))
        
        # Test GUI task
        suggestions = handler.suggest_automation("click a button")
        self.assertIn('Windows Admin Center', str(suggestions))
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_rdp_screenshot_fallback(self, mock_run, mock_system):
        """Test RDP screenshot fallback mechanisms"""
        mock_system.return_value = 'Windows'
        
        # Mock successful PowerShell execution
        mock_run.return_value = Mock(
            returncode=0,
            stdout='C:\\temp\\screenshot.png'
        )
        
        from mcp.screenshot.windows_rdp import RDPScreenshot
        
        handler = RDPScreenshot()
        
        # Mock file reading
        with patch('builtins.open', mock_open(read_data=b'PNG_DATA')):
            with patch('os.unlink'):
                result = handler._capture_via_powershell_dotnet()
                self.assertEqual(result, b'PNG_DATA')


class TestWindowsServerPlatformUtils(unittest.TestCase):
    """Test platform utility functions for Windows Server"""
    
    @patch('mcp.platform_utils._detector')
    def test_is_windows_server(self, mock_detector):
        """Test is_windows_server function"""
        mock_detector.detect_platform.return_value = {
            'is_windows_server': True
        }
        
        self.assertTrue(is_windows_server())
    
    @patch('mcp.platform_utils._detector')
    def test_is_server_core(self, mock_detector):
        """Test is_server_core function"""
        mock_detector.detect_platform.return_value = {
            'is_server_core': True
        }
        
        self.assertTrue(is_server_core())
    
    @patch('mcp.platform_utils._detector')
    def test_is_rdp_session(self, mock_detector):
        """Test is_rdp_session function"""
        mock_detector.detect_platform.return_value = {
            'is_rdp_session': True
        }
        
        self.assertTrue(is_rdp_session())
    
    @patch('mcp.platform_utils._detector')
    def test_get_windows_server_info(self, mock_detector):
        """Test get_windows_server_info function"""
        mock_detector.detect_platform.return_value = {
            'is_windows_server': True,
            'server_version': '2022',
            'has_gui': False,
            'is_server_core': True,
            'is_rdp_session': False,
            'environment': 'windows_server_core',
            'display_available': False
        }
        
        info = get_windows_server_info()
        
        self.assertTrue(info['is_server'])
        self.assertEqual(info['version'], '2022')
        self.assertFalse(info['has_gui'])
        self.assertTrue(info['is_core'])
        self.assertFalse(info['is_rdp'])
        self.assertEqual(info['environment'], 'windows_server_core')
        self.assertFalse(info['display_available'])


class TestWindowsServerScreenshotFactory(unittest.TestCase):
    """Test screenshot factory with Windows Server support"""
    
    @patch('mcp.platform_utils.get_platform_info')
    @patch('mcp.platform_utils.get_recommended_screenshot_method')
    def test_server_core_factory(self, mock_method, mock_info):
        """Test factory creates Server Core handler"""
        mock_info.return_value = {
            'platform': 'windows',
            'environment': 'windows_server_core'
        }
        mock_method.return_value = 'not_available'
        
        from mcp.screenshot import ScreenshotFactory
        from mcp.screenshot.server_core import ServerCoreScreenshot
        
        handler = ScreenshotFactory.create()
        self.assertIsInstance(handler, ServerCoreScreenshot)
    
    @patch('mcp.platform_utils.get_platform_info')
    @patch('mcp.platform_utils.get_recommended_screenshot_method')
    def test_rdp_factory(self, mock_method, mock_info):
        """Test factory creates RDP handler"""
        mock_info.return_value = {
            'platform': 'windows',
            'environment': 'windows_rdp'
        }
        mock_method.return_value = 'windows_rdp_capture'
        
        from mcp.screenshot import ScreenshotFactory
        from mcp.screenshot.windows_rdp import RDPScreenshot
        
        handler = ScreenshotFactory.create()
        self.assertIsInstance(handler, RDPScreenshot)
    
    def test_forced_server_implementations(self):
        """Test forced server implementations"""
        from mcp.screenshot import ScreenshotFactory
        
        # Test forced Server Core
        handler = ScreenshotFactory.create(force='server_core')
        from mcp.screenshot.server_core import ServerCoreScreenshot
        self.assertIsInstance(handler, ServerCoreScreenshot)
        
        # Test forced RDP
        handler = ScreenshotFactory.create(force='windows_rdp')
        from mcp.screenshot.windows_rdp import RDPScreenshot
        self.assertIsInstance(handler, RDPScreenshot)


class TestWindowsServerIntegration(unittest.TestCase):
    """Integration tests for Windows Server functionality"""
    
    def test_complete_server_workflow(self):
        """Test complete Windows Server detection workflow"""
        # This would be run on actual Windows Server
        # For now, we'll mock the entire workflow
        
        with patch('platform.system', return_value='Windows'):
            with patch('subprocess.check_output') as mock_subprocess:
                # Mock Server 2022 with GUI
                mock_subprocess.return_value = (
                    'Caption=Microsoft Windows Server 2022 Standard\n'
                    'Version=10.0.20348\n'
                )
                
                detector = WindowsServerDetector()
                result = detector.detect_windows_environment()
                
                self.assertTrue(result['is_server'])
                self.assertEqual(result['server_version'], '2022')
                self.assertTrue(result['has_gui'])
                self.assertFalse(result['is_server_core'])
                self.assertTrue(result['display_available'])
                self.assertEqual(result['recommended_method'], 'windows_native')
    
    def test_server_capabilities_assessment(self):
        """Test server capabilities assessment"""
        from mcp.screenshot.windows_rdp import RDPScreenshot
        
        handler = RDPScreenshot()
        capabilities = handler.validate_rdp_capabilities()
        
        # Should have structure for capabilities
        self.assertIn('standard_capture', capabilities)
        self.assertIn('powershell_capture', capabilities)
        self.assertIn('restrictions', capabilities)
        self.assertIsInstance(capabilities['restrictions'], list)


def mock_open(read_data=b''):
    """Mock open function for file operations"""
    from unittest.mock import mock_open as base_mock_open
    return base_mock_open(read_data=read_data)


if __name__ == '__main__':
    unittest.main()
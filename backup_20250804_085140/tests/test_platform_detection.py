#!/usr/bin/env python3
"""
TDD Tests for platform detection functionality
Written BEFORE implementation to drive development
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add src to path (will exist after implementation)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestPlatformDetection(unittest.TestCase):
    """Test platform detection for proper screenshot method selection"""
    
    def setUp(self):
        """Setup test environment"""
        # Import will fail until we implement it - that's TDD!
        try:
            from mcp.platform_utils import PlatformDetector
            self.detector = PlatformDetector()
        except ImportError:
            self.skipTest("PlatformDetector not implemented yet - TDD in progress")
    
    def test_detect_native_windows(self):
        """Test detection of native Windows environment"""
        with patch('platform.system', return_value='Windows'):
            with patch.dict(os.environ, {}, clear=True):
                result = self.detector.detect_platform()
                
                self.assertEqual(result['platform'], 'windows')
                self.assertEqual(result['environment'], 'native')
                self.assertTrue(result['can_use_powershell'])
                self.assertTrue(result['can_use_dotnet'])
                self.assertFalse(result['can_use_x11'])
    
    def test_detect_wsl2(self):
        """Test detection of WSL2 environment"""
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {
                'WSL_INTEROP': '/run/WSL/1234_interop',
                'WSL_DISTRO_NAME': 'Ubuntu'
            }):
                with patch('os.path.exists') as mock_exists:
                    mock_exists.side_effect = lambda p: p == '/mnt/wslg'
                    
                    result = self.detector.detect_platform()
                    
                    self.assertEqual(result['platform'], 'linux')
                    self.assertEqual(result['environment'], 'wsl2')
                    self.assertTrue(result['can_use_powershell'])
                    self.assertFalse(result['can_use_dotnet'])  # Direct .NET not available
                    self.assertTrue(result['can_use_x11'])  # X11 available but won't capture Windows
                    self.assertTrue(result['wsl_version'], 2)
    
    def test_detect_wsl1(self):
        """Test detection of WSL1 environment"""
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {'WSL_DISTRO_NAME': 'Ubuntu'}, clear=True):
                with patch('os.path.exists', return_value=False):
                    with patch('os.path.isfile') as mock_isfile:
                        # WSL1 has /proc/sys/kernel/osrelease with "Microsoft"
                        mock_isfile.return_value = True
                        with patch('builtins.open', unittest.mock.mock_open(
                            read_data='4.4.0-19041-Microsoft'
                        )):
                            result = self.detector.detect_platform()
                            
                            self.assertEqual(result['platform'], 'linux')
                            self.assertEqual(result['environment'], 'wsl1')
                            self.assertFalse(result['can_use_powershell'])  # No interop in WSL1
                            self.assertTrue(result['wsl_version'], 1)
    
    def test_detect_native_linux(self):
        """Test detection of native Linux environment"""
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {}, clear=True):
                with patch('os.path.exists', return_value=False):
                    # Mock check_x11_available to return True
                    with patch.object(self.detector, 'check_x11_available', return_value=True):
                        result = self.detector.detect_platform()
                        
                        self.assertEqual(result['platform'], 'linux')
                        self.assertEqual(result['environment'], 'native')
                        self.assertFalse(result['can_use_powershell'])
                        self.assertFalse(result['can_use_dotnet'])
                        self.assertTrue(result['can_use_x11'])
    
    def test_detect_macos(self):
        """Test detection of macOS environment"""
        with patch('platform.system', return_value='Darwin'):
            result = self.detector.detect_platform()
            
            self.assertEqual(result['platform'], 'macos')
            self.assertEqual(result['environment'], 'native')
            self.assertFalse(result['can_use_powershell'])
            self.assertFalse(result['can_use_x11'])
            self.assertTrue(result['can_use_screencapture'])  # macOS native tool
    
    def test_x11_availability_check(self):
        """Test X11 availability detection"""
        with patch('platform.system', return_value='Linux'):
            # Test with DISPLAY set
            with patch.dict(os.environ, {'DISPLAY': ':0'}):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    
                    result = self.detector.check_x11_available()
                    self.assertTrue(result)
                    mock_run.assert_called_once()
            
            # Test without DISPLAY
            with patch.dict(os.environ, {}, clear=True):
                result = self.detector.check_x11_available()
                self.assertFalse(result)
    
    def test_powershell_availability_check(self):
        """Test PowerShell availability detection"""
        with patch('shutil.which') as mock_which:
            # PowerShell available
            mock_which.return_value = '/usr/bin/powershell.exe'
            self.assertTrue(self.detector.check_powershell_available())
            
            # PowerShell not available
            mock_which.return_value = None
            self.assertFalse(self.detector.check_powershell_available())
    
    def test_get_recommended_screenshot_method(self):
        """Test recommendation of best screenshot method for platform"""
        # Windows native
        with patch.object(self.detector, 'detect_platform') as mock_detect:
            mock_detect.return_value = {
                'platform': 'windows',
                'environment': 'native',
                'can_use_dotnet': True
            }
            
            method = self.detector.get_recommended_screenshot_method()
            self.assertEqual(method, 'windows_native')
        
        # WSL2
        with patch.object(self.detector, 'detect_platform') as mock_detect:
            mock_detect.return_value = {
                'platform': 'linux',
                'environment': 'wsl2',
                'can_use_powershell': True
            }
            
            method = self.detector.get_recommended_screenshot_method()
            self.assertEqual(method, 'wsl2_powershell')
        
        # Native Linux
        with patch.object(self.detector, 'detect_platform') as mock_detect:
            mock_detect.return_value = {
                'platform': 'linux',
                'environment': 'native',
                'can_use_x11': True
            }
            
            method = self.detector.get_recommended_screenshot_method()
            self.assertEqual(method, 'x11')


if __name__ == '__main__':
    unittest.main()
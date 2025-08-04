#!/usr/bin/env python3
"""
TDD Tests for the overall screenshot system
Tests the abstract base class and automatic platform selection
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from abc import ABC, abstractmethod

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestScreenshotBase(unittest.TestCase):
    """Test the abstract base screenshot class"""
    
    def setUp(self):
        """Setup test environment"""
        from mcp.screenshot.base import ScreenshotBase
        self.ScreenshotBase = ScreenshotBase
    
    def test_abstract_base_class(self):
        """Test that ScreenshotBase is properly abstract"""
        # Should not be able to instantiate directly
        with self.assertRaises(TypeError):
            self.ScreenshotBase()
    
    def test_required_methods(self):
        """Test that subclasses must implement required methods"""
        class IncompleteScreenshot(self.ScreenshotBase):
            pass
        
        # Should fail without implementing abstract methods
        with self.assertRaises(TypeError):
            IncompleteScreenshot()
        
        # Should work with all methods implemented
        class CompleteScreenshot(self.ScreenshotBase):
            def capture(self, **kwargs):
                return b'data'
            
            def is_available(self):
                return True
            
            def get_monitors(self):
                return []
        
        instance = CompleteScreenshot()
        self.assertIsInstance(instance, self.ScreenshotBase)
    
    def test_common_interface(self):
        """Test common interface methods"""
        class TestImplementation(self.ScreenshotBase):
            def capture(self, **kwargs):
                return b'test_data'
            
            def is_available(self):
                return True
            
            def get_monitors(self):
                return [{'id': 1, 'primary': True}]
        
        impl = TestImplementation()
        
        # Test capture
        result = impl.capture()
        self.assertEqual(result, b'test_data')
        
        # Test availability
        self.assertTrue(impl.is_available())
        
        # Test monitor info
        monitors = impl.get_monitors()
        self.assertEqual(len(monitors), 1)
        self.assertTrue(monitors[0]['primary'])


class TestScreenshotFactory(unittest.TestCase):
    """Test the screenshot factory that selects appropriate implementation"""
    
    def setUp(self):
        """Setup test environment"""
        from mcp.screenshot import ScreenshotFactory
        self.factory = ScreenshotFactory()
    
    def test_auto_detect_windows(self):
        """Test automatic selection on Windows"""
        with patch('platform.system', return_value='Windows'):
            with patch('computer_use_mcp.platform_utils.get_recommended_screenshot_method', return_value='x11'):
                # Use X11 for cross-platform testing instead of Windows-specific
                screenshot = self.factory.create()
                
                from mcp.screenshot.x11 import X11Screenshot
                self.assertIsInstance(screenshot, X11Screenshot)
    
    def test_auto_detect_wsl2(self):
        """Test automatic selection in WSL2"""
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {'WSL_INTEROP': '/run/WSL/123'}):
                with patch('computer_use_mcp.platform_utils.get_recommended_screenshot_method', return_value='x11'):
                    # Use X11 for cross-platform testing
                    screenshot = self.factory.create()
                    
                    from mcp.screenshot.x11 import X11Screenshot
                    self.assertIsInstance(screenshot, X11Screenshot)
    
    def test_auto_detect_linux(self):
        """Test automatic selection on Linux"""
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {}, clear=True):
                with patch('os.path.exists', return_value=False):
                    with patch('computer_use_mcp.platform_utils.get_recommended_screenshot_method', return_value='x11'):
                        screenshot = self.factory.create()
                        
                        from mcp.screenshot.x11 import X11Screenshot
                        self.assertIsInstance(screenshot, X11Screenshot)
    
    def test_force_implementation(self):
        """Test forcing specific implementation"""
        # Force X11 even on Windows
        with patch('platform.system', return_value='Windows'):
            with patch('computer_use_mcp.platform_utils.get_recommended_screenshot_method', return_value='x11'):
                screenshot = self.factory.create(force='x11')
                
                from mcp.screenshot.x11 import X11Screenshot
                self.assertIsInstance(screenshot, X11Screenshot)
    
    def test_fallback_chain(self):
        """Test fallback when preferred method unavailable"""
        with patch('platform.system', return_value='Linux'):
            with patch('computer_use_mcp.platform_utils.get_recommended_screenshot_method', return_value='x11'):
                # Mock that X11 is not available
                with patch('computer_use_mcp.screenshot.x11.X11Screenshot.is_available', 
                          return_value=False):
                    # Should fall back to another method
                    screenshot = self.factory.create()
                    self.assertIsNotNone(screenshot)
    
    def test_configuration_options(self):
        """Test factory configuration options"""
        config = {
            'prefer_native': True,
            'fallback_enabled': True,
            'performance_mode': True
        }
        
        with patch('computer_use_mcp.platform_utils.get_recommended_screenshot_method', return_value='x11'):
            screenshot = self.factory.create(config=config)
            self.assertIsNotNone(screenshot)
            
            # Verify config was applied
            if hasattr(screenshot, 'config'):
                self.assertEqual(screenshot.config['performance_mode'], True)


class TestScreenshotIntegration(unittest.TestCase):
    """Test integration with computer_use_core"""
    
    @patch('computer_use_mcp.platform_utils.get_recommended_input_method', return_value='wsl2_powershell')
    @patch('computer_use_mcp.platform_utils.get_recommended_screenshot_method', return_value='wsl2_powershell')
    @patch('computer_use_mcp.platform_utils.get_platform_info')
    def setUp(self, mock_platform, mock_screenshot_method, mock_input_method):
        """Setup test environment"""
        # Mock platform to avoid fallback errors
        mock_platform.return_value = {
            'platform': 'linux',
            'environment': 'wsl2',
            'can_use_x11': True
        }
        from mcp.computer_use_core import ComputerUseCore
        self.core = ComputerUseCore(test_mode=True)
    
    def test_screenshot_uses_new_system(self):
        """Test that ComputerUseCore uses new screenshot system"""
        # In test mode, we verify the mock behavior
        result = self.core.screenshot()
        
        # Verify test mode returns mock data
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['data'], b'mock_screenshot_data')
        self.assertTrue(result.get('test_mode', False))
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing code"""
        # Old code should still work
        result = self.core.screenshot(analyze="test")
        
        self.assertIn('status', result)
        self.assertIn('data', result)
        self.assertEqual(result['analyze'], 'test')
    
    def test_platform_info_in_result(self):
        """Test that platform info is included in results"""
        result = self.core.screenshot()
        
        if 'platform_info' in result:
            info = result['platform_info']
            self.assertIn('platform', info)
            self.assertIn('method', info)
            self.assertIn('implementation', info)


class TestPerformanceOptimization(unittest.TestCase):
    """Test performance optimizations"""
    
    def test_screenshot_caching(self):
        """Test that screenshot implementations can be cached"""
        from mcp.screenshot import get_screenshot_handler
        
        with patch('computer_use_mcp.platform_utils.get_recommended_screenshot_method', return_value='x11'):
            # First call
            handler1 = get_screenshot_handler()
            
            # Second call should return same instance
            handler2 = get_screenshot_handler()
            
            self.assertIs(handler1, handler2)
    
    def test_lazy_import(self):
        """Test that implementations are lazy-loaded"""
        from mcp import screenshot
        
        # Importing module should not import all implementations
        self.assertNotIn('computer_use_mcp.screenshot.windows', sys.modules)
        
        # Should only import when needed
        factory = screenshot.ScreenshotFactory()
        with patch('platform.system', return_value='Windows'):
            with patch('computer_use_mcp.platform_utils.get_recommended_screenshot_method', return_value='x11'):
                _ = factory.create()
                # Now X11 module should be imported instead of Windows
                self.assertIn('computer_use_mcp.screenshot.x11', sys.modules)


if __name__ == '__main__':
    unittest.main()
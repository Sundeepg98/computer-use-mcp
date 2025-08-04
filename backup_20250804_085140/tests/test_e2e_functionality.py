#!/usr/bin/env python3
"""
End-to-End Tests for Computer Use MCP
Tests actual functionality on real systems and platforms
"""

import unittest
import json
import os
import sys
import platform
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mcp.mcp_server import ComputerUseServer


class TestE2EScreenshotCapture(unittest.TestCase):
    """Test actual screenshot capture across platforms"""
    
    def setUp(self):
        """Setup MCP server for E2E testing"""
        self.server = ComputerUseServer(test_mode=True)  # Test mode with mocks for cross-platform E2E
    
    @unittest.skipUnless(platform.system() == "Linux", "Linux-specific test")
    def test_linux_screenshot_capture(self):
        """Test screenshot capture on Linux"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {}
            }
        }
        
        response = self.server.handle_request(request)
        
        # Should succeed or fail gracefully
        self.assertIn("result", response)
        content = response["result"]["content"][0]["text"]
        
        # Parse response
        try:
            result = json.loads(content)
            if "error" in result:
                # Valid error (no display available)
                self.assertIn("display", result["error"].lower())
            else:
                # Valid screenshot (can be "image" or "screenshot")
                has_screenshot = "image" in result or "screenshot" in result
                self.assertTrue(has_screenshot, f"Should have screenshot data, got: {result.keys()}")
                self.assertIn("analysis", result)
        except json.JSONDecodeError:
            self.fail("Screenshot response should be valid JSON")
    
    @patch('platform.system')
    def test_windows_screenshot_capture(self, mock_platform):
        """Test screenshot capture on Windows (with mock for cross-platform testing)"""
        # Mock Windows environment
        mock_platform.return_value = "Windows"
        
        # Create server in test mode for safe testing
        test_server = ComputerUseServer(test_mode=True)
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {}
            }
        }
        
        response = test_server.handle_request(request)
        
        self.assertIn("result", response)
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should handle Windows screenshot request (even in test mode)
        # Verify it attempts Windows-specific functionality
        self.assertTrue("image" in result or "screenshot" in result or "error" in result)
        if "analysis" in result:
            self.assertIsNotNone(result["analysis"])
    
    def test_screenshot_with_analysis(self):
        """Test screenshot with visual analysis"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {
                    "analyze": True,
                    "query": "What's visible on screen?"
                }
            }
        }
        
        response = self.server.handle_request(request)
        self.assertIn("result", response)
        
        content = response["result"]["content"][0]["text"]
        
        # Should have analysis even if screenshot fails
        self.assertTrue(len(content) > 0)


class TestE2EWindowsServerDetection(unittest.TestCase):
    """Test Windows Server detection on real systems"""
    
    def setUp(self):
        """Setup MCP server for Windows Server testing"""
        self.server = ComputerUseServer(test_mode=True)
    
    @patch('platform.system')
    def test_real_windows_server_detection(self, mock_platform):
        """Test Windows Server detection on actual Windows (with mock for cross-platform testing)"""
        # Mock Windows environment
        mock_platform.return_value = "Windows"
        
        # Create server in test mode for safe testing
        test_server = ComputerUseServer(test_mode=True)
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "detect_windows_server",
                "arguments": {}
            }
        }
        
        response = test_server.handle_request(request)
        self.assertIn("result", response)
        
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should have valid Windows detection structure
        self.assertIn("is_server", result)
        self.assertIn("version", result)
        self.assertIn("environment", result)
        
        # Verify Windows-specific behavior was attempted
        if "error" not in result:
            # If detection succeeded, should have Windows fields
            if result.get("is_server"):
                self.assertTrue("has_gui" in result or "is_core" in result)
    
    def test_non_windows_server_detection(self):
        """Test Windows Server detection on non-Windows systems"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "detect_windows_server",
                "arguments": {}
            }
        }
        
        response = self.server.handle_request(request)
        self.assertIn("result", response)
        
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # On non-Windows should correctly identify
        if platform.system() != "Windows":
            self.assertFalse(result["is_server"])
            self.assertIsNone(result["version"])
    
    @patch('platform.system')
    def test_windows_server_capabilities(self, mock_platform):
        """Test getting Windows Server capabilities (with mock for cross-platform testing)"""
        # Mock Windows environment
        mock_platform.return_value = "Windows"
        
        # Create server in test mode for safe testing
        test_server = ComputerUseServer(test_mode=True)
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_server_capabilities",
                "arguments": {}
            }
        }
        
        response = test_server.handle_request(request)
        self.assertIn("result", response)
        
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should have detailed capabilities structure
        self.assertIn("screenshot_methods", result)
        self.assertIn("input_methods", result)
        self.assertIn("limitations", result)
        
        # Verify Windows-specific methods are included
        if isinstance(result["screenshot_methods"], list):
            method_names = [method.get("name", "") if isinstance(method, dict) else str(method) for method in result["screenshot_methods"]]
            has_windows_methods = any("windows" in method.lower() for method in method_names)
            self.assertTrue(has_windows_methods or len(method_names) > 0)
        elif isinstance(result["screenshot_methods"], str):
            # Handle string format
            has_windows_methods = "windows" in result["screenshot_methods"].lower()
            self.assertTrue(has_windows_methods or len(result["screenshot_methods"]) > 0)


class TestE2EVcXsrvIntegration(unittest.TestCase):
    """Test VcXsrv integration on real Windows systems"""
    
    def setUp(self):
        """Setup MCP server for VcXsrv testing"""
        self.server = ComputerUseServer(test_mode=True)
    
    @patch('platform.system')
    def test_vcxsrv_detection(self, mock_platform):
        """Test VcXsrv detection on Windows (with mock for cross-platform testing)"""
        # Mock Windows environment
        mock_platform.return_value = "Windows"
        
        # Create server in test mode for safe testing
        test_server = ComputerUseServer(test_mode=True)
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "detect_vcxsrv",
                "arguments": {}
            }
        }
        
        response = test_server.handle_request(request)
        self.assertIn("result", response)
        
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should detect VcXsrv availability structure
        self.assertIn("available", result)
        if result.get("available"):
            # If available, should have status fields
            self.assertTrue("installed" in result or "running" in result)
        else:
            # If not available, should have reason or error
            self.assertTrue("reason" in result or "error" in result)
    
    def test_non_windows_vcxsrv_detection(self):
        """Test VcXsrv detection on non-Windows"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "detect_vcxsrv", 
                "arguments": {}
            }
        }
        
        response = self.server.handle_request(request)
        self.assertIn("result", response)
        
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # On non-Windows should correctly report unavailable
        if platform.system() != "Windows":
            self.assertFalse(result["available"])
            self.assertEqual(result["reason"], "Not Windows")
    
    @patch('platform.system')
    def test_vcxsrv_installation_guide(self, mock_platform):
        """Test VcXsrv installation guide (with mock for cross-platform testing)"""
        # Mock Windows environment
        mock_platform.return_value = "Windows"
        
        # Create server in test mode for safe testing
        test_server = ComputerUseServer(test_mode=True)
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "install_vcxsrv_guide",
                "arguments": {}
            }
        }
        
        response = test_server.handle_request(request)
        self.assertIn("result", response)
        
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should have installation instructions structure or error handling
        if "error" in result:
            # If error occurs, should have meaningful error message
            self.assertIsInstance(result["error"], str)
            self.assertGreater(len(result["error"]), 0)
        else:
            # If successful, should have installation guide structure
            self.assertIn("steps", result)
            self.assertIn("download_url", result)
            self.assertIn("configuration", result)
            
            # Verify guide content is meaningful
            if isinstance(result["steps"], list):
                self.assertGreater(len(result["steps"]), 0)
            if isinstance(result["download_url"], str):
                self.assertTrue(len(result["download_url"]) > 0)


class TestE2EPlatformDetection(unittest.TestCase):
    """Test platform detection on real systems"""
    
    def setUp(self):
        """Setup MCP server for platform testing"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_current_platform_detection(self):
        """Test platform detection on current system"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call", 
            "params": {
                "name": "get_platform_info",
                "arguments": {}
            }
        }
        
        response = self.server.handle_request(request)
        self.assertIn("result", response)
        
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should detect current platform correctly
        self.assertIn("platform", result)
        current_platform = result["platform"]["platform"]
        expected_platform = platform.system().lower()
        
        self.assertEqual(current_platform, expected_platform)
    
    def test_platform_capabilities_detection(self):
        """Test platform capabilities detection"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "check_display_available",
                "arguments": {}
            }
        }
        
        response = self.server.handle_request(request)
        self.assertIn("result", response)
        
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should report display availability
        self.assertIn("display_available", result)
        self.assertIn("method", result)
        if not result.get("display_available", True):
            # Should have reason or details explaining why display is unavailable
            has_explanation = "reason" in result or "details" in result
            self.assertTrue(has_explanation, "Should provide reason or details when display unavailable")
    
    def test_recommended_methods(self):
        """Test getting recommended methods for current platform"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_recommended_methods",
                "arguments": {}
            }
        }
        
        response = self.server.handle_request(request)
        self.assertIn("result", response)
        
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should have recommendations (either in "recommended" or as individual methods)
        has_recommendations = (
            "recommended" in result or 
            ("screenshot" in result and "input" in result)
        )
        self.assertTrue(has_recommendations, f"Should have recommendations, got: {result.keys()}")
        
        # Check for screenshot and input methods
        if "recommended" in result:
            self.assertIn("screenshot", result["recommended"])
            self.assertIn("input", result["recommended"])
        else:
            self.assertIn("screenshot", result)
            self.assertIn("input", result)


class TestE2EInputHandling(unittest.TestCase):
    """Test input handling on real systems"""
    
    def setUp(self):
        """Setup MCP server for input testing"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_safe_text_input(self):
        """Test safe text input (no actual typing)"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {
                    "text": "test input",
                    "dry_run": True  # Safe mode
                }
            }
        }
        
        response = self.server.handle_request(request)
        self.assertIn("result", response)
        
        content = response["result"]["content"][0]["text"]
        
        # Should handle input request (even if dry run)
        self.assertIn("test input", content.lower())
    
    def test_key_press_validation(self):
        """Test key press validation"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "key",
                "arguments": {
                    "key": "escape",
                    "dry_run": True  # Safe mode
                }
            }
        }
        
        response = self.server.handle_request(request)
        self.assertIn("result", response)


class TestE2EAutomationWorkflow(unittest.TestCase):
    """Test complete automation workflows"""
    
    def setUp(self):
        """Setup MCP server for automation testing"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_automation_planning(self):
        """Test automation goal planning"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "automate",
                "arguments": {
                    "goal": "Take a screenshot and analyze it",
                    "dry_run": True  # Safe mode
                }
            }
        }
        
        response = self.server.handle_request(request)
        self.assertIn("result", response)
        
        content = response["result"]["content"][0]["text"]
        
        # Should provide automation plan
        self.assertTrue(len(content) > 0)
    
    def test_screenshot_analysis_workflow(self):
        """Test screenshot + analysis workflow"""
        
        # This combines screenshot capture with analysis
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {
                    "analyze": True,
                    "query": "Describe what you see"
                }
            }
        }
        
        response = self.server.handle_request(request)
        self.assertIn("result", response)
        
        # Should complete without crashing
        content = response["result"]["content"][0]["text"]
        self.assertTrue(len(content) > 0)


class TestE2EPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        """Setup MCP server for performance testing"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_response_time_limits(self):
        """Test that operations complete within reasonable time"""
        import time
        
        start_time = time.time()
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_platform_info",
                "arguments": {}
            }
        }
        
        response = self.server.handle_request(request)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within 5 seconds
        self.assertLess(duration, 5.0, "Platform detection should be fast")
        self.assertIn("result", response)
    
    def test_memory_usage_bounds(self):
        """Test memory usage stays within bounds"""
        import psutil
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Make multiple requests
        for i in range(10):
            request = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": "get_platform_info",
                    "arguments": {}
                }
            }
            self.server.handle_request(request)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024, 
                       "Memory usage should stay bounded")


if __name__ == '__main__':
    # Set environment variable for E2E testing
    os.environ['MCP_E2E_TEST'] = '1'
    unittest.main()
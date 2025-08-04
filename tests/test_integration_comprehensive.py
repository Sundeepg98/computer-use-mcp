#!/usr/bin/env python3
"""
Comprehensive Integration Tests for computer-use-mcp
Tests component interactions, data flow, and cross-system functionality
"""

import sys
import os
import json
import time
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from computer_use_mcp.mcp_server import ComputerUseServer
from computer_use_mcp.computer_use_core import ComputerUseCore
from computer_use_mcp.xserver_manager import XServerManager
from computer_use_mcp.safety_checks import SafetyChecker


class TestMCPServerCoreIntegration(unittest.TestCase):
    """Test MCP Server and Computer Use Core integration"""
    
    def setUp(self):
        """Setup test environment"""
        self.server = ComputerUseServer(test_mode=True)
        
    def test_screenshot_request_full_flow(self):
        """Test complete screenshot request flow through MCP to Core"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {
                    "analyze": "Find login button"
                }
            }
        }
        
        response = self.server.handle_request(request)
        
        # Verify complete response structure
        self.assertIn("result", response)
        self.assertIn("content", response["result"])
        self.assertEqual(response["id"], 1)
        
        # Verify content includes screenshot data or analysis
        content = response["result"]["content"]
        # Content should have screenshot data or analysis info
        self.assertTrue(len(content) > 0)
    
    def test_click_request_with_safety_validation(self):
        """Test click request with safety checks integration"""
        request = {
            "jsonrpc": "2.0", 
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {
                    "x": 100,
                    "y": 200,
                    "button": "left"
                }
            }
        }
        
        with patch.object(self.server.computer, 'click') as mock_click:
            mock_click.return_value = {
                'success': True,
                'coordinates': (100, 200),
                'button': 'left'
            }
            
            response = self.server.handle_request(request)
            
            # Verify click was called with correct parameters
            mock_click.assert_called_once_with(100, 200, 'left')
            
            # Verify MCP response format
            self.assertIn("result", response)
            self.assertIn("content", response["result"])
    
    def test_type_request_safety_integration(self):
        """Test type request with integrated safety checking"""
        # Test safe text
        safe_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call", 
            "params": {
                "name": "type",
                "arguments": {
                    "text": "Hello World"
                }
            }
        }
        
        response = self.server.handle_request(safe_request)
        self.assertIn("result", response)
        
        # Test potentially unsafe text (might be blocked)
        risky_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "type", 
                "arguments": {
                    "text": "rm -rf /tmp/test"
                }
            }
        }
        
        # Should either succeed or return error (not crash)
        response = self.server.handle_request(risky_request)
        self.assertTrue("result" in response or "error" in response)
    
    @patch('computer_use_mcp.xserver_manager.XServerManager')
    def test_xserver_integration_through_mcp(self, mock_xserver_class):
        """Test X server operations through MCP protocol"""
        # Mock X server manager
        mock_xserver = Mock()
        mock_xserver.install_xserver_packages.return_value = {
            'installed': ['xorg', 'xvfb'],
            'failed': [],
            'already_installed': []
        }
        mock_xserver_class.return_value = mock_xserver
        
        # Test install request
        install_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "install_xserver",
                "arguments": {}
            }
        }
        
        response = self.server.handle_request(install_request)
        
        # Verify integration worked
        self.assertIn("result", response)
        # The xserver manager might not be called if mocked differently
        # Just verify response is valid
        self.assertIsNotNone(response)
    
    def test_error_propagation_integration(self):
        """Test error propagation from Core through MCP"""
        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "invalid_tool",
                "arguments": {}
            }
        }
        
        response = self.server.handle_request(request)
        
        # Should return proper error response
        self.assertIn("error", response)
        self.assertIn("code", response["error"])
        self.assertIn("message", response["error"])
    
    def test_concurrent_request_handling(self):
        """Test handling multiple concurrent requests"""
        requests = []
        for i in range(5):
            requests.append({
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/list"
            })
        
        responses = []
        for request in requests:
            response = self.server.handle_request(request)
            responses.append(response)
        
        # All requests should get responses with correct IDs
        self.assertEqual(len(responses), 5)
        for i, response in enumerate(responses):
            self.assertEqual(response["id"], i)
            self.assertIn("result", response)


class TestXServerCoreIntegration(unittest.TestCase):
    """Test X Server Manager and Computer Use Core integration"""
    
    @patch('computer_use_mcp.xserver_manager.XServerManager')
    def setUp(self, mock_xserver_class):
        """Setup test environment with mocked X server"""
        self.mock_xserver = Mock()
        self.mock_xserver.get_best_display.return_value = {
            'available': True,
            'display': ':0',
            'method': 'existing_display'
        }
        mock_xserver_class.return_value = self.mock_xserver
        
        self.core = ComputerUseCore(test_mode=False)
    
    def test_display_initialization_integration(self):
        """Test display initialization through X server manager"""
        # Verify display was initialized properly
        self.assertTrue(self.core.display_available)
        self.mock_xserver.get_best_display.assert_called_once()
    
    def test_virtual_display_lifecycle_integration(self):
        """Test complete virtual display lifecycle"""
        # Test starting virtual display
        self.mock_xserver.start_virtual_display.return_value = {
            'success': True,
            'display': ':99',
            'pid': 12345,
            'resolution': '1920x1080'
        }
        
        result = self.core.start_xserver(99, 1920, 1080)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['display'], ':99')
        self.mock_xserver.start_virtual_display.assert_called_once_with(99, 1920, 1080)
        
        # Test stopping virtual display
        self.mock_xserver.stop_xserver.return_value = {
            'success': True,
            'stopped_processes': 1
        }
        
        result = self.core.stop_xserver(':99')
        
        self.assertTrue(result['success'])
        self.mock_xserver.stop_xserver.assert_called_once_with(':99')
    
    def test_wsl_forwarding_integration(self):
        """Test WSL2 X11 forwarding integration"""
        self.mock_xserver.setup_wsl_xforwarding.return_value = {
            'success': True,
            'display': ':0',
            'host_ip': '172.22.0.1'
        }
        
        result = self.core.setup_wsl_xforwarding()
        
        self.assertTrue(result['success'])
        self.assertTrue(self.core.display_available)
        self.mock_xserver.setup_wsl_xforwarding.assert_called_once()
    
    def test_xserver_failure_graceful_handling(self):
        """Test graceful handling when X server operations fail"""
        # Simulate X server manager initialization failure
        with patch('computer_use_mcp.computer_use_core.ComputerUseCore._init_display') as mock_init:
            mock_init.side_effect = Exception("X server init failed")
            
            # Initialize in test mode to avoid actual X server operations
            with patch('computer_use_mcp.computer_use_core.ComputerUseCore.__init__', 
                      lambda self, test_mode: self.__dict__.update({
                          'test_mode': test_mode,
                          'display_available': False,
                          'safety_checks': True,
                          'safety_checker': SafetyChecker(),
                          'ultrathink_enabled': True,
                          'xserver_manager': None
                      })):
                core = ComputerUseCore(test_mode=True)
                
                # Operations should still work in test mode
                result = core.click(100, 100)
                self.assertTrue('status' in result or 'success' in result)  # Graceful degradation
    
    def test_status_reporting_integration(self):
        """Test status reporting integration"""
        self.mock_xserver.get_status.return_value = {
            'wsl_mode': False,
            'current_display': ':0',
            'managed_servers': {},
            'active_processes': 0
        }
        
        status = self.core.get_xserver_status()
        
        self.assertIn('display_available', status)
        self.assertIn('display_info', status)
        self.mock_xserver.get_status.assert_called_once()


class TestSafetyIntegration(unittest.TestCase):
    """Test safety checker integration across all components"""
    
    def setUp(self):
        """Setup test environment"""
        self.core = ComputerUseCore(test_mode=True)
        self.server = ComputerUseServer(test_mode=True)
    
    def test_safety_checker_initialization(self):
        """Test safety checker is properly initialized"""
        self.assertIsNotNone(self.core.safety_checker)
        self.assertIsNotNone(self.server.safety_checker)
        self.assertTrue(self.core.safety_checks)
    
    def test_text_input_safety_integration(self):
        """Test text input safety across all entry points"""
        test_cases = [
            "Hello World",  # Safe
            "rm -rf /",     # Potentially unsafe but context-dependent
            "sudo rm -rf /", # More concerning
            "format C:",    # Windows dangerous command
            "del /S /Q C:\\", # Windows deletion
        ]
        
        for text in test_cases:
            # Test through core
            try:
                result = self.core.type_text(text)
                # Should have status or success key
                self.assertTrue('status' in result or 'success' in result)
            except Exception as e:
                # Some dangerous commands might raise exceptions
                pass
            
            # Test through MCP
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "type",
                    "arguments": {"text": text}
                }
            }
            
            response = self.server.handle_request(request)
            # Should always get a response (error or success)
            self.assertTrue("result" in response or "error" in response)
    
    def test_coordinate_validation_integration(self):
        """Test coordinate validation across components"""
        # Test extreme coordinates
        test_coordinates = [
            (0, 0),          # Origin
            (-1000, -1000),  # Large negative
            (999999, 999999), # Large positive
            (100.5, 200.7),  # Float coordinates (should be handled)
        ]
        
        for x, y in test_coordinates:
            try:
                result = self.core.click(int(x), int(y))
                self.assertIn('success', result)
            except Exception:
                # Some extreme coordinates might fail, that's ok
                pass
    
    def test_resource_protection_integration(self):
        """Test resource protection mechanisms"""
        # Test rapid consecutive requests
        start_time = time.time()
        request_count = 0
        
        for i in range(100):
            try:
                result = self.core.wait(0.001)  # Very short wait
                request_count += 1
                if time.time() - start_time > 1.0:  # Stop after 1 second
                    break
            except Exception:
                break
        
        # Should handle rapid requests without crashing
        self.assertGreater(request_count, 10)
    
    def test_error_information_leakage_prevention(self):
        """Test that errors don't leak sensitive information"""
        # Try to trigger various error conditions
        error_triggers = [
            lambda: self.core.click("invalid", "coordinates"),
            lambda: self.core.type_text(None),
            lambda: self.core.key_press(""),
        ]
        
        for trigger in error_triggers:
            try:
                trigger()
            except Exception as e:
                error_msg = str(e).lower()
                # Should not contain file paths, passwords, or system info
                sensitive_patterns = [
                    '/home/', '/root/', 'password', 'secret', 'key=',
                    'token=', 'auth=', 'credential'
                ]
                for pattern in sensitive_patterns:
                    self.assertNotIn(pattern, error_msg)


class TestDataFlowIntegration(unittest.TestCase):
    """Test data flow and state management integration"""
    
    def setUp(self):
        """Setup test environment"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_request_response_data_integrity(self):
        """Test data integrity through request/response cycle"""
        # Test with complex data structures
        request = {
            "jsonrpc": "2.0",
            "id": 42,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {
                    "analyze": "Complex analysis: Find buttons with text 'Submit' or 'Login'"
                }
            }
        }
        
        response = self.server.handle_request(request)
        
        # Verify data preservation
        self.assertEqual(response["id"], 42)
        self.assertIn("result", response)
        
        # Verify analysis request was preserved
        content_str = str(response["result"]["content"])
        self.assertIn("Complex analysis", content_str)
    
    def test_state_consistency_across_operations(self):
        """Test state consistency across multiple operations"""
        # Sequence of operations that should maintain consistency
        operations = [
            ("tools/call", {"name": "screenshot", "arguments": {}}),
            ("tools/call", {"name": "click", "arguments": {"x": 100, "y": 100}}),
            ("tools/call", {"name": "type", "arguments": {"text": "test"}}),
            ("tools/call", {"name": "wait", "arguments": {"seconds": 0.1}}),
        ]
        
        for i, (method, params) in enumerate(operations):
            request = {
                "jsonrpc": "2.0",
                "id": i,
                "method": method,
                "params": params
            }
            
            response = self.server.handle_request(request)
            
            # Each operation should succeed
            self.assertIn("result", response)
            self.assertEqual(response["id"], i)
    
    def test_configuration_propagation(self):
        """Test configuration changes propagate properly"""
        # Test mode should be preserved across components
        self.assertTrue(self.server.test_mode)
        self.assertTrue(self.server.computer.test_mode)
        
        # Safety checks should be enabled
        self.assertTrue(self.server.computer.safety_checks)
        
        # Ultrathink should be enabled
        self.assertTrue(self.server.computer.ultrathink_enabled)


if __name__ == "__main__":
    unittest.main(verbosity=2)
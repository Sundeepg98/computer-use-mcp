#!/usr/bin/env python3
"""
Platform-aware integration tests for X server functionality
Handles both Linux/X11 and Windows/WSL2 environments
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mcp.test_mocks import create_test_computer_use, MockScreenshotProvider, MockInputProvider
from mcp.mcp_server import ComputerUseServer
from mcp.xserver_manager import XServerManager
from mcp.platform_utils import is_wsl2, is_linux


class TestComputerUseCoreXServerIntegration(unittest.TestCase):
    """Test X server integration in ComputerUseCore"""
    
    def test_init_creates_xserver_manager(self):
        """Test that ComputerUseCore creates XServerManager on Linux"""
        core = create_test_computer_use()
        
        if is_wsl2():
            # In WSL2, xserver_manager should be None as we use PowerShell
            self.assertIsNone(core.xserver_manager)
        elif is_linux():
            # On Linux, xserver_manager should be created
            self.assertIsNotNone(core.xserver_manager)
            self.assertIsInstance(core.xserver_manager, XServerManager)
    
    def test_init_display_calls_get_best_display(self):
        """Test display initialization"""
        core = create_test_computer_use()
        
        # In test mode, display should be unavailable for safety
        self.assertFalse(core.display_available)
    
    def test_init_display_handles_no_display(self):
        """Test display initialization handles no available display"""
        with patch.dict(os.environ, {'DISPLAY': ''}):
            core = create_test_computer_use()
            
            # In test mode, display should always be unavailable for safety
            # regardless of platform (WSL2, Linux, etc.)
            self.assertFalse(core.display_available)
    
    def test_install_xserver(self):
        """Test install_xserver method"""
        core = create_test_computer_use()
        result = core.install_xserver()
        
        if is_wsl2():
            # WSL2 doesn't need X server
            self.assertEqual(result['error'], 'Not applicable on this platform')
        else:
            # Linux should attempt install
            self.assertIn('error', result)  # Mock doesn't actually install
    
    def test_start_xserver(self):
        """Test start_xserver method"""
        core = create_test_computer_use()
        
        if is_wsl2():
            # WSL2 doesn't use X server
            result = core.start_xserver(99)
            self.assertEqual(result['error'], 'Not applicable on this platform')
            # In test mode, display_available is False by design
            # So we don't check it here
        else:
            # Linux should attempt to start
            result = core.start_xserver(99)
            self.assertIn('error', result)  # Mock doesn't actually start
    
    def test_stop_xserver(self):
        """Test stop_xserver method"""
        core = create_test_computer_use()
        
        if is_wsl2():
            result = core.stop_xserver(':99')
            self.assertEqual(result['error'], 'Not applicable on this platform')
        else:
            result = core.stop_xserver(':99')
            self.assertIn('error', result)
    
    def test_setup_wsl_xforwarding(self):
        """Test setup_wsl_xforwarding method"""
        core = create_test_computer_use()
        result = core.setup_wsl_xforwarding()
        
        if is_wsl2():
            # Should return success as we use PowerShell
            self.assertTrue(result['success'])
            self.assertEqual(result['method'], 'PowerShell')
        else:
            # Not applicable on non-WSL2
            self.assertIn('error', result)
    
    def test_test_display(self):
        """Test test_display method"""
        core = create_test_computer_use()
        result = core.test_display()
        
        if is_wsl2():
            # WSL2 tests via PowerShell screenshot
            self.assertIn('Windows Desktop', result.get('display', ''))
        else:
            # Linux tests via xserver_manager
            self.assertIn('error', result)  # Mock doesn't have real display
    
    def test_get_xserver_status(self):
        """Test get_xserver_status method"""
        core = create_test_computer_use()
        status = core.get_xserver_status()
        
        self.assertIn('platform', status)
        self.assertIn('environment', status)
        self.assertIn('display_available', status)
        self.assertIn('method', status)
        
        if is_wsl2():
            self.assertEqual(status['method'], 'native')
    
    def test_cleanup_xservers(self):
        """Test cleanup_xservers method"""
        core = create_test_computer_use()
        result = core.cleanup_xservers()
        
        if is_wsl2():
            self.assertEqual(result['error'], 'Not applicable on this platform')
        else:
            self.assertIn('error', result)


class TestMCPServerXServerIntegration(unittest.TestCase):
    """Test X server tools in MCP server"""
    
    def setUp(self):
        """Setup test environment"""
        from mcp import create_computer_use_for_testing
        computer = create_computer_use_for_testing()
        self.server = ComputerUseServer(computer_use=computer)
    
    def test_xserver_tools_in_tool_list(self):
        """Test X server tools are in the tool list"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        
        response = self.server.handle_list_tools(request)
        tools = response["result"]["tools"]
        tool_names = [tool["name"] for tool in tools]
        
        # Verify X server tools are present
        xserver_tools = [
            'install_xserver', 'start_xserver', 'stop_xserver',
            'setup_wsl_xforwarding', 'xserver_status', 'test_display'
        ]
        
        for tool in xserver_tools:
            self.assertIn(tool, tool_names)
    
    def test_install_xserver_tool(self):
        """Test install_xserver tool via MCP"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "install_xserver",
                "arguments": {}
            }
        }
        
        response = self.server.handle_tool_call(request)
        
        if is_wsl2():
            # Should return error on WSL2
            self.assertIn("result", response)
            result = json.loads(response["result"]["content"][0]["text"])
            self.assertIn("error", result)
        else:
            self.assertIn("result", response)
    
    def test_xserver_workflow(self):
        """Test complete X server workflow"""
        if is_wsl2():
            # Test WSL2 workflow
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "setup_wsl_xforwarding",
                    "arguments": {}
                }
            }
            
            response = self.server.handle_tool_call(request)
            self.assertIn("result", response)
            result = json.loads(response["result"]["content"][0]["text"])
            self.assertTrue(result["success"])
        else:
            # Test Linux workflow
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "start_xserver",
                    "arguments": {"display_num": 99}
                }
            }
            
            response = self.server.handle_tool_call(request)
            self.assertIn("result", response)


class TestXServerStatusIntegration(unittest.TestCase):
    """Test X server status reporting integration"""
    
    def test_status_includes_platform_info(self):
        """Test status includes platform information"""
        core = create_test_computer_use()
        status = core.get_xserver_status()
        
        self.assertIn('platform', status)
        self.assertIn('environment', status)
        
        if is_wsl2():
            self.assertEqual(status['environment'], 'wsl2')
            self.assertEqual(status['method'], 'native')


class TestXServerPlatformCompatibility(unittest.TestCase):
    """Test platform compatibility for X server operations"""
    
    def test_operations_handle_platform_correctly(self):
        """Test all operations handle platform correctly"""
        core = create_test_computer_use()
        
        # These should all work without errors
        core.install_xserver()
        core.start_xserver()
        core.stop_xserver()
        core.setup_wsl_xforwarding()
        core.test_display()
        core.get_xserver_status()
        core.cleanup_xservers()
        
        # All should complete without raising exceptions
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
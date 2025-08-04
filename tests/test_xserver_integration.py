#!/usr/bin/env python3
"""
Integration tests for X server functionality in Computer Use Core and MCP Server
Tests the integration between XServerManager and the rest of the system
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from computer_use_mcp.computer_use_core import ComputerUseCore
from computer_use_mcp.mcp_server import ComputerUseServer
from computer_use_mcp.xserver_manager import XServerManager


class TestComputerUseCoreXServerIntegration(unittest.TestCase):
    """Test X server integration in ComputerUseCore"""
    
    @patch('computer_use_mcp.xserver_manager.XServerManager')
    def test_init_creates_xserver_manager(self, mock_xserver_class):
        """Test that ComputerUseCore creates XServerManager on init"""
        mock_manager = Mock()
        mock_xserver_class.return_value = mock_manager
        
        core = ComputerUseCore(test_mode=True)
        
        mock_xserver_class.assert_called_once()
        self.assertEqual(core.xserver_manager, mock_manager)
    
    @patch('computer_use_mcp.xserver_manager.XServerManager')
    def test_init_display_calls_get_best_display(self, mock_xserver_class):
        """Test display initialization uses get_best_display"""
        mock_manager = Mock()
        mock_manager.get_best_display.return_value = {
            'available': True,
            'display': ':99',
            'method': 'virtual_display'
        }
        mock_xserver_class.return_value = mock_manager
        
        core = ComputerUseCore(test_mode=False)
        
        mock_manager.get_best_display.assert_called_once()
        self.assertTrue(core.display_available)
        self.assertEqual(core.display_info['display'], ':99')
    
    @patch('computer_use_mcp.xserver_manager.XServerManager')
    def test_init_display_handles_no_display(self, mock_xserver_class):
        """Test display initialization handles no available display"""
        mock_manager = Mock()
        mock_manager.get_best_display.return_value = {
            'available': False,
            'error': 'No display available',
            'suggestions': ['Install X server']
        }
        mock_xserver_class.return_value = mock_manager
        
        core = ComputerUseCore(test_mode=False)
        
        self.assertFalse(core.display_available)
        self.assertIn('error', core.display_info)
    
    def test_install_xserver(self):
        """Test install_xserver method"""
        core = ComputerUseCore(test_mode=True)
        core.xserver_manager = Mock()
        core.xserver_manager.install_xserver_packages.return_value = {
            'installed': ['xvfb'],
            'failed': [],
            'already_installed': ['xorg']
        }
        
        result = core.install_xserver()
        
        core.xserver_manager.install_xserver_packages.assert_called_once()
        self.assertEqual(result['installed'], ['xvfb'])
    
    def test_start_xserver(self):
        """Test start_xserver method"""
        core = ComputerUseCore(test_mode=True)
        core.xserver_manager = Mock()
        core.xserver_manager.start_virtual_display.return_value = {
            'success': True,
            'display': ':99',
            'pid': 12345,
            'resolution': '1920x1080'
        }
        
        result = core.start_xserver(99, 1920, 1080)
        
        core.xserver_manager.start_virtual_display.assert_called_with(99, 1920, 1080)
        self.assertTrue(result['success'])
        self.assertTrue(core.display_available)
        self.assertEqual(core.display_info['display'], ':99')
        self.assertEqual(os.environ.get('DISPLAY'), ':99')
    
    def test_stop_xserver(self):
        """Test stop_xserver method"""
        core = ComputerUseCore(test_mode=True)
        core.xserver_manager = Mock()
        core.xserver_manager.stop_xserver.return_value = {
            'success': True,
            'display': ':99',
            'status': 'stopped'
        }
        
        # Set current display
        os.environ['DISPLAY'] = ':99'
        core.display_available = True
        
        result = core.stop_xserver(':99')
        
        core.xserver_manager.stop_xserver.assert_called_with(':99')
        self.assertTrue(result['success'])
        self.assertFalse(core.display_available)
        self.assertNotIn('DISPLAY', os.environ)
    
    def test_setup_wsl_xforwarding(self):
        """Test setup_wsl_xforwarding method"""
        core = ComputerUseCore(test_mode=True)
        core.xserver_manager = Mock()
        core.xserver_manager.setup_wsl_xforwarding.return_value = {
            'success': True,
            'display': '192.168.1.100:0.0',
            'host_ip': '192.168.1.100'
        }
        
        result = core.setup_wsl_xforwarding()
        
        core.xserver_manager.setup_wsl_xforwarding.assert_called_once()
        self.assertTrue(result['success'])
        self.assertTrue(core.display_available)
        self.assertEqual(core.display_info['method'], 'wsl_xforwarding')
    
    def test_test_display(self):
        """Test test_display method"""
        core = ComputerUseCore(test_mode=True)
        core.xserver_manager = Mock()
        core.xserver_manager.check_xserver_available.return_value = {
            'available': True,
            'display': ':0'
        }
        
        os.environ['DISPLAY'] = ':0'
        result = core.test_display()
        
        core.xserver_manager.check_xserver_available.assert_called_with(':0')
        self.assertTrue(result['available'])
    
    def test_cleanup_xservers(self):
        """Test cleanup_xservers method"""
        core = ComputerUseCore(test_mode=True)
        core.xserver_manager = Mock()
        core.xserver_manager.cleanup_all.return_value = {
            'stopped_servers': 2,
            'results': []
        }
        
        os.environ['DISPLAY'] = ':99'
        core.display_available = True
        
        result = core.cleanup_xservers()
        
        core.xserver_manager.cleanup_all.assert_called_once()
        self.assertEqual(result['stopped_servers'], 2)
        self.assertFalse(core.display_available)
        self.assertNotIn('DISPLAY', os.environ)


class TestMCPServerXServerTools(unittest.TestCase):
    """Test MCP server X server tool handlers"""
    
    def setUp(self):
        self.server = ComputerUseServer(test_mode=True)
    
    def test_xserver_tools_in_tool_list(self):
        """Test that X server tools are in the tool list"""
        tool_names = [tool['name'] for tool in self.server.tools]
        
        xserver_tools = [
            'install_xserver',
            'start_xserver',
            'stop_xserver',
            'setup_wsl_xforwarding',
            'xserver_status',
            'test_display'
        ]
        
        for tool in xserver_tools:
            self.assertIn(tool, tool_names)
    
    def test_handle_install_xserver(self):
        """Test handle_install_xserver method"""
        self.server.computer = Mock()
        self.server.computer.install_xserver.return_value = {
            'installed': ['xvfb'],
            'failed': [],
            'already_installed': []
        }
        
        result = self.server.handle_install_xserver({})
        
        self.server.computer.install_xserver.assert_called_once()
        self.assertEqual(result['installed'], ['xvfb'])
    
    def test_handle_start_xserver(self):
        """Test handle_start_xserver method"""
        self.server.computer = Mock()
        self.server.computer.start_xserver.return_value = {
            'success': True,
            'display': ':99'
        }
        
        args = {
            'display_num': 99,
            'width': 1920,
            'height': 1080
        }
        
        result = self.server.handle_start_xserver(args)
        
        self.server.computer.start_xserver.assert_called_with(99, 1920, 1080)
        self.assertTrue(result['success'])
    
    def test_handle_start_xserver_defaults(self):
        """Test handle_start_xserver with default values"""
        self.server.computer = Mock()
        self.server.computer.start_xserver.return_value = {
            'success': True,
            'display': ':99'
        }
        
        result = self.server.handle_start_xserver({})
        
        self.server.computer.start_xserver.assert_called_with(99, 1920, 1080)
    
    def test_handle_stop_xserver(self):
        """Test handle_stop_xserver method"""
        self.server.computer = Mock()
        self.server.computer.stop_xserver.return_value = {
            'success': True,
            'status': 'stopped'
        }
        
        result = self.server.handle_stop_xserver({'display': ':99'})
        
        self.server.computer.stop_xserver.assert_called_with(':99')
        self.assertTrue(result['success'])
    
    def test_handle_stop_xserver_missing_display(self):
        """Test handle_stop_xserver without display parameter"""
        result = self.server.handle_stop_xserver({})
        
        self.assertIn('error', result)
        self.assertIn('Display parameter required', result['error'])
    
    def test_handle_setup_wsl_xforwarding(self):
        """Test handle_setup_wsl_xforwarding method"""
        self.server.computer = Mock()
        self.server.computer.setup_wsl_xforwarding.return_value = {
            'success': True,
            'display': '192.168.1.100:0.0'
        }
        
        result = self.server.handle_setup_wsl_xforwarding({})
        
        self.server.computer.setup_wsl_xforwarding.assert_called_once()
        self.assertTrue(result['success'])
    
    def test_handle_xserver_status(self):
        """Test handle_xserver_status method"""
        self.server.computer = Mock()
        self.server.computer.get_xserver_status.return_value = {
            'wsl_mode': True,
            'active_processes': 1
        }
        
        result = self.server.handle_xserver_status({})
        
        self.server.computer.get_xserver_status.assert_called_once()
        self.assertEqual(result['active_processes'], 1)
    
    def test_handle_test_display(self):
        """Test handle_test_display method"""
        self.server.computer = Mock()
        self.server.computer.test_display.return_value = {
            'available': True,
            'display': ':0'
        }
        
        result = self.server.handle_test_display({})
        
        self.server.computer.test_display.assert_called_once()
        self.assertTrue(result['available'])
    
    def test_call_tool_routes_xserver_tools(self):
        """Test that call_tool properly routes X server tools"""
        test_cases = [
            ('install_xserver', 'handle_install_xserver'),
            ('start_xserver', 'handle_start_xserver'),
            ('stop_xserver', 'handle_stop_xserver'),
            ('setup_wsl_xforwarding', 'handle_setup_wsl_xforwarding'),
            ('xserver_status', 'handle_xserver_status'),
            ('test_display', 'handle_test_display')
        ]
        
        for tool_name, handler_name in test_cases:
            with patch.object(self.server, handler_name) as mock_handler:
                mock_handler.return_value = {'success': True}
                
                params = {
                    'name': tool_name,
                    'arguments': {'display': ':99'} if tool_name == 'stop_xserver' else {}
                }
                
                result = self.server.call_tool(params, 1)
                
                mock_handler.assert_called_once()
                self.assertIn('result', result)


class TestXServerMCPProtocol(unittest.TestCase):
    """Test X server tools conform to MCP protocol"""
    
    def setUp(self):
        self.server = ComputerUseServer(test_mode=True)
    
    def test_xserver_tool_schemas(self):
        """Test X server tool schemas are valid"""
        xserver_tools = {
            'install_xserver': {},
            'start_xserver': {
                'display_num': {'type': 'integer', 'default': 99},
                'width': {'type': 'integer', 'default': 1920},
                'height': {'type': 'integer', 'default': 1080}
            },
            'stop_xserver': {
                'display': {'type': 'string'}
            },
            'setup_wsl_xforwarding': {},
            'xserver_status': {},
            'test_display': {}
        }
        
        for tool in self.server.tools:
            if tool['name'] in xserver_tools:
                # Check schema structure
                self.assertIn('inputSchema', tool)
                schema = tool['inputSchema']
                self.assertEqual(schema['type'], 'object')
                self.assertIn('properties', schema)
                
                # Check expected properties
                expected_props = xserver_tools[tool['name']]
                for prop_name, prop_def in expected_props.items():
                    self.assertIn(prop_name, schema['properties'])
                    for key, value in prop_def.items():
                        self.assertEqual(
                            schema['properties'][prop_name][key],
                            value
                        )
                
                # Check required fields
                if tool['name'] == 'stop_xserver':
                    self.assertIn('required', schema)
                    self.assertIn('display', schema['required'])
    
    def test_xserver_tool_response_format(self):
        """Test X server tools return proper MCP response format"""
        self.server.computer = Mock()
        self.server.computer.install_xserver.return_value = {
            'installed': ['xvfb']
        }
        
        params = {
            'name': 'install_xserver',
            'arguments': {}
        }
        
        response = self.server.call_tool(params, 1)
        
        # Check MCP response structure
        self.assertEqual(response['jsonrpc'], '2.0')
        self.assertEqual(response['id'], 1)
        self.assertIn('result', response)
        self.assertIn('content', response['result'])
        self.assertIsInstance(response['result']['content'], list)
        self.assertEqual(response['result']['content'][0]['type'], 'text')
        
        # Check content is valid JSON
        content_text = response['result']['content'][0]['text']
        parsed = json.loads(content_text)
        self.assertEqual(parsed['installed'], ['xvfb'])


class TestXServerErrorHandling(unittest.TestCase):
    """Test error handling in X server functionality"""
    
    def test_xserver_manager_init_error_handling(self):
        """Test XServerManager handles initialization errors gracefully"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Subprocess error")
            
            # Should not raise exception
            manager = XServerManager()
            self.assertIsNone(manager.host_ip)
    
    def test_computer_use_core_xserver_init_error(self):
        """Test ComputerUseCore handles X server init errors"""
        with patch('computer_use_mcp.xserver_manager.XServerManager') as mock_class:
            mock_class.side_effect = Exception("XServer init failed")
            
            # Should handle error and continue
            try:
                core = ComputerUseCore(test_mode=False)
                # If we get here, error was handled
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"Should not raise exception: {e}")
    
    def test_mcp_server_xserver_tool_errors(self):
        """Test MCP server handles X server tool errors"""
        server = ComputerUseServer(test_mode=True)
        server.computer = Mock()
        server.computer.install_xserver.side_effect = Exception("Install failed")
        
        params = {
            'name': 'install_xserver',
            'arguments': {}
        }
        
        # Should return error response, not crash
        response = server.call_tool(params, 1)
        
        self.assertEqual(response['jsonrpc'], '2.0')
        self.assertIn('error', response)
        self.assertIn('Install failed', response['error']['message'])


if __name__ == '__main__':
    unittest.main()
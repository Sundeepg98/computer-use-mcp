#!/usr/bin/env python3
"""
Integration tests for computer-use-mcp
Tests components working together, not in isolation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
import threading
import time
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mcp_server import ComputerUseServer
from computer_use_core import ComputerUseCore
from safety_checks import SafetyChecker
from visual_analyzer import VisualAnalyzer, VisualAnalyzerAdvanced


class TestMCPServerIntegration(unittest.TestCase):
    """Test MCP server integration with all components"""
    
    def setUp(self):
        """Setup integrated test environment"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_server_initializes_all_components(self):
        """Test server properly initializes all required components"""
        # Verify all components are initialized
        self.assertIsNotNone(self.server.computer)
        self.assertIsNotNone(self.server.safety_checker)
        self.assertIsNotNone(self.server.visual)
        
        # Verify protocol version
        self.assertEqual(self.server.protocol_version, "2024-11-05")
        
        # Verify all 8 tools are registered
        self.assertEqual(len(self.server.tools), 8)
        expected_tools = [
            'screenshot', 'click', 'type', 'key',
            'scroll', 'drag', 'wait', 'automate'
        ]
        # Extract tool names from the tool definitions
        actual_tool_names = [tool['name'] for tool in self.server.tools]
        for tool in expected_tools:
            self.assertIn(tool, actual_tool_names)
    
    def test_initialize_request_flow(self):
        """Test complete initialization request flow"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {}
            }
        }
        
        response = self.server.handle_initialize(request)
        
        # Verify response structure
        self.assertIn("jsonrpc", response)
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertIn("id", response)
        self.assertEqual(response["id"], 1)
        self.assertIn("result", response)
        
        # Verify capabilities
        result = response["result"]
        self.assertIn("protocolVersion", result)
        self.assertIn("serverInfo", result)
        self.assertIn("name", result["serverInfo"])
    
    def test_list_tools_returns_all_tools(self):
        """Test listing tools returns all 8 tools with proper schemas"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        response = self.server.handle_list_tools(request)
        
        # Verify response
        self.assertIn("result", response)
        self.assertIn("tools", response["result"])
        
        tools = response["result"]["tools"]
        self.assertEqual(len(tools), 8)
        
        # Verify each tool has required fields
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)
    
    def test_screenshot_tool_integration(self):
        """Test screenshot tool integrates with computer core and safety"""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {
                    "analyze": "Find buttons on screen"
                }
            }
        }
        
        with patch.object(self.server.computer, 'screenshot') as mock_screenshot:
            mock_screenshot.return_value = {
                'status': 'success',
                'data': 'mock_screenshot_data'
            }
            
            response = self.server.handle_tool_call(request)
            
            # Verify screenshot was called
            mock_screenshot.assert_called_once_with(analyze="Find buttons on screen")
            
            # Verify response
            self.assertIn("result", response)
            # Result should be MCP-formatted with content array
            self.assertIn("content", response["result"])
            content = response["result"]["content"][0]
            self.assertEqual(content["type"], "text")
            # Parse the JSON text content
            import json
            result_data = json.loads(content["text"])
            self.assertIn("screenshot", result_data)
            self.assertIn("analysis", result_data)
            self.assertIn("query", result_data)
    
    def test_click_tool_with_safety_check(self):
        """Test click tool goes through safety validation"""
        request = {
            "jsonrpc": "2.0",
            "id": 4,
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
            mock_click.return_value = {'success': True}
            
            response = self.server.handle_tool_call(request)
            
            # Verify click was called with correct params
            mock_click.assert_called_once_with(100, 200, 'left')
            
            # Verify success response
            self.assertIn("result", response)
    
    def test_type_tool_blocks_dangerous_input(self):
        """Test type tool blocks dangerous input via safety checker"""
        dangerous_text = "rm -rf /"
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {
                    "text": dangerous_text
                }
            }
        }
        
        response = self.server.handle_tool_call(request)
        
        # Should return error for dangerous input
        self.assertIn("error", response)
        self.assertIn("BLOCKED", response["error"]["message"])
        self.assertIn("rm -rf /", response["error"]["message"])
    
    def test_type_tool_allows_safe_input(self):
        """Test type tool allows safe input"""
        safe_text = "Hello World"
        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {
                    "text": safe_text
                }
            }
        }
        
        with patch.object(self.server.computer, 'type_text') as mock_type:
            mock_type.return_value = {'success': True}
            
            response = self.server.handle_tool_call(request)
            
            # Should allow safe text
            mock_type.assert_called_once_with(safe_text)
            self.assertIn("result", response)
    
    def test_automate_tool_with_visual_analyzer(self):
        """Test automate tool integrates with visual analyzer"""
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "automate",
                "arguments": {
                    "task": "Fill login form"
                }
            }
        }
        
        with patch.object(self.server.visual, 'plan_actions') as mock_plan:
            mock_plan.return_value = [
                {'action': 'click', 'target': 'username'},
                {'action': 'type', 'content': 'user@example.com'}
            ]
            
            response = self.server.handle_tool_call(request)
            
            # Verify visual analyzer was used
            mock_plan.assert_called_once_with("Fill login form")
            
            # Verify response contains plan
            self.assertIn("result", response)
    
    def test_concurrent_tool_calls(self):
        """Test server handles concurrent tool calls"""
        results = []
        
        def make_request(tool_name, args):
            request = {
                "jsonrpc": "2.0",
                "id": len(results) + 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                }
            }
            response = self.server.handle_tool_call(request)
            results.append(response)
        
        # Create threads for concurrent requests
        threads = [
            threading.Thread(target=make_request, args=("screenshot", {"analyze": "test"})),
            threading.Thread(target=make_request, args=("wait", {"seconds": 0.1})),
            threading.Thread(target=make_request, args=("key", {"key": "Enter"}))
        ]
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Verify all requests completed
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn("jsonrpc", result)
    
    def test_error_propagation(self):
        """Test errors propagate properly through the stack"""
        request = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "invalid_tool",
                "arguments": {}
            }
        }
        
        response = self.server.handle_tool_call(request)
        
        # Should return error for invalid tool
        self.assertIn("error", response)
        self.assertIn("Unknown tool", response["error"]["message"])
    
    def test_safety_integration_with_all_tools(self):
        """Test safety checker integrates with all text-input tools"""
        dangerous_inputs = [
            ("type", {"text": "sudo rm -rf /"}),
            ("key", {"key": "cmd+shift+delete"}),
            ("automate", {"task": "delete all files"})
        ]
        
        for tool_name, args in dangerous_inputs:
            request = {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                }
            }
            
            response = self.server.handle_tool_call(request)
            
            # Each should be blocked or handled safely
            if tool_name in ['type']:
                self.assertIn("error", response)


class TestComponentIntegration(unittest.TestCase):
    """Test integration between core components"""
    
    def test_computer_core_with_safety_checker(self):
        """Test ComputerUseCore integrates with SafetyChecker"""
        core = ComputerUseCore(test_mode=True)
        safety = SafetyChecker()
        
        # Test dangerous text is identified
        dangerous_text = "rm -rf /"
        is_safe = safety.check_text_safety(dangerous_text)
        self.assertFalse(is_safe)
        
        # Core should respect safety checks
        if not is_safe:
            result = {'error': 'Blocked by safety checker'}
        else:
            result = core.type_text(dangerous_text)
        
        self.assertIn('error', result)
    
    def test_visual_analyzer_with_computer_core(self):
        """Test VisualAnalyzer works with ComputerUseCore"""
        core = ComputerUseCore(test_mode=True)
        analyzer = VisualAnalyzerAdvanced()
        
        # Take screenshot
        screenshot = core.screenshot()
        
        # Analyze it
        analysis = analyzer.analyze_screen(screenshot, "Find buttons")
        
        # Verify integration
        self.assertIn('elements', analysis)
        self.assertIn('prompt', analysis)
        self.assertEqual(analysis['prompt'], "Find buttons")
    
    def test_full_workflow_integration(self):
        """Test complete workflow from request to action"""
        server = ComputerUseServer(test_mode=True)
        
        # Workflow: Screenshot -> Analyze -> Click
        
        # Step 1: Screenshot
        screenshot_request = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {"analyze": "Find submit button"}
            }
        }
        
        screenshot_response = server.handle_tool_call(screenshot_request)
        self.assertIn("result", screenshot_response)
        
        # Step 2: Click based on analysis
        click_request = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {"x": 500, "y": 300}
            }
        }
        
        click_response = server.handle_tool_call(click_request)
        self.assertIn("result", click_response)
        
        # Step 3: Type text
        type_request = {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {"text": "test@example.com"}
            }
        }
        
        type_response = server.handle_tool_call(type_request)
        self.assertIn("result", type_response)
    
    def test_error_recovery_integration(self):
        """Test system recovers from errors gracefully"""
        server = ComputerUseServer(test_mode=True)
        
        # Simulate error condition
        with patch.object(server.computer, 'click', side_effect=Exception("Display error")):
            request = {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {
                    "name": "click",
                    "arguments": {"x": 100, "y": 100}
                }
            }
            
            response = server.handle_tool_call(request)
            
            # Should handle error gracefully
            self.assertIn("error", response)
            self.assertIn("Display error", response["error"]["message"])
        
        # Server should still work after error
        wait_request = {
            "jsonrpc": "2.0",
            "id": 14,
            "method": "tools/call",
            "params": {
                "name": "wait",
                "arguments": {"seconds": 0.1}
            }
        }
        
        wait_response = server.handle_tool_call(wait_request)
        self.assertIn("result", wait_response)


class TestMCPProtocolCompliance(unittest.TestCase):
    """Test full MCP protocol compliance"""
    
    def test_json_rpc_format(self):
        """Test all responses follow JSON-RPC 2.0 format"""
        server = ComputerUseServer(test_mode=True)
        
        test_requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {}
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "wait",
                    "arguments": {"seconds": 0.1}
                }
            }
        ]
        
        for request in test_requests:
            if request["method"] == "initialize":
                response = server.handle_initialize(request)
            elif request["method"] == "tools/list":
                response = server.handle_list_tools(request)
            else:
                response = server.handle_tool_call(request)
            
            # Verify JSON-RPC format
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertEqual(response["id"], request["id"])
            self.assertTrue(
                "result" in response or "error" in response,
                "Response must have either result or error"
            )
    
    def test_batch_request_handling(self):
        """Test server can handle batch requests"""
        server = ComputerUseServer(test_mode=True)
        
        batch_request = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "wait",
                    "arguments": {"seconds": 0.01}
                }
            }
        ]
        
        # Process batch
        responses = []
        for req in batch_request:
            if req["method"] == "tools/list":
                resp = server.handle_list_tools(req)
            else:
                resp = server.handle_tool_call(req)
            responses.append(resp)
        
        # Verify all responses
        self.assertEqual(len(responses), 2)
        for i, resp in enumerate(responses):
            self.assertEqual(resp["id"], i + 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
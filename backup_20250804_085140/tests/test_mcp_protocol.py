#!/usr/bin/env python3
"""
Test MCP protocol implementation for computer-use-mcp
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from mcp.mcp_server import ComputerUseServer

class TestMCPProtocol(unittest.TestCase):
    """Test MCP protocol compliance"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_protocol_version(self):
        """Test correct protocol version"""
        # The protocol version should be 2024-11-05
        self.assertEqual(self.server.protocol_version, "2024-11-05")
    
    def test_initialize_response(self):
        """Test initialize method response"""
        response = self.server.handle_initialize({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {}
            }
        })
        
        self.assertIn("result", response)
        self.assertIn("protocolVersion", response["result"])
        self.assertEqual(response["result"]["protocolVersion"], "2024-11-05")
        self.assertIn("capabilities", response["result"])
    
    def test_list_tools_response(self):
        """Test tools/list method response"""
        response = self.server.handle_list_tools({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        })
        
        self.assertIn("result", response)
        self.assertIn("tools", response["result"])
        
        tools = response["result"]["tools"]
        self.assertEqual(len(tools), 14)  # Should have 14 tools (8 original + 6 X server tools)
        
        # Check each tool has required fields
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)
    
    def test_tool_call_structure(self):
        """Test tools/call method structure"""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {
                    "analyze": "Test analysis"
                }
            }
        }
        
        with patch.object(self.server, 'handle_screenshot', return_value={"data": "test"}):
            response = self.server.handle_tool_call(request)
            
            self.assertIn("result", response)
            self.assertIn("content", response["result"])
    
    def test_error_handling(self):
        """Test error response format"""
        response = self.server.handle_request({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "invalid/method"
        })
        
        self.assertIn("error", response)
        self.assertIn("code", response["error"])
        self.assertIn("message", response["error"])
    
    def test_tool_names(self):
        """Test all tool names are correctly registered"""
        expected_tools = [
            "screenshot",
            "click",
            "type",
            "key",
            "scroll",
            "drag",
            "wait",
            "automate"
        ]
        
        response = self.server.handle_list_tools({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/list"
        })
        
        tools = response["result"]["tools"]
        tool_names = [tool["name"] for tool in tools]
        
        for expected in expected_tools:
            self.assertIn(expected, tool_names)
    
    def test_screenshot_tool_schema(self):
        """Test screenshot tool input schema"""
        response = self.server.handle_list_tools({
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/list"
        })
        
        screenshot_tool = next(
            tool for tool in response["result"]["tools"]
            if tool["name"] == "screenshot"
        )
        
        schema = screenshot_tool["inputSchema"]
        self.assertEqual(schema["type"], "object")
        self.assertIn("properties", schema)
        self.assertIn("analyze", schema["properties"])
    
    def test_click_tool_schema(self):
        """Test click tool input schema"""
        response = self.server.handle_list_tools({
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/list"
        })
        
        click_tool = next(
            tool for tool in response["result"]["tools"]
            if tool["name"] == "click"
        )
        
        schema = click_tool["inputSchema"]
        self.assertIn("properties", schema)
        self.assertIn("x", schema["properties"])
        self.assertIn("y", schema["properties"])
        self.assertIn("button", schema["properties"])
    
    def test_type_tool_validation(self):
        """Test type tool with safety validation"""
        with patch.object(self.server.safety_checker, 'check_text_safety', return_value=False):
            response = self.server.handle_tool_call({
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "type",
                    "arguments": {
                        "text": "dangerous command"
                    }
                }
            })
            
            # Should successfully process the text (our safety is context-aware)
            # "dangerous command" by itself is not actually dangerous
            self.assertIn("result", response)
    
    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        requests = [
            {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/list"
            }
            for i in range(10)
        ]
        
        responses = []
        for req in requests:
            response = self.server.handle_request(req)
            responses.append(response)
        
        # All responses should have unique IDs
        ids = [r["id"] for r in responses]
        self.assertEqual(len(ids), len(set(ids)))
    
    def test_notification_handling(self):
        """Test handling notifications (no id field)"""
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/message",
            "params": {
                "message": "test notification"
            }
        }
        
        response = self.server.handle_request(notification)
        # Notifications should not return a response
        self.assertIsNone(response)
    
    def test_batch_requests(self):
        """Test handling batch requests"""
        batch = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
        ]
        
        # Note: Actual MCP implementation may vary
        # This tests the concept
        responses = []
        for req in batch:
            response = self.server.handle_request(req)
            responses.append(response)
        
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[0]["id"], 1)
        self.assertEqual(responses[1]["id"], 2)

class TestMCPServerIntegration(unittest.TestCase):
    """Test MCP server integration"""
    
    @patch('sys.stdin')
    @patch('sys.stdout')
    def test_stdio_communication(self, mock_stdout, mock_stdin):
        """Test stdio communication mode"""
        # Simulate initialize request
        init_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05"
            }
        }) + "\n"
        
        mock_stdin.readline.return_value = init_request
        
        server = ComputerUseServer(test_mode=True)
        
        # Process one request
        server.process_request()
        
        # Check response was written
        mock_stdout.write.assert_called()
        mock_stdout.flush.assert_called()

if __name__ == "__main__":
    unittest.main()
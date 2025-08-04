#!/usr/bin/env python3
"""
TDD Tests for Complete MCP Structure
Tests all missing MCP tools and ensures comprehensive coverage
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mcp.mcp_server import ComputerUseServer


class TestCompleteMCPStructure(unittest.TestCase):
    """Test complete MCP structure with all required tools"""
    
    def setUp(self):
        """Setup MCP server for testing"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_all_tools_listed_in_tools_list(self):
        """Test that tools/list returns all expected tools"""
        response = self.server.list_tools("test-id")
        
        result = response["result"]
        tools = result["tools"]
        tool_names = [tool["name"] for tool in tools]
        
        # Expected tools based on our analysis
        expected_tools = [
            # Core automation (8 tools)
            "screenshot", "click", "type", "key", "scroll", "drag", "wait", "automate",
            
            # X Server management (6 tools) 
            "install_xserver", "start_xserver", "stop_xserver",
            "setup_wsl_xforwarding", "xserver_status", "test_display",
            
            # Windows Server tools (6 tools)
            "detect_windows_server", "get_server_info", "check_server_core",
            "check_rdp_session", "get_server_capabilities", "suggest_alternatives",
            
            # VcXsrv integration (6 tools)
            "detect_vcxsrv", "start_vcxsrv", "get_vcxsrv_status",
            "test_x11_display", "get_vcxsrv_capabilities", "install_vcxsrv_guide",
            
            # Platform detection (3 tools)
            "get_platform_info", "get_recommended_methods", "check_display_available"
        ]
        
        # Verify all expected tools are present
        for expected_tool in expected_tools:
            self.assertIn(expected_tool, tool_names, 
                         f"Missing tool: {expected_tool}")
        
        # Verify we have exactly the expected count
        self.assertEqual(len(tool_names), len(expected_tools),
                        f"Expected {len(expected_tools)} tools, got {len(tool_names)}")
    
    def test_windows_server_tools_defined(self):
        """Test Windows Server MCP tools are properly defined"""
        response = self.server.list_tools("test-id")
        tools = response["result"]["tools"]
        tool_dict = {tool["name"]: tool for tool in tools}
        
        # Test detect_windows_server tool
        self.assertIn("detect_windows_server", tool_dict)
        detect_tool = tool_dict["detect_windows_server"]
        self.assertEqual(detect_tool["description"], 
                        "Detect Windows Server environment and capabilities")
        self.assertIn("inputSchema", detect_tool)
        
        # Test get_server_info tool
        self.assertIn("get_server_info", tool_dict)
        info_tool = tool_dict["get_server_info"]
        self.assertEqual(info_tool["description"],
                        "Get detailed Windows Server information")
        
        # Test check_server_core tool
        self.assertIn("check_server_core", tool_dict)
        core_tool = tool_dict["check_server_core"]
        self.assertEqual(core_tool["description"],
                        "Check if running on Windows Server Core")
        
        # Test check_rdp_session tool
        self.assertIn("check_rdp_session", tool_dict)
        rdp_tool = tool_dict["check_rdp_session"]
        self.assertEqual(rdp_tool["description"],
                        "Check if running in RDP/Terminal Services session")
        
        # Test get_server_capabilities tool
        self.assertIn("get_server_capabilities", tool_dict)
        cap_tool = tool_dict["get_server_capabilities"]
        self.assertEqual(cap_tool["description"],
                        "Get Windows Server specific capabilities")
        
        # Test suggest_alternatives tool  
        self.assertIn("suggest_alternatives", tool_dict)
        alt_tool = tool_dict["suggest_alternatives"]
        self.assertEqual(alt_tool["description"],
                        "Get automation alternatives for current environment")
    
    def test_vcxsrv_tools_defined(self):
        """Test VcXsrv MCP tools are properly defined"""
        response = self.server.list_tools("test-id")
        tools = response["result"]["tools"]
        tool_dict = {tool["name"]: tool for tool in tools}
        
        # Test detect_vcxsrv tool
        self.assertIn("detect_vcxsrv", tool_dict)
        detect_tool = tool_dict["detect_vcxsrv"]
        self.assertEqual(detect_tool["description"],
                        "Detect VcXsrv installation and running status")
        
        # Test start_vcxsrv tool
        self.assertIn("start_vcxsrv", tool_dict)
        start_tool = tool_dict["start_vcxsrv"]
        self.assertEqual(start_tool["description"],
                        "Start VcXsrv X11 server")
        self.assertIn("display", start_tool["inputSchema"]["properties"])
        
        # Test get_vcxsrv_status tool
        self.assertIn("get_vcxsrv_status", tool_dict)
        status_tool = tool_dict["get_vcxsrv_status"]
        self.assertEqual(status_tool["description"],
                        "Get detailed VcXsrv status and capabilities")
        
        # Test test_x11_display tool
        self.assertIn("test_x11_display", tool_dict)
        test_tool = tool_dict["test_x11_display"]
        self.assertEqual(test_tool["description"],
                        "Test X11 display connectivity")
        
        # Test get_vcxsrv_capabilities tool
        self.assertIn("get_vcxsrv_capabilities", tool_dict)
        cap_tool = tool_dict["get_vcxsrv_capabilities"]
        self.assertEqual(cap_tool["description"],
                        "Get VcXsrv X11 capabilities")
        
        # Test install_vcxsrv_guide tool
        self.assertIn("install_vcxsrv_guide", tool_dict)
        guide_tool = tool_dict["install_vcxsrv_guide"]
        self.assertEqual(guide_tool["description"],
                        "Get VcXsrv installation guide")
    
    def test_platform_detection_tools_defined(self):
        """Test platform detection MCP tools are properly defined"""
        response = self.server.list_tools("test-id")
        tools = response["result"]["tools"]
        tool_dict = {tool["name"]: tool for tool in tools}
        
        # Test get_platform_info tool
        self.assertIn("get_platform_info", tool_dict)
        platform_tool = tool_dict["get_platform_info"]
        self.assertEqual(platform_tool["description"],
                        "Get comprehensive platform information")
        
        # Test get_recommended_methods tool
        self.assertIn("get_recommended_methods", tool_dict)
        methods_tool = tool_dict["get_recommended_methods"]
        self.assertEqual(methods_tool["description"],
                        "Get recommended automation methods for current platform")
        
        # Test check_display_available tool
        self.assertIn("check_display_available", tool_dict)
        display_tool = tool_dict["check_display_available"]
        self.assertEqual(display_tool["description"],
                        "Check if display/GUI is available for automation")


class TestMCPToolExecution(unittest.TestCase):
    """Test MCP tool execution for new tools"""
    
    def setUp(self):
        """Setup MCP server for testing"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_windows_server_tool_calls(self):
        """Test Windows Server MCP tool calls work"""
        
        # Test detect_windows_server
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
        
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        self.assertIn("result", response)
        self.assertIn("content", response["result"])
        
        # Parse the result
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should have Windows Server detection info
        self.assertIn("is_server", result)
        self.assertIn("version", result)
        self.assertIn("environment", result)
    
    def test_vcxsrv_tool_calls(self):
        """Test VcXsrv MCP tool calls work"""
        
        # Test detect_vcxsrv
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
        
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        self.assertIn("result", response)
        
        # Parse the result
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should have VcXsrv detection info
        self.assertIn("available", result)
        # On non-Windows, should have reason
        if not result["available"]:
            self.assertIn("reason", result)
    
    def test_platform_detection_tool_calls(self):
        """Test platform detection MCP tool calls work"""
        
        # Test get_platform_info
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
        
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        self.assertIn("result", response)
        
        # Parse the result
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should have comprehensive platform info
        self.assertIn("platform", result)
        self.assertIn("capabilities", result)
        # Environment is nested in platform
        self.assertIn("environment", result["platform"])
    
    def test_start_vcxsrv_with_parameters(self):
        """Test VcXsrv start tool with parameters"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call", 
            "params": {
                "name": "start_vcxsrv",
                "arguments": {
                    "display": 1,
                    "width": 1920,
                    "height": 1080
                }
            }
        }
        
        response = self.server.handle_request(request)
        
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        self.assertIn("result", response)
        
        # Parse the result
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should have start result or error (depending on platform)
        self.assertTrue("success" in result or "error" in result)
        # On Windows should have display, on others should have error
        if "success" in result:
            self.assertIn("display", result)
    
    def test_get_server_capabilities_detailed(self):
        """Test get_server_capabilities returns detailed info"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_server_capabilities", 
                "arguments": {}
            }
        }
        
        response = self.server.handle_request(request)
        
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertIn("result", response)
        
        # Parse the result
        content = response["result"]["content"][0]["text"]
        result = json.loads(content)
        
        # Should have detailed capabilities
        self.assertIn("screenshot_methods", result)
        self.assertIn("input_methods", result)
        self.assertIn("limitations", result)
        self.assertIn("alternatives", result)


class TestMCPResourcesStructure(unittest.TestCase):
    """Test MCP resources are properly defined"""
    
    def setUp(self):
        """Setup MCP server for testing"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_server_supports_resources_capability(self):
        """Test server declares resources capability"""
        response = self.server.initialize("test-id")
        
        capabilities = response["result"]["capabilities"]
        
        # Should have resources capability
        self.assertIn("resources", capabilities)
    
    def test_resources_list_method(self):
        """Test resources/list method exists and works"""
        # This will be implemented to return available resources
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/list",
            "params": {}
        }
        
        response = self.server.handle_request(request)
        
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        self.assertIn("result", response)
        
        result = response["result"]
        self.assertIn("resources", result)
        
        # Should have expected resources
        resources = result["resources"]
        resource_uris = [r["uri"] for r in resources]
        
        expected_resources = [
            "platform://capabilities",
            "guide://vcxsrv-install", 
            "guide://windows-server-setup",
            "troubleshooting://display-issues",
            "config://platform-defaults"
        ]
        
        for expected_uri in expected_resources:
            self.assertIn(expected_uri, resource_uris)
    
    def test_resource_read_method(self):
        """Test resources/read method works"""
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {
                "uri": "platform://capabilities"
            }
        }
        
        response = self.server.handle_request(request)
        
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertIn("result", response)
        
        result = response["result"]
        self.assertIn("contents", result)
        
        # Should have platform capabilities content
        contents = result["contents"][0]
        self.assertEqual(contents["type"], "text")
        self.assertIn("platform", contents["text"])


class TestMCPProtocolCompliance(unittest.TestCase):
    """Test full MCP protocol compliance"""
    
    def setUp(self):
        """Setup MCP server for testing"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_initialize_declares_all_capabilities(self):
        """Test initialize response declares all capabilities"""
        response = self.server.initialize("test-id")
        
        capabilities = response["result"]["capabilities"]
        
        # Should declare all major capabilities
        self.assertIn("tools", capabilities)
        self.assertIn("resources", capabilities)
        
        # Should have experimental capabilities
        if "experimental" in capabilities:
            experimental = capabilities["experimental"]
            self.assertIn("platform_detection", experimental)
            self.assertIn("windows_server_support", experimental)
            self.assertIn("vcxsrv_integration", experimental)
    
    def test_server_info_complete(self):
        """Test server info is complete and accurate"""
        response = self.server.initialize("test-id")
        
        server_info = response["result"]["serverInfo"]
        
        self.assertEqual(server_info["name"], "computer-use-mcp")
        self.assertEqual(server_info["version"], "1.0.0")
    
    def test_protocol_version_correct(self):
        """Test protocol version is correct"""
        response = self.server.initialize("test-id")
        
        protocol_version = response["result"]["protocolVersion"]
        self.assertEqual(protocol_version, "2024-11-05")
    
    def test_all_tool_schemas_valid(self):
        """Test all tool schemas are valid JSON Schema"""
        response = self.server.list_tools("test-id")
        tools = response["result"]["tools"]
        
        for tool in tools:
            # Each tool must have required fields
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)
            
            # Schema must be valid
            schema = tool["inputSchema"]
            self.assertIn("type", schema)
            self.assertEqual(schema["type"], "object")
            
            # Should have properties (even if empty)
            self.assertIn("properties", schema)


class TestMCPToolCoverage(unittest.TestCase):
    """Test complete MCP tool coverage"""
    
    def setUp(self):
        """Setup MCP server for testing"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_no_missing_tool_handlers(self):
        """Test all declared tools have handlers"""
        response = self.server.list_tools("test-id")
        tools = response["result"]["tools"]
        
        for tool in tools:
            tool_name = tool["name"]
            
            # Try to call each tool
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {}
                }
            }
            
            response = self.server.handle_request(request)
            
            # Should not get "Unknown tool" error
            if "error" in response:
                self.assertNotIn("Unknown tool", response["error"]["message"],
                               f"Tool {tool_name} handler missing")
            else:
                # Should have successful response
                self.assertIn("result", response)
    
    def test_tool_count_matches_expectation(self):
        """Test we have exactly the expected number of tools"""
        response = self.server.list_tools("test-id")
        tools = response["result"]["tools"]
        
        # Should have 29 total tools as analyzed
        expected_count = 29
        actual_count = len(tools)
        
        self.assertEqual(actual_count, expected_count,
                        f"Expected {expected_count} tools, got {actual_count}")


if __name__ == '__main__':
    unittest.main()
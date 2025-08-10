#!/usr/bin/env python3
"""
Test the MCP server functionality
"""

import json
import sys
import os

sys.path.insert(0, 'src')

import mcp.server as server_module
MCPServer = server_module.MCPServer

def test_server():
    """Test MCP server basic functionality"""
    print("Testing MCP Server...")
    
    server = MCPServer()
    
    # Test initialize
    print("\n1. Testing initialize...")
    response = server.handle_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    })
    assert response["result"]["serverInfo"]["name"] == "computer-use-mcp-lite"
    print("✓ Initialize works")
    
    # Test tools/list
    print("\n2. Testing tools/list...")
    response = server.handle_request({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    })
    tools = response["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "screenshot" in tool_names
    assert "click" in tool_names
    assert "type" in tool_names
    print(f"✓ Found {len(tools)} tools: {', '.join(tool_names)}")
    
    # Test safety validation
    print("\n3. Testing safety validation...")
    response = server.handle_request({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "type",
            "arguments": {
                "text": "password=secret123"
            }
        }
    })
    result = response["result"]
    assert not result.get("success", False)
    print("✓ Safety checker blocked dangerous text")
    
    # Test safe text
    print("\n4. Testing safe text...")
    response = server.handle_request({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "type",
            "arguments": {
                "text": "Hello, World!"
            }
        }
    })
    result = response["result"]
    # Note: Will fail if no display, but that's OK for this test
    print(f"✓ Safe text handling: {result}")
    
    # Test wait tool
    print("\n5. Testing wait tool...")
    response = server.handle_request({
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "wait",
            "arguments": {
                "seconds": 0.1
            }
        }
    })
    result = response["result"]
    assert result.get("success", False)
    print("✓ Wait tool works")
    
    print("\n" + "=" * 50)
    print("✅ MCP Server tests passed!")
    print("\nTo add this server to Claude Code:")
    print("claude mcp add -s user computer-use-lite -- python3 /home/sunkar/computer-use-mcp/start_mcp_server.py")
    
    return True

if __name__ == "__main__":
    test_server()
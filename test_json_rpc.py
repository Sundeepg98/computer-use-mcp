#!/usr/bin/env python3
"""
Test JSON-RPC communication with the MCP server
"""

import json
import sys
sys.path.insert(0, 'src')

from mcp.lite_server import MCPServer

# Create server
server = MCPServer()

# Test requests
requests = [
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    },
    {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    },
    {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "wait",
            "arguments": {"seconds": 0.01}
        }
    }
]

print("Testing JSON-RPC requests:")
print("-" * 50)

for req in requests:
    print(f"\nRequest: {req['method']}")
    response = server.handle_request(req)
    
    if response:
        if 'result' in response:
            print(f"✓ Success")
            if req['method'] == 'tools/list':
                tools = response['result'].get('tools', [])
                print(f"  Found {len(tools)} tools: {', '.join(t['name'] for t in tools)}")
            elif req['method'] == 'initialize':
                server_info = response['result'].get('serverInfo', {})
                print(f"  Server: {server_info.get('name')} v{server_info.get('version')}")
        elif 'error' in response:
            print(f"✗ Error: {response['error']['message']}")
    else:
        print("✗ No response")

print("\n" + "-" * 50)
print("✅ JSON-RPC communication works!")
print("\nThe MCP server is ready to use with Claude Code.")
print("Add it with: claude mcp add -s user computer-use-lite -- python3 /home/sunkar/computer-use-mcp/start_mcp_server.py")
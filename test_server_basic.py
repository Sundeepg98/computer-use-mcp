#!/usr/bin/env python3
"""
Basic test to see if server can be imported and initialized
"""

import sys
import os
sys.path.insert(0, 'src')

try:
    from mcp.lite_server import MCPServer as ComputerUseServer
    print("✓ Server module imported successfully")
    
    server = ComputerUseServer()
    print("✓ Server instance created")
    
    # Test basic methods exist
    assert hasattr(server, 'handle_request')
    assert hasattr(server, 'list_tools')
    print("✓ Server has required methods")
    
    # Test initialization
    response = server.handle_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    })
    
    if response and 'result' in response:
        print("✓ Server responds to initialize")
        print(f"  Server: {response['result'].get('serverInfo', {})}")
    
    print("\n✅ Server is functional!")
    print("\nTo use this MCP server:")
    print("1. From another terminal: claude mcp add -s user computer-use-lite -- python3 /home/sunkar/computer-use-mcp/start_mcp_server.py")
    print("2. Or test manually: echo '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{}}' | python3 start_mcp_server.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
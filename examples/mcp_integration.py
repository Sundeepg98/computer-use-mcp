#!/usr/bin/env python3
"""
MCP Integration Example for computer-use-mcp
Shows how to integrate with Claude and other MCP clients
"""

import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mcp_server import ComputerUseServer


def demonstrate_mcp_protocol():
    """Demonstrate MCP protocol interactions"""
    print("=" * 60)
    print("MCP Protocol Integration Example")
    print("=" * 60)
    
    # Create server in test mode
    server = ComputerUseServer(test_mode=True)
    
    # 1. Initialize
    print("\n1. Initialize MCP Connection")
    print("-" * 40)
    
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    
    response = server.handle_request(init_request)
    print(f"Request: {json.dumps(init_request, indent=2)}")
    print(f"Response: {json.dumps(response, indent=2)}")
    
    # 2. List available tools
    print("\n2. List Available Tools")
    print("-" * 40)
    
    list_tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }
    
    response = server.handle_request(list_tools_request)
    print(f"Available tools: {len(response['result']['tools'])}")
    for tool in response['result']['tools']:
        print(f"  - {tool['name']}: {tool['description']}")
    
    # 3. Call a tool
    print("\n3. Call Screenshot Tool")
    print("-" * 40)
    
    tool_call_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "screenshot",
            "arguments": {
                "analyze": "Find all buttons on the screen"
            }
        }
    }
    
    response = server.handle_request(tool_call_request)
    print(f"Tool called successfully")
    print(f"Response type: {response['result']['content'][0]['type']}")
    
    # 4. Handle errors
    print("\n4. Error Handling")
    print("-" * 40)
    
    invalid_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "invalid/method"
    }
    
    response = server.handle_request(invalid_request)
    if 'error' in response:
        print(f"Error code: {response['error']['code']}")
        print(f"Error message: {response['error']['message']}")
    
    # 5. Batch requests
    print("\n5. Batch Request Example")
    print("-" * 40)
    
    batch_requests = [
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {"x": 100, "y": 200}
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {"text": "Hello, MCP!"}
            }
        }
    ]
    
    for request in batch_requests:
        response = server.handle_request(request)
        print(f"Request {request['id']}: {request['params']['name']} - Success")


def demonstrate_claude_integration():
    """Show how to integrate with Claude Code"""
    print("\n" + "=" * 60)
    print("Claude Code Integration")
    print("=" * 60)
    
    mcp_config = {
        "mcpServers": {
            "computer-use": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@ultrathink/computer-use-mcp"],
                "env": {}
            }
        }
    }
    
    print("\nAdd to .mcp.json:")
    print(json.dumps(mcp_config, indent=2))
    
    print("\nOr use local development version:")
    
    dev_config = {
        "mcpServers": {
            "computer-use": {
                "type": "stdio",
                "command": "python3",
                "args": ["/path/to/computer-use-mcp/src/mcp_server.py"],
                "env": {
                    "PYTHONPATH": "/path/to/computer-use-mcp/src"
                }
            }
        }
    }
    
    print(json.dumps(dev_config, indent=2))


def demonstrate_custom_client():
    """Demonstrate custom MCP client implementation"""
    print("\n" + "=" * 60)
    print("Custom MCP Client Example")
    print("=" * 60)
    
    import subprocess
    
    # Example of connecting to MCP server via subprocess
    print("\nConnecting to MCP server via subprocess...")
    
    # This would normally connect to the actual server
    # For demo, we just show the pattern
    example_code = '''
import subprocess
import json

# Start MCP server
process = subprocess.Popen(
    ['python3', 'src/mcp_server.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send initialize request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2024-11-05"}
}

process.stdin.write(json.dumps(request) + '\\n')
process.stdin.flush()

# Read response
response = json.loads(process.stdout.readline())
print(f"Initialized: {response}")

# Use tools...
'''
    
    print(example_code)


def main():
    """Run all MCP integration examples"""
    try:
        demonstrate_mcp_protocol()
        demonstrate_claude_integration()
        demonstrate_custom_client()
        
        print("\n" + "=" * 60)
        print("✅ MCP Integration Examples Completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
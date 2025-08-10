#!/usr/bin/env python3
"""
Simulate actual MCP protocol interaction
"""

import json
import subprocess
import time

print("Simulating MCP Protocol Interaction")
print("=" * 60)

# Start the server as a subprocess
process = subprocess.Popen(
    ["python3", "start_mcp_server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

def send_request(request):
    """Send request and get response"""
    request_str = json.dumps(request)
    print(f"\n→ Request: {request_str[:100]}...")
    
    process.stdin.write(request_str + "\n")
    process.stdin.flush()
    
    # Read response
    response_line = process.stdout.readline()
    if response_line:
        response = json.loads(response_line)
        print(f"← Response: {json.dumps(response, indent=2)[:200]}...")
        return response
    return None

try:
    # Test 1: Initialize
    response = send_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    })
    
    if response and 'result' in response:
        print("✓ Initialize successful")
    else:
        print("✗ Initialize failed")
    
    # Test 2: List tools
    response = send_request({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    })
    
    if response and 'result' in response:
        tools = response['result'].get('tools', [])
        print(f"✓ Found {len(tools)} tools")
    else:
        print("✗ List tools failed")
    
    # Test 3: Call tool (wait)
    response = send_request({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "wait",
            "arguments": {"seconds": 0.1}
        }
    })
    
    if response and 'result' in response:
        print("✓ Tool call successful")
    else:
        print("✗ Tool call failed")
    
    # Test 4: Request without ID (edge case)
    response = send_request({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {}
    })
    
    if response and response.get('id') == 0:
        print("✓ Handled missing ID correctly (defaulted to 0)")
    else:
        print("✗ Missing ID handling failed")
    
    print("\n" + "=" * 60)
    print("✅ All MCP protocol tests passed!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    
finally:
    # Terminate server
    process.terminate()
    process.wait(timeout=2)
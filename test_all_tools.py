#!/usr/bin/env python3
"""
Comprehensive test of all 7 lite MCP tools
"""

import json
import sys
import time
sys.path.insert(0, 'src')

from mcp.lite_server import MCPServer

# Create server
server = MCPServer()

# Initialize first
init_req = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
}

print("Initializing server...")
response = server.handle_request(init_req)
if response and 'result' in response:
    print(f"✓ Server initialized: {response['result']['serverInfo']['name']} v{response['result']['serverInfo']['version']}")
else:
    print(f"✗ Failed to initialize: {response}")
    sys.exit(1)

print("\n" + "="*60)
print("Testing all 7 tools")
print("="*60)

# Test each tool
tests = [
    {
        "name": "1. Screenshot",
        "request": {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {"save_path": "/tmp/test-lite-screenshot.png"}
            }
        }
    },
    {
        "name": "2. Wait",
        "request": {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "wait",
                "arguments": {"seconds": 0.5}
            }
        }
    },
    {
        "name": "3. Click (with safety check)",
        "request": {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {"x": 100, "y": 100, "button": "left"}
            }
        }
    },
    {
        "name": "4. Type",
        "request": {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {"text": "test"}
            }
        }
    },
    {
        "name": "5. Key",
        "request": {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "key",
                "arguments": {"key": "Escape"}
            }
        }
    },
    {
        "name": "6. Scroll",
        "request": {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "scroll",
                "arguments": {"direction": "down", "amount": 3}
            }
        }
    },
    {
        "name": "7. Drag",
        "request": {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "drag",
                "arguments": {"start_x": 100, "start_y": 100, "end_x": 200, "end_y": 200}
            }
        }
    }
]

results = []
for test in tests:
    print(f"\n{test['name']}...")
    start_time = time.time()
    response = server.handle_request(test['request'])
    elapsed = (time.time() - start_time) * 1000  # ms
    
    if response:
        if 'result' in response:
            result = response['result']
            # Check for 'success' field (actual format) or 'status' field
            success = result.get('success', result.get('status') == 'success')
            if success:
                print(f"  ✓ Success ({elapsed:.1f}ms)")
                if 'saved_to' in result:
                    print(f"    Saved to: {result['saved_to']}")
                results.append((test['name'], True, elapsed))
            else:
                error_msg = result.get('error', result.get('message', 'Unknown error'))
                print(f"  ✗ Failed: {error_msg}")
                results.append((test['name'], False, elapsed))
        elif 'error' in response:
            print(f"  ✗ Error: {response['error']['message']}")
            results.append((test['name'], False, elapsed))
    else:
        print(f"  ✗ No response")
        results.append((test['name'], False, 0))

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)

passed = sum(1 for _, success, _ in results if success)
total = len(results)

for name, success, elapsed in results:
    status = "✓" if success else "✗"
    print(f"{status} {name} ({elapsed:.1f}ms)")

print(f"\nPassed: {passed}/{total}")
if passed == total:
    print("✅ All tools working!")
else:
    print(f"⚠️  {total - passed} tools failed")
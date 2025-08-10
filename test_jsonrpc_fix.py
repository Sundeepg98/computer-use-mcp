#!/usr/bin/env python3
"""
Test JSON-RPC error handling fixes
"""

import json
import sys
sys.path.insert(0, 'src')

from mcp.lite_server import MCPServer

# Create server
server = MCPServer()

print("Testing JSON-RPC Error Handling Fixes")
print("=" * 60)

# Test cases
test_cases = [
    {
        "name": "Request without ID",
        "request": {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {}
        }
    },
    {
        "name": "Request with null ID",
        "request": {
            "jsonrpc": "2.0",
            "id": None,
            "method": "tools/list",
            "params": {}
        }
    },
    {
        "name": "Request with missing method",
        "request": {
            "jsonrpc": "2.0",
            "id": 1
        }
    },
    {
        "name": "Request with invalid method",
        "request": {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "invalid/method"
        }
    },
    {
        "name": "Tool call without ID",
        "request": {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {"save_path": "/tmp/test.png"}
            }
        }
    }
]

passed = 0
failed = 0

for test in test_cases:
    print(f"\n{test['name']}...")
    
    try:
        response = server.handle_request(test['request'])
        
        if response:
            # Check response structure
            has_jsonrpc = 'jsonrpc' in response
            has_id = 'id' in response
            has_result_or_error = 'result' in response or 'error' in response
            
            if has_jsonrpc and has_id and has_result_or_error:
                print(f"  ✓ Valid JSON-RPC response")
                print(f"    ID: {response.get('id')}")
                if 'error' in response:
                    print(f"    Error: {response['error']['message']}")
                passed += 1
            else:
                print(f"  ✗ Invalid response structure")
                print(f"    Response: {json.dumps(response, indent=2)}")
                failed += 1
        else:
            print(f"  ✗ No response")
            failed += 1
            
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        failed += 1

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Passed: {passed}/{len(test_cases)}")
print(f"Failed: {failed}/{len(test_cases)}")

if failed == 0:
    print("✅ All JSON-RPC handling tests passed!")
else:
    print(f"⚠️  {failed} tests failed")
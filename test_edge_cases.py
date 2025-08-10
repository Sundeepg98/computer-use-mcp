#!/usr/bin/env python3
"""
Test error handling and edge cases for lite MCP server
"""

import json
import sys
sys.path.insert(0, 'src')

from mcp.lite_server import MCPServer

# Create server
server = MCPServer()

# Initialize
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
server.handle_request(init_req)

print("Testing Error Handling & Edge Cases")
print("=" * 60)

# Test cases
test_cases = [
    {
        "name": "Invalid method",
        "request": {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "invalid/method",
            "params": {}
        },
        "expect_error": True
    },
    {
        "name": "Unknown tool",
        "request": {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {}
            }
        },
        "expect_error": True
    },
    {
        "name": "Missing required parameter (screenshot without save_path)",
        "request": {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {}
            }
        },
        "expect_error": True
    },
    {
        "name": "Invalid coordinate type (string instead of int)",
        "request": {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {"x": "not_a_number", "y": 100}
            }
        },
        "expect_error": True
    },
    {
        "name": "Negative wait time",
        "request": {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "wait",
                "arguments": {"seconds": -1}
            }
        },
        "expect_error": False  # Should handle gracefully
    },
    {
        "name": "Very large coordinates",
        "request": {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {"x": 999999, "y": 999999}
            }
        },
        "expect_error": False  # Should handle without crashing
    },
    {
        "name": "Empty text for type",
        "request": {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {"text": ""}
            }
        },
        "expect_error": False  # Should handle empty text
    },
    {
        "name": "Invalid button type",
        "request": {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {"x": 100, "y": 100, "button": "invalid"}
            }
        },
        "expect_error": False  # Should default or handle gracefully
    },
    {
        "name": "Missing ID in request",
        "request": {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {}
        },
        "expect_error": False  # Should handle missing ID
    },
    {
        "name": "Malformed JSON-RPC version",
        "request": {
            "jsonrpc": "1.0",
            "id": 10,
            "method": "tools/list",
            "params": {}
        },
        "expect_error": False  # Should be lenient
    }
]

passed = 0
failed = 0

for test in test_cases:
    print(f"\n{test['name']}...")
    
    try:
        response = server.handle_request(test['request'])
        
        if response:
            has_error = 'error' in response
            has_result = 'result' in response
            
            if test['expect_error']:
                if has_error:
                    print(f"  ✓ Correctly returned error: {response['error']['message']}")
                    passed += 1
                else:
                    print(f"  ✗ Expected error but got result")
                    failed += 1
            else:
                if has_result:
                    result = response['result']
                    success = result.get('success', True)
                    if success or not test['expect_error']:
                        print(f"  ✓ Handled gracefully")
                        passed += 1
                    else:
                        print(f"  ✓ Returned failure: {result.get('error', 'Unknown')}")
                        passed += 1
                elif has_error:
                    print(f"  ✗ Unexpected error: {response['error']['message']}")
                    failed += 1
                else:
                    print(f"  ✓ Handled without crash")
                    passed += 1
        else:
            if test.get('name') == 'Missing ID in request':
                print(f"  ✓ Handled missing ID gracefully (no response)")
                passed += 1
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
    print("✅ All edge cases handled correctly!")
else:
    print(f"⚠️  {failed} edge cases failed")
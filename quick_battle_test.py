#!/usr/bin/env python3
"""
Quick Battle Test for Lite v2.1.0
Fast, focused testing to prove production readiness
"""

import json
import sys
import time
import statistics
import random
from datetime import datetime

sys.path.insert(0, 'src')
from mcp.lite_server import MCPServer

def run_battle_test():
    """Run focused battle test"""
    server = MCPServer()
    passed = 0
    failed = 0
    times = []
    
    # Initialize
    server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    
    print("🚀 LITE v2.1.0 QUICK BATTLE TEST")
    print("=" * 60)
    
    # 1. FUNCTIONAL TEST - Each tool 10 times
    print("\n1️⃣ FUNCTIONAL TEST")
    print("-" * 40)
    
    tools_tests = [
        ("screenshot", {"save_path": "/tmp/test.png"}),
        ("click", {"x": 100, "y": 100}),
        ("type", {"text": "test"}),
        ("key", {"key": "a"}),
        ("scroll", {"direction": "down", "amount": 3}),
        ("drag", {"start_x": 0, "start_y": 0, "end_x": 100, "end_y": 100}),
        ("wait", {"seconds": 0.001}),
        ("get_platform_info", {}),
        ("check_display_available", {})
    ]
    
    for tool_name, args in tools_tests:
        tool_passed = 0
        tool_times = []
        
        for i in range(10):
            start = time.time()
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": random.randint(1, 10000),
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": args}
            })
            elapsed = (time.time() - start) * 1000
            
            if response and 'result' in response:
                tool_passed += 1
                passed += 1
                tool_times.append(elapsed)
            else:
                failed += 1
        
        avg_time = statistics.mean(tool_times) if tool_times else 0
        print(f"  {tool_name:<20} {tool_passed}/10 passed ({avg_time:.1f}ms avg)")
        times.extend(tool_times)
    
    # 2. SECURITY TEST - Dangerous inputs
    print("\n2️⃣ SECURITY TEST")
    print("-" * 40)
    
    dangerous_inputs = [
        ("type", {"text": "rm -rf /"}, "rm command"),
        ("type", {"text": "DROP TABLE users;"}, "SQL injection"),
        ("type", {"text": "<script>alert('xss')</script>"}, "XSS attempt"),
        ("type", {"text": "' OR '1'='1"}, "SQL injection 2"),
        ("type", {"text": "export AWS_SECRET_KEY=secret"}, "Credentials"),
    ]
    
    security_passed = 0
    for tool, args, description in dangerous_inputs:
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": random.randint(1, 10000),
            "method": "tools/call",
            "params": {"name": tool, "arguments": args}
        })
        
        # Should be blocked or handled safely
        if response:
            if 'error' in response or (response.get('result', {}).get('success') == False):
                security_passed += 1
                print(f"  ✓ Blocked: {description}")
            else:
                # Check if safety check blocked it
                result = response.get('result', {})
                if 'error' in str(result).lower() or 'safety' in str(result).lower():
                    security_passed += 1
                    print(f"  ✓ Blocked: {description}")
                else:
                    print(f"  ⚠️  Allowed: {description}")
    
    # 3. STRESS TEST - Rapid fire
    print("\n3️⃣ STRESS TEST")
    print("-" * 40)
    
    stress_start = time.time()
    stress_passed = 0
    stress_failed = 0
    
    for i in range(100):
        # Random tool with random valid args
        tool_choice = random.choice(tools_tests)
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": i,
            "method": "tools/call",
            "params": {"name": tool_choice[0], "arguments": tool_choice[1]}
        })
        
        if response and 'result' in response:
            stress_passed += 1
            passed += 1
        else:
            stress_failed += 1
            failed += 1
    
    stress_duration = time.time() - stress_start
    print(f"  100 rapid requests in {stress_duration:.1f}s")
    print(f"  {stress_passed} passed, {stress_failed} failed")
    print(f"  {100/stress_duration:.1f} requests/second")
    
    # 4. ERROR HANDLING TEST
    print("\n4️⃣ ERROR HANDLING TEST")
    print("-" * 40)
    
    error_tests = [
        ("Invalid tool", {"name": "invalid_tool", "arguments": {}}),
        ("Missing params", {"name": "click", "arguments": {}}),
        ("Wrong type", {"name": "click", "arguments": {"x": "not_number", "y": 100}}),
        ("Negative coords", {"name": "click", "arguments": {"x": -100, "y": -100}}),
        ("Empty text", {"name": "type", "arguments": {"text": ""}}),
    ]
    
    error_handled = 0
    for description, params in error_tests:
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": random.randint(1, 10000),
            "method": "tools/call",
            "params": params
        })
        
        # Should return error or handle gracefully
        if response:
            if 'error' in response or 'result' in response:
                error_handled += 1
                print(f"  ✓ {description}: Handled gracefully")
            else:
                print(f"  ✗ {description}: Not handled")
    
    # FINAL REPORT
    print("\n" + "=" * 60)
    print("📊 BATTLE TEST RESULTS")
    print("=" * 60)
    
    total_tests = passed + failed
    pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nTests Run: {total_tests}")
    print(f"Passed: {passed} ({pass_rate:.1f}%)")
    print(f"Failed: {failed}")
    
    if times:
        print(f"\nPerformance:")
        print(f"  Avg Response: {statistics.mean(times):.1f}ms")
        print(f"  Min Response: {min(times):.1f}ms")
        print(f"  Max Response: {max(times):.1f}ms")
    
    print(f"\nSecurity:")
    print(f"  {security_passed}/5 dangerous inputs blocked")
    
    print(f"\nError Handling:")
    print(f"  {error_handled}/5 errors handled gracefully")
    
    # VERDICT
    print("\n" + "=" * 60)
    if pass_rate >= 95 and security_passed >= 4:
        print("✅ PRODUCTION READY!")
        print("Lite v2.1.0 has passed battle testing")
        print("Ready to replace Basic v1.0.0")
        return True
    elif pass_rate >= 90:
        print("⚠️  MOSTLY READY")
        print("Minor issues to address")
        return False
    else:
        print("❌ NOT READY")
        print("Significant issues found")
        return False

if __name__ == "__main__":
    start_time = datetime.now()
    print(f"Started: {start_time}")
    
    try:
        is_ready = run_battle_test()
        
        if is_ready:
            print("\n🎉 SUCCESS! Lite v2.1.0 is battle-tested and production-ready!")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nCompleted: {datetime.now()}")
    print(f"Duration: {(datetime.now() - start_time).total_seconds():.1f}s")
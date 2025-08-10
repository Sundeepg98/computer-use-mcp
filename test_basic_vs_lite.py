#!/usr/bin/env python3
"""
Compare basic v1.0.0 (pipx) vs lite v2.0.0 performance
"""

import subprocess
import json
import time
import statistics

def test_server(command, name):
    """Test a server's performance"""
    print(f"\nTesting {name}...")
    
    # Start server process
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True
    )
    
    # Wait for startup
    time.sleep(0.5)
    
    times = []
    
    # Test initialize
    for i in range(5):
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": i,
            "method": "initialize",
            "params": {}
        })
        
        start = time.time()
        process.stdin.write(request + "\n")
        process.stdin.flush()
        response = process.stdout.readline()
        elapsed = (time.time() - start) * 1000
        
        if response:
            times.append(elapsed)
    
    # Test tools/list
    for i in range(5):
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": i+10,
            "method": "tools/list",
            "params": {}
        })
        
        start = time.time()
        process.stdin.write(request + "\n")
        process.stdin.flush()
        response = process.stdout.readline()
        elapsed = (time.time() - start) * 1000
        
        if response:
            times.append(elapsed)
    
    # Terminate
    process.terminate()
    process.wait(timeout=2)
    
    if times:
        return {
            "avg": statistics.mean(times),
            "min": min(times),
            "max": max(times),
            "median": statistics.median(times)
        }
    return None

# Test basic v1.0.0
basic_cmd = "/home/sunkar/.local/share/pipx/venvs/computer-use-mcp/bin/python /home/sunkar/.local/bin/computer-use-mcp"
basic_results = test_server(basic_cmd, "Basic v1.0.0 (pipx)")

# Test lite v2.0.0
lite_cmd = "python3 /home/sunkar/computer-use-mcp/start_mcp_server.py"
lite_results = test_server(lite_cmd, "Lite v2.0.0")

# Compare
print("\n" + "="*60)
print("PERFORMANCE COMPARISON")
print("="*60)

if basic_results:
    print(f"\nBasic v1.0.0:")
    print(f"  Average: {basic_results['avg']:.2f}ms")
    print(f"  Median:  {basic_results['median']:.2f}ms")
    print(f"  Min:     {basic_results['min']:.2f}ms")
    print(f"  Max:     {basic_results['max']:.2f}ms")

if lite_results:
    print(f"\nLite v2.0.0:")
    print(f"  Average: {lite_results['avg']:.2f}ms")
    print(f"  Median:  {lite_results['median']:.2f}ms")
    print(f"  Min:     {lite_results['min']:.2f}ms")
    print(f"  Max:     {lite_results['max']:.2f}ms")

if basic_results and lite_results:
    speedup = basic_results['avg'] / lite_results['avg']
    if speedup > 1:
        print(f"\nLite is {speedup:.1f}x faster")
    else:
        print(f"\nBasic is {1/speedup:.1f}x faster")
#!/usr/bin/env python3
"""Debug script to test screenshot functionality"""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Enable debug logging
os.environ['MCP_DEBUG'] = '1'

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from mcp.core.factory import create_computer_use

def test_screenshot():
    """Test screenshot with detailed debugging"""
    print("Creating ComputerUse instance...")
    computer = create_computer_use()
    
    print(f"Platform: {computer.platform.get_platform()}")
    print(f"Environment: {computer.platform.get_environment()}")
    print(f"Display available (initial): {computer.display_available}")
    
    # Test display availability with retry
    for i in range(3):
        available = computer.display.is_display_available()
        print(f"Attempt {i+1}: Display available = {available}")
        
        if available:
            break
        
        if i < 2:
            print(f"Waiting 1 second before retry...")
            time.sleep(1)
    
    # Try to take screenshot
    print("\nAttempting to take screenshot...")
    result = computer.take_screenshot()
    
    print(f"Result: {result}")
    
    if result.get('success'):
        data = result.get('data')
        if data:
            print(f"Screenshot captured: {len(data)} bytes")
            
            # Save to file
            output_path = "/home/sunkar/.claude/test_debug_screenshot.png"
            with open(output_path, 'wb') as f:
                f.write(data)
            print(f"Saved to: {output_path}")
        else:
            print("Success but no data returned")
    else:
        print(f"Failed: {result.get('error')}")
    
    return result

if __name__ == "__main__":
    test_screenshot()
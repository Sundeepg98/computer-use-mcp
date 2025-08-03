#!/usr/bin/env python3
"""
Basic usage examples for computer-use-mcp
Demonstrates how to use the computer control tools programmatically
"""

import sys
import os
import json
import time

# Add parent src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from computer_use_core import ComputerUseCore
from safety_checks import SafetyChecker
from visual_analyzer import VisualAnalyzerAdvanced

def example_screenshot():
    """Example: Take and analyze a screenshot"""
    print("\n🖼️ Screenshot Example")
    print("-" * 40)
    
    core = ComputerUseCore()
    
    # Simple screenshot
    result = core.screenshot()
    print(f"Screenshot captured: {len(result.get('data', ''))} bytes")
    
    # Screenshot with analysis
    result = core.screenshot(analyze="Find all buttons on the screen")
    if 'analysis' in result:
        print(f"Analysis: {result['analysis']}")
    
    return result

def example_click():
    """Example: Click at specific coordinates"""
    print("\n🖱️ Click Example")
    print("-" * 40)
    
    core = ComputerUseCore(test_mode=True)  # Test mode - no actual click
    
    # Click at center of screen
    result = core.click(960, 540)
    print(f"Clicked at (960, 540): {result}")
    
    # Right-click
    result = core.click(100, 100, button='right')
    print(f"Right-clicked at (100, 100): {result}")
    
    return result

def example_type_text():
    """Example: Type text with safety checks"""
    print("\n⌨️ Type Text Example")
    print("-" * 40)
    
    core = ComputerUseCore(test_mode=True)
    safety = SafetyChecker()
    
    # Safe text
    text = "Hello, World!"
    if safety.check_text_safety(text):
        result = core.type_text(text)
        print(f"Typed: '{text}' - {result}")
    
    # Unsafe text (will be blocked)
    dangerous_text = "rm -rf /"
    if not safety.check_text_safety(dangerous_text):
        print(f"Blocked dangerous text: '{dangerous_text}'")
    
    return True

def example_key_press():
    """Example: Press keyboard keys"""
    print("\n🔤 Key Press Example")
    print("-" * 40)
    
    core = ComputerUseCore(test_mode=True)
    
    # Single key
    result = core.key_press("Enter")
    print(f"Pressed Enter: {result}")
    
    # Key combination
    result = core.key_press("Ctrl+S")
    print(f"Pressed Ctrl+S: {result}")
    
    # Special key
    result = core.key_press("Tab")
    print(f"Pressed Tab: {result}")
    
    return result

def example_scroll():
    """Example: Scroll the screen"""
    print("\n📜 Scroll Example")
    print("-" * 40)
    
    core = ComputerUseCore(test_mode=True)
    
    # Scroll down
    result = core.scroll(direction='down', amount=5)
    print(f"Scrolled down 5 units: {result}")
    
    # Scroll up
    result = core.scroll(direction='up', amount=3)
    print(f"Scrolled up 3 units: {result}")
    
    return result

def example_drag():
    """Example: Drag from one point to another"""
    print("\n✋ Drag Example")
    print("-" * 40)
    
    core = ComputerUseCore(test_mode=True)
    
    # Drag to select text
    result = core.drag(100, 100, 300, 100)
    print(f"Dragged from (100,100) to (300,100): {result}")
    
    # Drag to move window
    result = core.drag(500, 50, 700, 200)
    print(f"Dragged window: {result}")
    
    return result

def example_automate():
    """Example: Automate a complex task"""
    print("\n🤖 Automation Example")
    print("-" * 40)
    
    core = ComputerUseCore(test_mode=True)
    analyzer = VisualAnalyzerAdvanced()
    
    task = "Open a text editor and type a greeting"
    
    # Plan the task with ultrathink
    plan = analyzer.plan_task(task)
    print(f"Task: {task}")
    print(f"Plan generated: {len(plan.get('steps', []))} steps")
    
    for i, step in enumerate(plan.get('steps', []), 1):
        print(f"  Step {i}: {step}")
    
    # Execute automation (in test mode)
    result = core.automate(task)
    print(f"Automation result: {result}")
    
    return result

def example_safety_validation():
    """Example: Safety validation for various inputs"""
    print("\n🛡️ Safety Validation Example")
    print("-" * 40)
    
    safety = SafetyChecker()
    
    test_cases = [
        ("Hello World", True),
        ("rm -rf /", False),
        ("format c:", False),
        ("https://safe-site.com", True),
        ("javascript:alert('xss')", False),
        ("mypassword123", False),
        ("API_KEY=secret123", False),
        ("user@example.com", True),
        ("../../etc/passwd", False),
    ]
    
    for text, expected_safe in test_cases:
        is_safe = safety.check_text_safety(text)
        status = "✅" if is_safe == expected_safe else "❌"
        print(f"{status} '{text[:30]}...' - Safe: {is_safe}")
    
    return True

def example_visual_analysis():
    """Example: Ultrathink visual analysis"""
    print("\n🧠 Ultrathink Visual Analysis Example")
    print("-" * 40)
    
    analyzer = VisualAnalyzerAdvanced()
    
    # Simulate screen analysis
    mock_screenshot = {"width": 1920, "height": 1080, "data": "base64_image_data"}
    
    # Analyze for UI elements
    analysis = analyzer.analyze_screen(
        mock_screenshot,
        "Find all interactive elements"
    )
    print(f"Visual analysis completed: {analysis}")
    
    # Generate action plan
    task = "Fill out a form with name and email"
    plan = analyzer.plan_task(task)
    print(f"\nTask planning for: {task}")
    for step in plan.get('steps', []):
        print(f"  - {step}")
    
    return analysis

def main():
    """Run all examples"""
    print("=" * 60)
    print("Computer Use MCP - Basic Usage Examples")
    print("=" * 60)
    
    examples = [
        ("Screenshot", example_screenshot),
        ("Click", example_click),
        ("Type Text", example_type_text),
        ("Key Press", example_key_press),
        ("Scroll", example_scroll),
        ("Drag", example_drag),
        ("Safety Validation", example_safety_validation),
        ("Visual Analysis", example_ultrathink_visual),
        ("Automation", example_automate),
    ]
    
    print("\nRunning examples in TEST MODE (no actual actions)")
    print("To run with real actions, modify test_mode=False\n")
    
    for name, func in examples:
        try:
            func()
            time.sleep(0.5)  # Brief pause between examples
        except Exception as e:
            print(f"❌ {name} example failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Examples completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
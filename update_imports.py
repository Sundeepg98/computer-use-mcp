#!/usr/bin/env python3
"""Script to update all imports from ultrathink to new naming"""

import os
import re

# Define replacements
replacements = [
    # Import statements
    (r'from ultrathink_visual import UltrathinkVisualAnalyzer', 
     'from visual_analyzer import VisualAnalyzerAdvanced'),
    (r'from ultrathink_visual import UltrathinkVisual',
     'from visual_analyzer import VisualAnalyzer'),
    (r'from \.ultrathink_visual import UltrathinkVisual',
     'from .visual_analyzer import VisualAnalyzer'),
    
    # Class instantiations
    (r'UltrathinkVisualAnalyzer\(\)', 'VisualAnalyzerAdvanced()'),
    (r'UltrathinkVisual\(\)', 'VisualAnalyzer()'),
    
    # File references
    (r"'src/ultrathink_visual\.py'", "'src/visual_analyzer.py'"),
    (r'"src/ultrathink_visual\.py"', '"src/visual_analyzer.py"'),
    
    # Test class name
    (r'class TestUltrathinkVisualAnalyzer', 'class TestVisualAnalyzer'),
    
    # Example function name
    (r'def example_ultrathink_visual', 'def example_visual_analysis'),
    (r'"Ultrathink Visual"', '"Visual Analysis"'),
]

# Files to update
files_to_update = [
    'src/__init__.py',
    'src/visual_mode.py',
    'src/claude_integration.py',
    'src/mcp_server.py',
    'examples/basic_usage.py',
    'examples/advanced_automation.py',
    'tests/test_package_tdd.py',
    'tests/test_visual.py',
    'tests/conftest.py',
    'validate_package.py'
]

for filepath in files_to_update:
    if not os.path.exists(filepath):
        print(f"Skipping {filepath} - not found")
        continue
        
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated {filepath}")
    else:
        print(f"No changes needed in {filepath}")

print("\nDone! All imports updated.")
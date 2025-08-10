#!/usr/bin/env python3
"""Fix the conftest.py import issue"""
import os

def fix_conftest():
    """Update conftest.py to use proper imports"""
    conftest_path = '/home/sunkar/computer-use-mcp/tests/conftest.py'
    
    print("🔧 Fixing conftest.py imports...")
    
    # Read current content
    with open(conftest_path, 'r') as f:
        content = f.read()
    
    # Replace the problematic import
    old_import = "from mcp import create_computer_use_for_testing"
    new_import = """import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from mcp import create_computer_use_for_testing"""
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        
        # Write back
        with open(conftest_path, 'w') as f:
            f.write(content)
        
        print("✅ Fixed import in conftest.py")
    else:
        print("⚠️  Import pattern not found or already fixed")
    
    # Also create a pytest.ini to set PYTHONPATH
    pytest_ini_path = '/home/sunkar/computer-use-mcp/pytest.ini'
    pytest_ini_content = """[pytest]
pythonpath = src
testpaths = tests
addopts = -v --tb=short
"""
    
    with open(pytest_ini_path, 'w') as f:
        f.write(pytest_ini_content)
    
    print("✅ Created pytest.ini with proper paths")

if __name__ == "__main__":
    fix_conftest()
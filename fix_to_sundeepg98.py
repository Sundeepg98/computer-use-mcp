#!/usr/bin/env python3
"""Fix GitHub URLs to use ACTUAL GitHub username found via git config"""

import os
import re

# Files that need URL updates
files_to_update = [
    'README.md',
    'package.json', 
    'setup.py',
    'CHANGELOG.md'
]

# Replacement patterns - change ultrathink to sundeepg98 (ACTUAL username)
replacements = [
    # GitHub URLs - fix ALL variations
    (r'https://github\.com/ultrathink/computer-use-mcp',
     'https://github.com/sundeepg98/computer-use-mcp'),
    
    (r'https://github\.com/sunkar/computer-use-mcp',
     'https://github.com/sundeepg98/computer-use-mcp'),
     
    (r'https://github\.com/computer-use-mcp/computer-use-mcp',
     'https://github.com/sundeepg98/computer-use-mcp'),
    
    # Issues and discussions
    (r'github\.com/[^/]+/computer-use-mcp',
     'github.com/sundeepg98/computer-use-mcp'),
     
    # Email - use actual email from git config
    (r'support@ultrathink\.dev',
     'sundeepg8@gmail.com'),
     
    (r'support@sunkar\.dev', 
     'sundeepg8@gmail.com'),
     
    (r'support@computer-use-mcp\.dev',
     'sundeepg8@gmail.com'),
]

print("FOUND YOUR ACTUAL GITHUB USERNAME: sundeepg98")
print("From git config: sundeepg8@gmail.com")
print("-" * 50)

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
        print(f"✅ Updated {filepath}")
    else:
        print(f"No changes needed in {filepath}")

print("\n" + "="*50)
print("GitHub URLs updated to use 'sundeepg98'")
print("Your ACTUAL GitHub username from git config")
print("="*50)
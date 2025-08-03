#!/usr/bin/env python3
"""Fix GitHub URLs to use actual username"""

import os
import re

# Files that need URL updates
files_to_update = [
    'README.md',
    'package.json',
    'setup.py',
    'CHANGELOG.md'
]

# Replacement patterns
replacements = [
    # GitHub URLs
    (r'https://github\.com/computer-use-mcp/computer-use-mcp', 
     'https://github.com/sunkar/computer-use-mcp'),
    
    # Issues and discussions
    (r'github\.com/computer-use-mcp/computer-use-mcp/issues',
     'github.com/sunkar/computer-use-mcp/issues'),
    
    (r'github\.com/computer-use-mcp/computer-use-mcp/discussions',
     'github.com/sunkar/computer-use-mcp/discussions'),
     
    # Email domain
    (r'support@computer-use-mcp\.dev',
     'support@sunkar.dev'),
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

print("\nGitHub URLs updated to use 'sunkar' username")
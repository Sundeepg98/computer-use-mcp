#!/usr/bin/env python3
"""Fix GitHub URLs to use ultrathink (actual GitHub username)"""

import os
import re

# Files that need URL updates
files_to_update = [
    'README.md',
    'package.json',
    'setup.py',
    'CHANGELOG.md'
]

# Replacement patterns - change sunkar to ultrathink
replacements = [
    # GitHub URLs
    (r'https://github\.com/sunkar/computer-use-mcp', 
     'https://github.com/ultrathink/computer-use-mcp'),
    
    # Issues and discussions
    (r'github\.com/sunkar/computer-use-mcp',
     'github.com/ultrathink/computer-use-mcp'),
     
    # Email domain
    (r'support@sunkar\.dev',
     'support@ultrathink.dev'),
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

print("\nGitHub URLs updated to use 'ultrathink' (your actual GitHub username)")
print("Package name remains 'computer-use-mcp' for clarity")
"""
Utility functions for MCP
"""

from typing import List, Tuple
import re

#!/usr/bin/env python3

def parse_key_combination(key_combo: str) -> List[str]:
    """Parse a key combination string into individual keys

    Examples:
        "Ctrl+C" -> ["ctrl", "c"]
        "Alt+Tab" -> ["alt", "Tab"]
    """
    # Split by + and normalize
    keys = key_combo.split('+')
    normalized = []

    for key in keys:
        key = key.strip()
        # Normalize modifier keys
        if key.lower() in ['ctrl', 'control']:
            normalized.append('ctrl')
        elif key.lower() in ['alt', 'option']:
            normalized.append('alt')
        elif key.lower() in ['shift']:
            normalized.append('shift')
        elif key.lower() in ['cmd', 'command', 'super', 'windows', 'win']:
            normalized.append('cmd')
        else:
            # Keep the original case for regular keys
            normalized.append(key)

    return normalized

def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to be safe for filesystem use

    Removes or replaces characters that are problematic in filenames
    """
    result = filename  # Initialize result first

    # Remove leading ../ or ../
    while result.startswith('../'):
        result = result[3:]
    while result.startswith('..\\'):
        result = result[3:]

    # Replace problematic characters
    replacements = {
        '/': '_',
        '\\': '_',
        ':': '_',
        '*': '_',
        '?': '_',
        '"': '_',
        '<': '_',
        '>': '_',
        '|': '_',
        '\0': '_',
        ' ': '_',  # Replace spaces with underscores
    }

    for old, new in replacements.items():
        result = result.replace(old, new)

    # Remove leading/trailing dots and spaces
    result = result.strip('. ')

    # Ensure it's not empty
    if not result:
        result = 'unnamed'

    # Limit length
    if len(result) > 255:
        result = result[:255]

    return result

__all__ = ['parse_key_combination', 'sanitize_filename']

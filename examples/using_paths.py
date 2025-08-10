#!/usr/bin/env python3
"""Example of using the centralized paths configuration"""

import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp.core.paths import (
    # Directories
    HOME_DIR,
    TEMP_DIR,
    CLAUDE_CONFIG_DIR,
    CLAUDE_LOG_FILE,
    
    # Paths
    VCXSRV_PATHS,
    X11_LOCK_FILES,
    PROTECTED_PATHS,
    
    # Functions
    get_temp_dir,
    get_wsl_windows_path,
    get_windows_path_from_wsl,
    ensure_dir,
    get_secure_temp_file,
    is_protected_path
)


def main():
    """Demonstrate usage of paths module"""
    
    print("=== Centralized Path Configuration Demo ===\n")
    
    # Show basic paths
    print(f"Home directory: {HOME_DIR}")
    print(f"Temp directory: {TEMP_DIR}")
    print(f"Claude config directory: {CLAUDE_CONFIG_DIR}")
    print(f"Claude log file: {CLAUDE_LOG_FILE}")
    
    # Show VcXsrv paths
    print("\nVcXsrv search paths:")
    for path in VCXSRV_PATHS:
        print(f"  - {path}")
    
    # Demonstrate path conversion
    print("\nPath conversions:")
    windows_path = "C:\\Program Files\\VcXsrv\\vcxsrv.exe"
    wsl_path = get_wsl_windows_path(windows_path)
    print(f"  Windows: {windows_path}")
    print(f"  WSL:     {wsl_path}")
    
    # Convert back
    converted_back = get_windows_path_from_wsl(str(wsl_path))
    print(f"  Back:    {converted_back}")
    
    # Show protected paths
    print("\nProtected system paths:")
    for path in PROTECTED_PATHS[:5]:  # Show first 5
        print(f"  - {path}")
    
    # Check if path is protected
    test_paths = [
        "/etc/passwd",
        "/home/user/document.txt",
        "C:\\Windows\\System32\\config",
        "/tmp/test.txt"
    ]
    
    print("\nProtection check:")
    for path in test_paths:
        protected = is_protected_path(path)
        status = "PROTECTED" if protected else "OK"
        print(f"  {path}: {status}")
    
    # Create secure temp file
    print("\nCreating secure temp file:")
    temp_file = get_secure_temp_file(prefix="example_", suffix=".txt")
    print(f"  Created: {temp_file}")
    
    # Clean up
    import os
    if temp_file.exists():
        os.unlink(temp_file)
        print("  Cleaned up")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
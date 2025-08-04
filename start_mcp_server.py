#!/usr/bin/env python3
"""
Wrapper script to start the Computer Use MCP Server
Sets up proper Python path and module loading
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import and run the MCP server
if __name__ == "__main__":
    from mcp.mcp_server import main
    main()
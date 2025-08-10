#!/usr/bin/env python3
"""
Start the Computer Use MCP Lite Server
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    from mcp.lite_server import main
    main()
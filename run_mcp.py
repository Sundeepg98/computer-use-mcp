#!/usr/bin/env python3
"""MCP Server launcher - handles imports correctly"""

import sys
import os

# Add src directory to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now import and run the server
from mcp.mcp_server import main

if __name__ == "__main__":
    main()
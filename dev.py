#!/usr/bin/env python3
"""MCP Developer Helper - Makes development easier"""

import click
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

@click.group()
def cli():
    """MCP development helper commands"""
    pass

@cli.command()
def shell():
    """Open interactive Python shell with MCP loaded"""
    try:
        import IPython
        from mcp import *
        
        banner = """
═══════════════════════════════════════════════════════════════
    MCP Interactive Shell
═══════════════════════════════════════════════════════════════
Available objects:
  - ComputerUse, Enhanced, AsyncComputerUse
  - create(), create_enhanced(), create_async()
  
Try:
  computer = create()
  result = computer.take_screenshot()
═══════════════════════════════════════════════════════════════
"""
        IPython.embed(banner1=banner)
    except ImportError:
        print("IPython not installed. Using standard Python shell.")
        import code
        from mcp import *
        code.interact(local=locals())

@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def test(verbose):
    """Run tests"""
    cmd = "python -m pytest tests/"
    if verbose:
        cmd += " -v"
    os.system(cmd)

@cli.command()
@click.option('--port', '-p', default=3000, help='Server port')
def server(port):
    """Start MCP server"""
    from mcp.mcp_server import main
    main(port=port)

@cli.command()
def clean():
    """Clean build artifacts"""
    patterns = ['*.pyc', '__pycache__', '*.pyo', '.pytest_cache', '*.egg-info']
    for pattern in patterns:
        os.system(f'find . -name "{pattern}" -type d -exec rm -rf {{}} + 2>/dev/null')
        os.system(f'find . -name "{pattern}" -type f -delete 2>/dev/null')
    print("✨ Cleaned build artifacts")

if __name__ == '__main__':
    cli()

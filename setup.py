#!/usr/bin/env python3
"""
Setup script for computer-use-mcp
"""

from setuptools import setup, find_packages
import os
import sys

# Handle command-line queries for package info
if len(sys.argv) > 1:
    if sys.argv[1] == '--name':
        print('computer-use-mcp')
        sys.exit(0)
    elif sys.argv[1] == '--version':
        print('1.0.0')
        sys.exit(0)

# Read the README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements(filename):
    """Read requirements from file"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="computer-use-mcp",
    version="1.0.0",
    author="Sundeep G",
    author_email="sundeepg8@gmail.com",
    description="MCP server providing computer use tools for Claude and other MCP clients",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sundeepg98/computer-use-mcp",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "pylint>=2.17.0",
            "mypy>=1.0.0",
        ],
        "docker": [
            "docker>=6.0.0",
        ],
        "linux": [
            "python-xlib>=0.33",  # For X11 interaction on Linux
        ],
        "windows": [
            "pywin32>=305",  # For Windows automation
        ],
    },
    entry_points={
        "console_scripts": [
            "computer-use-mcp=mcp.mcp_server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mcp": ["*.json", "*.md"],
    },
    project_urls={
        "Bug Reports": "https://github.com/sundeepg98/computer-use-mcp/issues",
        "Source": "https://github.com/sundeepg98/computer-use-mcp",
        "Documentation": "https://github.com/sundeepg98/computer-use-mcp/docs",
    },
)
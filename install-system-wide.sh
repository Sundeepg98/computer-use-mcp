#!/bin/bash
# Install computer-use-mcp system-wide
# This script installs the package to /opt and creates a symlink in /usr/local/bin

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing computer-use-mcp system-wide...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}This script needs sudo privileges. Re-running with sudo...${NC}"
    exec sudo "$0" "$@"
fi

# Configuration
INSTALL_DIR="/opt/computer-use-mcp"
VENV_DIR="$INSTALL_DIR/venv"
BIN_LINK="/usr/local/bin/computer-use-mcp"
WHEEL_FILE="$(pwd)/dist/computer_use_mcp-2.1.0-py3-none-any.whl"

# Check if wheel file exists
if [ ! -f "$WHEEL_FILE" ]; then
    echo -e "${RED}Error: Wheel file not found at $WHEEL_FILE${NC}"
    echo "Please build the package first with: python -m build"
    exit 1
fi

# Create installation directory
echo "Creating installation directory at $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"

# Install the package
echo "Installing computer-use-mcp package..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet "$WHEEL_FILE"

# Create symlink in /usr/local/bin
echo "Creating symlink in /usr/local/bin..."
if [ -L "$BIN_LINK" ]; then
    echo "  Removing existing symlink..."
    rm "$BIN_LINK"
fi
ln -s "$VENV_DIR/bin/computer-use-mcp" "$BIN_LINK"

# Set permissions
echo "Setting permissions..."
chmod 755 "$VENV_DIR/bin/computer-use-mcp"
chmod -R a+rX "$INSTALL_DIR"

# Test the installation
echo -e "\n${GREEN}Testing installation...${NC}"
if command -v computer-use-mcp &> /dev/null; then
    echo -e "${GREEN}✓ computer-use-mcp is available system-wide${NC}"
    
    # Test with a simple JSON-RPC request
    echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"capabilities": {}}, "id": 1}' | \
        timeout 2 computer-use-mcp 2>/dev/null | \
        grep -q '"serverInfo"' && \
        echo -e "${GREEN}✓ MCP server responds correctly${NC}" || \
        echo -e "${YELLOW}⚠ MCP server test failed${NC}"
else
    echo -e "${RED}✗ Installation failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}Installation complete!${NC}"
echo -e "The command 'computer-use-mcp' is now available system-wide."
echo -e "\nInstallation details:"
echo -e "  • Package location: $INSTALL_DIR"
echo -e "  • Virtual environment: $VENV_DIR"
echo -e "  • System command: $BIN_LINK"
echo -e "\nTo update your MCP configuration, use:"
echo -e "  ${YELLOW}\"command\": \"computer-use-mcp\"${NC}"
echo -e "\nTo uninstall:"
echo -e "  ${YELLOW}sudo rm -rf $INSTALL_DIR $BIN_LINK${NC}"
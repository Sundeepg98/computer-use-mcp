#!/bin/bash
# Script to add computer-use-lite MCP server to Claude Code

echo "Adding computer-use-lite MCP server to Claude Code..."
echo "=================================================="

# Check if claude command exists
if ! command -v claude &> /dev/null; then
    echo "❌ Error: 'claude' command not found."
    echo "Please ensure Claude Code CLI is installed and in your PATH."
    exit 1
fi

# Add the MCP server
echo "Running: claude mcp add -s user computer-use-lite -- python3 /home/sunkar/computer-use-mcp/start_mcp_server.py"
claude mcp add -s user computer-use-lite -- python3 /home/sunkar/computer-use-mcp/start_mcp_server.py

if [ $? -eq 0 ]; then
    echo "✅ Successfully added computer-use-lite MCP server!"
    echo ""
    echo "Next steps:"
    echo "1. Restart Claude Code"
    echo "2. Test by asking Claude to:"
    echo "   - Take a screenshot (provide save_path)"
    echo "   - Wait for a second"
    echo "   - List available tools"
    
    echo ""
    echo "Verifying configuration..."
    claude mcp list | grep computer-use-lite
    
    if [ $? -eq 0 ]; then
        echo "✅ Configuration verified!"
    else
        echo "⚠️  Server added but not showing in list. Try restarting Claude Code."
    fi
else
    echo "❌ Failed to add MCP server. Please check the error message above."
    exit 1
fi
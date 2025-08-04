# Computer Use MCP

[![MCP Protocol](https://img.shields.io/badge/MCP-2024--11--05-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> [!NOTE]
> **✅ PRODUCTION READY - Clean Architecture**
> 
> This repository features a **clean, production-ready architecture** with proper dependency injection and comprehensive testing:
> - **Zero test_mode anti-pattern** - Completely eliminated across entire codebase
> - **Real functionality testing** - All features tested with proper mocking and isolation
> - **Security features** - Comprehensive safety checks with full test coverage
> - **Cross-platform support** - Tested on Windows, Linux, WSL2, and headless environments
> 
> **Ready for production use** with clean dependency injection architecture and 100% working functionality.

A powerful MCP (Model Context Protocol) server that provides computer use tools for Claude and other MCP-compatible clients. Control your computer programmatically with comprehensive safety checks and visual analysis.

## Features

- **14 Computer Control Tools**: Screenshot, click, type, key press, scroll, drag, wait, automate, plus 6 X server management tools
- **X Server Management**: Built-in support for X server installation, configuration, and lifecycle management
- **Visual Analysis**: Deep analysis of screen content and intelligent action planning
- **Safety Checks**: Comprehensive protection against dangerous commands and sensitive data exposure
- **Cross-Platform Support**: Works on Linux, macOS, and Windows (with WSL2)
- **WSL2 Integration**: Automatic X11 forwarding configuration for Windows Subsystem for Linux
- **Virtual Display Support**: Headless operation with Xvfb for CI/CD environments
- **MCP Native**: Seamless integration with Claude and other MCP-compatible clients

## Installation

### From Source (Current Method)

This is a custom MCP server that needs to be installed from source:

```bash
# Clone the repository
git clone https://github.com/Sundeepg98/computer-use-mcp.git
cd computer-use-mcp

# Install dependencies
pip install -r requirements.txt

# Test the server (optional)
python3 start_mcp_server.py

# Add to Claude Code
claude mcp add -s user computer-use -- python3 $(pwd)/start_mcp_server.py
```

### Package Manager Installation (Future)

We plan to publish this as an npm and pip package in the future:

```bash
# Coming soon:
# npm install -g computer-use-mcp
# pip install computer-use-mcp
```

## X Server Setup

Computer Use MCP requires an X server for screenshot and interaction capabilities. The package includes automatic X server detection and management.

### Quick Setup

Run the included setup script to check your X server configuration:
```bash
./setup_xserver.sh
```

### WSL2 Setup

For Windows Subsystem for Linux users:

1. **Install X Server on Windows** (choose one):
   - [VcXsrv](https://sourceforge.net/projects/vcxsrv/) (free, recommended)
   - [X410](https://x410.dev/) (paid, from Microsoft Store)
   - [Xming](https://sourceforge.net/projects/xming/) (free)

2. **Configure X Server**:
   - Launch with "Multiple windows" mode
   - Disable access control
   - Allow connections from WSL2

3. **Set DISPLAY in WSL2**:
   ```bash
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
   ```

4. **Add to ~/.bashrc** for persistence:
   ```bash
   echo 'export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0' >> ~/.bashrc
   ```

### Virtual Display (Headless)

For CI/CD or headless environments, use Xvfb:
```bash
# Install Xvfb
sudo apt-get install xvfb

# Start virtual display
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```

Or use the built-in MCP tools:
- `install_xserver` - Install required packages
- `start_xserver` - Start virtual display
- `xserver_status` - Check status

## Configuration

### For Claude Code

#### Using claude mcp add (Recommended)

```bash
# Clone the repository first
git clone https://github.com/Sundeepg98/computer-use-mcp.git
cd computer-use-mcp

# Add to Claude Code using official command
claude mcp add -s user computer-use -- python3 $(pwd)/start_mcp_server.py
```

#### Manual Configuration (Alternative)

If you prefer manual configuration, add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "computer-use": {
      "type": "stdio",
      "command": "python3",
      "args": ["/path/to/computer-use-mcp/start_mcp_server.py"],
      "env": {}
    }
  }
}
```

**Note**: Replace `/path/to/computer-use-mcp/` with the actual path where you cloned the repository.

#### Verify Installation

After adding the MCP server, verify it's working:

```bash
# Check MCP server status
claude mcp list

# You should see:
# computer-use: python3 /path/to/start_mcp_server.py - ✓ Connected

# Get detailed server info
claude mcp get computer-use
```

### For Standalone Usage

```python
from computer_use_mcp import ComputerUseServer

server = ComputerUseServer()
server.run()
```

## Available Tools

### 📸 Screenshot
Capture and analyze the current screen with visual analysis.

```json
{
  "tool": "screenshot",
  "arguments": {
    "analyze": "Find the submit button"
  }
}
```

### 🖱️ Click
Click at specific coordinates or on described elements.

```json
{
  "tool": "click",
  "arguments": {
    "x": 500,
    "y": 300,
    "button": "left"
  }
}
```

### ⌨️ Type
Type text with automatic safety validation.

```json
{
  "tool": "type",
  "arguments": {
    "text": "Hello, World!"
  }
}
```

### 🔤 Key Press
Press keyboard keys or combinations.

```json
{
  "tool": "key",
  "arguments": {
    "key": "Enter"
  }
}
```

### 📜 Scroll
Scroll in any direction.

```json
{
  "tool": "scroll",
  "arguments": {
    "direction": "down",
    "amount": 5
  }
}
```

### ✋ Drag
Click and drag between two points.

```json
{
  "tool": "drag",
  "arguments": {
    "start_x": 100,
    "start_y": 100,
    "end_x": 300,
    "end_y": 300
  }
}
```

### ⏱️ Wait
Wait for a specified duration.

```json
{
  "tool": "wait",
  "arguments": {
    "seconds": 2.5
  }
}
```

### 🤖 Automate
Automate complex tasks with intelligent planning.

```json
{
  "tool": "automate",
  "arguments": {
    "task": "Fill out the login form and submit"
  }
}
```

### 🖥️ Install X Server

Install required X server packages for display support.

```json
{
  "tool": "install_xserver",
  "arguments": {}
}
```

### 🚀 Start X Server

Start a virtual X server with custom resolution.

```json
{
  "tool": "start_xserver",
  "arguments": {
    "display_num": 99,
    "width": 1920,
    "height": 1080
  }
}
```

### 🛑 Stop X Server

Stop a running X server by display name.

```json
{
  "tool": "stop_xserver",
  "arguments": {
    "display": ":99"
  }
}
```

### 🔗 Setup WSL X Forwarding

Configure X11 forwarding for WSL2 to Windows host.

```json
{
  "tool": "setup_wsl_xforwarding",
  "arguments": {}
}
```

### 📊 X Server Status

Get status of X servers and display configuration.

```json
{
  "tool": "xserver_status",
  "arguments": {}
}
```

### 🧪 Test Display

Test the current display configuration.

```json
{
  "tool": "test_display",
  "arguments": {}
}
```

## Safety

The server includes comprehensive safety checks:

- **Command Blocking**: Prevents dangerous system commands (rm -rf, format, etc.)
- **Credential Protection**: Detects and masks passwords, API keys, and tokens
- **PII Detection**: Identifies and protects SSNs, credit cards, emails
- **Path Traversal Prevention**: Blocks access to sensitive system directories
- **URL Validation**: Prevents malicious URL schemes (javascript:, file://, etc.)

## Usage

### For Claude Code

Add to your `.mcp.json` as shown in Configuration section.

### Python API

```python
# Using the launcher script
import subprocess
subprocess.run(['python3', 'start_mcp_server.py'])

# Or directly with the MCP module
import sys
sys.path.append('src')
from mcp.mcp_server import main
main()
```

### CLI Usage

```bash
# Run the MCP server directly
python3 start_mcp_server.py

# Or test tools via JSON-RPC (for debugging)
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | python3 start_mcp_server.py
```

## Testing

Run the comprehensive test suite:

```bash
# All tests
python3 -m pytest tests/

# Specific test categories
python3 -m pytest tests/test_safety.py
python3 -m pytest tests/test_visual.py
python3 -m pytest tests/test_mcp_protocol.py

# With coverage
python3 -m pytest --cov=src tests/
```

## 📊 Architecture

```
computer-use-mcp/
├── src/mcp/                   # Clean MCP implementation
│   ├── mcp_server.py          # Main MCP server
│   ├── computer_use_refactored.py  # Core with dependency injection
│   ├── factory_refactored.py  # Factory pattern for DI
│   ├── safety_checks.py       # Safety validation
│   ├── visual_analyzer.py     # Visual analysis
│   ├── abstractions/          # Protocol definitions
│   ├── implementations/       # Platform implementations
│   ├── screenshot/            # Screenshot providers
│   └── input/                 # Input providers
├── start_mcp_server.py        # Server launcher
├── tests/                     # Comprehensive test suite
│   ├── test_mcp_protocol.py   # MCP protocol tests
│   ├── test_safety_security.py # Security tests
│   └── test_refactored_example.py # DI pattern tests
├── examples/
│   ├── basic_usage.py         # Simple examples
│   └── advanced_automation.py # Complex workflows
└── docs/
    ├── API.md                 # API documentation
    └── REFACTORING_GUIDE.md   # Architecture details
```

## 🔐 Security Considerations

- **Never run with elevated privileges** unless absolutely necessary
- **Review automation scripts** before execution
- **Use environment variables** for sensitive data
- **Enable additional safety checks** for production use
- **Monitor logs** for suspicious activity

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com) for the MCP protocol
- The open source community for invaluable contributions

## 🐛 Known Issues

- Screenshot may require X server configuration on Linux
- WSL2 requires additional display setup
- Some keyboard shortcuts may not work in all applications

## 📮 Support

- **Issues**: [GitHub Issues](https://github.com/sundeepg98/computer-use-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sundeepg98/computer-use-mcp/discussions)
- **Email**: sundeepg8@gmail.com

---

**Built with Clean Architecture - Production Ready with Dependency Injection**
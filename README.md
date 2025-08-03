# Computer Use MCP

[![MCP Protocol](https://img.shields.io/badge/MCP-2024--11--05-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A powerful MCP (Model Context Protocol) server that provides computer use tools for Claude and other MCP-compatible clients. Control your computer programmatically with comprehensive safety checks and visual analysis.

## Features

- **8 Computer Control Tools**: Screenshot, click, type, key press, scroll, drag, wait, and automate
- **Visual Analysis**: Deep analysis of screen content and intelligent action planning
- **Safety Checks**: Comprehensive protection against dangerous commands and sensitive data exposure
- **Cross-Platform Support**: Works on Linux, macOS, and Windows (with WSL2)
- **MCP Native**: Seamless integration with Claude and other MCP-compatible clients

## Installation

### Via npm (recommended)
```bash
npm install -g computer-use-mcp
```

### Via pip
```bash
pip install computer-use-mcp
```

### Via Docker
```bash
docker pull computer-use-mcp
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  computer-use-mcp
```

### From Source
```bash
git clone https://github.com/sundeepg98/computer-use-mcp.git
cd computer-use-mcp
pip install -r requirements.txt
python3 src/mcp_server.py
```

## Configuration

### For Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "computer-use": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "computer-use-mcp"],
      "env": {}
    }
  }
}
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
from computer_use_mcp import ComputerUseServer
server = ComputerUseServer()
server.run()
```

### CLI Usage

```bash
computer-use-mcp --help
computer-use-mcp --list-tools
computer-use-mcp --tool screenshot --analyze "Find buttons"
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
├── src/
│   ├── mcp_server.py          # Main MCP server
│   ├── computer_use_core.py   # Core computer control
│   ├── safety_checks.py       # Safety validation
│   ├── visual_analyzer.py     # Visual analysis
│   └── config.py              # Configuration
├── tests/
│   ├── test_safety.py         # Safety tests
│   ├── test_visual.py         # Visual analysis tests
│   └── test_mcp_protocol.py   # Protocol tests
├── docker/
│   └── Dockerfile             # Container definition
├── examples/
│   ├── basic_usage.py         # Simple examples
│   └── advanced_automation.py # Complex workflows
└── docs/
    ├── API.md                 # API documentation
    └── SECURITY.md           # Security details
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

**Built with Test-Driven Development - 100% Test Coverage**
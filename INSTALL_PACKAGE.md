# Installing computer-use-mcp as a Package

This guide explains how to install and use computer-use-mcp as a package instead of running directly from the repository.

## Installation Steps

### 1. Build the Package
```bash
cd /path/to/computer-use-mcp
python -m build
```

### 2. Install the Package

#### Option A: Install in Virtual Environment (Recommended)
```bash
# Create/activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package
pip install dist/computer_use_mcp-*.whl
```

#### Option B: Install with pipx (for global CLI usage)
```bash
pipx install dist/computer_use_mcp-*.whl
```

### 3. Update MCP Configuration

Update your `~/.claude.json` to use the installed package:

```json
{
  "mcpServers": {
    "computer-use": {
      "type": "stdio",
      "command": "/path/to/venv/bin/computer-use-mcp",
      "env": {
        "MCP_LOG_FILE": "/tmp/computer_use_mcp.log",
        "MCP_DEBUG": "1"
      }
    }
  }
}
```

Replace `/path/to/venv` with:
- Virtual environment: `/home/sunkar/computer-use-mcp/.venv`
- pipx installation: `~/.local/pipx/venvs/computer-use-mcp`

## Testing the Installation

Test the MCP server is working:
```bash
echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"capabilities": {}}, "id": 1}' | computer-use-mcp
```

Expected response:
```json
{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", ...}}
```

## Advantages of Package Installation

1. **Clean separation**: Code and configuration are separate
2. **Version management**: Easy to upgrade/downgrade versions
3. **Distribution**: Can be shared via PyPI or wheel files
4. **Dependencies**: Automatically manages dependencies
5. **Entry points**: Provides clean CLI commands

## Reverting to Repository Mode

To revert back to using the repository directly:
```bash
cp ~/.claude.json.bak ~/.claude.json
```

Or manually update the configuration to:
```json
{
  "mcpServers": {
    "computer-use": {
      "type": "stdio",
      "command": "python3",
      "args": ["/home/sunkar/computer-use-mcp/run_mcp.py"]
    }
  }
}
```
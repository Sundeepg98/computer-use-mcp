# Computer Use MCP - API Documentation

## Table of Contents
- [MCP Protocol](#mcp-protocol)
- [Available Tools](#available-tools)
- [Python API](#python-api)
- [Safety API](#safety-api)
- [Ultrathink API](#ultrathink-api)

## MCP Protocol

### Initialize
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {}
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    }
  }
}
```

### List Tools
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "screenshot",
        "description": "Capture and analyze screenshot",
        "inputSchema": {...}
      },
      ...
    ]
  }
}
```

## Available Tools

### Screenshot
Capture and analyze the current screen.

**Parameters:**
- `analyze` (string, optional): Analysis prompt for ultrathink

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "screenshot",
    "arguments": {
      "analyze": "Find all buttons on the screen"
    }
  }
}
```

### Click
Click at specific coordinates or on an element.

**Parameters:**
- `x` (integer, optional): X coordinate
- `y` (integer, optional): Y coordinate
- `element` (string, optional): Element description
- `button` (string, optional): "left", "right", or "middle"

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "click",
    "arguments": {
      "x": 500,
      "y": 300,
      "button": "left"
    }
  }
}
```

### Type
Type text with keyboard.

**Parameters:**
- `text` (string, required): Text to type

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "type",
    "arguments": {
      "text": "Hello, World!"
    }
  }
}
```

### Key
Press a key or key combination.

**Parameters:**
- `key` (string, required): Key to press (e.g., "Enter", "Ctrl+S")

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "key",
    "arguments": {
      "key": "Enter"
    }
  }
}
```

### Scroll
Scroll in a direction.

**Parameters:**
- `direction` (string, optional): "up" or "down" (default: "down")
- `amount` (integer, optional): Scroll amount (default: 3)

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "scroll",
    "arguments": {
      "direction": "down",
      "amount": 5
    }
  }
}
```

### Drag
Click and drag from one point to another.

**Parameters:**
- `start_x` (integer, required): Starting X coordinate
- `start_y` (integer, required): Starting Y coordinate
- `end_x` (integer, required): Ending X coordinate
- `end_y` (integer, required): Ending Y coordinate

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "drag",
    "arguments": {
      "start_x": 100,
      "start_y": 100,
      "end_x": 300,
      "end_y": 300
    }
  }
}
```

### Wait
Wait for specified duration.

**Parameters:**
- `seconds` (number, optional): Seconds to wait (default: 1)

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "wait",
    "arguments": {
      "seconds": 2.5
    }
  }
}
```

### Automate
Automate a complex task with ultrathink planning.

**Parameters:**
- `task` (string, required): Task description

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "automate",
    "arguments": {
      "task": "Fill out the login form and submit"
    }
  }
}
```

## Python API

### ComputerUseServer

```python
from mcp_server import ComputerUseServer

# Create server
server = ComputerUseServer(test_mode=False)

# Handle request
response = server.handle_request(request_dict)

# Run server (stdio mode)
server.run()
```

### ComputerUseCore

```python
from computer_use_core import ComputerUseCore

# Create core instance
core = ComputerUseCore(test_mode=False)

# Screenshot
result = core.screenshot(analyze="Find buttons")

# Click
result = core.click(x=500, y=300, button='left')

# Type text
result = core.type_text("Hello, World!")

# Press key
result = core.key_press("Enter")

# Scroll
result = core.scroll(direction='down', amount=5)

# Drag
result = core.drag(100, 100, 300, 300)

# Automate
result = core.automate("Complete the form")
```

## Safety API

### SafetyChecker

```python
from safety_checks import SafetyChecker

# Create checker
safety = SafetyChecker(
    custom_patterns=["FORBIDDEN"],
    whitelist=["safe_command"]
)

# Check text safety
is_safe = safety.check_text_safety("user input")

# Check command safety
is_safe = safety.check_command_safety("rm -rf /")

# Check URL safety
is_safe = safety.check_url_safety("https://example.com")
```

### Safety Patterns

The safety checker validates against:
- Dangerous system commands
- Credential patterns
- PII (Personally Identifiable Information)
- Path traversal attempts
- SQL injection patterns
- Command injection patterns
- XSS attempts
- Malicious URLs

## Ultrathink API

### UltrathinkVisualAnalyzer

```python
from ultrathink_visual import UltrathinkVisualAnalyzer

# Create analyzer
analyzer = UltrathinkVisualAnalyzer()

# Analyze screen
analysis = analyzer.analyze_screen(
    screenshot_data,
    "Find interactive elements"
)

# Plan task
plan = analyzer.plan_task("Click submit button")

# Plan workflow
workflow = analyzer.plan_workflow(
    "Login, navigate to settings, enable dark mode"
)

# Check similarity
similarity = analyzer.check_similarity(
    screenshot1,
    screenshot2
)

# Extract text (OCR)
text = analyzer.extract_text(screenshot_data)

# Validate action
is_valid = analyzer.validate_action(action_dict)

# Get confidence score
confidence = analyzer.get_confidence_score(action_dict)

# Plan error recovery
recovery = analyzer.plan_error_recovery(error_context)
```

### Analysis Response Format

```python
{
    "elements": [
        {
            "type": "button",
            "text": "Submit",
            "location": {"x": 500, "y": 300},
            "confidence": 0.95
        }
    ],
    "layout": "form",
    "suggestions": ["Click submit button"],
    "warnings": []
}
```

### Task Planning Format

```python
{
    "steps": [
        {
            "action": "screenshot",
            "purpose": "Identify form fields"
        },
        {
            "action": "click",
            "target": "username field"
        },
        {
            "action": "type",
            "text": "user@example.com"
        }
    ],
    "estimated_time": 5.0,
    "confidence": 0.85
}
```

## Error Handling

All API methods return consistent error formats:

### MCP Error Response
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "details": "Specific error information"
    }
  }
}
```

### Python Exception Hierarchy
```python
ComputerUseException
├── SafetyException
│   ├── DangerousCommandException
│   ├── CredentialDetectedException
│   └── PathTraversalException
├── ValidationException
│   ├── InvalidCoordinatesException
│   ├── InvalidTextException
│   └── InvalidToolException
└── ExecutionException
    ├── ScreenshotFailedException
    ├── ClickFailedException
    └── TimeoutException
```

## Configuration

### Environment Variables
```bash
# Display configuration
export DISPLAY=:0

# Python path
export PYTHONPATH=/path/to/computer-use-mcp/src

# Test mode
export COMPUTER_USE_TEST_MODE=true

# Debug logging
export COMPUTER_USE_DEBUG=true
```

### Configuration File
```json
{
  "test_mode": false,
  "safety": {
    "enabled": true,
    "custom_patterns": [],
    "whitelist": []
  },
  "ultrathink": {
    "enabled": true,
    "confidence_threshold": 0.7
  },
  "timeouts": {
    "default": 5000,
    "screenshot": 10000,
    "automation": 30000
  }
}
```

## Rate Limiting

The API implements rate limiting for safety:

- Screenshot: 10 per minute
- Click: 60 per minute
- Type: 30 per minute
- Automation: 5 per minute

## Versioning

The API follows semantic versioning:

- Current version: 1.0.0
- MCP protocol version: 2024-11-05
- Minimum Python version: 3.8

## Support

- GitHub Issues: https://github.com/ultrathink/computer-use-mcp/issues
- Documentation: https://github.com/ultrathink/computer-use-mcp/docs
- Email: support@ultrathink.dev
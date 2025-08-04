"""Mock data for testing"""

# Mock MCP responses
MOCK_INITIALIZE_RESPONSE = {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        }
    }
}

MOCK_TOOLS_LIST = [
    {
        "name": "screenshot",
        "description": "Capture and analyze screenshot",
        "inputSchema": {
            "type": "object",
            "properties": {
                "analyze": {"type": "string"}
            }
        }
    },
    {
        "name": "click",
        "description": "Click at coordinates",
        "inputSchema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "button": {"type": "string", "enum": ["left", "right", "middle"]}
            }
        }
    }
]

# Mock safety test cases
DANGEROUS_INPUTS = [
    "rm -rf /",
    "format c:",
    ":(){ :|:& };:",
    "password123",
    "API_KEY=secret",
    "../../etc/passwd",
    "javascript:alert('xss')",
]

SAFE_INPUTS = [
    "Hello, World!",
    "Click the button",
    "Open settings",
    "Save document",
    "https://example.com",
]

# Mock screenshot data
MOCK_SCREENSHOT_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

# Mock automation tasks
MOCK_AUTOMATION_TASKS = [
    {
        "task": "Click submit button",
        "steps": [
            {"action": "screenshot", "analyze": "Find submit button"},
            {"action": "click", "target": "submit button"}
        ]
    },
    {
        "task": "Fill form",
        "steps": [
            {"action": "click", "target": "name field"},
            {"action": "type", "text": "John Doe"},
            {"action": "key", "key": "Tab"},
            {"action": "type", "text": "john@example.com"}
        ]
    }
]
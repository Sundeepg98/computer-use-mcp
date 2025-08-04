"""Constants for computer-use-mcp package"""

# MCP Protocol
MCP_PROTOCOL_VERSION = "2024-11-05"
JSONRPC_VERSION = "2.0"

# Tool names
TOOL_SCREENSHOT = "screenshot"
TOOL_CLICK = "click"
TOOL_TYPE = "type"
TOOL_KEY = "key"
TOOL_SCROLL = "scroll"
TOOL_DRAG = "drag"
TOOL_WAIT = "wait"
TOOL_AUTOMATE = "automate"

ALL_TOOLS = [
    TOOL_SCREENSHOT,
    TOOL_CLICK,
    TOOL_TYPE,
    TOOL_KEY,
    TOOL_SCROLL,
    TOOL_DRAG,
    TOOL_WAIT,
    TOOL_AUTOMATE,
]

# Safety patterns
DANGEROUS_COMMANDS = [
    r"rm\s+-rf\s+/",
    r"format\s+[cC]:",
    r"del\s+/[fF]",
    r"dd\s+if=/dev/zero",
    r":\(\)\{.*:\|:&\s*\};:",  # Fork bomb
    r"chmod\s+-R\s+777",
    r">\s*/dev/[sh]da",
]

CREDENTIAL_PATTERNS = [
    r"password[=:\s]+\S+",
    r"api[_-]?key[=:\s]+\S+",
    r"token[=:\s]+\S+",
    r"secret[=:\s]+\S+",
    r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
]

# Limits
MAX_TEXT_LENGTH = 10000
MAX_COORDINATE_VALUE = 10000
MAX_WAIT_SECONDS = 60
MAX_SCROLL_AMOUNT = 100

# Timeouts (milliseconds)
DEFAULT_TIMEOUT = 5000
SCREENSHOT_TIMEOUT = 10000
AUTOMATION_TIMEOUT = 30000

# Display settings
DEFAULT_DISPLAY_WIDTH = 1920
DEFAULT_DISPLAY_HEIGHT = 1080
DEFAULT_DISPLAY_DEPTH = 24

# File paths
TEMP_SCREENSHOT_PATH = "/tmp/screenshot.png"
STATE_FILE_PATH = "/tmp/computer-use-mcp-state.json"
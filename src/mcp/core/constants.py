"""Constants for computer-use-mcp package"""

from pathlib import Path
import os
import tempfile


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
SECURE_TEMP_DIR = Path.home() / ".config" / "computer-use-mcp" / "temp"
TEMP_SCREENSHOT_PATH = str(SECURE_TEMP_DIR / "screenshot.png")
STATE_FILE_PATH = str(Path.home() / ".config" / "computer-use-mcp" / f"mcp_state_{os.getuid()}.json")

# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds
MIN_RETRY_DELAY = 0.1
MAX_RETRY_DELAY = 60.0
RETRY_EXPONENTIAL_BASE = 2.0
RETRY_JITTER_FACTOR = 0.1

# Authentication
AUTH_TOKEN_EXPIRY = 3600  # 1 hour in seconds

# Self-healing & monitoring
HEALTH_CHECK_INTERVAL_HEALTHY = 10.0  # seconds
HEALTH_CHECK_INTERVAL_UNHEALTHY = 2.0  # seconds
HEALTH_HISTORY_SIZE = 100
CONTEXT_HISTORY_SIZE = 50

# Performance thresholds
SLOW_RESPONSE_THRESHOLD = 1.0  # seconds
SUCCESS_RATE_HIGH = 0.8
SUCCESS_RATE_LOW = 0.5
HISTORICAL_RETRY_SUCCESS_THRESHOLD = 0.3

# Error recovery
MAX_RECOVERY_ATTEMPTS = 3
MAX_CONSECUTIVE_ERRORS = 5

# Security
SECURE_FILE_PERMISSIONS = 0o600
SECURE_DIR_PERMISSIONS = 0o700
MAX_JSON_SIZE = 10 * 1024 * 1024  # 10MB

# Timing delays (seconds)
CLICK_DELAY = 0.01
KEY_PRESS_DELAY = 0.05
XSERVER_START_DELAY = 2.0
VCXSRV_STARTUP_DELAY = 3.0

# Subprocess timeouts (seconds)
SUBPROCESS_TIMEOUT_SHORT = 2.0
SUBPROCESS_TIMEOUT_NORMAL = 5.0
SUBPROCESS_TIMEOUT_LONG = 10.0
SUBPROCESS_TIMEOUT_MEDIUM_LONG = 30.0
SUBPROCESS_TIMEOUT_VERY_LONG = 120.0
SUBPROCESS_TIMEOUT_EXTREME = 300.0

# Additional timeout constants
SUBPROCESS_TIMEOUT_QUICK = 3.0  # For quick operations like version checks
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 30.0  # For circuit breaker recovery

# Wait delays (seconds) - consolidating with existing delays
WAIT_DELAY_MINIMAL = 0.01  # Minimal delay for UI operations
WAIT_DELAY_SHORT = 0.05  # Short delay for input operations
WAIT_DELAY_QUICK = 0.1  # Quick delay between checks
WAIT_DELAY_MEDIUM = 0.2  # Medium delay for retries
WAIT_DELAY_NORMAL = 0.5  # Normal delay between operations
WAIT_DELAY_STANDARD = 1.0  # Standard wait between operations
WAIT_DELAY_LONG = 2.0  # Longer wait for initialization

# Code constants
JSONRPC_INTERNAL_ERROR_CODE = -32603

# JSON RPC version
JSONRPC_VERSION = "2.0"

# Self-healing settings
HEAL_COOLDOWN = 5.0  # seconds
MONITORING_LOOP_ERROR_SLEEP = 5.0  # seconds
THREAD_JOIN_TIMEOUT = 5.0  # seconds
INPUT_RESET_DELAY = 0.5  # seconds
CONNECTION_RESET_DELAY = 1.0  # seconds
OPERATION_DELAY = 0.5  # seconds
OPERATION_COOLDOWN = 0.2  # seconds
SCREENSHOT_SLOW_THRESHOLD = 2.0  # seconds
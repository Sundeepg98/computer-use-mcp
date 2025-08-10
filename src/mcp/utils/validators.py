"""Validation utilities for computer-use-mcp"""

from typing import Any, Dict, Optional, Tuple
import re

from ..core.constants import JSONRPC_VERSION
from ..core.constants import (
    ALL_TOOLS,
    MAX_COORDINATE_VALUE,
    MAX_TEXT_LENGTH,
    MAX_WAIT_SECONDS,
    MAX_SCROLL_AMOUNT,
)


def validate_coordinates(x: Any, y: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate screen coordinates

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        x_val = int(x)
        y_val = int(y)

        if x_val < 0 or y_val < 0:
            return False, "Coordinates must be non-negative"

        if x_val > MAX_COORDINATE_VALUE or y_val > MAX_COORDINATE_VALUE:
            return False, f"Coordinates exceed maximum value ({MAX_COORDINATE_VALUE})"

        return True, None

    except (TypeError, ValueError):
        return False, "Coordinates must be integers"


def validate_text_input(text: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate text input for typing

    Args:
        text: Text to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if text is None:
        return False, "Text cannot be None"

    if not isinstance(text, str):
        return False, "Text must be a string"

    if len(text) > MAX_TEXT_LENGTH:
        return False, f"Text exceeds maximum length ({MAX_TEXT_LENGTH})"

    # Check for control characters (except common ones like newline, tab)
    if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', text):
        return False, "Text contains invalid control characters"

    return True, None


def validate_tool_name(tool_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate tool name

    Args:
        tool_name: Name of the tool

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not tool_name:
        return False, "Tool name cannot be empty"

    if tool_name not in ALL_TOOLS:
        return False, f"Unknown tool: {tool_name}. Valid tools: {', '.join(ALL_TOOLS)}"

    return True, None


def validate_mcp_request(request: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate MCP protocol request

    Args:
        request: MCP request dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if 'jsonrpc' not in request:
        return False, "Missing 'jsonrpc' field"

    if request['jsonrpc'] != JSONRPC_VERSION:
        return False, f"Invalid JSON-RPC version: {request['jsonrpc']}"

    if 'method' not in request:
        return False, "Missing 'method' field"

    # Check id field (required for requests, not for notifications)
    if 'id' in request:
        if not isinstance(request['id'], (str, int, type(None))):
            return False, "Invalid 'id' type"

    return True, None


def validate_scroll_params(direction: str, amount: int) -> Tuple[bool, Optional[str]]:
    """
    Validate scroll parameters

    Args:
        direction: Scroll direction (up/down)
        amount: Scroll amount

    Returns:
        Tuple of (is_valid, error_message)
    """
    if direction not in ['up', 'down']:
        return False, "Direction must be 'up' or 'down'"

    try:
        amount_val = int(amount)
        if amount_val < 1 or amount_val > MAX_SCROLL_AMOUNT:
            return False, f"Scroll amount must be between 1 and {MAX_SCROLL_AMOUNT}"
        return True, None
    except (TypeError, ValueError):
        return False, "Scroll amount must be an integer"


def validate_wait_duration(seconds: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate wait duration

    Args:
        seconds: Duration in seconds

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        duration = float(seconds)
        if duration <= 0:
            return False, "Wait duration must be positive"
        if duration > MAX_WAIT_SECONDS:
            return False, f"Wait duration exceeds maximum ({MAX_WAIT_SECONDS} seconds)"
        return True, None
    except (TypeError, ValueError):
        return False, "Wait duration must be a number"


def validate_button_type(button: str) -> Tuple[bool, Optional[str]]:
    """
    Validate mouse button type

    Args:
        button: Button type (left/right/middle)

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_buttons = ['left', 'right', 'middle']
    if button not in valid_buttons:
        return False, f"Invalid button: {button}. Must be one of: {', '.join(valid_buttons)}"
    return True, None
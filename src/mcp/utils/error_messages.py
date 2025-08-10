"""
Centralized error messages for consistency across the MCP codebase.

This module defines all error messages as constants to prevent duplication
and ensure consistency in error reporting.
"""


# Display-related errors
ERROR_NO_DISPLAY = "No display available"
ERROR_DISPLAY_NOT_AVAILABLE = "Display not available"
ERROR_COULD_NOT_ESTABLISH_DISPLAY = "Could not establish display"
ERROR_X_SERVER_NOT_RESPONSIVE = "X server not responsive"
ERROR_NO_X_SERVER_AVAILABLE = "No X server available"
ERROR_FAILED_TO_START_X_SERVER = "Failed to start X server"

# Input validation errors
ERROR_COORDINATES_MUST_BE_INTEGERS = "Coordinates must be integers"
ERROR_ALL_COORDINATES_MUST_BE_INTEGERS = "All coordinates must be integers"
ERROR_INVALID_DIRECTION = "Invalid direction: {direction}"
ERROR_INVALID_KEY = "Invalid key: {key}"

# Platform-specific errors
ERROR_NOT_WSL = "Not running in WSL environment"
ERROR_NOT_IN_WSL_MODE = "Not in WSL mode"
ERROR_WINDOWS_X_SERVER_NOT_ACCESSIBLE = "Windows X server not accessible"
ERROR_COULD_NOT_DETERMINE_HOST_IP = "Could not determine Windows host IP"

# VcXsrv-specific errors
ERROR_VCXSRV_NOT_INSTALLED = "VcXsrv is not installed"
ERROR_VCXSRV_NOT_INSTALLED_FULL = "VcXsrv not installed"
ERROR_VCXSRV_STARTED_BUT_NO_DISPLAY = "VcXsrv started but display not available"

# Operation errors
ERROR_OPERATION_VALIDATION_FAILED = "Operation validation failed"
ERROR_FAILED_TO_PREPARE_OPERATION = "Failed to prepare for operation"
ERROR_ELEMENT_NOT_FOUND = "Element not found"
ERROR_FAILED_TO_GET_ACTIVE_WINDOW = "Failed to get active window"

# Service errors
ERROR_SERVICE_TEMPORARILY_UNAVAILABLE = "Service temporarily unavailable"

# Safety errors
ERROR_SAFETY_CHECK_FAILED = "Safety check failed: {error}"
ERROR_PERMISSION_DENIED = "Permission denied: {action}"
ERROR_BLOCKED_ACTION = "Blocked action: {action}"

# Generic errors
ERROR_UNKNOWN = "Unknown error"
ERROR_TIMEOUT = "Operation timed out"
ERROR_NOT_IMPLEMENTED = "Not implemented"

# Format helper functions
def format_error(template: str, **kwargs) -> str:
    """Format an error message with parameters."""
    return template.format(**kwargs)

def get_coordinate_error(coord_type: str = "all") -> str:
    """Get appropriate coordinate error message."""
    if coord_type == "all":
        return ERROR_ALL_COORDINATES_MUST_BE_INTEGERS
    return ERROR_COORDINATES_MUST_BE_INTEGERS

def get_platform_error(platform: str) -> str:
    """Get platform-specific error message."""
    platform_errors = {
        'wsl': ERROR_NOT_WSL,
        'windows_x': ERROR_WINDOWS_X_SERVER_NOT_ACCESSIBLE,
        'host_ip': ERROR_COULD_NOT_DETERMINE_HOST_IP,
    }
    return platform_errors.get(platform, ERROR_UNKNOWN)
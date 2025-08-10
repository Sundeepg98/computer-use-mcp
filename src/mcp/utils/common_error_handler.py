"""Common error handling utilities"""
    """Standard error handling for MCP tools"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def handle_tool_error(error: Exception, tool_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    logger.error(f"{tool_name} error: {error}", exc_info=True)

    response = {
        "error": f"Failed to execute {tool_name}: {str(error)}",
        "tool": tool_name
    }

    if params:
        response["attempted_params"] = params

    return response

def safe_execute(func, *args, **kwargs) -> Tuple[bool, Any]:
    """Safely execute a function with error handling"""
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
        return False, str(e)

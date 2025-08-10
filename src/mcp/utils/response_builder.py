"""Common response builders for MCP protocol"""
    """Build standard success response"""

from typing import Dict, Any, Optional

def build_success_response(result: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    response = {"status": "success", "result": result}
    if metadata:
        response.update(metadata)
    return response

def build_error_response(error: str, code: int = -1, data: Optional[Any] = None) -> Dict[str, Any]:
    """Build standard error response"""
    response = {
        "status": "error",
        "error": {
            "code": code,
            "message": error
        }
    }
    if data is not None:
        response["error"]["data"] = data
    return response

"""
ProtocolHandler - Handles MCP JSON-RPC protocol communication

Extracted from mcp_server.py to follow Single Responsibility Principle.
Manages request/response formatting and protocol compliance.
"""

from typing import Dict, Any, Optional, Tuple, List
import base64
import logging


logger = logging.getLogger(__name__)


class ProtocolHandler:
    """Handles MCP JSON-RPC 2.0 protocol"""

    # Standard JSON-RPC error codes
    ERROR_PARSE = -32700
    ERROR_INVALID_REQUEST = -32600
    ERROR_METHOD_NOT_FOUND = -32601
    ERROR_INVALID_PARAMS = -32602
    ERROR_INTERNAL = -32603

    def __init__(self) -> None:
        """Initialize protocol handler"""
        self.protocol_version = "2024-11-05"

    def validate_request(self, request: Dict[str, Any]) -> None:
        """
        Validate JSON-RPC request structure

        Args:
            request: The request to validate

        Raises:
            ValueError: If request is invalid
        """
        if 'jsonrpc' not in request:
            raise ValueError("Missing jsonrpc field")

        if request['jsonrpc'] != '2.0':
            raise ValueError(f"Invalid jsonrpc version: {request['jsonrpc']}")

        if 'method' not in request:
            raise ValueError("Missing method field")

    def is_notification(self, request: Dict[str, Any]) -> bool:
        """
        Check if request is a notification (no id field)

        Args:
            request: The request to check

        Returns:
            True if notification, False otherwise
        """
        return 'id' not in request

    def parse_method(self, request: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """
        Parse method into namespace and action

        Args:
            request: The request containing method

        Returns:
            Tuple of (namespace, action) or (method, None)
        """
        method = request.get('method', '')

        if '/' in method:
            parts = method.split('/', 1)
            return parts[0], parts[1]

        return method, None

    def create_success_response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        """
        Create a JSON-RPC success response

        Args:
            request_id: The request ID
            result: The result data

        Returns:
            Formatted success response
        """
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': result
        }

    def create_error_response(
        self,
        request_id: Any,
        code: int,
        message: str,
        data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Create a JSON-RPC error response

        Args:
            request_id: The request ID
            code: Error code
            message: Error message
            data: Optional error data

        Returns:
            Formatted error response
        """
        response = {
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': code,
                'message': message
            }
        }

        if data is not None:
            response['error']['data'] = data

        return response

    def format_tool_response(self, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format tool execution result for MCP protocol

        Args:
            tool_result: Raw tool execution result

        Returns:
            Formatted response with content array
        """
        content = []

        # Add text content for status
        if tool_result.get('success'):
            status_text = "Operation completed successfully"
        else:
            status_text = f"Operation failed: {tool_result.get('error', 'Unknown error')}"

        content.append({
            'type': 'text',
            'text': status_text
        })

        # Add binary data if present (e.g., screenshots)
        if 'data' in tool_result and isinstance(tool_result['data'], bytes):
            content.append({
                'type': 'image',
                'data': base64.b64encode(tool_result['data']).decode('utf-8')
            })

        # Add metadata as text if present
        if 'metadata' in tool_result:
            content.append({
                'type': 'text',
                'text': f"Metadata: {tool_result['metadata']}"
            })

        # Include additional fields from tool result
        for key, value in tool_result.items():
            if key not in ['success', 'error', 'data', 'metadata']:
                content.append({
                    'type': 'text',
                    'text': f"{key}: {value}"
                })

        return {'content': content}

    def create_method_not_found_error(self, request_id: Any, method: str) -> Dict[str, Any]:
        """Create standard method not found error"""
        return self.create_error_response(
            request_id,
            self.ERROR_METHOD_NOT_FOUND,
            "Method not found",
            {'method': method}
        )

    def create_invalid_params_error(
        self,
        request_id: Any,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create standard invalid parameters error"""
        return self.create_error_response(
            request_id,
            self.ERROR_INVALID_PARAMS,
            message,
            details
        )

    def create_internal_error(
        self,
        request_id: Any,
        message: str = "Internal error",
        exception: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """Create standard internal error"""
        data = {'message': message}
        if exception:
            data['exception'] = str(exception)
            data['type'] = type(exception).__name__

        return self.create_error_response(
            request_id,
            self.ERROR_INTERNAL,
            message,
            data
        )
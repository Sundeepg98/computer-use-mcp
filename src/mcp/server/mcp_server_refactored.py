"""
ComputerUseServer - Refactored MCP Server

This is a refactored version of mcp_server.py that delegates responsibilities
to specialized components, following the Single Responsibility Principle.
"""

from typing import Dict, Any, Optional, List
import asyncio
import json
import logging
import sys

from .computer_use import ComputerUse
from .factory import create_computer_use
from .protocol_handler import ProtocolHandler
from .safety_checks import SafetyChecker
from .tool_manager import ToolManager
from .validation_handler import ValidationHandler



logger = logging.getLogger(__name__)


class ComputerUseServer:
    """MCP Server providing computer use tools - Refactored version"""


    def __init__(self, computer_use: Optional[ComputerUse] = None) -> None:
        """
        Initialize MCP server with specialized components

        Args:
            computer_use: Optional ComputerUse instance. If not provided,
                         creates a default instance for the current platform.
        """
        # Initialize computer instance
        if computer_use:
            self.computer = computer_use
        else:
            self.computer = create_computer_use()

        # Initialize components
        self.tool_manager = ToolManager(self.computer)
        self.protocol_handler = ProtocolHandler()
        self.validation_handler = ValidationHandler()
        self.safety_checker = SafetyChecker()

        # Keep alias for backward compatibility
        self.safety = self.safety_checker

    async def run(self) -> None:
        """Run the MCP server"""
        logger.info("Starting Computer Use MCP Server (Refactored)")

        # Send initialization
        await self._send_initialize()

        # Main loop
        async for line in self._read_input():
            try:
                if not line.strip():
                    continue

                request = json.loads(line)
                response = self.handle_request(request)

                if response:  # Don't send response for notifications
                    await self._send_response(response)

            except json.JSONDecodeError as e:
                error_response = self.protocol_handler.create_error_response(
                    None,
                    ProtocolHandler.ERROR_PARSE,
                    f"Parse error: {e}"
                )
                await self._send_response(error_response)
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle incoming JSON-RPC request

        Args:
            request: The JSON-RPC request

        Returns:
            Response dict or None for notifications
        """
        try:
            # Validate request structure
            self.protocol_handler.validate_request(request)

            # Don't respond to notifications
            if self.protocol_handler.is_notification(request):
                logger.info(f"Received notification: {request.get('method')}")
                return None

            # Parse method
            namespace, action = self.protocol_handler.parse_method(request)
            request_id = request.get('id')
            params = request.get('params', {})

            # Route to appropriate handler
            if namespace == 'initialize':
                return self._handle_initialize(request_id, params)

            elif namespace == 'tools':
                if action == 'list':
                    return self._handle_list_tools(request_id)
                elif action == 'call':
                    return self._handle_tool_call(request_id, params)
                else:
                    return self.protocol_handler.create_method_not_found_error(
                        request_id, f"tools/{action}"
                    )

            elif namespace == 'resources':
                if action == 'list':
                    return self._handle_list_resources(request_id)
                elif action == 'read':
                    return self._handle_read_resource(request_id, params)
                else:
                    return self.protocol_handler.create_method_not_found_error(
                        request_id, f"resources/{action}"
                    )

            else:
                return self.protocol_handler.create_method_not_found_error(
                    request_id, request.get('method')
                )

        except ValueError as e:
            # Request validation error
            return self.protocol_handler.create_error_response(
                request.get('id'),
                ProtocolHandler.ERROR_INVALID_REQUEST,
                str(e)
            )
        except Exception as e:
            # Internal error
            logger.error(f"Error handling request: {e}", exc_info=True)
            return self.protocol_handler.create_internal_error(
                request.get('id'),
                "Internal server error",
                e
            )

    def _handle_initialize(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        logger.info("Handling initialize request")

        result = {
            "protocolVersion": self.protocol_handler.protocol_version,
            "capabilities": {
                "tools": {},
                "resources": {
                    "list": True,
                    "read": True
                }
            },
            "serverInfo": {
                "name": "computer-use-mcp",
                "version": "1.0.0"
            }
        }

        return self.protocol_handler.create_success_response(request_id, result)

    def _handle_list_tools(self, request_id: Any) -> Dict[str, Any]:
        """Handle tools/list request"""
        logger.info("Listing available tools")

        tools = self.tool_manager.define_tools()
        result = {"tools": tools}

        return self.protocol_handler.create_success_response(request_id, result)

    def _handle_tool_call(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})

        logger.info(f"Calling tool: {tool_name}")

        try:
            # Validate tool exists
            if not self.tool_manager.get_tool(tool_name):
                return self.protocol_handler.create_invalid_params_error(
                    request_id,
                    f"Unknown tool: {tool_name}",
                    {'tool': tool_name}
                )

            # Validate parameters
            is_valid, error = self.validation_handler.validate_tool_params(tool_name, arguments)
            if not is_valid:
                return self.protocol_handler.create_invalid_params_error(
                    request_id,
                    error,
                    {'tool': tool_name, 'arguments': arguments}
                )

            # Execute tool
            result = self.tool_manager.execute_tool(tool_name, arguments)

            # Format response
            formatted_result = self.protocol_handler.format_tool_response(result)

            return self.protocol_handler.create_success_response(request_id, formatted_result)

        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            return self.protocol_handler.create_internal_error(
                request_id,
                f"Tool execution failed: {str(e)}",
                e
            )

    def _handle_list_resources(self, request_id: Any) -> Dict[str, Any]:
        """Handle resources/list request"""
        resources = [
            {
                "uri": "platform://capabilities",
                "name": "Platform Capabilities",
                "description": "Current platform capabilities and limitations",
                "mimeType": "application/json"
            },
            {
                "uri": "help://troubleshooting",
                "name": "Troubleshooting Guide",
                "description": "Common issues and solutions",
                "mimeType": "text/markdown"
            }
        ]

        result = {"resources": resources}
        return self.protocol_handler.create_success_response(request_id, result)

    def _handle_read_resource(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request"""
        uri = params.get('uri')

        if uri == "platform://capabilities":
            content = [{
                "type": "text",
                "text": json.dumps(self.computer.platform.get_platform(), indent=2)
            }]
        elif uri == "help://troubleshooting":
            content = [{
                "type": "text",
                "text": self._get_troubleshooting_guide()
            }]
        else:
            return self.protocol_handler.create_invalid_params_error(
                request_id,
                f"Unknown resource: {uri}",
                {'uri': uri}
            )

        result = {"content": content}
        return self.protocol_handler.create_success_response(request_id, result)

    def _get_troubleshooting_guide(self) -> str:
        """Get troubleshooting guide content"""
        return """# Computer Use MCP Troubleshooting Guide

## Common Issues and Solutions

### No Display Available
- Ensure X11 server is running (VcXsrv on Windows, XQuartz on macOS)
- Check DISPLAY environment variable
- Try running with sudo if permission issues

### Screenshot Failures
- Verify display permissions
- Check if running in headless environment
- Try different screenshot methods

### Input Not Working
- Ensure you have appropriate permissions
- Check if another application has captured input
- Verify X11 tools are installed (xdotool on Linux)
"""

    async def _send_initialize(self) -> None:
        """Send initialization message"""
        message = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        await self._send_response(message)

    async def _send_response(self, response: Dict[str, Any]) -> None:
        """Send response to stdout"""
        print(json.dumps(response), flush=True)

    async def _read_input(self):
        """Read input from stdin"""
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line = await reader.readline()
            if not line:
                break
            yield line.decode('utf-8')


    def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    server = ComputerUseServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Minimal MCP Server for Computer Use Lite
Handles JSON-RPC protocol for MCP tools
"""

import json
import sys
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .core.factory import create_computer_use
from .core.safety import get_safety_checker

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class MCPServer:
    """Minimal MCP Server for Computer Use"""
    
    def __init__(self):
        """Initialize MCP server"""
        self.protocol_version = "2024-11-05"
        self.computer = create_computer_use()
        self.safety = get_safety_checker()
        
    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming MCP request"""
        request_id = request.get("id", 0)  # Default to 0 if no id
        method = request.get("method")
        params = request.get("params", {})
        
        # Route to appropriate handler
        if method == "initialize":
            return self.initialize(request_id)
        elif method == "tools/list":
            return self.list_tools(request_id)
        elif method == "tools/call":
            return self.call_tool(params, request_id)
        else:
            return self.error_response(request_id, f"Unknown method: {method}")
    
    def initialize(self, request_id: Any) -> Dict[str, Any]:
        """Handle initialization request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": self.protocol_version,
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": "computer-use-mcp-lite",
                    "version": "2.0.0"
                }
            }
        }
    
    def list_tools(self, request_id: Any) -> Dict[str, Any]:
        """List available tools"""
        tools = [
            {
                "name": "screenshot",
                "description": "Capture a screenshot",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "save_path": {
                            "type": "string",
                            "description": "Path to save screenshot"
                        }
                    },
                    "required": ["save_path"]
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
                        "button": {
                            "type": "string",
                            "enum": ["left", "right", "middle"],
                            "default": "left"
                        }
                    },
                    "required": ["x", "y"]
                }
            },
            {
                "name": "type",
                "description": "Type text",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "key",
                "description": "Press a key",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"}
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "scroll",
                "description": "Scroll",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down"]
                        },
                        "amount": {
                            "type": "integer",
                            "default": 3
                        }
                    }
                }
            },
            {
                "name": "drag",
                "description": "Drag from one point to another",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "start_x": {"type": "integer"},
                        "start_y": {"type": "integer"},
                        "end_x": {"type": "integer"},
                        "end_y": {"type": "integer"}
                    },
                    "required": ["start_x", "start_y", "end_x", "end_y"]
                }
            },
            {
                "name": "wait",
                "description": "Wait for seconds",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "seconds": {
                            "type": "number",
                            "default": 1.0
                        }
                    }
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools
            }
        }
    
    def call_tool(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Call a tool"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "screenshot":
                save_path = arguments.get("save_path")
                if not save_path:
                    return self.error_response(request_id, "save_path is required")
                
                result = self.computer.take_screenshot()
                
                if result.get('success') and save_path:
                    # Save screenshot
                    save_path = os.path.expanduser(save_path)
                    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                    
                    screenshot_data = result.get('data', b'')
                    if screenshot_data:
                        with open(save_path, 'wb') as f:
                            f.write(screenshot_data)
                        result['saved_to'] = save_path
                
                return self.success_response(request_id, result)
                
            elif tool_name == "click":
                x = arguments.get("x")
                y = arguments.get("y")
                button = arguments.get("button", "left")
                result = self.computer.click(x, y, button)
                return self.success_response(request_id, result)
                
            elif tool_name == "type":
                text = arguments.get("text", "")
                result = self.computer.type_text(text)
                return self.success_response(request_id, result)
                
            elif tool_name == "key":
                key = arguments.get("key", "")
                result = self.computer.key_press(key)
                return self.success_response(request_id, result)
                
            elif tool_name == "scroll":
                direction = arguments.get("direction", "down")
                amount = arguments.get("amount", 3)
                result = self.computer.scroll(direction, amount)
                return self.success_response(request_id, result)
                
            elif tool_name == "drag":
                result = self.computer.drag(
                    arguments.get("start_x"),
                    arguments.get("start_y"),
                    arguments.get("end_x"),
                    arguments.get("end_y")
                )
                return self.success_response(request_id, result)
                
            elif tool_name == "wait":
                seconds = arguments.get("seconds", 1.0)
                result = self.computer.wait(seconds)
                return self.success_response(request_id, result)
                
            else:
                return self.error_response(request_id, f"Unknown tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return self.error_response(request_id, str(e))
    
    def success_response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        """Create success response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    
    def error_response(self, request_id: Any, message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": message
            }
        }
    
    def run(self):
        """Run the MCP server (stdio mode)"""
        logger.info("Computer Use MCP Lite server started")
        
        while True:
            try:
                # Read line from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                # Parse JSON request
                request = json.loads(line)
                
                # Get request ID - use 0 if not provided
                request_id = request.get("id", 0)
                
                try:
                    # Handle request
                    response = self.handle_request(request)
                    
                    # Send response
                    if response:
                        sys.stdout.write(json.dumps(response) + "\n")
                        sys.stdout.flush()
                        
                except Exception as e:
                    # Send error response for any exception during handling
                    error_response = self.error_response(request_id, str(e))
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()
                    logger.error(f"Error handling request: {e}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                # Send JSON-RPC parse error
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error",
                        "data": str(e)
                    }
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()
            except KeyboardInterrupt:
                logger.info("Server stopped by user")
                break
            except Exception as e:
                logger.error(f"Server error: {e}")


def main():
    """Main entry point"""
    server = MCPServer()
    server.run()


if __name__ == "__main__":
    main()
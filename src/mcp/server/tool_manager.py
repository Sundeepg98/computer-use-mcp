"""
ToolManager - Manages MCP tool definitions and execution

Extracted from mcp_server.py to follow Single Responsibility Principle.
Handles tool registration, validation, and execution.
"""

import time
from typing import Dict, Any, List, Optional, Tuple
import base64
import logging

from ..core.computer_use import ComputerUse


logger = logging.getLogger(__name__)


class ToolManager:
    """Manages MCP tools for computer automation"""


    def __init__(self, computer: ComputerUse) -> None:
        """
        Initialize ToolManager with computer instance

        Args:
            computer: ComputerUse instance for executing actions
        """
        self.computer = computer
        self.tools = self.define_tools()
        self._tools_by_name = {tool['name']: tool for tool in self.tools}

def define_tools(self) -> List[Dict[str, Any]]:
        """Define available MCP tools"""
        return [
            {
                "name": "screenshot",
                "description": "Capture a screenshot and save to file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "method": {
                            "type": "string",
                            "description": "Screenshot method to use",
                            "enum": [
                                "windows_native",
                                "windows_rdp_capture",
                                "wsl2_powershell",
                                "x11",
                                "vcxsrv_x11",
                                "server_core",
                                "macos_screencapture"
                            ],
                            "default": "recommended"
                        },
                        "save_path": {
                            "type": "string",
                            "description": "Optional path to save screenshot file"
                        },
                    }
                }
            },
            {
                "name": "click",
                "description": "Click at coordinates or on element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "integer",
                            "description": "X coordinate"
                        },
                        "y": {
                            "type": "integer",
                            "description": "Y coordinate"
                        },
                        "button": {
                            "type": "string",
                            "enum": ["left", "right", "middle"],
                            "default": "left"
                        },
                        "element": {
                            "type": "string",
                            "description": "Element description (alternative to x,y)"
                        }
                    },
                    "oneOf": [
                        {"required": ["x", "y"]},
                        {"required": ["element"]}
                    ]
                }
            },
            {
                "name": "type",
                "description": "Type text with keyboard",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to type"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "key",
                "description": "Press a key or key combination",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Key to press (e.g., Enter, Tab, Ctrl+C)"
                        }
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "scroll",
                "description": "Scroll in a direction",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down"],
                            "default": "down"
                        },
                        "amount": {
                            "type": "integer",
                            "description": "Number of scroll units",
                            "default": 3
                        }
                    }
                }
            },
            {
                "name": "drag",
                "description": "Click and drag from one point to another",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "start_x": {
                            "type": "integer",
                            "description": "Starting X coordinate"
                        },
                        "start_y": {
                            "type": "integer",
                            "description": "Starting Y coordinate"
                        },
                        "end_x": {
                            "type": "integer",
                            "description": "Ending X coordinate"
                        },
                        "end_y": {
                            "type": "integer",
                            "description": "Ending Y coordinate"
                        }
                    },
                    "required": ["start_x", "start_y", "end_x", "end_y"]
                }
            },
            {
                "name": "wait",
                "description": "Wait for specified seconds",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "seconds": {
                            "type": "number",
                            "description": "Seconds to wait",
                            "default": 1
                        }
                    }
                }
            },
            {
                "name": "get_platform_info",
                "description": "Get comprehensive platform information",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "check_display_available",
                "description": "Check if display/GUI is available for automation",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool definition by name"""
        return self._tools_by_name.get(name)

def list_tool_names(self) -> List[str]:
        """Get list of available tool names"""
        return list(self._tools_by_name.keys())

def validate_parameters(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate parameters for a tool

        Returns:
            Tuple of (is_valid, error_message)
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return False, f"Unknown tool: {tool_name}"

        # Basic type validation for common tools
        if tool_name == 'click':
            if 'x' in params and 'y' in params:
                if not isinstance(params.get('x'), int) or not isinstance(params.get('y'), int):
                    return False, "Coordinates must be integers"

        elif tool_name == 'type':
            if 'text' not in params:
                return False, "Missing required parameter: text"
            if not isinstance(params.get('text'), str):
                return False, "Text must be a string"

        elif tool_name == 'drag':
            required = ['start_x', 'start_y', 'end_x', 'end_y']
            for field in required:
                if field not in params:
                    return False, f"Missing required parameter: {field}"
                if not isinstance(params.get(field), int):
                    return False, f"{field} must be an integer"

        return True, None

def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with given parameters

        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool is unknown or parameters are invalid
        """
        # Validate tool exists
        if tool_name not in self._tools_by_name:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Validate parameters
        is_valid, error = self.validate_parameters(tool_name, params)
        if not is_valid:
            raise ValueError(f"Invalid parameters: {error}")

        # Execute tool
        logger.info(f"Executing tool: {tool_name} with params: {params}")

        try:
            if tool_name == "screenshot":
                result = self.computer.take_screenshot()

            elif tool_name == "click":
                x = params.get('x')
                y = params.get('y')
                button = params.get('button', 'left')
                result = self.computer.click(x, y, button)

            elif tool_name == "type":
                text = params.get('text', '')
                result = self.computer.type_text(text)

            elif tool_name == "key":
                key = params.get('key', '')
                result = self.computer.key_press(key)

            elif tool_name == "scroll":
                direction = params.get('direction', 'down')
                amount = params.get('amount', 3)
                result = self.computer.scroll(direction, amount)

            elif tool_name == "drag":
                result = self.computer.drag(
                    params['start_x'], params['start_y'],
                    params['end_x'], params['end_y']
                )

            elif tool_name == "wait":
                seconds = params.get('seconds', 1)
                time.sleep(seconds)
                result = {'success': True, 'waited': seconds}

            elif tool_name == "get_platform_info":
                result = {
                    'success': True,
                    'platform': self.computer.platform.get_platform()
                }

            elif tool_name == "check_display_available":
                result = {
                    'success': True,
                    'available': self.computer.display.is_display_available()
                }

            else:
                raise ValueError(f"Tool execution not implemented: {tool_name}")

            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
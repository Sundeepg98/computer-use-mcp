#!/usr/bin/env python3
"""
MCP Server for Computer Use
Provides computer use capabilities as native Claude tools via MCP protocol
"""

import json
import sys
import os
import base64
from typing import Dict, Any, List, Optional

from .computer_use_core import ComputerUseCore
from .safety_checks import SafetyChecker
from .visual_analyzer import VisualAnalyzer

# Simple stderr logging for debugging
def log(message):
    """Simple logging to stderr for debugging"""
    print(f"[MCP] {message}", file=sys.stderr)


class ComputerUseServer:
    """MCP Server providing computer use tools"""
    
    def __init__(self, test_mode=False):
        """Initialize MCP server"""
        self.test_mode = test_mode
        self.protocol_version = "2024-11-05"
        self.computer = ComputerUseCore(test_mode=test_mode)
        self.safety_checker = SafetyChecker()
        self.visual = VisualAnalyzer()
        # Keep aliases for backward compatibility
        self.safety = self.safety_checker
        self.ultrathink = self.visual
        self.tools = self._define_tools()
        
    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define available MCP tools"""
        return [
            {
                "name": "screenshot",
                "description": "Capture and analyze screenshot with ultrathink",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "analyze": {
                            "type": "string",
                            "description": "What to analyze in the screenshot"
                        }
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
                        "element": {
                            "type": "string",
                            "description": "Element description (alternative to x,y)"
                        },
                        "button": {
                            "type": "string",
                            "enum": ["left", "right", "middle"],
                            "default": "left"
                        }
                    }
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
                            "default": 3,
                            "description": "Number of scroll units"
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
                            "default": 1.0,
                            "description": "Seconds to wait"
                        }
                    }
                }
            },
            {
                "name": "automate",
                "description": "Automate a complex task with ultrathink planning",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Task to automate"
                        }
                    },
                    "required": ["task"]
                }
            },
            {
                "name": "install_xserver",
                "description": "Install X server packages for display support",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "start_xserver",
                "description": "Start virtual X server with specified configuration",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "display_num": {
                            "type": "integer",
                            "default": 99,
                            "description": "Display number (e.g., 99 for :99)"
                        },
                        "width": {
                            "type": "integer",
                            "default": 1920,
                            "description": "Screen width in pixels"
                        },
                        "height": {
                            "type": "integer",
                            "default": 1080,
                            "description": "Screen height in pixels"
                        }
                    }
                }
            },
            {
                "name": "stop_xserver",
                "description": "Stop X server by display name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "display": {
                            "type": "string",
                            "description": "Display to stop (e.g., ':99')"
                        }
                    },
                    "required": ["display"]
                }
            },
            {
                "name": "setup_wsl_xforwarding",
                "description": "Setup X11 forwarding for WSL2 to Windows host",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "xserver_status",
                "description": "Get status of X servers and display configuration",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "test_display",
                "description": "Test current display configuration",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    def process_request(self):
        """Process one request from stdin"""
        try:
            line = sys.stdin.readline()
            if not line:
                return None
            request = json.loads(line)
            response = self.handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            return response
        except Exception as e:
            log(f"Error processing request: {e}")
            return None
    
    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming MCP request"""
        # Validate JSON-RPC 2.0 structure
        request_id = request.get("id")
        
        # Check for jsonrpc field
        if "jsonrpc" not in request:
            return self.error_response(request_id, "Missing 'jsonrpc' field")
        
        if request["jsonrpc"] != "2.0":
            return self.error_response(request_id, f"Invalid jsonrpc version: {request['jsonrpc']}")
        
        # Check for method field
        if "method" not in request:
            return self.error_response(request_id, "Missing 'method' field")
        
        method = request.get("method")
        if method is None:
            return self.error_response(request_id, "Method cannot be null")
        
        # For non-notifications, id must be present
        if "id" not in request:
            # This is a notification, process but don't respond
            return None
        
        # Check if id is null (test expects this to be invalid)
        if request_id is None:
            return self.error_response(request_id, "ID cannot be null")
        
        params = request.get("params", {})
        
        try:
            if method == "initialize":
                return self.initialize(request_id)
            elif method == "tools/list":
                return self.list_tools(request_id)
            elif method == "tools/call":
                # Validate params for tools/call
                if method == "tools/call" and params is None:
                    return self.error_response(request_id, "Missing params for tools/call")
                return self.call_tool(params, request_id)
            else:
                return self.error_response(request_id, f"Unknown method: {method}")
        except Exception as e:
            log(f"Error handling request: {e}")
            return self.error_response(request_id, str(e))
    
    def handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize method request"""
        return self.initialize(request.get("id"))
    
    def handle_list_tools(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list method request"""
        return self.list_tools(request.get("id"))
    
    def handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call method request"""
        return self.call_tool(request.get("params", {}), request.get("id"))
    
    def initialize(self, request_id: Any) -> Dict[str, Any]:
        """Handle initialization request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "computer-use-mcp",
                    "version": "1.0.0"
                }
            }
        }
    
    def list_tools(self, request_id: Any) -> Dict[str, Any]:
        """List available tools"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": self.tools
            }
        }
    
    def call_tool(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Execute tool call"""
        # Validate params structure
        if not isinstance(params, dict):
            return self.error_response(request_id, "Params must be an object")
        
        tool_name = params.get("name")
        if not tool_name:
            return self.error_response(request_id, "Missing tool name")
        
        arguments = params.get("arguments", {})
        
        # Safety check first
        try:
            action_desc = f"{tool_name} {arguments}"
            self.safety.validate_action(action_desc)
        except Exception as e:
            if "BLOCKED" in str(e):
                return self.error_response(request_id, str(e))
        
        # Add ultrathink enhancement
        log(f"Ultrathink analyzing: {tool_name} with {arguments}")
        
        # Execute tool
        try:
            if tool_name == "screenshot":
                result = self.handle_screenshot(arguments)
            elif tool_name == "click":
                result = self.handle_click(arguments)
            elif tool_name == "type":
                result = self.handle_type(arguments)
            elif tool_name == "key":
                result = self.handle_key(arguments)
            elif tool_name == "scroll":
                result = self.handle_scroll(arguments)
            elif tool_name == "drag":
                result = self.handle_drag(arguments)
            elif tool_name == "wait":
                result = self.handle_wait(arguments)
            elif tool_name == "automate":
                result = self.handle_automate(arguments)
            elif tool_name == "install_xserver":
                result = self.handle_install_xserver(arguments)
            elif tool_name == "start_xserver":
                result = self.handle_start_xserver(arguments)
            elif tool_name == "stop_xserver":
                result = self.handle_stop_xserver(arguments)
            elif tool_name == "setup_wsl_xforwarding":
                result = self.handle_setup_wsl_xforwarding(arguments)
            elif tool_name == "xserver_status":
                result = self.handle_xserver_status(arguments)
            elif tool_name == "test_display":
                result = self.handle_test_display(arguments)
            else:
                return self.error_response(request_id, f"Unknown tool: {tool_name}")
            
            # Wrap result in content array for MCP protocol
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result)
                        }
                    ]
                }
            }
        except Exception as e:
            log(f"Tool execution failed: {e}")
            return self.error_response(request_id, str(e))
    
    def handle_screenshot(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle screenshot tool"""
        # Pass analyze parameter to screenshot method
        analyze_prompt = args.get("analyze", "")
        screenshot_result = self.computer.screenshot(analyze=analyze_prompt)
        
        # Extract the actual image data
        if isinstance(screenshot_result, dict):
            screenshot_data = screenshot_result.get('data', b'')
        else:
            screenshot_data = screenshot_result
        
        # Analyze with visual analyzer
        analysis = self.visual.analyze_visual_context(screenshot_data)
        
        # Convert screenshot to base64 for transport if it's bytes
        if isinstance(screenshot_data, bytes):
            screenshot_b64 = base64.b64encode(screenshot_data).decode('utf-8')
        else:
            # In test mode, data might be a string
            screenshot_b64 = str(screenshot_data)
        
        return {
            "screenshot": screenshot_b64,
            "analysis": analysis,
            "query": analyze_prompt,
            "status": screenshot_result.get('status', 'success') if isinstance(screenshot_result, dict) else 'success'
        }
    
    def handle_click(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle click tool"""
        if args.get("element"):
            # Would need element detection
            return {"error": "Element detection not yet implemented"}
        
        # Get coordinates without defaults
        x = args.get("x")
        y = args.get("y")
        button = args.get("button", "left")
        
        # Validate coordinates are present
        if x is None or y is None:
            raise ValueError("Missing required coordinates x and y")
        
        try:
            x_int = int(x)
            y_int = int(y)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid coordinates: x={x}, y={y}")
        
        return self.computer.click(x_int, y_int, button)
    
    def handle_type(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle type tool"""
        text = args.get("text", "")
        
        # Validate text
        if text is None:
            raise ValueError("Text cannot be None")
        
        # Safety check content
        content_check = self.safety.check_content(str(text))
        if not content_check['safe']:
            text = self.safety.sanitize_text(str(text))
        
        return self.computer.type_text(str(text))
    
    def handle_key(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle key press tool"""
        key = args.get("key", "")
        return self.computer.key_press(key)
    
    def handle_scroll(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scroll tool"""
        direction = args.get("direction", "down")
        amount = args.get("amount", 3)
        
        # Validate direction
        if direction not in ["up", "down"]:
            raise ValueError(f"Invalid scroll direction: {direction}")
        
        # Validate amount
        try:
            amount_int = int(amount)
            if amount_int < 0:
                raise ValueError(f"Scroll amount must be positive: {amount}")
        except (TypeError, ValueError):
            raise ValueError(f"Invalid scroll amount: {amount}")
        
        return self.computer.scroll(direction, amount_int)
    
    def handle_drag(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle drag tool"""
        start_x = args.get("start_x")
        start_y = args.get("start_y")
        end_x = args.get("end_x")
        end_y = args.get("end_y")
        
        # Validate all coordinates are present
        if start_x is None or start_y is None or end_x is None or end_y is None:
            raise ValueError("All drag coordinates must be provided")
        
        try:
            start_x_int = int(start_x)
            start_y_int = int(start_y)
            end_x_int = int(end_x)
            end_y_int = int(end_y)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid drag coordinates")
        
        return self.computer.drag(start_x_int, start_y_int, end_x_int, end_y_int)
    
    def handle_wait(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle wait tool"""
        seconds = args.get("seconds", 1.0)
        
        # Validate seconds
        try:
            seconds_float = float(seconds)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid wait duration: {seconds}")
        
        return self.computer.wait(seconds_float)
    
    def handle_automate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle automation tool"""
        task = args.get("task", "")
        
        # Plan with ultrathink
        plan = self.ultrathink.plan_actions(task)
        
        # Execute plan
        results = []
        for step in plan:
            # Execute each step
            # This would need more implementation
            results.append({"step": step, "status": "simulated"})
        
        return {
            "task": task,
            "plan": plan,
            "results": results
        }
    
    def handle_install_xserver(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle X server installation"""
        return self.computer.install_xserver()
    
    def handle_start_xserver(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle starting X server"""
        display_num = args.get("display_num", 99)
        width = args.get("width", 1920)
        height = args.get("height", 1080)
        return self.computer.start_xserver(display_num, width, height)
    
    def handle_stop_xserver(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle stopping X server"""
        display = args.get("display")
        if not display:
            return {"error": "Display parameter required"}
        return self.computer.stop_xserver(display)
    
    def handle_setup_wsl_xforwarding(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WSL X11 forwarding setup"""
        return self.computer.setup_wsl_xforwarding()
    
    def handle_xserver_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle X server status request"""
        return self.computer.get_xserver_status()
    
    def handle_test_display(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle display test request"""
        return self.computer.test_display()
    
    def error_response(self, request_id: Any, message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": message
            }
        }
    
    def run(self):
        """Run MCP server (stdio mode)"""
        while True:
            try:
                # Read line from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                # Skip empty lines
                line = line.strip()
                if not line:
                    continue
                
                # Parse JSON request
                request = json.loads(line)
                
                # Handle request
                response = self.handle_request(request)
                
                # Send response
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                # Send error response for invalid JSON
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()
            except Exception as e:
                log(f"Server error: {e}")


def main():
    """Main entry point"""
    # Create and run server
    server = ComputerUseServer()
    server.run()


if __name__ == "__main__":
    main()
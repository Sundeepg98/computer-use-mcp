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

from computer_use_core import ComputerUseCore
from safety_checks import SafetyChecker
from visual_analyzer import VisualAnalyzer

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
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        # Notifications (no id field) should not return a response
        if request_id is None and "id" not in request:
            # This is a notification, process but don't respond
            return None
        
        try:
            if method == "initialize":
                return self.initialize(request_id)
            elif method == "tools/list":
                return self.list_tools(request_id)
            elif method == "tools/call":
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
        tool_name = params.get("name")
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
        
        x = args.get("x", 0)
        y = args.get("y", 0)
        button = args.get("button", "left")
        
        return self.computer.click(x, y, button)
    
    def handle_type(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle type tool"""
        text = args.get("text", "")
        
        # Safety check content
        content_check = self.safety.check_content(text)
        if not content_check['safe']:
            text = self.safety.sanitize_text(text)
        
        return self.computer.type_text(text)
    
    def handle_key(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle key press tool"""
        key = args.get("key", "")
        return self.computer.key_press(key)
    
    def handle_scroll(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scroll tool"""
        direction = args.get("direction", "down")
        amount = args.get("amount", 3)
        return self.computer.scroll(direction, amount)
    
    def handle_drag(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle drag tool"""
        start_x = args.get("start_x", 0)
        start_y = args.get("start_y", 0)
        end_x = args.get("end_x", 0)
        end_y = args.get("end_y", 0)
        return self.computer.drag(start_x, start_y, end_x, end_y)
    
    def handle_wait(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle wait tool"""
        seconds = args.get("seconds", 1.0)
        return self.computer.wait(seconds)
    
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
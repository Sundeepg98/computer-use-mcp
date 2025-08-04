#!/usr/bin/env python3
"""
MCP Server for Computer Use
Provides computer use capabilities as native Claude tools via MCP protocol
"""

import json
import sys
import os
import base64
import time
from typing import Dict, Any, List, Optional

from .factory_refactored import create_computer_use
from .safety_checks import SafetyChecker

# Simple stderr logging for debugging
def log(message):
    """Simple logging to stderr for debugging"""
    print(f"[MCP] {message}", file=sys.stderr)


class ComputerUseServer:
    """MCP Server providing computer use tools"""
    
    def __init__(self, computer_use=None):
        """Initialize MCP server
        
        Args:
            computer_use: Optional ComputerUse instance. If not provided,
                         creates a default instance for the current platform.
        """
        self.protocol_version = "2024-11-05"
        # Use injected instance or create default
        if computer_use:
            self.computer = computer_use
        else:
            from .factory_refactored import create_computer_use
            self.computer = create_computer_use()
        self.safety_checker = SafetyChecker()
        # Keep alias for backward compatibility
        self.safety = self.safety_checker
        self.tools = self._define_tools()
        
    def _define_tools(self) -> List[Dict[str, Any]]:
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
    

    def _validate_request(self, request: Dict[str, Any]) -> None:
        """Validate JSON-RPC request structure"""
        if 'jsonrpc' not in request:
            raise ValueError("Missing jsonrpc field")
        if request['jsonrpc'] != '2.0':
            raise ValueError("Invalid jsonrpc version")
        if 'method' not in request:
            raise ValueError("Missing method field")
    
    def _build_error_response(self, id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
        """Build JSON-RPC error response"""
        error = {
            'code': code,
            'message': message
        }
        if data is not None:
            error['data'] = data
        
        return {
            'jsonrpc': '2.0',
            'id': id,
            'error': error
        }

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
            elif method == "resources/list":
                return self.list_resources(request_id)
            elif method == "resources/read":
                if params is None:
                    return self.error_response(request_id, "Missing params for resources/read")
                return self.read_resource(params, request_id)
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
                    "tools": {},
                    "resources": {},
                    "experimental": {
                        "platform_detection": True,
                        "windows_server_support": True,
                        "vcxsrv_integration": True
                    }
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
    
    def list_resources(self, request_id: Any) -> Dict[str, Any]:
        """List available resources"""
        resources = [
            {
                "uri": "platform://capabilities",
                "name": "Platform Capabilities",
                "description": "Current platform capabilities and limitations",
                "mimeType": "application/json"
            },
            {
                "uri": "guide://vcxsrv-install",
                "name": "VcXsrv Installation Guide", 
                "description": "Step-by-step VcXsrv installation guide",
                "mimeType": "text/markdown"
            },
            {
                "uri": "guide://windows-server-setup",
                "name": "Windows Server Setup Guide",
                "description": "Windows Server automation setup guide",
                "mimeType": "text/markdown"
            },
            {
                "uri": "troubleshooting://display-issues",
                "name": "Display Issues Troubleshooting",
                "description": "Common display and screenshot issues",
                "mimeType": "text/markdown"
            },
            {
                "uri": "config://platform-defaults",
                "name": "Platform Default Configuration",
                "description": "Default configuration for current platform",
                "mimeType": "application/json"
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": resources
            }
        }
    
    def read_resource(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Read a specific resource"""
        uri = params.get("uri")
        if not uri:
            return self.error_response(request_id, "Missing resource URI")
        
        try:
            if uri == "platform://capabilities":
                content = self._get_platform_capabilities()
            elif uri == "guide://vcxsrv-install":
                content = self._get_vcxsrv_install_guide()
            elif uri == "guide://windows-server-setup":
                content = self._get_windows_server_setup_guide()
            elif uri == "troubleshooting://display-issues":
                content = self._get_display_troubleshooting()
            elif uri == "config://platform-defaults":
                content = self._get_platform_defaults()
            else:
                return self.error_response(request_id, f"Unknown resource URI: {uri}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "contents": [
                        {
                            "type": "text",
                            "text": content
                        }
                    ]
                }
            }
        except Exception as e:
            return self.error_response(request_id, f"Failed to read resource: {e}")
    
    def _get_platform_capabilities(self) -> str:
        """Get platform capabilities resource"""
        try:
            from .platform_utils import get_platform_info, get_windows_server_info, get_vcxsrv_status
            
            platform_info = get_platform_info()
            capabilities = {
                "platform": platform_info,
                "screenshot_available": self.computer.display_available,
                "recommended_methods": {
                    "screenshot": platform_info.get("recommended_screenshot_method", "unknown"),
                    "input": platform_info.get("recommended_input_method", "unknown")
                }
            }
            
            # Add Windows Server info if applicable
            if platform_info.get('platform') == 'windows':
                capabilities["windows_server"] = get_windows_server_info()
                capabilities["vcxsrv"] = get_vcxsrv_status()
            
            return json.dumps(capabilities, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get capabilities: {e}"})
    
    def _get_vcxsrv_install_guide(self) -> str:
        """Get VcXsrv installation guide resource"""
        guide = """# VcXsrv Installation Guide

## Overview
VcXsrv is an X11 server for Windows that enables running Linux GUI applications.

## Installation Steps

1. **Download VcXsrv**
   - Visit: https://sourceforge.net/projects/vcxsrv/
   - Download the latest installer

2. **Run Installer**
   - Run as Administrator
   - Follow installation wizard
   - Use default settings

3. **Launch XLaunch**
   - Start XLaunch from Start Menu
   - Configure display settings:
     - Multiple windows mode (recommended)
     - Display number: 0
     - Enable clipboard sharing
     - Disable access control (-ac)

4. **Windows Firewall**
   - Allow VcXsrv through Windows Firewall when prompted
   - Both Private and Public networks

## WSL2 Setup

1. **Get Windows Host IP**
   ```bash
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
   ```

2. **Test Connection**
   ```bash
   xeyes  # Should show eyes that follow mouse
   ```

## Troubleshooting

- **Connection refused**: Check Windows Firewall
- **No display**: Verify DISPLAY variable
- **Black screen**: Try different display modes
"""
        return guide
    
    def _get_windows_server_setup_guide(self) -> str:
        """Get Windows Server setup guide resource"""
        guide = """# Windows Server Automation Setup

## Server Editions Supported

- **Windows Server 2022** ✅ Full support
- **Windows Server 2019** ✅ Full support  
- **Windows Server 2016** ✅ Full support
- **Windows Server Core** ⚠️ Limited GUI (use VcXsrv)

## Setup by Environment

### Windows Server with GUI
- **Screenshot**: Native Windows GDI
- **Input**: Native SendInput API
- **Setup**: No additional setup required

### Windows Server Core
- **Screenshot**: Not available (no GUI)
- **Alternatives**:
  1. Install VcXsrv for X11 GUI
  2. Use PowerShell automation
  3. Use Windows Admin Center

### RDP Sessions
- **Screenshot**: RDP-aware capture
- **Limitations**: Captures RDP window only
- **Best Practice**: Use native tools on RDP client

## PowerShell Automation (Server Core)

```powershell
# Service management
Get-Service | Where-Object {$_.Status -eq "Running"}
Restart-Service -Name "ServiceName"

# File operations
Get-ChildItem -Path C:\\ -Recurse -Filter "*.log"
Copy-Item -Path "source" -Destination "dest" -Recurse

# Network configuration
Get-NetAdapter | Select-Object Name, Status, LinkSpeed
```

## VcXsrv on Server Core

1. **Install VcXsrv on Windows client machine**
2. **Configure remote access**
3. **Set DISPLAY variable**
4. **Test with simple X11 applications**
"""
        return guide
    
    def _get_display_troubleshooting(self) -> str:
        """Get display troubleshooting resource"""
        guide = """# Display & Screenshot Troubleshooting

## Common Issues

### Black/Empty Screenshots

**WSL2 Environment:**
- **Cause**: X11 captures virtual display buffer
- **Solution**: Use PowerShell bridge for Windows desktop capture

**Server Core:**
- **Cause**: No GUI available
- **Solution**: Install VcXsrv or use PowerShell automation

### Permission Errors

**Linux:**
- **Cause**: No access to X11 display
- **Solution**: `xhost +local:` or proper DISPLAY variable

**Windows:**
- **Cause**: Insufficient privileges
- **Solution**: Run as Administrator

### Performance Issues

**Large Screenshots:**
- **Solution**: Use region capture instead of full screen
- **Example**: `screenshot(region={'x': 0, 'y': 0, 'width': 800, 'height': 600})`

**Slow Capture:**
- **Solution**: Check system resources and display drivers

### Network Issues (Remote)

**RDP Sessions:**
- **Issue**: Multi-monitor confusion
- **Solution**: Use single monitor RDP or specify monitor

**VcXsrv Remote:**
- **Issue**: Firewall blocking X11
- **Solution**: Configure Windows Firewall rules

## Environment-Specific Solutions

| Environment | Issue | Solution |
|-------------|-------|----------|
| WSL2 | Black screenshots | Use `wsl2_powershell` method |
| Server Core | No screenshots | Install VcXsrv or use PowerShell |
| RDP | Partial capture | Use RDP-aware methods |
| VcXsrv | Connection refused | Check firewall and DISPLAY |

## Diagnostic Commands

```bash
# Test X11 connectivity
xset q

# Check display variable
echo $DISPLAY

# Test screenshot tools
scrot test.png
import -window root test.png

# Windows PowerShell test
powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen"
```
"""
        return guide
    
    def _get_platform_defaults(self) -> str:
        """Get platform default configuration resource"""
        try:
            from .platform_utils import get_platform_info, get_recommended_screenshot_method, get_recommended_input_method
            
            platform_info = get_platform_info()
            
            defaults = {
                "platform": platform_info.get('platform'),
                "environment": platform_info.get('environment'),
                "methods": {
                    "screenshot": get_recommended_screenshot_method(),
                    "input": get_recommended_input_method()
                },
                "capabilities": {
                    "display_available": platform_info.get('display_available', True),
                    "gui_available": platform_info.get('has_gui', True),
                    "x11_available": platform_info.get('can_use_x11', False),
                    "powershell_available": platform_info.get('can_use_powershell', False)
                },
                "recommended_settings": {
                    "screenshot_format": "png",
                    "screenshot_quality": "high",
                    "input_delay": 0.1,
                    "retry_attempts": 3
                }
            }
            
            # Add platform-specific settings
            if platform_info.get('environment') == 'wsl2':
                defaults["wsl2_settings"] = {
                    "use_powershell_bridge": True,
                    "capture_windows_desktop": True
                }
            
            elif platform_info.get('environment') == 'windows_server_core':
                defaults["server_core_settings"] = {
                    "recommend_vcxsrv": True,
                    "recommend_powershell": True,
                    "recommend_admin_center": True
                }
            
            return json.dumps(defaults, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get defaults: {e}"})
    
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
            elif tool_name == "get_platform_info":
                result = self.handle_get_platform_info(arguments)
            elif tool_name == "check_display_available":
                result = self.handle_check_display_available(arguments)
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
        """Handle screenshot tool - captures and saves screenshots"""
        # Extract parameters
        method = args.get("method", "recommended")
        save_path = args.get("save_path", "")
        
        # If no save_path is provided, don't actually take the screenshot
        # This avoids creating large intermediate objects
        if not save_path:
            result = {
                "status": "error",
                "message": "save_path parameter is required to capture screenshots",
                "note": "Screenshots must be saved to disk to avoid token limits"
            }
            return result
        
        # Take screenshot only if we're going to save it
        if method != "recommended":
            try:
                from .screenshot import ScreenshotFactory
                # Create screenshot handler with specific method
                screenshot_handler = ScreenshotFactory.create(force=method)
                screenshot_data = screenshot_handler.capture()
                # Wrap raw bytes in expected format
                screenshot_result = {
                    'success': True,
                    'data': screenshot_data,
                    'method': method,
                    'status': 'success'
                }
            except Exception as e:
                # Fallback to default method if specific method fails
                log(f"Specific method {method} failed: {e}")
                screenshot_result = self.computer.take_screenshot()
        else:
            # Use recommended method (current behavior)
            screenshot_result = self.computer.take_screenshot()
        
        # Extract the actual image data only if we need to save it
        screenshot_data = None
        if save_path:
            if isinstance(screenshot_result, dict):
                screenshot_data = screenshot_result.get('data', b'')
            else:
                screenshot_data = screenshot_result
        
        # Save to file if save_path is provided
        saved_to = None
        if save_path and isinstance(screenshot_data, bytes):
            try:
                import os
                from pathlib import Path
                
                # Expand user path and make absolute
                save_path = os.path.expanduser(save_path)
                save_path = os.path.abspath(save_path)
                
                # Create directory if needed
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Save the screenshot
                with open(save_path, 'wb') as f:
                    f.write(screenshot_data)
                
                saved_to = save_path
                log(f"Screenshot saved to: {save_path}")
            except Exception as e:
                log(f"Failed to save screenshot to {save_path}: {e}")
        
        # Don't include the actual screenshot data to avoid token limits
        # The screenshot is saved to file if save_path is provided
        result = {
            "status": screenshot_result.get('status', 'success') if isinstance(screenshot_result, dict) else 'success',
            "method_used": method if method != "recommended" else "auto-detected",
            "message": "Screenshot captured successfully"
        }
        
        # Add saved_to field if file was saved
        if saved_to:
            result["saved_to"] = saved_to
            result["message"] = f"Screenshot saved to {saved_to}"
        else:
            result["message"] = "Screenshot captured (use save_path parameter to save to file)"
            
        return result
    
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
        
        # Enhanced safety check for all security threats
        if not self.safety.check_text_safety(str(text)):
            raise Exception(f"BLOCKED: {self.safety.last_error}")
        
        return self.computer.type_text(str(text))
    
    def handle_key(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle key press tool"""
        key = args.get("key", "")
        
        # Enhanced safety check for key presses
        if not self.safety.check_text_safety(str(key)):
            raise Exception(f"BLOCKED: {self.safety.last_error}")
        
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
    def handle_get_platform_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle platform info request"""
        try:
            from .platform_utils import get_platform_info, get_windows_server_info, get_vcxsrv_status
            
            platform_info = get_platform_info()
            
            # Add comprehensive info
            result = {
                "platform": platform_info,
                "capabilities": {
                    "screenshot_available": self.computer.display_available,
                    "input_available": True,  # Always available in some form
                    "gui_available": platform_info.get('display_available', True)
                }
            }
            
            # Add Windows Server specific info
            if platform_info.get('platform') == 'windows':
                server_info = get_windows_server_info()
                result["windows_server"] = server_info
                
                # Add VcXsrv info
                vcxsrv_info = get_vcxsrv_status()
                result["vcxsrv"] = vcxsrv_info
            
            return result
        except Exception as e:
            return {"error": f"Platform info failed: {e}"}
    def handle_check_display_available(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle display availability check"""
        try:
            from .platform_utils import get_platform_info
            
            platform_info = get_platform_info()
            
            result = {
                "display_available": self.computer.display_available,
                "gui_available": platform_info.get('display_available', True),
                "method": platform_info.get('environment'),
                "details": {}
            }
            
            # Add method-specific details
            if platform_info.get('environment') == 'windows_server_core':
                result["details"]["server_core"] = True
                result["details"]["vcxsrv_available"] = platform_info.get('vcxsrv_display_available', False)
            
            elif platform_info.get('environment') == 'windows_rdp':
                result["details"]["rdp_session"] = True
                result["details"]["captures_rdp_window"] = True
            
            elif platform_info.get('environment') == 'wsl2':
                result["details"]["wsl2"] = True
                result["details"]["uses_powershell"] = True
            
            return result
        except Exception as e:
            return {"error": f"Display check failed: {e}"}
    
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
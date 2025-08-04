"""Helper utilities for computer-use-mcp"""

import base64
import io
import json
import os
import subprocess
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def encode_image(image_path: str) -> Optional[str]:
    """
    Encode image file to base64
    
    Args:
        image_path: Path to image file
    
    Returns:
        Base64 encoded string or None if error
    """
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to encode image: {e}")
        return None


def decode_image(base64_string: str, output_path: Optional[str] = None) -> Optional[str]:
    """
    Decode base64 string to image file
    
    Args:
        base64_string: Base64 encoded image
        output_path: Optional path to save decoded image
    
    Returns:
        Path to saved image or None if error
    """
    try:
        image_data = base64.b64decode(base64_string)
        
        if output_path is None:
            output_path = f"/tmp/decoded_image_{int(time.time())}.png"
        
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        return output_path
    except Exception as e:
        logger.error(f"Failed to decode image: {e}")
        return None


def get_display_info() -> Dict[str, Any]:
    """
    Get display information
    
    Returns:
        Dictionary with display info
    """
    info = {
        'width': 1920,
        'height': 1080,
        'depth': 24,
        'display': os.environ.get('DISPLAY', ':0'),
    }
    
    # Try to get actual display info on Linux
    if os.name == 'posix':
        try:
            result = subprocess.run(
                ['xdpyinfo'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Parse xdpyinfo output
                for line in result.stdout.split('\n'):
                    if 'dimensions:' in line:
                        # Extract resolution
                        parts = line.split()
                        if len(parts) >= 2:
                            resolution = parts[1]
                            if 'x' in resolution:
                                w, h = resolution.split('x')
                                info['width'] = int(w)
                                info['height'] = int(h)
                        break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    
    return info


def safe_execute(command: list, timeout: int = 5) -> Tuple[bool, str, str]:
    """
    Safely execute a system command
    
    Args:
        command: Command and arguments as list
        timeout: Timeout in seconds
    
    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, "", str(e)


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """
    Decorator to retry function on failure
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Delay between attempts in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay} seconds..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed")
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def load_state(state_file: str = "/tmp/computer-use-mcp-state.json") -> Dict[str, Any]:
    """
    Load persistent state
    
    Args:
        state_file: Path to state file
    
    Returns:
        State dictionary
    """
    try:
        if Path(state_file).exists():
            with open(state_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load state: {e}")
    
    return {}


def save_state(state: Dict[str, Any], state_file: str = "/tmp/computer-use-mcp-state.json") -> bool:
    """
    Save persistent state
    
    Args:
        state: State dictionary to save
        state_file: Path to state file
    
    Returns:
        True if successful
    """
    try:
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        return False


def format_mcp_response(result: Any, error: Optional[str] = None, request_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Format MCP protocol response
    
    Args:
        result: Result data
        error: Error message if any
        request_id: Request ID
    
    Returns:
        Formatted MCP response
    """
    response = {
        "jsonrpc": "2.0",
    }
    
    if request_id is not None:
        response["id"] = request_id
    
    if error:
        response["error"] = {
            "code": -32603,  # Internal error
            "message": error
        }
    else:
        response["result"] = result
    
    return response


def get_platform_info() -> Dict[str, str]:
    """
    Get platform information
    
    Returns:
        Platform info dictionary
    """
    import platform
    
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
    }
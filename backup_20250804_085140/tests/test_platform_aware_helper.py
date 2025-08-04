"""
Platform-aware test helpers
Makes tests work with both Linux and Windows implementations
"""

import os
import subprocess
from unittest.mock import MagicMock, patch
from typing import Dict, Any, Optional


def is_wsl2_test_environment():
    """Check if we're in WSL2 during testing"""
    return os.path.exists('/mnt/wslg') or os.environ.get('WSL_INTEROP')


def create_platform_aware_subprocess_mock():
    """Create subprocess mock that handles both xdotool and PowerShell commands"""
    def run_side_effect(cmd, *args, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stdout = b''
        result.stderr = b''
        
        if isinstance(cmd, list):
            # Handle xdotool commands
            if len(cmd) > 0 and cmd[0] == 'xdotool':
                if 'getmouselocation' in cmd:
                    result.stdout = 'x:123 y:456 screen:0 window:12345'
                elif 'which' in cmd:
                    result.stdout = '/usr/bin/xdotool'
                return result
            
            # Handle scrot commands
            elif len(cmd) > 0 and cmd[0] == 'scrot':
                if '--silent' in cmd and len(cmd) > 2:
                    output_path = cmd[2]
                    # Create a minimal PNG file
                    with open(output_path, 'wb') as f:
                        f.write(b'\x89PNG\r\n\x1a\n' + b'MOCK_DATA')
                return result
            
            # Handle PowerShell commands
            elif len(cmd) > 0 and cmd[0] == 'powershell.exe':
                # Extract PowerShell script
                if '-Command' in cmd:
                    ps_script = cmd[cmd.index('-Command') + 1]
                    
                    # Handle mouse position query
                    if '[System.Windows.Forms.Cursor]::Position' in ps_script:
                        result.stdout = '123,456\n'
                    
                    # Handle screenshot capture
                    elif 'System.Drawing.Bitmap' in ps_script:
                        # Simulate successful screenshot
                        if 'Out-File' in ps_script:
                            # Extract output path from PowerShell script
                            import re
                            match = re.search(r'Out-File.*"([^"]+)"', ps_script)
                            if match:
                                output_path = match.group(1)
                                with open(output_path, 'wb') as f:
                                    f.write(b'\x89PNG\r\n\x1a\n' + b'MOCK_SCREENSHOT_DATA')
                return result
        
        return result
    
    mock_run = MagicMock(side_effect=run_side_effect)
    return mock_run


def adapt_test_for_platform(test_func):
    """Decorator to adapt tests for platform differences"""
    def wrapper(*args, **kwargs):
        # If we're in WSL2, tests will use PowerShell instead of xdotool
        if is_wsl2_test_environment():
            # Patch subprocess to handle both command types
            with patch('subprocess.run', create_platform_aware_subprocess_mock()):
                return test_func(*args, **kwargs)
        else:
            # Run test as-is for Linux
            return test_func(*args, **kwargs)
    return wrapper


def get_expected_command_for_action(action: str, **params) -> Dict[str, Any]:
    """Get expected command based on platform and action"""
    if is_wsl2_test_environment():
        # Return PowerShell commands
        if action == 'click':
            return {
                'cmd': 'powershell.exe',
                'contains': ['System.Windows.Forms.Cursor', 'mouse_event']
            }
        elif action == 'type':
            return {
                'cmd': 'powershell.exe',
                'contains': ['System.Windows.Forms.SendKeys']
            }
        elif action == 'screenshot':
            return {
                'cmd': 'powershell.exe',
                'contains': ['System.Drawing.Bitmap']
            }
        elif action == 'move':
            return {
                'cmd': 'powershell.exe',
                'contains': ['System.Windows.Forms.Cursor']
            }
    else:
        # Return xdotool commands
        if action == 'click':
            return {
                'cmd': 'xdotool',
                'args': ['click', str(params.get('button', '1'))]
            }
        elif action == 'type':
            return {
                'cmd': 'xdotool',
                'args': ['type', '--clearmodifiers', params.get('text', '')]
            }
        elif action == 'screenshot':
            return {
                'cmd': 'scrot',
                'args': ['--silent']
            }
        elif action == 'move':
            return {
                'cmd': 'xdotool',
                'args': ['mousemove', str(params.get('x', 0)), str(params.get('y', 0))]
            }
    
    return {}
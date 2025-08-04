"""
Platform-aware test configuration
Makes tests work across Windows, WSL2, and Linux
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

# Detect test environment
IS_WSL2 = os.path.exists('/mnt/wslg') or os.environ.get('WSL_INTEROP')
IS_WINDOWS = sys.platform == 'win32'
IS_LINUX = sys.platform.startswith('linux') and not IS_WSL2

# Default to Linux behavior for CI/tests
TEST_PLATFORM = os.environ.get('TEST_PLATFORM', 'linux')


@pytest.fixture(autouse=True)
def mock_platform_for_tests():
    """Automatically mock platform to Linux for consistent test behavior"""
    if TEST_PLATFORM == 'linux':
        # Mock as native Linux for tests
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {}, clear=True):
                # Ensure DISPLAY is set for X11 tests
                os.environ['DISPLAY'] = ':0'
                with patch('os.path.exists') as mock_exists:
                    # Make sure WSL2 detection returns False
                    def exists_side_effect(path):
                        if path == '/mnt/wslg':
                            return False
                        return os.path.exists(path)
                    mock_exists.side_effect = exists_side_effect
                    yield
    else:
        yield


@pytest.fixture
def mock_subprocess_for_xdotool():
    """Mock subprocess to handle xdotool commands"""
    with patch('subprocess.run') as mock_run:
        def run_side_effect(cmd, *args, **kwargs):
            # Handle xdotool commands
            if isinstance(cmd, list) and len(cmd) > 0:
                if cmd[0] == 'xdotool':
                    if 'getmouselocation' in cmd:
                        result = MagicMock()
                        result.returncode = 0
                        result.stdout = 'x:123 y:456 screen:0 window:12345'
                        return result
                    else:
                        # Success for other xdotool commands
                        result = MagicMock()
                        result.returncode = 0
                        result.stdout = b''
                        result.stderr = b''
                        return result
                elif cmd[0] == 'scrot':
                    # Simulate successful screenshot
                    result = MagicMock()
                    result.returncode = 0
                    # Create a small test PNG file
                    if '--silent' in cmd and len(cmd) > 2:
                        output_path = cmd[2]
                        with open(output_path, 'wb') as f:
                            # Minimal PNG header
                            f.write(b'\x89PNG\r\n\x1a\n' + b'MOCK_DATA')
                    return result
                elif cmd[0] == 'which':
                    # Simulate tool availability
                    result = MagicMock()
                    if len(cmd) > 1 and cmd[1] in ['xdotool', 'scrot', 'import', 'xwd']:
                        result.returncode = 0
                        result.stdout = f'/usr/bin/{cmd[1]}'
                    else:
                        result.returncode = 1
                    return result
            
            # Default behavior
            return MagicMock(returncode=0, stdout=b'', stderr=b'')
        
        mock_run.side_effect = run_side_effect
        yield mock_run


@pytest.fixture
def force_linux_platform():
    """Force platform detection to Linux"""
    with patch('computer_use_mcp.platform_utils.PlatformDetector.detect_platform') as mock_detect:
        mock_detect.return_value = {
            'platform': 'linux',
            'environment': 'native',
            'can_use_powershell': False,
            'can_use_dotnet': False,
            'can_use_x11': True,
            'can_use_screencapture': False,
            'wsl_version': None
        }
        yield


@pytest.fixture
def force_wsl2_platform():
    """Force platform detection to WSL2"""
    with patch('computer_use_mcp.platform_utils.PlatformDetector.detect_platform') as mock_detect:
        mock_detect.return_value = {
            'platform': 'linux',
            'environment': 'wsl2',
            'can_use_powershell': True,
            'can_use_dotnet': False,
            'can_use_x11': True,
            'can_use_screencapture': False,
            'wsl_version': 2
        }
        yield
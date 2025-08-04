"""Pytest configuration and shared fixtures"""

import sys
import os
from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import platform-aware configurations
from conftest_platform_aware import *


@pytest.fixture
def mock_server():
    """Mock MCP server for testing"""
    from mcp.mcp_server import ComputerUseServer
    server = ComputerUseServer(test_mode=True)
    return server


@pytest.fixture
def mock_safety_checker():
    """Mock safety checker for testing"""
    from mcp.safety_checks import SafetyChecker
    return SafetyChecker()


@pytest.fixture
def mock_ultrathink():
    """Mock ultrathink analyzer for testing"""
    from mcp.visual_analyzer import VisualAnalyzer as VisualAnalyzerAdvanced
    analyzer = VisualAnalyzerAdvanced()
    analyzer.analyze_screen = Mock(return_value={'elements': []})
    analyzer.plan_task = Mock(return_value={'steps': ['step1', 'step2']})
    return analyzer


@pytest.fixture
def sample_mcp_request():
    """Sample MCP request for testing"""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }


@pytest.fixture
def sample_screenshot_data():
    """Sample screenshot data for testing"""
    return {
        'width': 1920,
        'height': 1080,
        'data': 'base64_mock_image_data'
    }


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create temporary test directory"""
    test_dir = tmp_path / "test_workspace"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def mock_xserver_manager():
    """Mock X server manager for testing"""
    from mcp.xserver_manager import XServerManager
    manager = Mock(spec=XServerManager)
    
    # Setup default return values
    manager.wsl_mode = False
    manager.host_ip = None
    manager.xserver_processes = {}
    manager.display_ports = {}
    
    manager.check_xserver_available.return_value = {
        'available': True,
        'display': ':0',
        'method': 'native_x11'
    }
    
    manager.get_best_display.return_value = {
        'available': True,
        'display': ':0',
        'method': 'existing_display'
    }
    
    manager.install_xserver_packages.return_value = {
        'installed': [],
        'failed': [],
        'already_installed': ['xorg', 'xvfb']
    }
    
    manager.start_virtual_display.return_value = {
        'success': True,
        'display': ':99',
        'pid': 12345,
        'resolution': '1920x1080'
    }
    
    manager.get_status.return_value = {
        'wsl_mode': False,
        'current_display': ':0',
        'managed_servers': {},
        'active_processes': 0
    }
    
    return manager


@pytest.fixture
def sample_xserver_tool_request():
    """Sample X server tool MCP request"""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "start_xserver",
            "arguments": {
                "display_num": 99,
                "width": 1920,
                "height": 1080
            }
        }
    }


@pytest.fixture
def mock_display_env(monkeypatch):
    """Mock DISPLAY environment variable"""
    def _set_display(display_value):
        if display_value:
            monkeypatch.setenv('DISPLAY', display_value)
        else:
            monkeypatch.delenv('DISPLAY', raising=False)
    return _set_display


@pytest.fixture
def mock_wsl_environment(monkeypatch):
    """Mock WSL2 environment"""
    # Mock /proc/version to indicate WSL
    def mock_open_wsl(filename, mode='r'):
        if filename == '/proc/version':
            from io import StringIO
            return StringIO('Linux version 5.10.16.3-microsoft-standard-WSL2')
        return open(filename, mode)
    
    monkeypatch.setattr('builtins.open', mock_open_wsl)
    
    # Mock resolv.conf for host IP
    def mock_subprocess_run(cmd, **kwargs):
        if 'resolv.conf' in str(cmd):
            return Mock(
                stdout='nameserver 192.168.1.100\n',
                returncode=0
            )
        return Mock(returncode=0)
    
    monkeypatch.setattr('subprocess.run', mock_subprocess_run)
    
    return {
        'host_ip': '192.168.1.100',
        'wsl_version': 'WSL2'
    }
"""Pytest configuration and shared fixtures"""

import sys
import os
from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture
def mock_server():
    """Mock MCP server for testing"""
    from mcp_server import ComputerUseServer
    server = ComputerUseServer(test_mode=True)
    return server


@pytest.fixture
def mock_safety_checker():
    """Mock safety checker for testing"""
    from safety_checks import SafetyChecker
    return SafetyChecker()


@pytest.fixture
def mock_ultrathink():
    """Mock ultrathink analyzer for testing"""
    from visual_analyzer import VisualAnalyzerAdvanced
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
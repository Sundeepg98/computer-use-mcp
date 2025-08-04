#!/usr/bin/env python3
"""
Platform-aware test helpers
"""

import sys
from unittest.mock import Mock, MagicMock

def adapt_test_for_platform(test_func):
    """Decorator to adapt tests for current platform"""
    def wrapper(*args, **kwargs):
        # Just run the test as-is
        return test_func(*args, **kwargs)
    return wrapper

def create_platform_aware_subprocess_mock():
    """Create a subprocess mock that works across platforms"""
    mock = Mock()
    
    # Mock the run method
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = b"mock output"
    mock_result.stderr = b""
    
    mock.run = Mock(return_value=mock_result)
    mock.PIPE = -1
    mock.DEVNULL = -3
    
    return mock

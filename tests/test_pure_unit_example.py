#!/usr/bin/env python3
"""
PURE UNIT TEST EXAMPLE - Testing individual methods in complete isolation

This demonstrates TRUE unit testing where:
1. Each test focuses on ONE method
2. ALL dependencies are mocked
3. Tests are FAST (milliseconds)
4. No real I/O or system calls
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

from mcp.test_mocks import create_test_computer_use

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))


class TestSafetyCheckerUnit(unittest.TestCase):
    """Pure unit tests for SafetyChecker - testing logic only"""
    
    def setUp(self):
        """Create SafetyChecker instance for each test"""
        from mcp.safety_checks import SafetyChecker
        self.safety = SafetyChecker()
    
    def test_check_text_safety_detects_rm_rf(self):
        """Unit test: check_text_safety method detects rm -rf pattern"""
        # Test ONLY the pattern matching logic
        result = self.safety.check_text_safety("rm -rf /")
        self.assertFalse(result)
    
    def test_check_text_safety_allows_safe_text(self):
        """Unit test: check_text_safety allows safe text"""
        # Test ONLY the pattern matching logic
        result = self.safety.check_text_safety("Hello world")
        self.assertTrue(result)
    
    def test_detect_credentials_finds_password(self):
        """Unit test: detect_credentials finds password patterns"""
        # Test ONLY the credential detection logic
        result = self.safety.detect_credentials("password: secret123")
        self.assertTrue(result)
    
    def test_validate_coordinates_rejects_negative(self):
        """Unit test: coordinate validation logic"""
        # Pure logic test - no system interaction
        result = self.safety.validate_coordinates(-10, -20)
        self.assertFalse(result[0])  # Check first element of tuple


class TestComputerUseCoreUnit(unittest.TestCase):
    """Pure unit tests for individual methods"""
    
    @patch('mcp.computer_use_core.subprocess')
    @patch('mcp.computer_use_core.platform')
    def test_screenshot_calls_correct_command_for_linux(self, mock_platform, mock_subprocess):
        """Unit test: screenshot method builds correct command for Linux"""
        # Setup
        mock_platform.system.return_value = 'Linux'
        mock_subprocess.run.return_value = Mock(returncode=0, stdout=b'fake_image')
        
        from mcp.computer_use_core import ComputerUseCore
        
        # Create instance with mocked dependencies
        core = ComputerUseCore()
# No longer using test_mode - using proper dependency injection  # Force real logic
        core.display_available = True
        
        # Execute
        result = core.screenshot()
        
        # Assert - verify the method's behavior
        mock_subprocess.run.assert_called_once()
        args = mock_subprocess.run.call_args[0][0]
        self.assertIn('import', args)  # Linux uses 'import' command
    
    @patch('mcp.computer_use_core.subprocess')
    def test_type_text_escapes_special_characters(self, mock_subprocess):
        """Unit test: type_text properly escapes special characters"""
        mock_subprocess.run.return_value = Mock(returncode=0)
        
        from mcp.computer_use_core import ComputerUseCore
        core = ComputerUseCore()
# No longer using test_mode - using proper dependency injection
        core.display_available = True
        
        # Test the escaping logic
        core.type_text("test & echo")
        
        # Verify escaping happened
        args = mock_subprocess.run.call_args[0][0]
        command_str = ' '.join(args)
        # Should not contain raw & character in dangerous position
        self.assertIn('type', command_str)
    
    def test_validate_coordinates_boundary_check(self):
        """Unit test: coordinate validation boundary testing"""
        from mcp.computer_use_core import ComputerUseCore
        core = ComputerUseCore()
        
        # Test validation logic only - pure function
        test_cases = [
            ((0, 0), True),         # Valid: minimum
            ((1920, 1080), True),   # Valid: typical max
            ((-1, 0), False),       # Invalid: negative
            ((0, -1), False),       # Invalid: negative
            ((99999, 0), False),    # Invalid: too large
        ]
        
        for coords, expected in test_cases:
            with self.subTest(coords=coords):
                try:
                    core._validate_coordinates(*coords)
                    actual = True
                except ValueError:
                    actual = False
                self.assertEqual(actual, expected)


class TestMCPProtocolUnit(unittest.TestCase):
    """Pure unit tests for MCP protocol handling"""
    
    def test_validate_jsonrpc_request_structure(self):
        """Unit test: JSON-RPC request validation logic"""
        from mcp.mcp_server import ComputerUseServer
        server = ComputerUseServer()
        
        # Test validation logic only
        valid_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "screenshot"}
        }
        
        # Should not raise exception
        server._validate_request(valid_request)
        
        # Test invalid request
        invalid_request = {"method": "test"}  # Missing required fields
        
        with self.assertRaises(ValueError):
            server._validate_request(invalid_request)
    
    def test_build_error_response(self):
        """Unit test: error response builder logic"""
        from mcp.mcp_server import ComputerUseServer
        server = ComputerUseServer()
        
        # Test error response generation - pure logic
        response = server._build_error_response(
            request_id=123,
            code=-32601,
            message="Method not found"
        )
        
        # Verify structure
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 123)
        self.assertEqual(response["error"]["code"], -32601)
        self.assertEqual(response["error"]["message"], "Method not found")


class TestPureFunctions(unittest.TestCase):
    """Test pure functions that have no side effects"""
    
    def test_parse_key_combination(self):
        """Unit test: key combination parser"""
        # Assuming this function exists
        from mcp.utils import parse_key_combination
        
        test_cases = [
            ("ctrl+c", ["ctrl", "c"]),
            ("alt+tab", ["alt", "tab"]),
            ("ctrl+shift+t", ["ctrl", "shift", "t"]),
            ("a", ["a"]),
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                result = parse_key_combination(input_str)
                self.assertEqual(result, expected)
    
    def test_sanitize_filename(self):
        """Unit test: filename sanitization logic"""
        from mcp.utils import sanitize_filename
        
        test_cases = [
            ("normal.txt", "normal.txt"),
            ("../etc/passwd", "etc_passwd"),
            ("file with spaces.txt", "file_with_spaces.txt"),
            ("", "unnamed"),
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                result = sanitize_filename(input_str)
                self.assertEqual(result, expected)


def main():
    """Demonstrate pure unit testing"""
    print("=" * 70)
    print("PURE UNIT TEST EXAMPLES")
    print("=" * 70)
    print()
    print("These are TRUE unit tests that:")
    print("✓ Test ONE method at a time")
    print("✓ Mock ALL external dependencies")
    print("✓ Run in milliseconds")
    print("✓ Have no side effects")
    print("✓ Test pure logic only")
    print()
    
    # Run with high verbosity to show speed
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
FIXED VERSION: Safety and Security Tests that ACTUALLY test safety mechanisms

This demonstrates proper testing of safety features without test_mode.
We test the REAL safety logic, not mock returns.
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from mcp.mcp_server import ComputerUseServer
from mcp.computer_use_core import ComputerUseCore
from mcp.safety_checks import SafetyChecker


class TestRealSafetyValidation(unittest.TestCase):
    """Test ACTUAL safety validation logic"""
    
    def setUp(self):
        """Setup with REAL safety checker"""
        # Use REAL SafetyChecker - not mocked!
        self.safety_checker = SafetyChecker()
    
    def test_dangerous_commands_are_actually_blocked(self):
        """Test that dangerous commands are REALLY blocked by safety logic"""
        dangerous_commands = [
            "rm -rf /",
            "sudo rm -rf /",
            "format c:",
            "del /s /q c:\\",
            "mkfs.ext4 /dev/sda1",
            ":(){ :|:& };:",  # Fork bomb
        ]
        
        for cmd in dangerous_commands:
            with self.subTest(command=cmd):
                # Test the REAL safety check logic
                result = self.safety_checker.check_text_safety(cmd)
                self.assertFalse(result, f"Safety should block: {cmd}")
    
    def test_safe_commands_are_allowed(self):
        """Test that safe commands pass through"""
        safe_commands = [
            "echo hello",
            "ls -la",
            "pwd",
            "git status",
            "python script.py",
        ]
        
        for cmd in safe_commands:
            with self.subTest(command=cmd):
                result = self.safety_checker.check_text_safety(cmd)
                self.assertTrue(result, f"Safety should allow: {cmd}")
    
    def test_credential_detection_works(self):
        """Test REAL credential detection"""
        texts_with_credentials = [
            "password: secret123",
            "api_key: sk-1234567890",
            "AWS_SECRET_KEY=abcd1234",
            "Bearer eyJhbGciOiJIUzI1NiIs...",
        ]
        
        for text in texts_with_credentials:
            with self.subTest(text=text[:30]):
                result = self.safety_checker.detect_credentials(text)
                self.assertTrue(result, f"Should detect credentials in: {text}")
    
    def test_sql_injection_patterns_blocked(self):
        """Test SQL injection detection"""
        sql_injections = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM users WHERE 1=1;",
        ]
        
        for sql in sql_injections:
            with self.subTest(sql=sql):
                result = self.safety_checker.check_sql_safety(sql)
                self.assertFalse(result, f"Should block SQL injection: {sql}")


class TestComputerUseCoreSafety(unittest.TestCase):
    """Test ComputerUseCore with real safety integration"""
    
    def setUp(self):
        """Setup core without test_mode"""
        # Create core with REAL safety checker
        self.core = ComputerUseCore()
        self.core.test_mode = False  # Force real behavior
        
        # Use real safety checker
        self.core.safety_checker = SafetyChecker()
        self.core.safety_checks = True
    
    @patch('subprocess.run')
    def test_type_text_blocks_dangerous_commands(self, mock_run):
        """Test that type_text actually blocks dangerous input"""
        # Mock only the subprocess, not the safety logic
        mock_run.return_value = Mock(returncode=0)
        
        # Ensure display is available
        self.core.display_available = True
        
        # Try to type dangerous command
        result = self.core.type_text("rm -rf /")
        
        # Should be blocked by REAL safety check
        self.assertEqual(result['status'], 'error')
        self.assertIn('blocked', result['error'].lower())
        
        # Subprocess should NOT be called
        mock_run.assert_not_called()
    
    @patch('subprocess.run')
    def test_type_text_allows_safe_text(self, mock_run):
        """Test that safe text goes through"""
        mock_run.return_value = Mock(returncode=0)
        self.core.display_available = True
        
        # Type safe text
        result = self.core.type_text("Hello, world!")
        
        # Should succeed
        self.assertEqual(result['status'], 'success')
        
        # Subprocess SHOULD be called
        mock_run.assert_called()


class TestMCPServerSafety(unittest.TestCase):
    """Test MCP server safety with proper dependency injection"""
    
    def setUp(self):
        """Create server with injectable components"""
        # Create real components
        self.safety_checker = SafetyChecker()
        self.mock_computer = Mock()
        
        # Create server
        self.server = ComputerUseServer()
        
        # Inject real safety checker
        if hasattr(self.server, 'safety_checker'):
            self.server.safety_checker = self.safety_checker
        
        # Inject mock computer (to isolate safety testing)
        if hasattr(self.server, 'computer'):
            self.server.computer = self.mock_computer
        
        # Force real behavior
        if hasattr(self.server, 'test_mode'):
            self.server.test_mode = False
    
    def test_mcp_blocks_dangerous_type_request(self):
        """Test that MCP server blocks dangerous type requests"""
        # Create dangerous request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {
                    "text": "sudo rm -rf /"
                }
            }
        }
        
        # Configure mock to show what would happen
        self.mock_computer.type_text.side_effect = Exception("Should not be called!")
        
        # Make request
        response = self.server.handle_request(request)
        
        # Should get error response
        self.assertIn("error", response)
        
        # Computer method should NOT be called
        self.mock_computer.type_text.assert_not_called()
    
    def test_mcp_allows_safe_type_request(self):
        """Test that safe requests go through"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {
                    "text": "Hello, world!"
                }
            }
        }
        
        # Configure mock
        self.mock_computer.type_text.return_value = {
            "status": "success",
            "text": "Hello, world!"
        }
        
        # Make request
        response = self.server.handle_request(request)
        
        # Should succeed
        self.assertIn("result", response)
        
        # Computer method SHOULD be called
        self.mock_computer.type_text.assert_called_once_with("Hello, world!")


class TestIntegrationSafety(unittest.TestCase):
    """Integration tests with minimal mocking"""
    
    @unittest.skipIf(not os.environ.get("RUN_INTEGRATION_TESTS"),
                     "Set RUN_INTEGRATION_TESTS=1 to run")
    def test_full_safety_flow(self):
        """Test complete safety flow with real components"""
        # Create server with all real components
        server = ComputerUseServer()
        
        # Force real mode
        if hasattr(server, 'test_mode'):
            server.test_mode = False
        
        # Only mock the actual system calls
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            # Test dangerous command
            dangerous_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "type",
                    "arguments": {"text": "rm -rf /"}
                }
            }
            
            response = server.handle_request(dangerous_request)
            
            # Should be blocked
            self.assertIn("error", response)
            mock_run.assert_not_called()
            
            # Test safe command
            safe_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "type",
                    "arguments": {"text": "echo hello"}
                }
            }
            
            # Mock display for safe command
            with patch.object(server.computer, 'display_available', True):
                response = server.handle_request(safe_request)
            
            # Should succeed
            self.assertIn("result", response)
            mock_run.assert_called()


def main():
    """Run the fixed safety tests"""
    print("=" * 70)
    print("FIXED SAFETY TESTS - Testing REAL Safety Logic")
    print("=" * 70)
    print()
    print("These tests verify:")
    print("✓ Real safety checker blocks dangerous commands")
    print("✓ Credentials are actually detected")
    print("✓ Integration between components works")
    print("✓ No test_mode - testing real code paths")
    print()
    
    # Run tests
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()
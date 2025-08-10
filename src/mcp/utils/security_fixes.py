"""
Security utilities for MCP package
"""

import shlex
import subprocess
import tempfile
import os
from typing import List, Dict, Any, Tuple

# Security constants
SECURE_FILE_PERMISSIONS = 0o600
SECURE_DIR_PERMISSIONS = 0o700


class SecureSubprocess:
    """Secure subprocess execution with input validation"""

    @staticmethod
    def escape_shell_arg(arg: str) -> str:
        """Safely escape shell arguments"""
        return shlex.quote(str(arg))

    @staticmethod
    def validate_command(cmd: List[str]) -> bool:
        """Validate command is safe to execute"""
        dangerous_patterns = [
            ';', '|', '&', '$', '`', '\\', '\n', '\r',
            '$(', '${', '<(', '>(', '>>', '<<'
        ]

        cmd_str = ' '.join(cmd)
        for pattern in dangerous_patterns:
            if pattern in cmd_str:
                raise ValueError(f"Dangerous pattern '{pattern}' in command")

        return True

    @staticmethod
    def run_safe(cmd: List[str], timeout: int = 30, **kwargs) -> subprocess.CompletedProcess:
        """Safely run subprocess with validation"""
        # Validate command
        SecureSubprocess.validate_command(cmd)

        # Set secure defaults
        kwargs.setdefault('timeout', timeout)
        kwargs.setdefault('shell', False)
        kwargs.setdefault('capture_output', True)
        kwargs.setdefault('text', True)

        # Run with resource limits
        return subprocess.run(cmd, **kwargs)


class SecureInputHandler:
    """Secure input handling with validation"""

    @staticmethod
    def validate_coordinates(x: Any, y: Any) -> Tuple[int, int]:
        """Validate and sanitize coordinates"""
        try:
            x = int(x)
            y = int(y)
        except (ValueError, TypeError):
            raise ValueError("Coordinates must be integers")

        # Bounds checking
        if x < 0 or y < 0:
            raise ValueError("Coordinates must be non-negative")

        if x > 10000 or y > 10000:  # Reasonable screen size limit
            raise ValueError("Coordinates exceed screen bounds")

        return x, y

    @staticmethod
    def validate_text_input(text: str, max_length: int = 10000) -> str:
        """Validate and sanitize text input"""
        if not isinstance(text, str):
            raise TypeError("Text must be a string")

        if len(text) > max_length:
            raise ValueError(f"Text exceeds maximum length of {max_length}")

        # Remove null bytes and other dangerous characters
        text = text.replace('\x00', '')

        return text

    @staticmethod
    def validate_key_input(key: str) -> str:
        """Validate keyboard key input"""
        if not isinstance(key, str):
            raise TypeError("Key must be a string")

        # Limit key length
        if len(key) > 50:
            raise ValueError("Key name too long")

        # Basic validation - alphanumeric, function keys, modifiers
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-')
        if not all(c in allowed_chars for c in key.replace(' ', '')):
            raise ValueError("Invalid characters in key")

        return key


class SecureXdotoolWrapper:
    """Secure wrapper for xdotool commands"""

    @staticmethod
    def type_text(text: str) -> Dict[str, Any]:
        """Safely type text using xdotool"""
        # Validate input
        text = SecureInputHandler.validate_text_input(text)

        # Use xdotool directly with properly escaped text
        # Create a temporary secure method without using pipes
        try:
            # Write text to secure temp file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                tmp.write(text)
                tmp_path = tmp.name

            # Set secure permissions
            os.chmod(tmp_path, SECURE_FILE_PERMISSIONS)

            # Use xdotool to type from file
            cmd = ['xdotool', 'type', '--clearmodifiers', '--file', tmp_path]

            result = SecureSubprocess.run_safe(cmd, timeout=10)

            # Cleanup temp file
            os.unlink(tmp_path)

            return {
                'success': result.returncode == 0,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def key_press(key: str) -> Dict[str, Any]:
        """Safely press a key using xdotool"""
        # Validate input
        key = SecureInputHandler.validate_key_input(key)

        try:
            cmd = ['xdotool', 'key', '--clearmodifiers', key]
            result = SecureSubprocess.run_safe(cmd, timeout=5)

            return {
                'success': result.returncode == 0,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def mouse_move(x: int, y: int) -> Dict[str, Any]:
        """Safely move mouse using xdotool"""
        # Validate coordinates
        x, y = SecureInputHandler.validate_coordinates(x, y)

        try:
            cmd = ['xdotool', 'mousemove', str(x), str(y)]
            result = SecureSubprocess.run_safe(cmd, timeout=5)

            return {
                'success': result.returncode == 0,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def mouse_click(button: str = 'left') -> Dict[str, Any]:
        """Safely click mouse button using xdotool"""
        # Map button names
        button_map = {
            'left': '1',
            'middle': '2',
            'right': '3'
        }
        button_num = button_map.get(button.lower(), '1')

        try:
            cmd = ['xdotool', 'click', button_num]
            result = SecureSubprocess.run_safe(cmd, timeout=5)

            return {
                'success': result.returncode == 0,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
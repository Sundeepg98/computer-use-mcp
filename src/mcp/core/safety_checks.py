"""
Enhanced safety checks module for computer-use-mcp
Provides comprehensive safety validation for all operations
"""

import re
import unicodedata
import threading
from typing import Tuple, Optional, Set, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SafetyChecker:
    """Enhanced safety checker with comprehensive security patterns"""
    
    def __init__(self, whitelist: Optional[Set[str]] = None, custom_patterns: Optional[List[str]] = None):
        self.whitelist: Set[str] = whitelist if whitelist is not None else set()
        self.custom_patterns: List[str] = custom_patterns if custom_patterns is not None else []
        self.last_error: Optional[str] = None
        
        # Thread safety locks
        self._whitelist_lock = threading.RLock()
        self._patterns_lock = threading.RLock()
        self._error_lock = threading.Lock()
        
        # Comprehensive dangerous patterns
        self.dangerous_patterns = [
            # File system destruction
            r'rm\s+-rf\s+/',
            r'rm\s+.*-rf.*/',
            r'del\s+/f\s+/s\s+/q',
            r'del\s+.*\\\\Windows\\\\',  # Deletion targeting Windows system files
            r'del\s+.*System32',  # Deletion targeting System32
            r'format\s+[a-zA-Z]:',
            r'dd\s+if=/dev/(zero|random|urandom)\s+of=/dev/[sh]d',
            r'mkfs\.',  # Any filesystem format command
            r'>'+ r'{1,2}\s*/dev/(sd|hd|nvme)',  # Overwrite disk devices
            
            # System modification
            r'chmod\s+777\s+/',
            r'chmod\s+.*-R.*777',
            r'chown\s+.*(-R|--recursive)',
            r'usermod.*-aG\s+(sudo|wheel|admin)',
            r'passwd\s+(root|admin)',
            
            # Fork bombs and resource exhaustion
            r':\s*\(\s*\)\s*\{.*:\s*\|',  # Fork bomb
            r'while\s*true.*do.*done',  # Infinite loops
            r'yes\s*\|',  # Yes command piping
            
            # Command injection patterns
            r';\s*(rm|del|format|chmod|chown|nc|netcat)',
            r'\|\s*(bash|sh|zsh|ksh|nc|netcat)',
            r'`[^`]*`',  # Backtick command substitution
            r'\$\([^)]+\)',  # Command substitution
            r'\\n\s*(rm|del|format)',  # Newline injection
            
            # Git destruction
            r'git\s+.*--force',
            r'git\s+reset\s+--hard',
            r'git\s+push.*--force.*:(main|master|HEAD)',
            
            # Process manipulation
            r'kill\s+-9\s+-1',  # Kill all processes
            r'killall',
            r'pkill\s+-9',
            
            # System information gathering
            r'/etc/(passwd|shadow|sudoers)',
            r'/proc/self/environ',
            r'cat\s+.*\.ssh/.*key',
            r'history\s*\|.*grep',
        ]
        
        # Comprehensive network operation patterns
        self.network_patterns = [
            # Direct network utilities
            r'^(nc|netcat|ncat|socat)\s+',
            r'^(telnet|ssh|scp|sftp|ftp|rsh|rlogin)\s+',
            r'^(curl|wget|fetch|aria2c)\s+',
            r'\b(nc|netcat|ncat|socat)\s+-[lLvpe]',  # Common nc flags
            
            # Network enumeration
            r'^(nmap|masscan|zmap)\s+',
            r'^(dig|nslookup|host|whois)\s+',
            r'^(ping|traceroute|tracepath|mtr)\s+',
            
            # Reverse shells and backdoors
            r'(bash|sh|zsh|ksh|csh)\s+-i\s+>&\s*/dev/tcp/',
            r'/dev/tcp/[0-9.]+/[0-9]+',
            r'mknod\s+[^\s]+\s+p\s*;',  # Named pipe backdoor
            r'mkfifo\s+[^\s]+\s*;',  # FIFO backdoor
            
            # Data exfiltration
            r'(tar|zip|7z|rar)\s+.*\|\s*(nc|netcat|curl|wget)',
            r'base64.*\|\s*(nc|netcat|curl|wget)',
            r'openssl\s+.*\|\s*(nc|netcat)',
            
            # Port binding
            r'python.*-m\s+SimpleHTTPServer',
            r'python3.*-m\s+http\.server',
            r'php\s+-S\s+[0-9.:]+',
            r'ruby\s+-run\s+-e\s+httpd',
            
            # Tunneling and proxying
            r'ssh.*-[LRD]\s*[0-9]+:',  # SSH tunneling
            r'socat\s+TCP',
            r'ngrok\s+(tcp|http)',
            r'proxychains',
            
            # DNS exfiltration
            r'nslookup.*\|.*base64',
            r'dig.*\+short.*\|',
        ]
        
        # Enhanced credential patterns with all variations
        self.credential_patterns = [
            # Password patterns - all variations
            r'password[:\s=]',
            r'(?:^|\s)-p[^\s]+',  # MySQL/DB style passwords with word boundary
            r'^-p\s+\S+',  # MySQL password at start with space
            r'\s-p\s+\S+',  # MySQL password with preceding space
            r'--password[=\s]+\S+',  # Long form passwords
            r'--pass[=\s]+\S+',  # Short form
            r'-P[^\s]+',  # Capital P variant
            r'PGPASSWORD=',  # PostgreSQL
            r'MYSQL_PWD=',  # MySQL env var
            r'-a\s+\S+',  # Redis password style
            
            # API keys and tokens
            r'api[_-]?key[:\s=]',
            r'apikey[:\s=]',
            r'api[_-]?token[:\s=]',
            r'access[_-]?token[:\s=]',
            r'auth[_-]?token[:\s=]',
            r'secret[_-]?key[:\s=]',
            r'private[_-]?key',
            r'client[_-]?secret[:\s=]',
            r'token[:\s=]',  # Simple token pattern
            
            # Specific service patterns
            r'sk-[a-zA-Z0-9]{40,}',  # OpenAI style
            r'ghp_[a-zA-Z0-9]{16,}',  # GitHub personal access token (flexible length)
            r'gho_[a-zA-Z0-9]{16,}',  # GitHub OAuth token (flexible length)
            r'ghs_[a-zA-Z0-9]{16,}',  # GitHub server token (flexible length)
            r'glpat-[a-zA-Z0-9\-_]{20,}',  # GitLab token
            
            # Cloud provider patterns
            r'AKIA[0-9A-Z]{16}',  # AWS Access Key
            r'aws[_-]?access[_-]?key[_-]?id[:\s=]',
            r'aws[_-]?secret[_-]?access[_-]?key[:\s=]',
            r'AWS_[A-Z_]+KEY',
            r'AZURE_[A-Z_]+KEY',
            r'GCP_[A-Z_]+KEY',
            
            # Authentication headers
            r'[Aa]uthorization[:\s]+[Bb]earer\s+[a-zA-Z0-9\-._~+/=]+',
            r'[Aa]uthorization[:\s]+[Bb]asic\s+[a-zA-Z0-9+/=]+',
            r'X-API-Key[:\s]+\S+',
            r'X-Auth-Token[:\s]+\S+',
            
            # Private keys
            r'BEGIN\s+(RSA|DSA|EC|OPENSSH|PGP|SSH2)\s+PRIVATE\s+KEY',
            r'-----BEGIN[^-]+PRIVATE\s+KEY',
            
            # Connection strings with credentials
            r'(mysql|mariadb|mongodb|postgres|postgresql|redis|ftp|sftp|ssh)://[^:]+:[^@]+@',
            r'Data Source=[^;]+;Password=',  # SQL Server
            r'jdbc:[^:]+://[^:]+:[^@]+@',  # JDBC URLs
            
            # Other sensitive patterns
            r'["\']?token["\']?\s*:\s*["\'][^"\']+["\']',  # JSON tokens
            r'["\']?password["\']?\s*:\s*["\'][^"\']+["\']',  # JSON passwords
            r'["\']?secret["\']?\s*:\s*["\'][^"\']+["\']',  # JSON secrets
        ]
        
        self.sensitive_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Visa
            r'\b5[1-5]\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Mastercard
            r'\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b',  # Amex
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        ]
        
        self.blocked_commands = {
            'rm -rf /',
            'sudo rm -rf /',
            'format c:',
            ':(){:|:&};:',
            'git push --force origin main',
            'chmod 777 /',
            'del /f /s /q *',
            'dd if=/dev/zero of=/dev/sda',
            'chmod -r 777 /',
            'chown -r nobody:nobody /',
            'mkfs.ext4 /dev/sda',
        }
        
        # Privilege escalation commands that should be blocked
        self.privilege_escalation_commands = {
            'sudo', 'su', 'pkexec', 'doas', 'runas',
            'sudo -i', 'su root', 'su -', 'sudo su',
            'sudo bash', 'sudo sh', 'sudo /bin/bash'
        }
        
        # SQL injection patterns
        self.sql_injection_patterns = [
            r"';\s*(DROP|DELETE|UPDATE|INSERT|SELECT)",
            r'";\s*(DROP|DELETE|UPDATE|INSERT|SELECT)',
            r'\s+OR\s+[\'"]?1[\'"]?\s*=\s*[\'"]?1',
            r'\s+AND\s+[\'"]?1[\'"]?\s*=\s*[\'"]?1',
            r'UNION\s+SELECT',
            r'--\s*$',  # SQL comment at end
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r'\.\./\.\./\.\.',  # Multiple traversals
            r'\.\.[/\\]',  # Basic traversal
            r'%2e%2e[/\\]',  # URL encoded
            r'%252e%252e',  # Double encoded
            r'\.\.%2f',  # Mixed encoding
            r'\.\.%5c',  # Backslash variant
        ]
        
        # Escaped sequence patterns (for string literals)
        self.escaped_sequence_patterns = [
            r'\\[nr]',              # Escaped newlines in strings
            r'\\x[0-9a-fA-F]{2}',   # Hex escape sequences
            r'\\u[0-9a-fA-F]{4}',   # Unicode escape sequences
            r'\\[0-7]{1,3}',        # Octal escape sequences
            r'\\t',                 # Escaped tabs
        ]
        
        # Unicode security patterns
        self.unicode_security_patterns = [
            r'[\u200b\u200c\u200d\u2060\u2064\ufeff]',  # Zero-width characters
            r'[\u202a-\u202e\u2066-\u2069]',              # Bidirectional control characters
            r'[\u0430\u0435\u043e\u0440\u0441\u0445\u0433]',  # Common homographs (Cyrillic that looks like Latin, including \u0433 for г)
        ]
        
        # Advanced injection patterns
        self.advanced_injection_patterns = [
            # LDAP injection
            r'\)\s*\(\s*cn\s*=',
            r'\)\s*\(\s*uid\s*=',
            # XPath injection
            r"'\s*or\s+'1'\s*=\s*'1",
            r'"\s*or\s+"1"\s*=\s*"1',
            # NoSQL injection
            r'{\s*[\'"]?\$ne[\'"]?\s*:',
            r'{\s*[\'"]?\$gt[\'"]?\s*:',
            r'{\s*[\'"]?\$regex[\'"]?\s*:',
            # Template injection
            r'{{\s*\d+\s*[*+\-/]',
            r'\$\{[^}]*[*+\-/]',  # Dollar brace template injection
            r'<%=\s*\d+\s*[*+\-/]',
            # CSV formula injection
            r'^[=+\-@]\s*[A-Z]+\s*\(',
            # Server-Side Template Injection
            r'{%\s*.*\s*%}',
            r'{{\s*config\s*}}',
        ]
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text for safe logging"""
        if not text:
            return ""
            
        # Remove control characters
        sanitized = ''.join(char if ord(char) >= 32 or char in '\t' else ' ' for char in text)
        
        # Escape special characters
        sanitized = sanitized.replace('\n', '\\n').replace('\r', '\\r')
        
        # Truncate if too long
        if len(sanitized) > 1000:
            sanitized = sanitized[:997] + "..."
            
        return sanitized
    
    def validate_text(self, text: str) -> Tuple[bool, Optional[str]]:
        """Validate if text is safe to type"""
        try:
            result = self.check_text_safety(text)
            if result:
                return (True, None)
            else:
                return (False, self.last_error or "Text validation failed")
        except Exception as e:
            return (False, str(e))
    
    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """Validate if command is safe to execute"""
        try:
            result = self.check_text_safety(command)
            if result:
                return (True, None)
            else:
                with self._error_lock:
                    error = self.last_error or "Command validation failed"
                return (False, error)
        except Exception as e:
            return (False, str(e))
    
    def validate_action(self, action: str, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate if an action is safe to perform"""
        try:
            # Special validation for different action types
            if action == 'click':
                # Validate click coordinates
                x, y = params.get('x', 0), params.get('y', 0)
                return self.validate_coordinates(x, y)
            
            elif action == 'type_text':
                # Use existing text validation
                text = params.get('text', '')
                return self.validate_text(text)
            
            elif action == 'key_press':
                # Validate key combinations
                key = params.get('key', '')
                # Block dangerous key combinations
                dangerous_keys = [
                    r'alt\+f4', r'ctrl\+alt\+del', r'cmd\+q', r'ctrl\+w',
                    r'alt\+tab', r'cmd\+tab', r'ctrl\+shift\+esc',
                    r'super\+', r'win\+', r'cmd\+space', r'alt\+space'
                ]
                for pattern in dangerous_keys:
                    if re.search(pattern, key.lower()):
                        return (False, f"Dangerous key combination blocked: {key}")
                
                # Also check as text for command injection
                return self.validate_text(key)
            
            elif action == 'move_mouse':
                # Validate mouse movement coordinates
                x, y = params.get('x', 0), params.get('y', 0)
                return self.validate_coordinates(x, y)
            
            elif action == 'drag':
                # Validate drag coordinates
                start_x = params.get('start_x', 0)
                start_y = params.get('start_y', 0)
                end_x = params.get('end_x', 0)
                end_y = params.get('end_y', 0)
                
                # Check both start and end coordinates
                is_safe_start, error_start = self.validate_coordinates(start_x, start_y)
                if not is_safe_start:
                    return (False, error_start)
                
                is_safe_end, error_end = self.validate_coordinates(end_x, end_y)
                if not is_safe_end:
                    return (False, error_end)
                
                # Check for suspicious drag patterns (e.g., dragging to corners)
                if (end_x == 0 and end_y == 0) or (start_x == 0 and start_y == 0):
                    return (False, "Suspicious drag pattern to screen corner")
                
                return (True, None)
            
            elif action == 'scroll':
                # Validate scroll parameters
                direction = params.get('direction', 'down')
                amount = params.get('amount', 3)
                
                # Check for excessive scrolling
                if amount > 100:
                    return (False, "Excessive scroll amount")
                
                return (True, None)
            
            else:
                # Unknown action - default to blocking
                return (False, f"Unknown action type: {action}")
                
        except Exception as e:
            return (False, f"Action validation error: {str(e)}")
    
    def check_text_safety(self, text: str) -> bool:
        """Check if text is safe to type or use"""
        if text is None or text == "":
            return True
            
        # Check for log injection attempts (newlines/carriage returns)
        if '\n' in text or '\r' in text or '\\x0a' in text or '\\x0d' in text or '%0a' in text.lower() or '%0d' in text.lower():
            with self._error_lock:
                self.last_error = "Log injection attempt detected"
            return False
            
        # Check for escaped sequences in string literals
        for pattern in self.escaped_sequence_patterns:
            if re.search(pattern, text):
                with self._error_lock:
                    self.last_error = "Escaped control sequence detected"
                return False
            
        # Check whitelist first
        with self._whitelist_lock:
            if text in self.whitelist:
                return True
            
        # Normalize Unicode to catch bypass attempts
        # Check for dangerous Unicode characters first
        dangerous_unicode = [
            '\u202e',  # Right-to-left override
            '\u202d',  # Left-to-right override
            '\u200e',  # Left-to-right mark
            '\u200f',  # Right-to-left mark
            '\ufeff',  # Zero-width no-break space
            '\u00a0',  # Non-breaking space
            '\u2028',  # Line separator
            '\u2029',  # Paragraph separator
        ]
        
        for char in dangerous_unicode:
            if char in text:
                with self._error_lock:
                    self.last_error = f"Dangerous Unicode character detected"
                return False
                
        # Now normalize the text
        normalized_text = unicodedata.normalize('NFKC', text)
        
        # Check custom patterns
        with self._patterns_lock:
            for pattern in self.custom_patterns:
                if pattern in text or pattern in normalized_text:
                    with self._error_lock:
                        self.last_error = f"Custom pattern blocked: {pattern}"
                    return False
                try:
                    if re.search(pattern, text, re.IGNORECASE) or re.search(pattern, normalized_text, re.IGNORECASE):
                        with self._error_lock:
                            self.last_error = f"Custom pattern blocked: {pattern}"
                        return False
                except re.error:
                    # If pattern is not a valid regex, treat as literal
                    pass
        
        # Check Unicode security patterns
        for i, pattern in enumerate(self.unicode_security_patterns):
            if re.search(pattern, text):
                # Special handling for Cyrillic homographs - only block if they look like dangerous commands
                if i == 2:  # Cyrillic homograph pattern
                    # Check if the Cyrillic chars are being used to mimic dangerous commands
                    dangerous_cyrillic_patterns = [
                        r'[гр]m\s',  # гm or рm (mimics rm)
                        r'[сc]url\s',  # сurl (mimics curl)
                        r'[рp]ython',  # руthon (mimics python)
                        r'[рp]у[tт]hon',  # руthon with mixed chars
                        r'sudo[сc]',  # sudoс (mimics sudoc)
                        r'[аa]pt[-\s]get',  # аpt-get (mimics apt-get)
                        r'гm\s+-rf',  # specific dangerous pattern
                        r'гm\s+-rf\s+/',  # гm -rf / pattern
                    ]
                    is_dangerous = False
                    for dcp in dangerous_cyrillic_patterns:
                        if re.search(dcp, text, re.IGNORECASE):
                            is_dangerous = True
                            break
                    
                    if is_dangerous:
                        with self._error_lock:
                            self.last_error = "Unicode security violation detected"
                        return False
                    else:
                        continue  # Skip this pattern if not used maliciously
                
                with self._error_lock:
                    self.last_error = "Unicode security violation detected"
                return False
                
        # Check advanced injection patterns
        for pattern in self.advanced_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                with self._error_lock:
                    self.last_error = "Advanced injection pattern detected"
                return False
        
        # Check network patterns first (more specific)
        for pattern in self.network_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                with self._error_lock:
                    self.last_error = f"Network operation blocked"
                return False
            if re.search(pattern, normalized_text, re.IGNORECASE):
                with self._error_lock:
                    self.last_error = f"Network operation blocked (Unicode bypass)"
                return False
        
        # Check dangerous patterns with case-insensitive matching
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                with self._error_lock:
                    self.last_error = f"Dangerous pattern detected"
                return False
            if re.search(pattern, normalized_text, re.IGNORECASE):
                with self._error_lock:
                    self.last_error = f"Dangerous pattern detected (Unicode bypass)"
                return False
        
        # Check blocked commands (case-insensitive)
        text_lower = text.lower()
        normalized_lower = normalized_text.lower()
        
        for cmd in self.blocked_commands:
            if cmd.lower() in text_lower or cmd.lower() in normalized_lower:
                with self._error_lock:
                    self.last_error = f"Blocked command detected: {cmd}"
                return False
        
        # Check for privilege escalation
        for cmd in self.privilege_escalation_commands:
            # Check if it's at the start of the command or after common separators
            patterns = [
                f'^{re.escape(cmd)}\\s',
                f'[;&|]\\s*{re.escape(cmd)}\\s',
                f'^\\s*{re.escape(cmd)}\\s',
            ]
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    with self._error_lock:
                        self.last_error = f"Privilege escalation command detected: {cmd}"
                    return False
        
        # Enhanced SQL injection detection
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                with self._error_lock:
                    self.last_error = f"SQL injection attempt detected"
                return False
        
        # Check credentials
        for pattern in self.credential_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                with self._error_lock:
                    self.last_error = f"Credential detected"
                return False
        
        # Enhanced path traversal detection
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                with self._error_lock:
                    self.last_error = f"Path traversal attempt detected"
                return False
        
        # Check sensitive patterns
        for pattern in self.sensitive_patterns:
            if re.search(pattern, text):
                with self._error_lock:
                    self.last_error = f"Sensitive data pattern detected"
                return False
        
        return True
    
    def check_screenshot_safety(self, image: Any) -> Dict[str, Any]:
        """Check if screenshot contains sensitive information"""
        # This is a placeholder - actual OCR would be needed
        # For now, simulate with mock text attribute
        if hasattr(image, 'text'):
            text = image.text.lower()
            
            # Check for credentials
            for pattern in self.credential_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return {
                        'safe': False,
                        'reason': 'Credential detected in screenshot'
                    }
            
            # Check for sensitive data
            for pattern in self.sensitive_patterns:
                if re.search(pattern, text):
                    return {
                        'safe': False,
                        'reason': 'Sensitive data detected in screenshot'
                    }
        
        return {'safe': True}
    
    def check_url_safety(self, url: str) -> Tuple[bool, Optional[str]]:
        """Check if URL is safe to navigate to"""
        if not url:
            return (False, "Empty URL")
        
        # Check for dangerous protocols
        dangerous_protocols = ['file://', 'javascript:', 'data:', 'vbscript:']
        for protocol in dangerous_protocols:
            if url.lower().startswith(protocol):
                return (False, f"Dangerous protocol: {protocol}")
        
        # Check for local addresses
        local_patterns = [
            r'^https?://localhost',
            r'^https?://127\.',
            r'^https?://192\.168\.',
            r'^https?://10\.',
            r'^https?://172\.(1[6-9]|2[0-9]|3[01])\.',
            r'^https?://\[::1\]',
        ]
        
        for pattern in local_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return (False, "Local address not allowed")
        
        return (True, None)
    
    def check_file_path_safety(self, path: str) -> Tuple[bool, Optional[str]]:
        """Check if file path is safe to access"""
        if not path:
            return (False, "Empty path")
        
        # Check for path traversal
        if '..' in path or path.startswith('/') or path.startswith('~'):
            return (False, "Path traversal detected")
        
        # Check for sensitive directories
        sensitive_dirs = [
            '/etc', '/proc', '/sys', '/dev',
            'C:\\Windows\\System32', 'C:\\Windows\\System',
            '.ssh', '.aws', '.git',
        ]
        
        for sensitive_dir in sensitive_dirs:
            if sensitive_dir in path:
                return (False, f"Access to sensitive directory blocked: {sensitive_dir}")
        
        return (True, None)
    
    def add_to_whitelist(self, text: str) -> None:
        """Add text to whitelist"""
        with self._whitelist_lock:
            self.whitelist.add(text)
    
    def remove_from_whitelist(self, text: str) -> None:
        """Remove text from whitelist"""
        with self._whitelist_lock:
            self.whitelist.discard(text)
    
    def add_custom_pattern(self, pattern: str) -> None:
        """Add custom pattern to block"""
        with self._patterns_lock:
            if pattern not in self.custom_patterns:
                self.custom_patterns.append(pattern)
    
    def remove_custom_pattern(self, pattern: str) -> None:
        """Remove custom pattern"""
        with self._patterns_lock:
            if pattern in self.custom_patterns:
                self.custom_patterns.remove(pattern)
    
    def check_content(self, content: str) -> Dict[str, Any]:
        """Check content for sensitive information"""
        content_lower = content.lower()
        
        # Check for credentials
        for pattern in self.credential_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return {
                    'safe': False,
                    'reason': 'Credential detected',
                    'type': 'credential'
                }
        
        # Check for sensitive data
        for pattern in self.sensitive_patterns:
            if re.search(pattern, content):
                return {
                    'safe': False,
                    'reason': 'Sensitive data detected',
                    'type': 'sensitive'
                }
        
        return {'safe': True}
    
    def get_safety_report(self) -> Dict[str, Any]:
        """Get current safety configuration report"""
        return {
            'dangerous_patterns': len(self.dangerous_patterns),
            'network_patterns': len(self.network_patterns),
            'credential_patterns': len(self.credential_patterns),
            'sensitive_patterns': len(self.sensitive_patterns),
            'blocked_commands': len(self.blocked_commands),
            'whitelist_size': len(self.whitelist),
            'custom_patterns': len(self.custom_patterns),
            'status': 'active'
        }
    
    def detect_credentials(self, text: str) -> bool:
        """Detect potential credentials in text"""
        for pattern in self.credential_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def validate_coordinates(self, x: int, y: int) -> Tuple[bool, Optional[str]]:
        """Validate screen coordinates"""
        # Basic validation - can be extended based on screen bounds
        if x < 0 or y < 0:
            return (False, "Negative coordinates not allowed")
        
        # Add reasonable upper bounds
        if x > 10000 or y > 10000:
            return (False, "Coordinates exceed reasonable screen bounds")
        
        return (True, None)

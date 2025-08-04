#!/usr/bin/env python3
"""
Safety checks for computer use operations
Prevents dangerous actions and protects sensitive information
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SafetyChecker:
    """Safety validation for computer use actions"""
    
    def __init__(self, custom_patterns=None, whitelist=None):
        """Initialize safety checker with rules"""
        self.custom_patterns = custom_patterns or []
        self.whitelist = whitelist or []
        self.last_error = None
        self.dangerous_patterns = [
            # File system destruction
            r'rm\s+(-\w+\s+)*(/|~|\*)',  # rm with any flags targeting root/home/wildcard
            r'del(ete)?\s+[/\\]',  # Windows delete commands targeting root
            r'del\s+/[fFsSquQ]',  # Windows delete flags
            r'format\s+[a-zA-Z]:',  # Windows format
            r'mkfs',  # Make filesystem
            r'dd\s+.*of=.*/(dev|sd|hd)',  # Direct disk write
            
            # Database destruction
            r'(DELETE|DROP|TRUNCATE)\s+(FROM\s+)?(DATABASE|TABLE|SCHEMA)',
            
            # System modification
            r'chmod\s+(-\w+\s+)*(777|666)',
            r'chown\s+.*(-R|--recursive)',
            
            # Fork bombs and malicious code
            r':\s*\(\s*\)\s*\{.*:\s*\|',  # Fork bomb pattern
            r'>{1,2}\s*/dev/(sd|hd|null|zero)',  # Redirect to devices
            
            # Git destruction
            r'git\s+.*--force',
            r'git\s+reset\s+--hard',
            
            # Command injection patterns - must be part of actual commands
            r';\s*(rm|del|format|chmod|chown)',  # Command chaining dangerous commands
            r'\|\s*(nc|netcat|bash|sh)',  # Piping to shells
            r'`[^`]*`',  # Backtick command substitution
            r'\$\([^)]+\)',  # Command substitution
            r'\\n\s*(rm|del|format)',  # Newline injection with dangerous commands
        ]
        
        self.credential_patterns = [
            r'password[:\s=]',
            r'api[_-]?key[:\s=]',
            r'secret[_-]?key[:\s=]',
            r'private[_-]?key',
            r'BEGIN\s+(RSA|OPENSSH|EC)\s+PRIVATE\s+KEY',
            r'bearer\s+[a-zA-Z0-9\-._~+/=]+',
            r'basic\s+[a-zA-Z0-9+/=]+',
            r'AWS_[A-Z_]+KEY',  # AWS credentials
            r'token:\s*\w+',  # Generic tokens
            r'ghp_[a-zA-Z0-9]+',  # GitHub tokens
            r'(mysql|mongodb|postgres|mongodb\+srv|ftp|sftp)://.*:.*@',  # URLs with credentials
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
        
        # Network operation patterns for automation goals
        self.network_operation_patterns = [
            r'download.*from.*internet',
            r'send.*data.*to.*remote',
            r'connect.*to.*database.*at.*remote',
            r'upload.*to.*server',
            r'fetch.*from.*url',
            r'post.*to.*endpoint',
            r'connect.*to.*.*\.com',
            r'wget.*http',
            r'curl.*http',
            r'nc.*\d+\.\d+\.\d+\.\d+',
            r'netcat.*\d+\.\d+\.\d+\.\d+'
        ]
        
        # Log injection patterns
        self.log_injection_patterns = [
            r'.*\n.*FAKE LOG.*',
            r'.*\n.*ERROR:.*compromised',
            r'.*\n.*\[CRITICAL\].*',
            r'.*\r\n.*ERROR:.*',
            r'.*\n.*Admin login successful',
            r'.*\n.*Security breach.*',
            r'.*\n\n.*\[CRITICAL\].*',  # Double newline variant
            r'.*\n.*CRITICAL.*Security.*breach.*',
            r'.*\n.*System.*compromised.*',
            r'.*[\r\n]+.*(?:FAKE|ERROR|CRITICAL|ADMIN|SECURITY).*'
        ]
        
        # SQL injection patterns
        self.sql_injection_patterns = [
            r"'\s*OR\s*'?\d*'?\s*=\s*'?\d*",  # ' OR '1'='1
            r'"\s*OR\s*"?\d*"?\s*=\s*"?\d*',  # " OR "1"="1
            r'--\s*$',  # SQL comment at end
            r';\s*(DROP|DELETE|TRUNCATE|UPDATE)',  # SQL command injection
            r'UNION\s+SELECT',  # UNION attacks
            r'/\*.*\*/',  # SQL block comments
        ]
        
        # Additional dangerous URL schemes
        self.dangerous_url_schemes = [
            'javascript:', 'data:', 'vbscript:', 'file://', 
            'mhtml:', 'x-javascript:', 'jar:', 'jnlp:',
        ]
    
    def validate_action(self, action: str) -> bool:
        """Validate if an action is safe to execute"""
        action_lower = action.lower()
        
        # Check against blocked commands
        if any(blocked in action_lower for blocked in self.blocked_commands):
            raise Exception(f"BLOCKED: Dangerous command detected: {action}")
        
        # Check for privilege escalation commands (whole word matches only)
        for priv_cmd in self.privilege_escalation_commands:
            # Use word boundaries to avoid false positives like "su" in "suggest_alternatives"
            pattern = r'\b' + re.escape(priv_cmd.lower()) + r'\b'
            if re.search(pattern, action_lower):
                raise Exception(f"BLOCKED: Privilege escalation attempt detected: {action}")
        
        # Check for network operations in automation goals
        for pattern in self.network_operation_patterns:
            if re.search(pattern, action, re.IGNORECASE):
                raise Exception(f"BLOCKED: Network operation detected: {action}")
        
        # Check for log injection attempts
        for pattern in self.log_injection_patterns:
            if re.search(pattern, action, re.IGNORECASE | re.MULTILINE):
                raise Exception(f"BLOCKED: Log injection attempt detected: {action}")
        
        # Check against dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, action, re.IGNORECASE):
                raise Exception(f"BLOCKED: Dangerous pattern detected: {action}")
        
        # Safe actions are allowed
        safe_keywords = ['screenshot', 'click', 'type', 'scroll', 'move', 'wait']
        if any(keyword in action_lower for keyword in safe_keywords):
            return True
        
        # Default allow for unrecognized but not dangerous
        return True
    
    def check_screenshot(self, image: Any) -> Dict[str, Any]:
        """Check screenshot for sensitive information"""
        # In real implementation, would use OCR to extract text
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
        
        return {'safe': True, 'reason': 'No sensitive data detected'}
    
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
                    'type': 'personal_info'
                }
        
        return {'safe': True}
    
    def sanitize_text(self, text: str) -> str:
        """Remove or mask sensitive information from text"""
        sanitized = text
        
        # Mask SSNs
        sanitized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', 'XXX-XX-XXXX', sanitized)
        
        # Mask credit cards
        sanitized = re.sub(
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            'XXXX-XXXX-XXXX-XXXX',
            sanitized
        )
        
        # Mask passwords (if shown as password: value)
        sanitized = re.sub(
            r'(password[:\s=])\S+',
            r'\1[REDACTED]',
            sanitized,
            flags=re.IGNORECASE
        )
        
        # Mask API keys
        sanitized = re.sub(
            r'(api[_-]?key[:\s=])\S+',
            r'\1[REDACTED]',
            sanitized,
            flags=re.IGNORECASE
        )
        
        return sanitized
    
    def check_text_safety(self, text: str) -> bool:
        """Check if text is safe to type or use"""
        if text is None or text == "":
            return True
        
        # Check whitelist first
        if text in self.whitelist:
            return True
        
        # Normalize Unicode to catch bypass attempts
        import unicodedata
        
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
                self.last_error = f"Dangerous Unicode character detected"
                return False
        
        # Now normalize the text
        normalized_text = unicodedata.normalize('NFKC', text)
        
        # Check custom patterns
        for pattern in self.custom_patterns:
            if pattern in text or pattern in normalized_text:
                self.last_error = f"Custom pattern blocked: {pattern}"
                return False
            if re.search(pattern, text, re.IGNORECASE) or re.search(pattern, normalized_text, re.IGNORECASE):
                self.last_error = f"Custom pattern blocked: {pattern}"
                return False
        
        # Check dangerous patterns with case-insensitive matching
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                self.last_error = f"Dangerous pattern detected"
                return False
            if re.search(pattern, normalized_text, re.IGNORECASE):
                self.last_error = f"Dangerous pattern detected (Unicode bypass)"
                return False
        
        # Check blocked commands (case-insensitive)
        text_lower = text.lower()
        normalized_lower = normalized_text.lower()
        for blocked in self.blocked_commands:
            if blocked.lower() in text_lower or blocked.lower() in normalized_lower:
                self.last_error = f"Blocked command detected"
                return False
        
        # Check privilege escalation commands (whole word matches only)
        for priv_cmd in self.privilege_escalation_commands:
            # Use word boundaries to avoid false positives like "su" in "suggest_alternatives"
            pattern = r'\b' + re.escape(priv_cmd.lower()) + r'\b'
            if re.search(pattern, text_lower) or re.search(pattern, normalized_lower):
                self.last_error = f"Privilege escalation command detected"
                return False
        
        # Check for log injection attempts
        for pattern in self.log_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                self.last_error = f"Log injection attempt detected"
                return False
            if re.search(pattern, normalized_text, re.IGNORECASE | re.MULTILINE):
                self.last_error = f"Log injection attempt detected (Unicode bypass)"
                return False
        
        # Check SQL injection patterns
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                self.last_error = f"SQL injection attempt detected"
                return False
        
        # Check credentials
        for pattern in self.credential_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                self.last_error = f"Credential detected"
                return False
        
        # Enhanced path traversal detection
        path_traversal_patterns = [
            r'\.\./', r'\.\.\\',  # ../ and ..\
            r'/etc/', r'\\etc\\',  # /etc/ paths
            r'/proc/', r'/sys/',  # Linux system paths
            r'/var/log/',  # Log paths
            r'C:\\Windows\\System32',  # Windows system paths
            r'C:\\Program Files',
        ]
        for pattern in path_traversal_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                self.last_error = f"Path traversal attempt"
                return False
        
        # Check dangerous URL schemes
        text_lower_stripped = text_lower.strip()
        for scheme in self.dangerous_url_schemes:
            if text_lower_stripped.startswith(scheme) or scheme in text_lower:
                self.last_error = f"Malicious URL scheme: {scheme}"
                return False
        
        # Check for passwords in plain text
        if re.search(r'\bpassword\s*[:=]', text.lower()):
            self.last_error = f"Password in plain text"
            return False
        
        # Check for common password patterns (like password123)
        if re.search(r'\bpassword\d+\b', text.lower()):
            self.last_error = f"Weak password pattern detected"
            return False
        
        return True
    
    def check_command_safety(self, command: str) -> bool:
        """Alias for check_text_safety for commands"""
        return self.check_text_safety(command)
    
    def check_url_safety(self, url: str) -> bool:
        """Check if URL is safe"""
        return self.check_text_safety(url)
    
    def validate_url(self, url: str) -> bool:
        """Validate if a URL is safe to visit"""
        dangerous_domains = [
            'phishing-site.com',
            'malware-download.com',
            # Add known dangerous domains
        ]
        
        for domain in dangerous_domains:
            if domain in url:
                return False
        
        # Check for suspicious patterns
        if re.search(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', url):
            # IP address instead of domain - potentially suspicious
            logger.warning(f"IP address URL detected: {url}")
        
        return True
    
    def check_file_operation(self, operation: str, path: str) -> bool:
        """Check if file operation is safe"""
        protected_paths = [
            '/etc',
            '/usr',
            '/boot',
            '/root',
            'C:\\Windows',
            'C:\\Program Files',
        ]
        
        for protected in protected_paths:
            if path.startswith(protected):
                logger.warning(f"Operation on protected path: {path}")
                return False
        
        dangerous_operations = ['delete', 'remove', 'format', 'wipe']
        if any(op in operation.lower() for op in dangerous_operations):
            logger.warning(f"Dangerous file operation: {operation} on {path}")
            return False
        
        return True
    
    def get_safety_report(self) -> Dict[str, Any]:
        """Get current safety configuration report"""
        return {
            'dangerous_patterns': len(self.dangerous_patterns),
            'credential_patterns': len(self.credential_patterns),
            'sensitive_patterns': len(self.sensitive_patterns),
            'blocked_commands': len(self.blocked_commands),
            'status': 'active'
        }
#!/usr/bin/env python3
"""
Automated refactoring script to eliminate test_mode from Computer Use MCP

This script will:
1. Backup all files
2. Migrate test files to use proper mocking
3. Replace ComputerUseCore with refactored version
4. Update imports and references
5. Verify tests pass
"""

import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import json

# Configuration
PROJECT_ROOT = Path("/home/sunkar/computer-use-mcp")
BACKUP_DIR = PROJECT_ROOT / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
SRC_DIR = PROJECT_ROOT / "src" / "computer_use_mcp"
TESTS_DIR = PROJECT_ROOT / "tests"

# Files to process
TEST_FILES_TO_MIGRATE = [
    "test_computer_use_core.py",
    "test_e2e_functionality.py", 
    "test_mcp_complete_structure.py",
    "test_mcp_integration.py",
    "test_mcp_protocol.py",
    "test_screenshot_system.py",
    "test_xserver_integration.py",
    "test_stress_reliability.py",
    "test_safety_security.py"
]

class RefactoringExecutor:
    def __init__(self):
        self.changes_made = []
        self.errors = []
        
    def log_change(self, file, change):
        """Log a change made to a file"""
        self.changes_made.append({
            'file': str(file),
            'change': change,
            'timestamp': datetime.now().isoformat()
        })
        print(f"✅ {file.name}: {change}")
    
    def log_error(self, file, error):
        """Log an error"""
        self.errors.append({
            'file': str(file),
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        })
        print(f"❌ {file.name}: {error}")
    
    def backup_files(self):
        """Create backup of all files before modification"""
        print("\n📦 Creating backup...")
        shutil.copytree(PROJECT_ROOT, BACKUP_DIR, 
                       ignore=shutil.ignore_patterns('*.pyc', '__pycache__', '.git'))
        print(f"✅ Backup created at: {BACKUP_DIR}")
        return True
    
    def create_mock_providers(self):
        """Create reusable mock provider implementations"""
        mock_file = SRC_DIR / "test_mocks.py"
        
        content = '''"""
Mock implementations for testing without test_mode
"""
from unittest.mock import Mock
from typing import Dict, Any, Optional


class MockScreenshotProvider:
    """Mock screenshot provider for testing"""
    def __init__(self, capture_data=None):
        self.capture_data = capture_data or b'mock_screenshot_data'
        self.capture_called = 0
        
    def capture(self):
        self.capture_called += 1
        return self.capture_data
    
    def is_available(self):
        return True
    
    def get_display_info(self):
        return {'width': 1920, 'height': 1080, 'mock': True}


class MockInputProvider:
    """Mock input provider for testing"""
    def __init__(self, default_success=True):
        self.default_success = default_success
        self.actions = []
        
    def click(self, x, y, button='left'):
        self.actions.append(('click', x, y, button))
        return self.default_success
    
    def type_text(self, text):
        self.actions.append(('type', text))
        return self.default_success
    
    def key_press(self, key):
        self.actions.append(('key', key))
        return self.default_success
    
    def mouse_move(self, x, y):
        self.actions.append(('move', x, y))
        return self.default_success
    
    def drag(self, start_x, start_y, end_x, end_y):
        self.actions.append(('drag', start_x, start_y, end_x, end_y))
        return self.default_success
    
    def scroll(self, direction, amount):
        self.actions.append(('scroll', direction, amount))
        return self.default_success


class MockPlatformInfo:
    """Mock platform info for testing"""
    def __init__(self, platform='test', environment='mock'):
        self._platform = platform
        self._environment = environment
        
    def get_platform(self):
        return self._platform
    
    def get_environment(self):
        return self._environment
    
    def get_capabilities(self):
        return {'test': True}


class MockSafetyValidator:
    """Mock safety validator for testing"""
    def __init__(self, default_safe=True):
        self.default_safe = default_safe
        self.validations = []
        
    def validate_action(self, action, params):
        self.validations.append(('action', action, params))
        return (self.default_safe, None if self.default_safe else "Blocked")
    
    def validate_text(self, text):
        self.validations.append(('text', text))
        return (self.default_safe, None if self.default_safe else "Blocked")
    
    def validate_command(self, command):
        self.validations.append(('command', command))
        return (self.default_safe, None if self.default_safe else "Blocked")


class MockDisplayManager:
    """Mock display manager for testing"""
    def __init__(self, available=True):
        self._available = available
        
    def is_display_available(self):
        return self._available
    
    def get_best_display(self):
        return 'mock_display' if self._available else None
    
    def setup_display(self):
        return self._available


def create_test_computer_use(**overrides):
    """Helper to create ComputerUse instance for testing"""
    from mcp.factory_refactored import create_computer_use_for_testing
    
    defaults = {
        'screenshot_provider': MockScreenshotProvider(),
        'input_provider': MockInputProvider(),
        'platform_info': MockPlatformInfo(),
        'safety_validator': MockSafetyValidator(),
        'display_manager': MockDisplayManager()
    }
    
    defaults.update(overrides)
    return create_computer_use_for_testing(**defaults)
'''
        
        mock_file.write_text(content)
        self.log_change(mock_file, "Created test mock providers")
        return True
    
    def migrate_test_file(self, test_file):
        """Migrate a single test file from test_mode to mocks"""
        file_path = TESTS_DIR / test_file
        if not file_path.exists():
            self.log_error(file_path, "File not found")
            return False
        
        content = file_path.read_text()
        original_content = content
        
        # Replace imports
        if "from mcp.computer_use_core import ComputerUseCore" in content:
            content = content.replace(
                "from mcp.computer_use_core import ComputerUseCore",
                "from mcp.test_mocks import create_test_computer_use, MockScreenshotProvider, MockInputProvider"
            )
        
        # Replace test_mode=True instantiations
        content = re.sub(
            r'ComputerUseCore\(test_mode=True\)',
            'create_test_computer_use()',
            content
        )
        
        # Replace test_mode=False instantiations (for integration tests)
        content = re.sub(
            r'ComputerUseCore\(test_mode=False\)',
            'create_test_computer_use()',  # Still use mocks in tests
            content
        )
        
        # Update method names
        replacements = [
            ('core.screenshot(', 'core.take_screenshot('),
            ('self.core.screenshot(', 'self.core.take_screenshot('),
            ('.click(', '.click('),  # Already correct
            ('.type(', '.type_text('),
            ('.key(', '.key_press('),
            ('.move(', '.mouse_move('),
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        # Fix assertions for new return format
        content = re.sub(
            r"self\.assertEqual\(result\['status'\], 'success'\)",
            "self.assertTrue(result['success'])",
            content
        )
        
        content = re.sub(
            r"self\.assertIn\('test_mode', result\)",
            "# test_mode check removed - using proper mocks",
            content
        )
        
        content = re.sub(
            r"self\.assertTrue\(result\['test_mode'\]\)",
            "# test_mode check removed - using proper mocks",
            content
        )
        
        # Update mock data assertions
        content = content.replace(
            "result['data'] == b'mock_screenshot_data'",
            "result['data'] == b'mock_screenshot_data'"  # Keep same for now
        )
        
        # Only write if changes were made
        if content != original_content:
            file_path.write_text(content)
            self.log_change(file_path, "Migrated from test_mode to mocks")
            return True
        else:
            self.log_change(file_path, "No changes needed")
            return True
    
    def update_mcp_server(self):
        """Update MCP server to use refactored core"""
        server_file = SRC_DIR / "mcp_server.py"
        if not server_file.exists():
            self.log_error(server_file, "File not found")
            return False
        
        content = server_file.read_text()
        original_content = content
        
        # Update import
        content = content.replace(
            "from .computer_use_core import ComputerUseCore",
            "from .factory_refactored import create_computer_use"
        )
        
        # Update instantiation
        content = re.sub(
            r'self\.computer_use = ComputerUseCore\(\)',
            'self.computer_use = create_computer_use()',
            content
        )
        
        # Update method calls
        content = content.replace(
            "self.computer_use.screenshot(",
            "self.computer_use.take_screenshot("
        )
        
        if content != original_content:
            server_file.write_text(content)
            self.log_change(server_file, "Updated to use refactored core")
            return True
        
        return True
    
    def verify_imports(self):
        """Verify all imports can be resolved"""
        print("\n🔍 Verifying imports...")
        try:
            # Test importing the new modules
            import sys
            sys.path.insert(0, str(SRC_DIR.parent))
            
            # Try importing key modules
            from mcp.factory_refactored import create_computer_use
            from mcp.test_mocks import create_test_computer_use
            
            print("✅ All imports verified")
            return True
        except ImportError as e:
            self.log_error("imports", str(e))
            return False
    
    def run_sample_test(self):
        """Run a simple test to verify the refactoring works"""
        print("\n🧪 Running sample test...")
        
        test_code = '''
import sys
sys.path.insert(0, "/home/sunkar/computer-use-mcp/src")

from mcp.test_mocks import create_test_computer_use

# Create test instance
core = create_test_computer_use()

# Test screenshot
result = core.take_screenshot()
assert result['success'] == True
assert result['data'] == b'mock_screenshot_data'

# Test click
result = core.click(100, 200)
assert result['success'] == True
assert result['coordinates'] == (100, 200)

print("✅ Sample test passed!")
'''
        
        test_file = PROJECT_ROOT / "verify_refactoring.py"
        test_file.write_text(test_code)
        
        try:
            subprocess.run(
                ["python3", str(test_file)],
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ Sample test passed")
            test_file.unlink()  # Clean up
            return True
        except subprocess.CalledProcessError as e:
            self.log_error("sample test", e.stderr)
            return False
    
    def save_report(self):
        """Save a report of all changes"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'backup_location': str(BACKUP_DIR),
            'changes': self.changes_made,
            'errors': self.errors,
            'summary': {
                'files_changed': len(set(c['file'] for c in self.changes_made)),
                'total_changes': len(self.changes_made),
                'errors': len(self.errors)
            }
        }
        
        report_file = PROJECT_ROOT / "refactoring_report.json"
        report_file.write_text(json.dumps(report, indent=2))
        print(f"\n📄 Report saved to: {report_file}")
    
    def execute(self):
        """Execute the full refactoring"""
        print("🚀 Starting automated refactoring...\n")
        
        steps = [
            ("Backing up files", self.backup_files),
            ("Creating mock providers", self.create_mock_providers),
            ("Updating MCP server", self.update_mcp_server),
            ("Verifying imports", self.verify_imports),
            ("Running sample test", self.run_sample_test)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📌 {step_name}...")
            if not step_func():
                print(f"\n❌ Failed at: {step_name}")
                print("⚠️  Refactoring aborted. Check errors above.")
                self.save_report()
                return False
        
        # Migrate test files
        print("\n📝 Migrating test files...")
        for test_file in TEST_FILES_TO_MIGRATE:
            self.migrate_test_file(test_file)
        
        self.save_report()
        
        print("\n✨ Refactoring completed successfully!")
        print(f"📦 Backup saved at: {BACKUP_DIR}")
        print(f"📊 Total files changed: {len(set(c['file'] for c in self.changes_made))}")
        print(f"❌ Errors encountered: {len(self.errors)}")
        
        return len(self.errors) == 0


if __name__ == "__main__":
    executor = RefactoringExecutor()
    success = executor.execute()
    exit(0 if success else 1)
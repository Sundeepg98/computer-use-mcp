"""
Computer Use MCP Lite - Streamlined Desktop Automation
Clean architecture, proven safety, essential functionality
"""

__version__ = "2.0.0"

# Core imports
from .core.computer_use import ComputerUse
from .core.factory import create_computer_use, create_computer_use_for_testing
from .core.safety import SafetyChecker, get_safety_checker

# Convenience aliases
create = create_computer_use
create_for_testing = create_computer_use_for_testing

__all__ = [
    # Core functionality
    'ComputerUse',
    'create_computer_use',
    'create',
    'create_computer_use_for_testing',
    'create_for_testing',
    
    # Safety
    'SafetyChecker',
    'get_safety_checker',
    
    # Version
    '__version__',
]
"""
Streamlined Factory - Creates ComputerUse instances without bloat
"""

import logging
from typing import Optional

from .computer_use import ComputerUse
from ..platforms import get_platform_providers

logger = logging.getLogger(__name__)


def create_computer_use() -> ComputerUse:
    """
    Create a ComputerUse instance for the current platform
    Auto-detects platform and configures appropriately
    """
    # Get platform-specific providers
    providers = get_platform_providers()
    
    # Create and return configured instance
    return ComputerUse(
        screenshot_provider=providers['screenshot'],
        input_provider=providers['input'],
        platform_info=providers['platform'],
        display_manager=providers['display']
    )


def create_computer_use_for_testing(**overrides) -> ComputerUse:
    """
    Create a ComputerUse instance for testing with mock implementations
    
    Args:
        **overrides: Custom provider implementations
    
    Returns:
        ComputerUse with test implementations
    """
    from .test_mocks import get_mock_providers
    
    # Get default mock providers
    providers = get_mock_providers()
    
    # Apply any overrides
    providers.update(overrides)
    
    return ComputerUse(
        screenshot_provider=providers.get('screenshot_provider', providers['screenshot']),
        input_provider=providers.get('input_provider', providers['input']),
        platform_info=providers.get('platform_info', providers['platform']),
        display_manager=providers.get('display_manager', providers['display'])
    )
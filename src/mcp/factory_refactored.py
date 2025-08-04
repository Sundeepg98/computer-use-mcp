#!/usr/bin/env python3
"""
Factory for creating ComputerUseRefactored instances

This factory creates properly configured instances with all dependencies,
eliminating the need for test_mode by allowing dependency injection.
"""

import logging
from typing import Optional

from .computer_use_refactored import ComputerUseRefactored
from .platform_utils import get_platform_info, get_recommended_screenshot_method
from .screenshot import ScreenshotFactory
from .input import InputFactory
from .safety_checks import SafetyChecker

# Import platform implementations
from .implementations.platform_info_impl import PlatformInfoImpl
from .implementations.display_manager_impl import DisplayManagerImpl

logger = logging.getLogger(__name__)


class ComputerUseFactory:
    """Factory for creating ComputerUse instances with proper dependencies"""
    
    @staticmethod
    def create_default() -> ComputerUseRefactored:
        """
        Create a ComputerUse instance with default platform-specific implementations
        
        Returns:
            ComputerUseRefactored configured for the current platform
        """
        # Get platform info
        platform_info = PlatformInfoImpl()
        
        # Create screenshot provider
        screenshot_provider = ScreenshotFactory.create()
        
        # Create input provider
        input_provider = InputFactory.create()
        
        # Create safety validator
        safety_validator = SafetyChecker()
        
        # Create display manager
        display_manager = DisplayManagerImpl()
        
        # Create and return configured instance
        return ComputerUseRefactored(
            screenshot_provider=screenshot_provider,
            input_provider=input_provider,
            platform_info=platform_info,
            safety_validator=safety_validator,
            display_manager=display_manager
        )
    
    @staticmethod
    def create_with_overrides(
        screenshot_provider=None,
        input_provider=None,
        platform_info=None,
        safety_validator=None,
        display_manager=None
    ) -> ComputerUseRefactored:
        """
        Create a ComputerUse instance with custom implementations
        
        This is primarily for testing - allows injecting mock implementations
        
        Args:
            screenshot_provider: Custom screenshot implementation
            input_provider: Custom input implementation
            platform_info: Custom platform info implementation
            safety_validator: Custom safety validator
            display_manager: Custom display manager
            
        Returns:
            ComputerUseRefactored with custom implementations
        """
        # Use defaults for any not provided
        screenshot_provider = screenshot_provider or ScreenshotFactory.create()
        input_provider = input_provider or InputFactory.create()
        platform_info = platform_info or PlatformInfoImpl()
        safety_validator = safety_validator or SafetyChecker()
        display_manager = display_manager or DisplayManagerImpl()
        return ComputerUseRefactored(
            screenshot_provider=screenshot_provider,
            input_provider=input_provider,
            platform_info=platform_info,
            safety_validator=safety_validator,
            display_manager=display_manager
        )


def create_computer_use() -> ComputerUseRefactored:
    """
    Convenience function to create a default ComputerUse instance
    
    Returns:
        ComputerUseRefactored configured for the current platform
    """
    return ComputerUseFactory.create_default()


def create_computer_use_for_testing(**overrides) -> ComputerUseRefactored:
    """
    Create a ComputerUse instance for testing with mock implementations
    
    Args:
        **overrides: Keyword arguments for custom implementations
        
    Returns:
        ComputerUseRefactored with test implementations
    """
    # Import mocks
    from .test_mocks import (
        MockScreenshotProvider, MockInputProvider, MockPlatformInfo,
        MockSafetyValidator, MockDisplayManager, MockVisualAnalyzer
    )
    
    # Set defaults to mocks
    defaults = {
        'screenshot_provider': MockScreenshotProvider(),
        'input_provider': MockInputProvider(),
        'platform_info': MockPlatformInfo(),
        'safety_validator': MockSafetyValidator(),
        'display_manager': MockDisplayManager(),
        'visual_analyzer': MockVisualAnalyzer()
    }
    
    # Apply overrides
    defaults.update(overrides)
    
    return ComputerUseFactory.create_with_overrides(**defaults)
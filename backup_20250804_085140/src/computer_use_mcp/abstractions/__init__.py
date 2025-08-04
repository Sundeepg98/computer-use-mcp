"""
Platform abstractions for Computer Use MCP

This module provides clean interfaces for platform-specific implementations,
enabling proper dependency injection and testability without test_mode.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, Protocol


class ScreenshotProvider(Protocol):
    """Protocol for screenshot implementations"""
    
    @abstractmethod
    def capture(self) -> Any:
        """Capture a screenshot and return as image data"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this screenshot method is available"""
        pass
    
    @abstractmethod
    def get_display_info(self) -> Dict[str, Any]:
        """Get information about the display"""
        pass


class InputProvider(Protocol):
    """Protocol for input implementations"""
    
    @abstractmethod
    def click(self, x: int, y: int, button: str = 'left') -> bool:
        """Perform a mouse click"""
        pass
    
    @abstractmethod
    def type_text(self, text: str) -> bool:
        """Type text"""
        pass
    
    @abstractmethod
    def key_press(self, key: str) -> bool:
        """Press a specific key"""
        pass
    
    @abstractmethod
    def mouse_move(self, x: int, y: int) -> bool:
        """Move mouse to position"""
        pass
    
    @abstractmethod
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        """Drag from start to end position"""
        pass
    
    @abstractmethod
    def scroll(self, direction: str, amount: int) -> bool:
        """Scroll in direction by amount"""
        pass


class PlatformInfo(Protocol):
    """Protocol for platform information"""
    
    @abstractmethod
    def get_platform(self) -> str:
        """Get platform name (windows, linux, macos)"""
        pass
    
    @abstractmethod
    def get_environment(self) -> str:
        """Get environment details (native, wsl2, etc)"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, bool]:
        """Get platform capabilities"""
        pass


class SafetyValidator(Protocol):
    """Protocol for safety validation"""
    
    @abstractmethod
    def validate_action(self, action: str, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate if an action is safe to perform
        Returns (is_safe, error_message)
        """
        pass
    
    @abstractmethod
    def validate_text(self, text: str) -> Tuple[bool, Optional[str]]:
        """Validate if text is safe to type"""
        pass
    
    @abstractmethod
    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """Validate if command is safe to execute"""
        pass


class DisplayManager(Protocol):
    """Protocol for display management"""
    
    @abstractmethod
    def is_display_available(self) -> bool:
        """Check if display is available"""
        pass
    
    @abstractmethod
    def get_best_display(self) -> Optional[str]:
        """Get the best available display"""
        pass
    
    @abstractmethod
    def setup_display(self) -> bool:
        """Setup display if needed"""
        pass
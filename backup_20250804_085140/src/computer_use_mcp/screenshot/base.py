"""
Base classes for screenshot implementations
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ScreenshotBase(ABC):
    """Abstract base class for screenshot implementations"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize screenshot handler
        
        Args:
            config: Configuration options
        """
        self.config = config or {}
        self._setup()
    
    def _setup(self):
        """Setup implementation-specific requirements"""
        pass
    
    @abstractmethod
    def capture(self, **kwargs) -> bytes:
        """
        Capture screenshot
        
        Args:
            **kwargs: Implementation-specific options
            - region: Dict with x, y, width, height for region capture
            - monitor: Monitor number (1-based) for multi-monitor
            - quality: JPEG quality (1-100) if applicable
            
        Returns:
            Screenshot data as PNG bytes
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this implementation is available on current system
        
        Returns:
            True if available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_monitors(self) -> List[Dict[str, Any]]:
        """
        Get information about available monitors
        
        Returns:
            List of monitor information dicts with:
            - id: Monitor identifier
            - x, y: Position
            - width, height: Dimensions
            - primary: True if primary monitor
        """
        pass
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> bytes:
        """
        Capture specific region (convenience method)
        
        Args:
            x, y: Top-left coordinates
            width, height: Region dimensions
            
        Returns:
            Screenshot data as PNG bytes
        """
        return self.capture(region={'x': x, 'y': y, 'width': width, 'height': height})
    
    def capture_monitor(self, monitor_id: int) -> bytes:
        """
        Capture specific monitor (convenience method)
        
        Args:
            monitor_id: Monitor number (1-based)
            
        Returns:
            Screenshot data as PNG bytes
        """
        return self.capture(monitor=monitor_id)
    
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get capabilities of this implementation
        
        Returns:
            Dict of capability flags
        """
        return {
            'region_capture': True,
            'multi_monitor': True,
            'cursor_capture': False,
            'video_capture': False,
            'transparency': False
        }


class ScreenshotError(Exception):
    """Base exception for screenshot errors"""
    pass


class ScreenshotNotAvailableError(ScreenshotError):
    """Raised when screenshot method is not available"""
    pass


class ScreenshotCaptureError(ScreenshotError):
    """Raised when screenshot capture fails"""
    pass
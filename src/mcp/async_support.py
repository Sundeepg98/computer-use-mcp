#!/usr/bin/env python3
"""
Async support for Computer Use MCP
Provides async/await interfaces for better performance
"""

import asyncio
from typing import Dict, Any, Optional, Protocol
from concurrent.futures import ThreadPoolExecutor

from .abstractions import (
    ScreenshotProvider, InputProvider, PlatformInfo,
    SafetyValidator, DisplayManager
)
from .computer_use_refactored import ComputerUseRefactored


class AsyncScreenshotProvider(Protocol):
    """Async version of ScreenshotProvider"""
    
    async def capture(self) -> Any:
        """Capture a screenshot asynchronously"""
        pass
    
    async def is_available(self) -> bool:
        """Check if screenshot method is available"""
        pass
    
    async def get_display_info(self) -> Dict[str, Any]:
        """Get display information"""
        pass


class AsyncInputProvider(Protocol):
    """Async version of InputProvider"""
    
    async def click(self, x: int, y: int, button: str = 'left') -> bool:
        """Perform a mouse click asynchronously"""
        pass
    
    async def type_text(self, text: str) -> bool:
        """Type text asynchronously"""
        pass
    
    async def key_press(self, key: str) -> bool:
        """Press a key asynchronously"""
        pass
    
    async def mouse_move(self, x: int, y: int) -> bool:
        """Move mouse asynchronously"""
        pass
    
    async def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        """Drag asynchronously"""
        pass
    
    async def scroll(self, direction: str, amount: int) -> bool:
        """Scroll asynchronously"""
        pass


class SyncToAsyncAdapter:
    """Adapts synchronous providers to async interface using thread pool"""
    
    def __init__(self, sync_provider, executor: Optional[ThreadPoolExecutor] = None):
        self.sync_provider = sync_provider
        self.executor = executor or ThreadPoolExecutor(max_workers=4)
    
    def __getattr__(self, name):
        """Wrap any method call in async executor"""
        sync_method = getattr(self.sync_provider, name)
        
        async def async_wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, sync_method, *args, **kwargs
            )
        
        return async_wrapper


class ComputerUseAsync:
    """
    Async version of ComputerUse with non-blocking operations
    """
    
    def __init__(
        self,
        screenshot_provider: AsyncScreenshotProvider,
        input_provider: AsyncInputProvider,
        platform_info: PlatformInfo,
        safety_validator: SafetyValidator,
        display_manager: DisplayManager,
        visual_analyzer: Optional[Any] = None,
        enable_ultrathink: bool = True
    ):
        """Initialize async computer use"""
        self.screenshot = screenshot_provider
        self.input = input_provider
        self.platform = platform_info
        self.safety = safety_validator
        self.display = display_manager
        self.visual_analyzer = visual_analyzer
        self.ultrathink_enabled = enable_ultrathink
        
        # Get platform info
        self.display_available = self.display.is_display_available()
    
    @classmethod
    def from_sync(cls, sync_computer_use: ComputerUseRefactored, executor=None):
        """Create async version from sync implementation"""
        return cls(
            screenshot_provider=SyncToAsyncAdapter(sync_computer_use.screenshot, executor),
            input_provider=SyncToAsyncAdapter(sync_computer_use.input, executor),
            platform_info=sync_computer_use.platform,
            safety_validator=sync_computer_use.safety,
            display_manager=sync_computer_use.display,
            visual_analyzer=sync_computer_use.visual_analyzer,
            enable_ultrathink=sync_computer_use.ultrathink_enabled
        )
    
    async def take_screenshot(self, analyze: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot asynchronously"""
        try:
            # Check display availability
            if not self.display.is_display_available():
                return {
                    'success': False,
                    'error': 'No display available',
                    'platform': self.platform.get_platform()
                }
            
            # Capture screenshot asynchronously
            screenshot_data = await self.screenshot.capture()
            
            result = {
                'success': True,
                'data': screenshot_data,
                'platform': self.platform.get_platform(),
                'method': self.screenshot.__class__.__name__
            }
            
            # Perform analysis if requested
            if analyze and self.ultrathink_enabled and self.visual_analyzer:
                # Run analysis in thread pool if sync
                if hasattr(self.visual_analyzer, 'analyze'):
                    loop = asyncio.get_event_loop()
                    analysis = await loop.run_in_executor(
                        None, self.visual_analyzer.analyze, screenshot_data, analyze
                    )
                else:
                    # Assume async analyzer
                    analysis = await self.visual_analyzer.analyze(screenshot_data, analyze)
                result['analysis'] = analysis
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': self.platform.get_platform()
            }
    
    async def click(self, x: int, y: int, button: str = 'left') -> Dict[str, Any]:
        """Perform a mouse click asynchronously"""
        try:
            # Validate coordinates
            if not isinstance(x, int) or not isinstance(y, int):
                return {
                    'success': False,
                    'error': 'Coordinates must be integers'
                }
            
            # Safety check (run in thread if sync)
            is_safe, error = self.safety.validate_action('click', {
                'x': x, 'y': y, 'button': button
            })
            if not is_safe:
                return {
                    'success': False,
                    'error': f'Safety check failed: {error}'
                }
            
            # Check display
            if not self.display.is_display_available():
                return {
                    'success': False,
                    'error': 'No display available'
                }
            
            # Perform click asynchronously
            success = await self.input.click(x, y, button)
            
            return {
                'success': success,
                'action': 'click',
                'coordinates': (x, y),
                'button': button
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def type_text(self, text: str) -> Dict[str, Any]:
        """Type text asynchronously"""
        try:
            # Safety check
            is_safe, error = self.safety.validate_text(text)
            if not is_safe:
                return {
                    'success': False,
                    'error': f'Safety check failed: {error}'
                }
            
            # Type text asynchronously
            success = await self.input.type_text(text)
            
            return {
                'success': success,
                'action': 'type',
                'text': text[:20] + '...' if len(text) > 20 else text
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def batch_operations(self, operations: list) -> list:
        """Execute multiple operations concurrently"""
        tasks = []
        
        for op in operations:
            if op['type'] == 'screenshot':
                task = self.take_screenshot(op.get('analyze'))
            elif op['type'] == 'click':
                task = self.click(op['x'], op['y'], op.get('button', 'left'))
            elif op['type'] == 'type':
                task = self.type_text(op['text'])
            else:
                # Unknown operation
                task = asyncio.create_task(
                    asyncio.coroutine(lambda: {'success': False, 'error': f'Unknown operation: {op["type"]}'})()
                )
            
            tasks.append(task)
        
        # Execute all operations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        return [
            {'success': False, 'error': str(r)} if isinstance(r, Exception) else r
            for r in results
        ]


def create_async_computer_use(executor: Optional[ThreadPoolExecutor] = None):
    """Create async computer use instance from sync implementation"""
    from .factory_refactored import create_computer_use
    sync_instance = create_computer_use()
    return ComputerUseAsync.from_sync(sync_instance, executor)


def create_async_computer_use_for_testing(executor: Optional[ThreadPoolExecutor] = None, **overrides):
    """Create async computer use instance for testing"""
    from .factory_refactored import create_computer_use_for_testing
    sync_instance = create_computer_use_for_testing(**overrides)
    return ComputerUseAsync.from_sync(sync_instance, executor)


# Example usage:
if __name__ == "__main__":
    async def main():
        # Create async instance
        computer = create_async_computer_use()
        
        # Single operation
        result = await computer.take_screenshot()
        print(f"Screenshot: {result}")
        
        # Batch operations
        operations = [
            {'type': 'screenshot'},
            {'type': 'click', 'x': 100, 'y': 200},
            {'type': 'type', 'text': 'Hello async!'}
        ]
        results = await computer.batch_operations(operations)
        for i, result in enumerate(results):
            print(f"Operation {i}: {result}")
    
    # Run async example
    asyncio.run(main())
"""
Caching layer for Computer Use MCP
Provides intelligent caching for expensive operations
"""

from collections import OrderedDict
from functools import wraps
from typing import Dict, Any, Optional, Callable, Tuple
import hashlib
import threading
import time

from ..core.factory import create_computer_use
from .abstractions import ScreenshotProvider, InputProvider


class LRUCache:
    """Thread-safe LRU cache implementation"""


    def __init__(self, maxsize: int = 100, ttl: Optional[float] = None) -> None:
        """
        Initialize LRU cache

        Args:
            maxsize: Maximum number of items to store
            ttl: Time to live in seconds (None = no expiration)
        """
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            # Check if key exists
            if key not in self.cache:
                self.misses += 1
                return None

            # Check TTL
            if self.ttl and time.time() - self.timestamps[key] > self.ttl:
                del self.cache[key]
                del self.timestamps[key]
                self.misses += 1
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]

    def put(self, key: str, value: Any) -> None:
        """Put item in cache"""
        with self.lock:
            # If key exists, update and move to end
            if key in self.cache:
                self.cache[key] = value
                self.cache.move_to_end(key)
                self.timestamps[key] = time.time()
                return

            # Add new item
            self.cache[key] = value
            self.timestamps[key] = time.time()

            # Remove oldest if over capacity
            if len(self.cache) > self.maxsize:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]

    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0
            return {
                'size': len(self.cache),
                'maxsize': self.maxsize,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'ttl': self.ttl
            }


class CachedScreenshotProvider:
    """Screenshot provider with intelligent caching"""


    def __init__(
        self,
        provider: ScreenshotProvider,
        cache_size: int = 10,
        ttl: float = 0.1,  # 100ms default
        hash_display: bool = True
    ):
        """
        Initialize cached screenshot provider

        Args:
            provider: Underlying screenshot provider
            cache_size: Maximum cached screenshots
            ttl: Time to live in seconds
            hash_display: Include display state in cache key
        """
        self.provider = provider
        self.cache = LRUCache(maxsize=cache_size, ttl=ttl)
        self.hash_display = hash_display

    def _get_cache_key(self) -> str:
        """Generate cache key based on display state"""
        if not self.hash_display:
            return "screenshot"

        # Include display info in cache key
        try:
            display_info = self.provider.get_display_info()
            key_data = f"{display_info.get('width')}x{display_info.get('height')}"
            return hashlib.sha256(key_data.encode()).hexdigest()
        except (AttributeError, KeyError, TypeError):
            return "screenshot"

    def capture(self) -> Any:
        """Capture screenshot with caching"""
        cache_key = self._get_cache_key()

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Capture new screenshot
        screenshot = self.provider.capture()
        self.cache.put(cache_key, screenshot)
        return screenshot

    def is_available(self) -> bool:
        """Check if screenshot is available"""
        return self.provider.is_available()

    def get_display_info(self) -> Dict[str, Any]:
        """Get display info (also cached)"""
        cache_key = "display_info"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        info = self.provider.get_display_info()
        self.cache.put(cache_key, info)
        return info

    def invalidate_cache(self) -> None:
        """Invalidate all cached screenshots"""
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()


class CachedInputProvider:
    """Input provider with result caching for idempotent operations"""


    def __init__(self, provider: InputProvider, cache_mouse_position: bool = True) -> None:
        """
        Initialize cached input provider

        Args:
            provider: Underlying input provider
            cache_mouse_position: Cache mouse position for short time
        """
        self.provider = provider
        self.position_cache = LRUCache(maxsize=1, ttl=0.05) if cache_mouse_position else None
        self.last_action_time = 0

    def click(self, x: int, y: int, button: str = 'left') -> Dict[str, Any]:
        """Click (not cached - has side effects)"""
        self.last_action_time = time.time()
        if self.position_cache:
            self.position_cache.clear()  # Invalidate position
        return self.provider.click(x, y, button)

    def type_text(self, text: str) -> Dict[str, Any]:
        """Type text (not cached - has side effects)"""
        self.last_action_time = time.time()
        return self.provider.type_text(text)

    def key_press(self, key: str) -> Dict[str, Any]:
        """Press key (not cached - has side effects)"""
        self.last_action_time = time.time()
        return self.provider.key_press(key)

    def mouse_move(self, x: int, y: int) -> Dict[str, Any]:
        """Move mouse (cached position)"""
        self.last_action_time = time.time()
        if self.position_cache:
            self.position_cache.put("pos", (x, y))
        return self.provider.mouse_move(x, y)

    def get_mouse_position(self) -> Tuple[int, int]:
        """Get cached mouse position if available"""
        if self.position_cache:
            pos = self.position_cache.get("pos")
            if pos:
                return pos
        # Fallback to provider if it has this method
        if hasattr(self.provider, 'get_mouse_position'):
            return self.provider.get_mouse_position()
        return (0, 0)

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """Drag (not cached)"""
        self.last_action_time = time.time()
        if self.position_cache:
            self.position_cache.put("pos", (end_x, end_y))
        return self.provider.drag(start_x, start_y, end_x, end_y)

    def scroll(self, direction: str, amount: int) -> Dict[str, Any]:
        """Scroll (not cached)"""
        self.last_action_time = time.time()
        return self.provider.scroll(direction, amount)


def cache_method(ttl: float = 1.0, key_func: Optional[Callable] = None) -> Callable:
    """
    Decorator to cache method results

    Args:
        ttl: Time to live in seconds
        key_func: Function to generate cache key from arguments
    """

    def decorator(func) -> Callable:
        cache = LRUCache(maxsize=100, ttl=ttl)

        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            # Generate cache key
            if key_func:
                cache_key = key_func(self, *args, **kwargs)
            else:
                # Default key generation
                cache_key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"

            # Try cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute and cache
            result = func(self, *args, **kwargs)
            cache.put(cache_key, result)
            return result

        # Add cache control methods
        wrapper.clear_cache = cache.clear
        wrapper.get_cache_stats = cache.get_stats

        return wrapper

    return decorator


class SmartCache:
    """
    Intelligent cache that adapts based on usage patterns
    """


    def __init__(self, initial_ttl: float = 0.1, adapt_ttl: bool = True) -> None:
        """
        Initialize smart cache

        Args:
            initial_ttl: Initial time to live
            adapt_ttl: Adapt TTL based on access patterns
        """
        self.cache = LRUCache(maxsize=50, ttl=initial_ttl)
        self.initial_ttl = initial_ttl
        self.adapt_ttl = adapt_ttl
        self.access_times = {}
        self.ttl_adjustments = {}

    def get(self, key: str) -> Optional[Any]:
        """Get with adaptive TTL"""
        current_time = time.time()

        # Track access pattern
        if key in self.access_times:
            interval = current_time - self.access_times[key][-1]
            self.access_times[key].append(current_time)

            # Adapt TTL based on access frequency
            if self.adapt_ttl and len(self.access_times[key]) >= 3:
                avg_interval = sum(
                    self.access_times[key][i] - self.access_times[key][i-1]
                    for i in range(1, len(self.access_times[key]))
                ) / (len(self.access_times[key]) - 1)

                # Set TTL to slightly longer than average access interval
                adapted_ttl = min(avg_interval * 1.5, self.initial_ttl * 10)
                self.cache.ttl = adapted_ttl
                self.ttl_adjustments[key] = adapted_ttl
        else:
            self.access_times[key] = [current_time]

        # Keep only recent access times
        if len(self.access_times[key]) > 10:
            self.access_times[key] = self.access_times[key][-10:]

        return self.cache.get(key)

    def put(self, key: str, value: Any) -> None:
        """Put value in cache"""
        self.cache.put(key, value)

    def get_insights(self) -> Dict[str, Any]:
        """Get cache usage insights"""
        stats = self.cache.get_stats()
        stats['ttl_adjustments'] = self.ttl_adjustments
        stats['access_patterns'] = {
            key: {
                'count': len(times),
                'avg_interval': sum(times[i] - times[i-1] for i in range(1, len(times))) / (len(times) - 1)
                if len(times) > 1 else 0
            }
            for key, times in self.access_times.items()
        }
        return stats


# Factory functions with caching
def create_cached_computer_use(cache_screenshots: bool = True, screenshot_ttl: float = 0.1) -> Any:
    """Create computer use instance with caching"""

    instance = create_computer_use()

    if cache_screenshots:
        # Wrap screenshot provider with cache
        instance.screenshot = CachedScreenshotProvider(
            instance.screenshot,
            ttl=screenshot_ttl
        )

    return instance
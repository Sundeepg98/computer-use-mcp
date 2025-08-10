"""Safe JSON encoder for handling non-serializable objects"""

import json
import threading
from typing import Any


class SafeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles non-serializable objects"""
    
    def default(self, obj: Any) -> Any:
        # Handle threading objects
        if isinstance(obj, (threading.Lock, threading.RLock, threading.Event, threading.Condition)):
            return f"<{obj.__class__.__name__} object>"
        
        # Handle file objects
        if hasattr(obj, 'read') or hasattr(obj, 'write'):
            return f"<File object: {getattr(obj, 'name', 'unknown')}>"
        
        # Handle objects with to_dict method
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        
        # Handle objects with __dict__
        if hasattr(obj, '__dict__'):
            # Filter out private attributes and non-serializable objects
            safe_dict = {}
            for k, v in obj.__dict__.items():
                if k.startswith('_'):
                    continue  # Skip private attributes
                try:
                    json.dumps(v, cls=SafeJSONEncoder)  # Test if serializable
                    safe_dict[k] = v
                except (TypeError, ValueError):
                    safe_dict[k] = str(v)  # Convert to string if not serializable
            return safe_dict
        
        # Let the base class handle it
        return super().default(obj)

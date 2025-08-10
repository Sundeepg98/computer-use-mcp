"""
X11 screenshot implementation for Linux
"""

from typing import Optional, Dict, Any, List
import logging
import os
import subprocess
import tempfile

from ..constants import SUBPROCESS_TIMEOUT_NORMAL
from .base import ScreenshotBase, ScreenshotCaptureError


logger = logging.getLogger(__name__)


class X11Screenshot(ScreenshotBase):
    """X11 screenshot implementation using various tools"""


    def capture(self, **kwargs) -> bytes:
        """Capture screenshot using X11 tools"""
        methods = [
            self._capture_with_scrot,
            self._capture_with_import,
            self._capture_with_xwd,
        ]

        logger.info(f"Starting X11 screenshot capture (DISPLAY={os.environ.get('DISPLAY', 'not set')})")
        
        last_error = None
        for method in methods:
            try:
                logger.info(f"Trying method: {method.__name__}")
                result = method(**kwargs)
                logger.info(f"Method {method.__name__} succeeded: {len(result)} bytes")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Method {method.__name__} failed: {e}")
                continue

        raise ScreenshotCaptureError(f"All X11 methods failed: {last_error}")

    def _capture_with_scrot(self, **kwargs) -> bytes:
        """Capture using scrot"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Remove --silent to see any error messages
            cmd = ['scrot', tmp_path]

            # Handle region capture
            region = kwargs.get('region')
            if region:
                cmd.extend(['--select', f"{region['x']},{region['y']},{region['width']},{region['height']}"])

            # Ensure DISPLAY is in environment
            env = os.environ.copy()
            logger.debug(f"Running command: {' '.join(cmd)} with DISPLAY={env.get('DISPLAY', 'not set')}")
            result = subprocess.run(cmd, capture_output=True, timeout=SUBPROCESS_TIMEOUT_NORMAL, env=env)
            
            logger.debug(f"scrot returncode: {result.returncode}")
            if result.stderr:
                logger.debug(f"scrot stderr: {result.stderr.decode()}")

            if result.returncode != 0:
                raise ScreenshotCaptureError(f"scrot failed: {result.stderr.decode()}")

            # Add a small delay to ensure file is written
            import time
            time.sleep(0.1)
            
            # Check file size before reading
            file_size = os.path.getsize(tmp_path)
            logger.debug(f"Screenshot file size: {file_size} bytes at {tmp_path}")
            
            with open(tmp_path, 'rb') as f:
                data = f.read()
                logger.debug(f"Read {len(data)} bytes from file")
                return data
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _capture_with_import(self, **kwargs) -> bytes:
        """Capture using ImageMagick import"""
        cmd = ['import', '-window', 'root', 'png:-']

        # Handle region capture
        region = kwargs.get('region')
        if region:
            cmd = ['import', '-crop',
                   f"{region['width']}x{region['height']}+{region['x']}+{region['y']}",
                   'png:-']

        result = subprocess.run(cmd, capture_output=True, timeout=5)

        if result.returncode != 0:
            raise ScreenshotCaptureError(f"import failed: {result.stderr.decode()}")

        return result.stdout

    def _capture_with_xwd(self, **kwargs) -> bytes:
        """Capture using xwd + convert"""
        with tempfile.NamedTemporaryFile(suffix='.xwd', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Capture with xwd
            xwd_cmd = ['xwd', '-root', '-out', tmp_path]
            result = subprocess.run(xwd_cmd, capture_output=True, timeout=SUBPROCESS_TIMEOUT_NORMAL)

            if result.returncode != 0:
                raise ScreenshotCaptureError(f"xwd failed: {result.stderr.decode()}")

            # Convert to PNG
            convert_cmd = ['convert', tmp_path, 'png:-']
            result = subprocess.run(convert_cmd, capture_output=True, timeout=5)

            if result.returncode != 0:
                raise ScreenshotCaptureError(f"convert failed: {result.stderr.decode()}")

            return result.stdout
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def is_available(self) -> bool:
        """Check if X11 screenshot is available"""
        display = os.environ.get('DISPLAY')
        logger.debug(f"Checking X11 availability: DISPLAY={display}")
        
        if not display:
            logger.debug("X11 not available: No DISPLAY environment variable")
            return False

        # Check if at least one tool is available
        tools = ['scrot', 'import', 'xwd']
        available_tools = []
        for tool in tools:
            try:
                result = subprocess.run(['which', tool], capture_output=True)
                if result.returncode == 0:
                    available_tools.append(tool)
            except (subprocess.SubprocessError, OSError, FileNotFoundError):
                continue

        logger.debug(f"Available X11 tools: {available_tools}")
        
        if available_tools:
            return True
        
        logger.debug("X11 not available: No screenshot tools found")
        return False

    def get_monitors(self) -> List[Dict[str, Any]]:
        """Get monitor information using xrandr"""
        try:
            result = subprocess.run(['xrandr'], capture_output=True, text=True)
            if result.returncode != 0:
                return self._get_fallback_monitors()

            monitors = []
            monitor_id = 1

            for line in result.stdout.split('\n'):
                if ' connected' in line and ' disconnected' not in line:
                    parts = line.split()
                    # Parse resolution and position
                    geometry = parts[2] if parts[2] != 'primary' else parts[3]

                    # Format: 1920x1080+0+0
                    if '+' in geometry:
                        res, pos = geometry.split('+', 1)
                        width, height = map(int, res.split('x'))
                        x, y = map(int, pos.split('+'))

                        monitors.append({
                            'id': monitor_id,
                            'x': x,
                            'y': y,
                            'width': width,
                            'height': height,
                            'primary': 'primary' in line
                        })
                        monitor_id += 1

            return monitors if monitors else self._get_fallback_monitors()

        except Exception as e:
            logger.warning(f"Failed to get monitors via xrandr: {e}")
            return self._get_fallback_monitors()

    def _get_fallback_monitors(self) -> List[Dict[str, Any]]:
        """Get fallback monitor configuration"""
        return [{
            'id': 1,
            'x': 0,
            'y': 0,
            'width': 1920,
            'height': 1080,
            'primary': True
        }]
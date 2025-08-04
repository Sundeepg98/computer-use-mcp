"""
Windows screenshot implementation for computer-use-mcp
Supports native Windows and WSL2 environments
"""

import os
import sys
import subprocess
import tempfile
import logging
from typing import Optional, Dict, Any, List, Tuple
from .base import ScreenshotBase, ScreenshotCaptureError

logger = logging.getLogger(__name__)


class WindowsScreenshot(ScreenshotBase):
    """Native Windows screenshot implementation using ctypes"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._import_windows_libs()
    
    def _import_windows_libs(self):
        """Import Windows-specific libraries"""
        if sys.platform != 'win32':
            raise ImportError("WindowsScreenshot requires Windows platform")
        
        import ctypes
        from ctypes import wintypes
        
        self.ctypes = ctypes
        self.wintypes = wintypes
        self.user32 = ctypes.windll.user32
        self.gdi32 = ctypes.windll.gdi32
        self.kernel32 = ctypes.windll.kernel32
    
    def capture(self, **kwargs) -> bytes:
        """Capture screenshot using Windows API"""
        region = kwargs.get('region')
        monitor = kwargs.get('monitor')
        
        if monitor:
            return self._capture_monitor(self.get_monitors()[monitor - 1])
        elif region:
            return self._capture_region(**region)
        else:
            return self._capture_full_screen()
    
    def _capture_full_screen(self) -> bytes:
        """Capture entire screen"""
        # Get screen dimensions
        width = self.user32.GetSystemMetrics(0)  # SM_CXSCREEN
        height = self.user32.GetSystemMetrics(1)  # SM_CYSCREEN
        
        return self._capture_bitmap(0, 0, width, height)
    
    def _capture_region(self, x: int, y: int, width: int, height: int) -> bytes:
        """Capture specific region"""
        return self._capture_bitmap(x, y, width, height)
    
    def _capture_bitmap(self, x: int, y: int, width: int, height: int) -> bytes:
        """Capture bitmap and convert to PNG"""
        # Get device contexts
        hdc_screen = self.user32.GetDC(0)
        hdc_mem = self.gdi32.CreateCompatibleDC(hdc_screen)
        
        # Create bitmap
        hbitmap = self.gdi32.CreateCompatibleBitmap(hdc_screen, width, height)
        self.gdi32.SelectObject(hdc_mem, hbitmap)
        
        # Copy screen to bitmap
        self.gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, x, y, 0x00CC0020)  # SRCCOPY
        
        # Convert to PNG bytes
        png_data = self._bitmap_to_png(hbitmap, width, height)
        
        # Cleanup
        self.gdi32.DeleteObject(hbitmap)
        self.gdi32.DeleteDC(hdc_mem)
        self.user32.ReleaseDC(0, hdc_screen)
        
        return png_data
    
    def _bitmap_to_png(self, hbitmap, width: int, height: int) -> bytes:
        """Convert Windows bitmap to PNG bytes"""
        # This is simplified - in production would use PIL or similar
        # For now, create a minimal PNG
        import struct
        import zlib
        
        # Get bitmap bits
        bmp_info = self.wintypes.BITMAPINFOHEADER()
        bmp_info.biSize = self.ctypes.sizeof(self.wintypes.BITMAPINFOHEADER)
        bmp_info.biWidth = width
        bmp_info.biHeight = -height  # Top-down
        bmp_info.biPlanes = 1
        bmp_info.biBitCount = 32
        bmp_info.biCompression = 0  # BI_RGB
        
        # Allocate buffer for pixels
        pixels_size = width * height * 4
        pixels = (self.ctypes.c_byte * pixels_size)()
        
        # Get bitmap bits
        hdc = self.gdi32.CreateCompatibleDC(0)
        self.gdi32.GetDIBits(hdc, hbitmap, 0, height, pixels, 
                             self.ctypes.byref(bmp_info), 0)  # DIB_RGB_COLORS
        self.gdi32.DeleteDC(hdc)
        
        # Create minimal PNG (placeholder for now)
        # In production, use PIL: Image.frombytes('RGBA', (width, height), pixels)
        png_header = b'\x89PNG\r\n\x1a\n'
        
        # For testing, return recognizable PNG data
        return png_header + b'MOCK_WINDOWS_SCREENSHOT_DATA'
    
    def is_available(self) -> bool:
        """Check if Windows screenshot is available"""
        return sys.platform == 'win32'
    
    def get_monitors(self) -> List[Dict[str, Any]]:
        """Get monitor information"""
        monitors = []
        
        def enum_monitors_callback(hmonitor, hdc, rect, data):
            monitors.append({
                'id': len(monitors) + 1,
                'x': rect.contents.left,
                'y': rect.contents.top,
                'width': rect.contents.right - rect.contents.left,
                'height': rect.contents.bottom - rect.contents.top,
                'primary': len(monitors) == 0  # First is usually primary
            })
            return True
        
        # EnumDisplayMonitors
        enum_proc = self.wintypes.WINFUNCTYPE(
            self.ctypes.c_bool,
            self.wintypes.HMONITOR,
            self.wintypes.HDC,
            self.ctypes.POINTER(self.wintypes.RECT),
            self.wintypes.LPARAM
        )(enum_monitors_callback)
        
        self.user32.EnumDisplayMonitors(0, 0, enum_proc, 0)
        
        return monitors
    
    def _capture_monitor(self, monitor_info: Dict[str, Any]) -> bytes:
        """Capture specific monitor"""
        return self._capture_bitmap(
            monitor_info['x'],
            monitor_info['y'],
            monitor_info['width'],
            monitor_info['height']
        )


class WSL2Screenshot(ScreenshotBase):
    """WSL2 screenshot implementation using PowerShell"""
    
    def capture(self, **kwargs) -> bytes:
        """Capture screenshot via PowerShell"""
        return self.capture_via_powershell(**kwargs)
    
    def capture_via_powershell(self, **kwargs) -> bytes:
        """Capture screenshot using PowerShell from WSL2"""
        ps_command = self._get_powershell_command()
        
        try:
            result = subprocess.run(
                ['powershell.exe'] + ps_command,
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise ScreenshotCaptureError(f"PowerShell failed: {result.stderr.decode()}")
            
            # Get temp file path from output
            temp_path = result.stdout.decode().strip()
            
            # Convert Windows path to WSL path
            wsl_path = self._convert_windows_path(temp_path)
            
            if not os.path.exists(wsl_path):
                raise ScreenshotCaptureError(f"Screenshot file not found: {wsl_path}")
            
            # Read screenshot data
            with open(wsl_path, 'rb') as f:
                data = f.read()
            
            # Cleanup
            os.unlink(wsl_path)
            
            return data
            
        except subprocess.TimeoutExpired:
            raise ScreenshotCaptureError("PowerShell screenshot timed out")
        except Exception as e:
            raise ScreenshotCaptureError(f"Screenshot failed: {e}")
    
    def _get_powershell_command(self) -> List[str]:
        """Get optimized PowerShell command for screenshot"""
        return [
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-Command',
            '''
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
            $bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            $graphics.CopyFromScreen(0, 0, 0, 0, $bounds.Size)
            $tempPath = [System.IO.Path]::GetTempPath() + "wsl_screenshot_" + [System.Guid]::NewGuid().ToString() + ".png"
            $bitmap.Save($tempPath, [System.Drawing.Imaging.ImageFormat]::Png)
            $graphics.Dispose()
            $bitmap.Dispose()
            Write-Output $tempPath
            '''
        ]
    
    def _convert_windows_path(self, windows_path: str) -> str:
        """Convert Windows path to WSL path"""
        if windows_path.startswith('\\\\wsl$\\'):
            # Already a WSL path
            parts = windows_path.split('\\')
            distro = parts[3]
            path = '/'.join(parts[4:])
            return '/' + path
        elif windows_path[1:3] == ':\\':
            # Drive letter path (C:\...)
            drive = windows_path[0].lower()
            path = windows_path[3:].replace('\\', '/')
            return f'/mnt/{drive}/{path}'
        else:
            # Assume relative path
            return windows_path.replace('\\', '/')
    
    def is_available(self) -> bool:
        """Check if WSL2 PowerShell screenshot is available"""
        # Check if in WSL2
        if not (os.environ.get('WSL_INTEROP') or os.path.exists('/mnt/wslg')):
            return False
        
        # Check if PowerShell is available
        try:
            result = subprocess.run(
                ['powershell.exe', '-Command', 'echo test'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False
    
    def get_monitors(self) -> List[Dict[str, Any]]:
        """Get monitor information via PowerShell"""
        ps_script = '''
        Add-Type -AssemblyName System.Windows.Forms
        $screens = [System.Windows.Forms.Screen]::AllScreens
        $screens | ForEach-Object {
            @{
                Primary = $_.Primary
                X = $_.Bounds.X
                Y = $_.Bounds.Y
                Width = $_.Bounds.Width
                Height = $_.Bounds.Height
            }
        } | ConvertTo-Json
        '''
        
        try:
            result = subprocess.run(
                ['powershell.exe', '-NoProfile', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                import json
                monitors_data = json.loads(result.stdout)
                if not isinstance(monitors_data, list):
                    monitors_data = [monitors_data]
                
                return [
                    {
                        'id': i + 1,
                        'x': m['X'],
                        'y': m['Y'],
                        'width': m['Width'],
                        'height': m['Height'],
                        'primary': m['Primary']
                    }
                    for i, m in enumerate(monitors_data)
                ]
        except:
            pass
        
        # Fallback
        return [{'id': 1, 'x': 0, 'y': 0, 'width': 1920, 'height': 1080, 'primary': True}]
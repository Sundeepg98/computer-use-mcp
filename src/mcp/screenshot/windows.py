"""
Windows screenshot implementation for computer-use-mcp
Supports native Windows and WSL2 environments
"""

import io
import json
from typing import Optional, Dict, Any, List, Tuple
import logging
import os
import subprocess
import sys
import tempfile

from PIL import Image
from ctypes import wintypes
import ctypes
import struct
import zlib

from .base import ScreenshotBase, ScreenshotCaptureError


logger = logging.getLogger(__name__)


class WindowsScreenshot(ScreenshotBase):
    """Native Windows screenshot implementation using ctypes"""


    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._import_windows_libs()

    def _import_windows_libs(self) -> None:
        """Import Windows-specific libraries"""
        if sys.platform != 'win32':
            raise ImportError("WindowsScreenshot requires Windows platform")


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

        # Convert bitmap to PNG using a temporary file
        try:
            # Try to use PIL if available
            try:

                # Convert BGRA to RGBA
                pixel_array = bytearray(pixels)
                for i in range(0, len(pixel_array), 4):
                    pixel_array[i], pixel_array[i+2] = pixel_array[i+2], pixel_array[i]

                # Create PIL Image and save to bytes
                img = Image.frombytes('RGBA', (width, height), bytes(pixel_array))
                img = img.transpose(Image.FLIP_TOP_BOTTOM)  # Windows bitmaps are bottom-up

                png_buffer = io.BytesIO()
                img.save(png_buffer, format='PNG')
                return png_buffer.getvalue()

            except ImportError:
                # Fallback: Save bitmap to file and use system tools
                with tempfile.NamedTemporaryFile(suffix='.bmp', delete=False) as bmp_file:
                    # Write BMP header
                    bmp_header = bytearray(b'BM')  # Signature
                    file_size = 54 + len(pixels)  # Header + pixel data
                    bmp_header.extend(file_size.to_bytes(4, 'little'))
                    bmp_header.extend(b'\x00\x00\x00\x00')  # Reserved
                    bmp_header.extend((54).to_bytes(4, 'little'))  # Offset to pixel data

                    # Write DIB header
                    dib_header = bytearray()
                    dib_header.extend((40).to_bytes(4, 'little'))  # Header size
                    dib_header.extend(width.to_bytes(4, 'little'))
                    dib_header.extend(height.to_bytes(4, 'little'))
                    dib_header.extend((1).to_bytes(2, 'little'))  # Planes
                    dib_header.extend((32).to_bytes(2, 'little'))  # Bits per pixel
                    dib_header.extend((0).to_bytes(4, 'little'))  # Compression
                    dib_header.extend(len(pixels).to_bytes(4, 'little'))  # Image size
                    dib_header.extend((0).to_bytes(4, 'little'))  # X pixels per meter
                    dib_header.extend((0).to_bytes(4, 'little'))  # Y pixels per meter
                    dib_header.extend((0).to_bytes(4, 'little'))  # Colors used
                    dib_header.extend((0).to_bytes(4, 'little'))  # Important colors

                    bmp_file.write(bmp_header)
                    bmp_file.write(dib_header)
                    bmp_file.write(pixels)
                    bmp_path = bmp_file.name

                # Convert BMP to PNG using PowerShell
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as png_file:
                    png_path = png_file.name

                ps_script = f'''
                Add-Type -AssemblyName System.Drawing
                $bmp = [System.Drawing.Bitmap]::FromFile("{bmp_path}")
                $bmp.Save("{png_path}", [System.Drawing.Imaging.ImageFormat]::Png)
                $bmp.Dispose()
                '''

                result = subprocess.run(
                    ['powershell', '-Command', ps_script],
                    capture_output=True,
                    timeout=5
                )

                if result.returncode == 0:
                    with open(png_path, 'rb') as f:
                        png_data = f.read()
                else:
                    raise ScreenshotCaptureError(f"PowerShell conversion failed: {result.stderr}")

                # Cleanup temp files
                try:
                    os.unlink(bmp_path)
                    os.unlink(png_path)
                except OSError:
                    pass

                return png_data

        except Exception as e:
            logger.error(f"Failed to convert screenshot to PNG: {e}")
            # Return a valid minimal PNG as last resort
            # 1x1 transparent PNG
            return (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
                   b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f'
                   b'\x00\x00\x01\x01\x00\x00\x05\x00\x01\x0d\x0a\x2d\xb4\x00\x00\x00\x00'
                   b'IEND\xaeB`\x82')

    def is_available(self) -> bool:
        """Check if Windows screenshot is available"""
        return sys.platform == 'win32'

    def get_monitors(self) -> List[Dict[str, Any]]:
        """Get monitor information"""
        monitors = []

        def enum_monitors_callback(hmonitor: Any, hdc: Any, rect: Any, data: Any) -> bool:
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
            $tempPath = [System.IO.Path]::GetTempPath() + "wsl_screenshot_" + `
                [System.Guid]::NewGuid().ToString() + ".png"
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
        except (subprocess.SubprocessError, OSError):
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
        except (KeyError, ValueError, TypeError) as e:
            logger.debug(f"Failed to parse monitor information: {e}")

        # Fallback
        return [{'id': 1, 'x': 0, 'y': 0, 'width': 1920, 'height': 1080, 'primary': True}]
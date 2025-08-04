#!/usr/bin/env python3
"""
Windows RDP/Terminal Services screenshot implementation
Handles screenshot capture in Remote Desktop sessions
"""

import os
import subprocess
import tempfile
import logging
from typing import Optional, Dict, Any, Tuple
from .windows import WindowsScreenshot
from .base import ScreenshotCaptureError

logger = logging.getLogger(__name__)


class RDPScreenshot(WindowsScreenshot):
    """Screenshot implementation for RDP/Terminal Services sessions"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize RDP screenshot handler"""
        super().__init__(config)
        self.session_info = self._get_session_info()
        
    def _get_session_info(self) -> Dict[str, Any]:
        """Get current RDP session information"""
        info = {
            'session_id': os.environ.get('SESSIONNAME', 'Console'),
            'client_name': os.environ.get('CLIENTNAME', 'Local'),
            'is_remote': False
        }
        
        # Check if this is a remote session
        if info['session_id'] != 'Console' and 'RDP' in info['session_id']:
            info['is_remote'] = True
            
        return info
    
    def capture(self, **kwargs) -> bytes:
        """Capture screenshot in RDP session"""
        logger.info(f"Capturing RDP session screenshot (session: {self.session_info['session_id']})")
        
        # In RDP sessions, we need to handle potential restrictions
        try:
            # First try standard Windows capture
            return super().capture(**kwargs)
        except Exception as e:
            logger.warning(f"Standard capture failed in RDP: {e}")
            
            # Try alternative methods
            return self._capture_rdp_alternative(**kwargs)
    
    def _capture_rdp_alternative(self, **kwargs) -> bytes:
        """Alternative capture method for restricted RDP environments"""
        
        # Method 1: Try using PowerShell with .NET
        try:
            return self._capture_via_powershell_dotnet()
        except Exception as e:
            logger.warning(f"PowerShell .NET capture failed: {e}")
        
        # Method 2: Try using clip.exe workaround (captures to clipboard first)
        try:
            return self._capture_via_clipboard()
        except Exception as e:
            logger.warning(f"Clipboard capture failed: {e}")
        
        # Method 3: Use PrintScreen simulation
        try:
            return self._capture_via_printscreen()
        except Exception as e:
            logger.warning(f"PrintScreen capture failed: {e}")
            
        raise ScreenshotCaptureError(
            "All RDP screenshot methods failed. "
            "This may be due to RDP session restrictions."
        )
    
    def _capture_via_powershell_dotnet(self) -> bytes:
        """Capture using PowerShell and .NET in RDP session"""
        ps_script = '''
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        
        # Handle RDP session specifically
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen
        $bounds = $screen.Bounds
        
        # Create bitmap with session awareness
        $bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        
        # Use CopyFromScreen with RDP-aware parameters
        try {
            $graphics.CopyFromScreen(
                [System.Drawing.Point]::Empty,
                [System.Drawing.Point]::Empty,
                $bounds.Size,
                [System.Drawing.CopyPixelOperation]::SourceCopy
            )
        } catch {
            # Fallback for restricted RDP
            $graphics.CopyFromScreen(0, 0, 0, 0, $bounds.Size)
        }
        
        # Save to temp file
        $tempFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.png'
        $bitmap.Save($tempFile, [System.Drawing.Imaging.ImageFormat]::Png)
        
        # Cleanup
        $graphics.Dispose()
        $bitmap.Dispose()
        
        # Output the temp file path
        Write-Output $tempFile
        '''
        
        try:
            # Run PowerShell script
            result = subprocess.run(
                ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise Exception(f"PowerShell failed: {result.stderr}")
            
            # Get temp file path from output
            temp_file = result.stdout.strip()
            
            # Read the PNG data
            with open(temp_file, 'rb') as f:
                png_data = f.read()
            
            # Cleanup temp file
            try:
                os.unlink(temp_file)
            except:
                pass
                
            return png_data
            
        except Exception as e:
            raise ScreenshotCaptureError(f"PowerShell .NET capture failed: {e}")
    
    def _capture_via_clipboard(self) -> bytes:
        """Capture screenshot via clipboard (RDP workaround)"""
        ps_script = '''
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        
        # Simulate PrintScreen to capture to clipboard
        [System.Windows.Forms.SendKeys]::SendWait("{PRTSC}")
        
        # Wait for clipboard
        Start-Sleep -Milliseconds 500
        
        # Get image from clipboard
        $image = [System.Windows.Forms.Clipboard]::GetImage()
        if ($null -eq $image) {
            throw "No image in clipboard"
        }
        
        # Save to temp file
        $tempFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.png'
        $image.Save($tempFile, [System.Drawing.Imaging.ImageFormat]::Png)
        $image.Dispose()
        
        Write-Output $tempFile
        '''
        
        try:
            result = subprocess.run(
                ['powershell.exe', '-NoProfile', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise Exception(f"Clipboard capture failed: {result.stderr}")
                
            temp_file = result.stdout.strip()
            
            with open(temp_file, 'rb') as f:
                png_data = f.read()
                
            try:
                os.unlink(temp_file)
            except:
                pass
                
            return png_data
            
        except Exception as e:
            raise ScreenshotCaptureError(f"Clipboard capture failed: {e}")
    
    def _capture_via_printscreen(self) -> bytes:
        """Capture using PrintScreen key simulation"""
        # This is similar to clipboard but with more robust handling
        ps_script = '''
        Add-Type @"
        using System;
        using System.Drawing;
        using System.Drawing.Imaging;
        using System.Windows.Forms;
        using System.Runtime.InteropServices;
        
        public class RDPScreenCapture {
            [DllImport("user32.dll")]
            private static extern IntPtr GetDesktopWindow();
            
            [DllImport("user32.dll")]
            private static extern IntPtr GetWindowDC(IntPtr hWnd);
            
            [DllImport("user32.dll")]
            private static extern bool ReleaseDC(IntPtr hWnd, IntPtr hDC);
            
            [DllImport("user32.dll")]
            private static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
            
            [StructLayout(LayoutKind.Sequential)]
            private struct RECT {
                public int Left;
                public int Top;
                public int Right;
                public int Bottom;
            }
            
            public static string CaptureScreen() {
                IntPtr desktop = GetDesktopWindow();
                RECT rect;
                GetWindowRect(desktop, out rect);
                
                int width = rect.Right - rect.Left;
                int height = rect.Bottom - rect.Top;
                
                Bitmap bitmap = new Bitmap(width, height);
                Graphics g = Graphics.FromImage(bitmap);
                IntPtr hDC = g.GetHdc();
                IntPtr desktopDC = GetWindowDC(desktop);
                
                // Try to BitBlt the desktop
                bool success = BitBlt(hDC, 0, 0, width, height, desktopDC, 0, 0, 0x00CC0020);
                
                g.ReleaseHdc(hDC);
                ReleaseDC(desktop, desktopDC);
                g.Dispose();
                
                string tempFile = System.IO.Path.GetTempFileName().Replace(".tmp", ".png");
                bitmap.Save(tempFile, ImageFormat.Png);
                bitmap.Dispose();
                
                return tempFile;
            }
            
            [DllImport("gdi32.dll")]
            private static extern bool BitBlt(IntPtr hdcDest, int nXDest, int nYDest,
                int nWidth, int nHeight, IntPtr hdcSrc, int nXSrc, int nYSrc, uint dwRop);
        }
"@
        
        $tempFile = [RDPScreenCapture]::CaptureScreen()
        Write-Output $tempFile
        '''
        
        try:
            result = subprocess.run(
                ['powershell.exe', '-NoProfile', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                raise Exception(f"PrintScreen capture failed: {result.stderr}")
                
            temp_file = result.stdout.strip()
            
            with open(temp_file, 'rb') as f:
                png_data = f.read()
                
            try:
                os.unlink(temp_file)
            except:
                pass
                
            return png_data
            
        except Exception as e:
            raise ScreenshotCaptureError(f"PrintScreen capture failed: {e}")
    
    def get_monitors(self) -> list:
        """Get monitor information in RDP session"""
        # In RDP, we typically have one virtual monitor
        # But multi-monitor RDP is possible
        return super().get_monitors()
    
    def validate_rdp_capabilities(self) -> Dict[str, Any]:
        """Check what capture capabilities are available in RDP session"""
        capabilities = {
            'standard_capture': False,
            'powershell_capture': False,
            'clipboard_capture': False,
            'bitblt_capture': False,
            'restrictions': []
        }
        
        # Test standard capture
        try:
            super()._capture_full_screen()
            capabilities['standard_capture'] = True
        except:
            capabilities['restrictions'].append('Standard GDI capture blocked')
        
        # Test PowerShell availability
        try:
            subprocess.run(['powershell.exe', '-Command', 'echo test'], 
                         capture_output=True, timeout=5)
            capabilities['powershell_capture'] = True
        except:
            capabilities['restrictions'].append('PowerShell not available')
            
        # Check for known RDP restrictions
        if os.environ.get('SESSIONNAME', '').startswith('RDP-'):
            capabilities['restrictions'].append('Running in RDP session')
            
        return capabilities
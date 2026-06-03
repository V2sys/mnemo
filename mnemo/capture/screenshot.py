"""
mnemo/capture/screenshot.py
Owner: Vinayak

Fast screen capture via mss. Perceptual-hash deduplication via ImageHash.
On capture, calls OCR, then hands off to Vedansh's summarizer.

Pipeline:
    hotkey → mss.grab() → dedup check (ImageHash) → ocr.extract() → summarizer.summarize()
"""

import io
import logging
import platform
import time
from collections.abc import Callable

import imagehash
import mss
import mss.tools
from PIL import Image

from mnemo.capture.ocr import extract_text
from mnemo.schema import SCREENSHOT_HASH_DIFF_THRESHOLD, ScreenshotCapture

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


class ScreenshotEngine:
    def __init__(
        self,
        on_capture: Callable[[ScreenshotCapture], None],
    ) -> None:
        """
        on_capture: a callback into Vedansh's summarizer.
        Vinayak does NOT call Phi-3 directly — passes through this hook.
        """
        self.on_capture = on_capture
        self._last_hash = None

    def capture(self) -> ScreenshotCapture | None:
        """Capture the screen, dedup, return the capture record or None if skipped."""
        try:
            # 1. mss.mss() → grab primary monitor
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # primary monitor, index 0 is "all"
                raw = sct.grab(monitor)
                img_bytes = mss.tools.to_png(raw.rgb, raw.size)

            # 2. ImageHash.average_hash(img) → compare to self._last_hash
            img = Image.open(io.BytesIO(img_bytes))
            current_hash = imagehash.average_hash(img)
            
            if self._last_hash is not None:
                diff = current_hash - self._last_hash
                # threshold: skip if fewer than 13 bits differ (~20% of 64)
                threshold_bits = int(SCREENSHOT_HASH_DIFF_THRESHOLD * 64)
                log.info(f"Screenshot diff={diff} bits (threshold={threshold_bits})")
                if diff < threshold_bits:
                    log.info(f"Screenshot skipped — diff={diff} bits (threshold={threshold_bits})")
                    return None
            
            self._last_hash = current_hash

            # 3. Get active window info:
            app_name, window_title = get_active_window_info()

            # 4. OCR:
            ocr_text = extract_text(img_bytes)

            # 5. Build ScreenshotCapture:
            capture: ScreenshotCapture = {
                "type": "screenshot",
                "image_bytes": img_bytes,
                "ocr_text": ocr_text,
                "app_name": app_name,
                "window_title": window_title,
                "timestamp": int(time.time())
            }
            
            self.on_capture(capture)
            return capture

        except Exception as e:
            log.error(f"Screenshot capture failed: {e}")
            return None


def get_active_window_info() -> tuple[str, str]:
    """Return (app_name, window_title) of the foreground window via pywin32."""
    if not IS_WINDOWS:
        return ("unknown", "unknown")

    try:
        import psutil
        import win32gui
        import win32process

        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return ("system", "no active window")
            
        window_title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        if pid == 0:
            return ("system", window_title or "idle")
            
        process = psutil.Process(pid)
        app_name = process.name()  # e.g. "chrome.exe"
        return (app_name, window_title)
    except Exception as e:
        log.error(f"Could not get window info: {e}")
        return ("unknown", "unknown")

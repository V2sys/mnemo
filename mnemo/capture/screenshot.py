"""
mnemo/capture/screenshot.py
Owner: Vinayak

Fast screen capture via mss. Perceptual-hash deduplication via ImageHash.
On capture, calls OCR, then hands off to Vedansh's summarizer.

Pipeline:
    hotkey → mss.grab() → dedup check (ImageHash) → ocr.extract() → summarizer.summarize()
"""

import logging
from typing import Callable

from mnemo.schema import ScreenshotCapture, SCREENSHOT_HASH_DIFF_THRESHOLD

log = logging.getLogger(__name__)


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
        # TODO(week 2):
        # 1. mss.mss() → grab primary monitor
        # 2. ImageHash.average_hash(img) → compare to self._last_hash
        # 3. if diff < SCREENSHOT_HASH_DIFF_THRESHOLD → return None
        # 4. ocr.extract_text(img) → ocr_text
        # 5. get_active_window_info() → app_name, window_title
        # 6. build ScreenshotCapture dict, call self.on_capture(capture)
        raise NotImplementedError("Vinayak — week 2 deliverable")


def get_active_window_info() -> tuple[str, str]:
    """Return (app_name, window_title) of the foreground window via pywin32."""
    # TODO(week 2):
    # win32gui.GetForegroundWindow() → hwnd
    # GetWindowText, GetWindowThreadProcessId → process name
    raise NotImplementedError("Vinayak — week 2 deliverable")

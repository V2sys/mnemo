"""
mnemo/daemon/hotkey.py
Owner: Vinayak

Global hotkey registration via the `keyboard` library.
Fires events into a queue consumed by Vedansh's UI and the screenshot module.

Responsibilities:
- Register Ctrl+Space (summon UI)
- Register Ctrl+Shift+Space (capture + summarize screenshot)
- Push events to subscribers on a queue

Note: `keyboard` requires admin on some systems; document in setup.md.
"""

import logging
import queue
import threading
from typing import Callable

from mnemo.config import SUMMON_HOTKEY, SCREENSHOT_HOTKEY

log = logging.getLogger(__name__)


class HotkeyManager:
    def __init__(
        self,
        on_summon: Callable[[], None],
        on_screenshot: Callable[[], None],
    ) -> None:
        self.on_summon = on_summon
        self.on_screenshot = on_screenshot
        self.events: queue.Queue[str] = queue.Queue()
        self._thread: threading.Thread | None = None

    def start_background(self) -> None:
        """Register global hotkeys on a background thread."""
        def _run():
            try:
                import keyboard
                keyboard.add_hotkey(SUMMON_HOTKEY, self._on_summon_event)
                keyboard.add_hotkey(SCREENSHOT_HOTKEY, self._on_screenshot_event)
                log.info(f"Registered hotkeys: {SUMMON_HOTKEY} (summon), {SCREENSHOT_HOTKEY} (screenshot)")
                keyboard.wait()
            except ImportError:
                log.warning("keyboard library not available or requires root. Hotkeys disabled.")
            except Exception as e:
                log.error(f"Failed to register hotkeys: {e}")

        self._thread = threading.Thread(target=_run, daemon=True, name="HotkeyManager")
        self._thread.start()

    def _on_summon_event(self) -> None:
        log.info("Summon hotkey fired")
        self.events.put("summon")
        try:
            self.on_summon()
        except Exception as e:
            log.error(f"Error in on_summon callback: {e}")

    def _on_screenshot_event(self) -> None:
        log.info("Screenshot hotkey fired")
        self.events.put("screenshot")
        try:
            self.on_screenshot()
        except Exception as e:
            log.error(f"Error in on_screenshot callback: {e}")

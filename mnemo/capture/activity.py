"""
mnemo/capture/activity.py
Owner: Vinayak

Passive activity monitoring — polls the active window every ACTIVITY_POLL_INTERVAL_SEC.
Writes directly to the activity_log table. No embedding, no Phi-3.

Only active when Mode == "memory" (opt-in). Disabled by default.
"""

import logging
import threading
import time

from mnemo.schema import ACTIVITY_POLL_INTERVAL_SEC

log = logging.getLogger(__name__)


class ActivityMonitor:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._enabled = False
        self._last_window: tuple[str, str] | None = None

    def set_enabled(self, enabled: bool) -> None:
        """Toggle by user via tray menu."""
        self._enabled = enabled

    def start_background(self) -> None:
        """Begin polling on a background thread."""
        # TODO(week 3):
        # self._thread = threading.Thread(target=self._loop, daemon=True)
        # self._thread.start()
        raise NotImplementedError("Vinayak — week 3 deliverable")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            if self._enabled:
                # TODO(week 3):
                # get active window via pywin32
                # if different from self._last_window: write to activity_log
                pass
            time.sleep(ACTIVITY_POLL_INTERVAL_SEC)

    def shutdown(self) -> None:
        self._stop_event.set()

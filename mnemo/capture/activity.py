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
    def __init__(self, store=None) -> None:
        self._store = store
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._enabled = False
        self._last_window: tuple[str, str] | None = None

    def set_enabled(self, enabled: bool) -> None:
        """Toggle by user via tray menu."""
        self._enabled = enabled
        log.info("Activity monitor %s", "enabled" if enabled else "disabled")

    def start_background(self) -> None:
        """Begin polling on a background thread."""
        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
            name="mnemo-activity"
        )
        self._thread.start()
        log.info("Activity monitor started (enabled=%s)", self._enabled)

    def _loop(self) -> None:
        import psutil
        try:
            import win32gui
            import win32process
        except ImportError:
            log.warning("pywin32 not found. Activity monitoring disabled.")
            return

        while not self._stop_event.is_set():
            if self._enabled:
                try:
                    hwnd = win32gui.GetForegroundWindow()
                    window_title = win32gui.GetWindowText(hwnd)
                    if not window_title:
                        time.sleep(ACTIVITY_POLL_INTERVAL_SEC)
                        continue

                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        app_name = psutil.Process(pid).name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        app_name = "unknown"

                    current = (app_name, window_title)

                    # Only log when the window actually changes
                    if current != self._last_window:
                        self._last_window = current
                        if self._store:
                            self._store.save_activity(app_name, window_title)
                            log.debug("Activity: %s — %s", app_name, window_title)

                except Exception as e:
                    log.debug("Activity poll error: %s", e)

            time.sleep(ACTIVITY_POLL_INTERVAL_SEC)

    def shutdown(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)

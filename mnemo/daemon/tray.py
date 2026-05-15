"""
mnemo/daemon/tray.py
Owner: Vinayak

System tray icon and background daemon lifecycle.
Uses pystray for the icon, runs on its own thread.

Responsibilities:
- Show a Mnemo icon in the system tray
- Right-click menu: Pause / Mode (Focus/Memory) / Settings / Quit
- Start the file watcher, activity monitor, and hotkey manager
- Graceful shutdown on Quit

Stays off the main thread — main thread is reserved for the UI (Tkinter).
"""

import logging
import threading
from typing import Callable

log = logging.getLogger(__name__)


class TrayDaemon:
    def __init__(self, on_quit: Callable[[], None]) -> None:
        self.on_quit = on_quit
        self._thread: threading.Thread | None = None

    def start_background(self) -> None:
        """Start the tray icon on a background thread."""
        # TODO(week 1):
        # - Create pystray.Icon with menu items
        # - menu: Pause/Resume, Mode (Focus/Memory), Quit
        # - Run icon.run() inside self._thread
        raise NotImplementedError("Vinayak — week 1 deliverable")

    def shutdown(self) -> None:
        """Stop the tray icon cleanly."""
        raise NotImplementedError("Vinayak — week 1 deliverable")

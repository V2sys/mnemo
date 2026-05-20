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
from typing import Callable, Optional
import pystray
from PIL import Image, ImageDraw

log = logging.getLogger(__name__)


class TrayDaemon:
    def __init__(self, on_quit: Callable[[], None], on_summon: Optional[Callable[[], None]] = None) -> None:
        self.on_quit = on_quit
        self.on_summon = on_summon
        self._icon = None
        self._thread: threading.Thread | None = None

    def start_background(self) -> None:
        """Start the tray icon on a background thread."""
        def setup_icon():
            image = self._create_icon_image()
            menu = pystray.Menu(
                pystray.MenuItem("Mnemo - Running", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Open", self._on_open),
                pystray.MenuItem("Quit", self._on_quit_click)
            )
            self._icon = pystray.Icon("Mnemo", image, menu=menu)
            self._icon.run()

        self._thread = threading.Thread(target=setup_icon, daemon=True, name="TrayDaemon")
        self._thread.start()

    def shutdown(self) -> None:
        """Stop the tray icon cleanly."""
        if self._icon:
            self._icon.stop()
        self.on_quit()

    def _on_open(self, icon, item) -> None:
        if self.on_summon:
            self.on_summon()

    def _on_quit_click(self, icon, item) -> None:
        self.shutdown()

    def _create_icon_image(self) -> Image.Image:
        image = Image.new('RGB', (64, 64), color='white')
        dc = ImageDraw.Draw(image)
        dc.ellipse([0, 0, 64, 64], fill='#0B57D0')
        return image

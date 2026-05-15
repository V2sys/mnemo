"""
mnemo/__main__.py

Entry point. Wires together all the layers and starts the daemon.
Run with: python -m mnemo
"""

import sys
import logging
from pathlib import Path


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    )
    log = logging.getLogger("mnemo")
    log.info("Mnemo starting up...")

    # TODO(week 1): wire up daemon → capture → memory → ai → ui
    #
    # from mnemo.daemon.tray import TrayDaemon
    # from mnemo.daemon.hotkey import HotkeyManager
    # from mnemo.memory.store import MemoryStore
    # from mnemo.ai.phi3 import Phi3Engine
    # from mnemo.ui.overlay import OverlayUI
    #
    # store = MemoryStore()
    # phi3 = Phi3Engine()
    # ui = OverlayUI(query_engine=..., action_router=...)
    # tray = TrayDaemon(on_quit=ui.shutdown)
    # hotkey = HotkeyManager(on_summon=ui.show)
    # tray.start_background()
    # hotkey.start_background()
    # ui.run_main_loop()

    log.warning("Not yet implemented — see TODOs in each module.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

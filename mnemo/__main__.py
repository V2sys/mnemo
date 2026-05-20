import logging
import sys
import time
import threading

from mnemo import config
from mnemo.memory.store import MemoryStore
from mnemo.memory.embedder import Embedder
from mnemo.capture.file_watcher import FileWatcher
from mnemo.daemon.tray import TrayDaemon
from mnemo.daemon.hotkey import HotkeyManager

def setup_logging():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format, stream=sys.stdout)
    
    file_handler = logging.FileHandler(config.LOGS_DIR / "mnemo.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(file_handler)

def main():
    config.ensure_dirs()
    setup_logging()
    log = logging.getLogger(__name__)

    store = MemoryStore()
    store.open()
    store.purge_expired_raw_text()

    embedder = Embedder()
    try:
        embedder.load()
    except FileNotFoundError as e:
        log.error(str(e))
        log.error("Please refer to docs/setup.md for instructions.")
        sys.exit(1)

    file_watcher = FileWatcher(config.WATCH_DIRS, store, embedder)
    file_watcher.start_background()

    def on_summon():
        log.info("summon fired — UI not wired yet")

    def on_screenshot():
        log.info("screenshot fired — capture not wired yet")

    shutdown_event = threading.Event()
    def on_quit():
        shutdown_event.set()

    tray = TrayDaemon(on_quit=on_quit, on_summon=on_summon)
    tray.start_background()

    hotkey = HotkeyManager(on_summon=on_summon, on_screenshot=on_screenshot)
    hotkey.start_background()

    log.info("Mnemo is running. Press Ctrl+Space to summon.")
    
    try:
        while not shutdown_event.is_set():
            shutdown_event.wait(1)
    except KeyboardInterrupt:
        log.info("Keyboard interrupt received.")
    finally:
        log.info("Shutting down...")
        store.close()
        tray.shutdown()
        sys.exit(0)

if __name__ == "__main__":
    main()

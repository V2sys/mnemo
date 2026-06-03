import hashlib
import json
import logging
import sys
import threading
import time

from mnemo import config
from mnemo.ai.phi3 import Phi3Engine
from mnemo.ai.summarizer import Summarizer
from mnemo.capture.file_watcher import FileWatcher
from mnemo.capture.screenshot import ScreenshotEngine
from mnemo.daemon.hotkey import HotkeyManager
from mnemo.daemon.tray import TrayDaemon
from mnemo.memory.embedder import Embedder
from mnemo.memory.store import MemoryStore
from mnemo.schema import RAW_TEXT_RETENTION_DAYS


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

    phi3 = Phi3Engine()
    summarizer = None
    try:
        phi3.load()
        summarizer = Summarizer(phi3)
    except Exception as e:
        log.warning(f"Phi-3 engine failed to load: {e}. Summarization disabled.")

    file_watcher = FileWatcher(config.WATCH_DIRS, store, embedder, summarizer)
    file_watcher.start_background()

    def on_screenshot_taken(capture):
        """Called by ScreenshotEngine after a successful capture."""
        if not capture["ocr_text"] and not capture["app_name"]:
            return  # nothing to store

        # Get summary if summarizer is available
        if summarizer is not None and capture["ocr_text"]:
            try:
                from mnemo.ai.phi3 import inference_pool
                future = inference_pool.submit(
                    summarizer.summarize, capture["ocr_text"]
                )
                summary = future.result(timeout=60)
            except Exception as e:
                log.warning("Screenshot summarization failed: %s", e)
                summary = capture["ocr_text"][:500]
        else:
            summary = capture["ocr_text"][:500] if capture["ocr_text"] else None

        # Build and store the memory record
        raw_text = capture["ocr_text"] or ""
        content_hash = hashlib.md5(raw_text.encode()).hexdigest()

        # Dedup — skip if same screenshot already stored
        if store.find_by_hash(content_hash):
            log.debug("Screenshot already in memory — skipping store")
            return

        record = {
            "type": "screenshot",
            "source": f"{capture['app_name']} — {capture['window_title']}",
            "content_hash": content_hash,
            "raw_text": raw_text,
            "raw_text_expires": int(time.time()) + RAW_TEXT_RETENTION_DAYS * 86400,
            "summary": summary,
            "timestamp": capture["timestamp"],
            "metadata": json.dumps({
                "app": capture["app_name"],
                "window_title": capture["window_title"]
            })
        }
        
        embedding_text = raw_text if raw_text else (summary or "")
        if embedding_text.strip():
            embedding = embedder.encode(embedding_text)
            mem_id = store.save_memory(record, embedding)
            log.info(f"Screenshot stored (id={mem_id}): {capture['window_title']}")

    screenshot_engine = ScreenshotEngine(on_capture=on_screenshot_taken)

    def on_summon():
        log.info("summon fired — UI not wired yet")

    shutdown_event = threading.Event()
    def on_quit():
        shutdown_event.set()

    tray = TrayDaemon(on_quit=on_quit, on_summon=on_summon)
    tray.start_background()

    hotkey = HotkeyManager(
        on_summon=on_summon, 
        on_screenshot=lambda: screenshot_engine.capture()
    )
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

import hashlib
import json
import logging
import sys
import threading
import time

from mnemo import config
from mnemo.ai.phi3 import Phi3Engine, inference_pool
from mnemo.ai.summarizer import Summarizer
from mnemo.ai.query_engine import QueryEngine
from mnemo.actions.router import ActionRouter
from mnemo.capture.file_watcher import FileWatcher
from mnemo.capture.screenshot import ScreenshotEngine
from mnemo.capture.activity import ActivityMonitor
from mnemo.daemon.hotkey import HotkeyManager
from mnemo.daemon.tray import TrayDaemon
from mnemo.ui.overlay import MnemoOverlay
from mnemo.memory.embedder import Embedder
from mnemo.memory.store import MemoryStore
from mnemo.schema import RAW_TEXT_RETENTION_DAYS

# Model unloading configuration
IDLE_UNLOAD_SECONDS = 300  # 5 minutes
_unload_timer: threading.Timer | None = None
_phi3: Phi3Engine | None = None

def setup_logging():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format, stream=sys.stdout)
    
    file_handler = logging.FileHandler(config.LOGS_DIR / "mnemo.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(file_handler)

def _do_unload():
    global _phi3
    if _phi3 and _phi3.is_loaded:
        _phi3.unload()
        logging.getLogger(__name__).info("Phi-3 unloaded after idle period.")

def _schedule_unload():
    global _unload_timer
    if _unload_timer:
        _unload_timer.cancel()
    _unload_timer = threading.Timer(IDLE_UNLOAD_SECONDS, _do_unload)
    _unload_timer.daemon = True
    _unload_timer.start()

def _on_query_started():
    """Called before every query to ensure model is loaded."""
    global _phi3
    if _phi3 and not _phi3.is_loaded:
        logging.getLogger(__name__).info("Reloading Phi-3 on demand...")
        _phi3.load()
    _schedule_unload()

def main():
    global _phi3
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

    _phi3 = Phi3Engine()
    summarizer = None
    try:
        _phi3.load()
        summarizer = Summarizer(_phi3)
        _schedule_unload()  # Start the idle timer after initial load
    except Exception as e:
        log.warning(f"Phi-3 engine failed to load: {e}. Summarization disabled.")

    file_watcher = FileWatcher(config.WATCH_DIRS, store, embedder, summarizer)
    
    log.info("Running first-run bulk index...")
    try:
        file_watcher.bulk_index_directory()
    except Exception as e:
        log.warning("Bulk index failed: %s — continuing anyway", e)
    log.info("Bulk index done. Starting file watcher...")
        
    file_watcher.start_background()

    activity_monitor = ActivityMonitor(store=store)
    activity_monitor.set_enabled(config.DEFAULT_MODE == "memory")
    activity_monitor.start_background()

    def on_screenshot_taken(capture):
        """Called by ScreenshotEngine after a successful capture."""
        if not capture["ocr_text"] and not capture["app_name"]:
            return  # nothing to store

        # Get summary if summarizer is available
        summary = None
        if summarizer is not None and capture["ocr_text"]:
            try:
                # Ensure model is loaded for summarization
                _on_query_started()
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

    query_engine = QueryEngine(phi3=_phi3, embedder=embedder, store=store)
    action_router = ActionRouter()

    def handle_query(query_text: str):
        from mnemo.schema import QueryRequest
        
        # Ensure model is loaded before handling query
        _on_query_started()
        
        request: QueryRequest = {
            "query": query_text,
            "top_k": 3,
            "type_filter": None
        }
        print(f"\nProcessing query: '{query_text}'...")
        # Tell UI we are loading
        app.after(0, app.show_loading)
        
        try:
            response = query_engine.handle(request)
            print("\n--- Response ---")
            print(f"Intent classified as: {response['response_type'].upper()}")
            
            if response["response_type"] == "action":
                print(f"Action Detected: {response.get('action')}")
                action_payload = response.get("action")
                if action_payload:
                    action_router.execute(action_payload)
                app.after(0, app.hide_window)
            else:
                print(f"Confidence: {response.get('confidence', 'none').upper()}")
                print(f"\nAnswer:\n{response.get('text', '')}")
                app.after(0, lambda: app.render_response(response))
                
            print("----------------\n")
        except Exception as e:
            print(f"Query failed: {e}")
            app.after(0, app.hide_window)

    # Initialize UI on the main thread
    app = MnemoOverlay(on_submit=handle_query)

    def on_summon():
        log.info("summon fired")
        # CustomTkinter needs to run GUI updates on the main thread
        app.after(0, app.show_window)

    def on_quit():
        app.quit()

    def on_mode_change(is_memory_mode: bool):
        activity_monitor.set_enabled(is_memory_mode)

    tray = TrayDaemon(
        on_quit=on_quit, 
        on_summon=on_summon,
        on_mode_change=on_mode_change,
        initial_memory_mode=(config.DEFAULT_MODE == "memory")
    )
    tray.start_background()

    hotkey = HotkeyManager(
        on_summon=on_summon, 
        on_screenshot=lambda: screenshot_engine.capture()
    )
    hotkey.start_background()

    log.info("Mnemo is running. Press Ctrl+Space to summon.")
    
    try:
        app.mainloop()
    except KeyboardInterrupt:
        log.info("Keyboard interrupt received.")
    finally:
        log.info("Shutting down...")
        if _unload_timer:
            _unload_timer.cancel()
        activity_monitor.shutdown()
        store.close()
        tray.shutdown()
        sys.exit(0)

if __name__ == "__main__":
    main()

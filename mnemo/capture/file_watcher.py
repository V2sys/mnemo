"""
mnemo/capture/file_watcher.py
Owner: Vinayak

Monitor watched directories for new/modified files.
Extract text from supported types, hand off to the embedder + store.

Pipeline:
    watchdog event → extract_text() → hash + dedup → embedder.encode() → store.save()

Runs on its own thread (watchdog manages this).
"""

import hashlib
import json
import logging
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from mnemo.ai.summarizer import Summarizer
from mnemo.memory.embedder import Embedder
from mnemo.memory.store import MemoryStore
from mnemo.schema import (
    FILE_SUMMARY_CHAR_THRESHOLD,
    SUPPORTED_FILE_TYPES,
    MemoryRecord,
)

log = logging.getLogger(__name__)


class FileWatcher(FileSystemEventHandler):
    def __init__(self, watch_dirs: tuple[Path, ...], store: MemoryStore, embedder: Embedder, summarizer: Summarizer = None) -> None:
        self.watch_dirs = watch_dirs
        self._store = store
        self._embedder = embedder
        self._summarizer = summarizer
        self._observer = None

    def start_background(self) -> None:
        """Start watchdog observers on each directory."""
        self._observer = Observer()
        for d in self.watch_dirs:
            p = Path(d)
            if p.exists():
                self._observer.schedule(self, str(p), recursive=True)
                log.info(f"Watching directory: {p}")
        self._observer.start()

    def bulk_index_directory(self) -> None:
        """
        Scan all WATCH_DIRS recursively on startup and index any
        file not already in the store. Skips files whose content
        hash is already present (dedup). Runs once on first boot.
        Called from __main__.py before start_background().
        """
        total = 0
        skipped = 0
        errors = 0

        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                log.warning("Watch dir does not exist: %s", watch_dir)
                continue

            log.info("Bulk indexing: %s", watch_dir)
            for path in watch_dir.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in SUPPORTED_FILE_TYPES:
                    continue
                # Skip files larger than 10MB — too slow to index at startup
                if path.stat().st_size > 10 * 1024 * 1024:
                    log.debug("Skipping large file: %s", path.name)
                    skipped += 1
                    continue
                try:
                    self._process(path)
                    total += 1
                except Exception as e:
                    log.warning("Bulk index error for %s: %s", path.name, e)
                    errors += 1

        log.info(
            "Bulk index complete — indexed: %d, skipped: %d, errors: %d",
            total, skipped, errors
        )

    def on_modified(self, event) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in SUPPORTED_FILE_TYPES:
            return
        try:
            self._process(path)
        except Exception as e:
            log.error(f"Error processing {path}: {e}")

    def on_created(self, event) -> None:
        self.on_modified(event)

    def _process(self, path: Path) -> None:
        """Extract text and pass to the pipeline."""
        text = extract_text(path)
        if not text or not text.strip():
            return
            
        content_hash = hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()
        
        existing_id = self._store.find_by_hash(content_hash)
        if existing_id is not None:
            log.info(f"skipped (unchanged): {path}")
            return
            
        # Prepend the filename so the vector database and the summarizer know what file this is!
        content_with_metadata = f"File Name: {path.name}\n\n{text}"
        
        embedding = self._embedder.encode(content_with_metadata)
        
        summary = None
        if self._summarizer is not None and len(text) > FILE_SUMMARY_CHAR_THRESHOLD:
            try:
                from mnemo.ai.phi3 import inference_pool
                future = inference_pool.submit(self._summarizer.summarize, content_with_metadata)
                summary = future.result(timeout=60)
                log.info(f"Summary generated for {path.name}")
            except Exception as e:
                log.warning(f"Summarization failed for {path.name}: {e}")
                summary = None
            
        record: MemoryRecord = {
            "type": "file",
            "source": str(path),
            "content_hash": content_hash,
            "raw_text": text,
            "raw_text_expires": 0,
            "summary": summary,
            "timestamp": int(time.time()),
            "metadata": json.dumps({"filename": path.name})
        }
        
        self._store.save_memory(record, embedding)
        log.info(f"indexed: {path.name}")


def extract_text(path: Path) -> str:
    """Extract text from supported file types."""
    try:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    ext = page.extract_text()
                    if ext:
                        pages_text.append(ext)
                return "\n".join(pages_text).strip()
        elif suffix == ".docx":
            import docx
            doc = docx.Document(path)
            return "\n".join([p.text for p in doc.paragraphs]).strip()
        elif suffix in (".txt", ".md"):
            return path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception as e:
        log.warning(f"Failed to extract text from {path}: {e}")
        return ""
    return ""

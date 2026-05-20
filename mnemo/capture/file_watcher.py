"""
mnemo/capture/file_watcher.py
Owner: Vinayak

Monitor watched directories for new/modified files.
Extract text from supported types, hand off to the embedder + store.

Pipeline:
    watchdog event → extract_text() → hash + dedup → embedder.encode() → store.save()

Runs on its own thread (watchdog manages this).
"""

import logging
import hashlib
import time
import json
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from mnemo.schema import SUPPORTED_FILE_TYPES, FileCapture, MemoryRecord, FILE_SUMMARY_CHAR_THRESHOLD
from mnemo.memory.store import MemoryStore
from mnemo.memory.embedder import Embedder

log = logging.getLogger(__name__)


class FileWatcher(FileSystemEventHandler):
    def __init__(self, watch_dirs: tuple[Path, ...], store: MemoryStore, embedder: Embedder) -> None:
        self.watch_dirs = watch_dirs
        self._store = store
        self._embedder = embedder
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
            
        embedding = self._embedder.encode(text)
        
        summary = None
        if len(text) > FILE_SUMMARY_CHAR_THRESHOLD:
            summary = "pending"
            
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

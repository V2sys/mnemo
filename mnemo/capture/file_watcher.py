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
from pathlib import Path

from watchdog.events import FileSystemEventHandler

from mnemo.schema import SUPPORTED_FILE_TYPES, FileCapture

log = logging.getLogger(__name__)


class FileWatcher(FileSystemEventHandler):
    def __init__(self, watch_dirs: tuple[Path, ...]) -> None:
        self.watch_dirs = watch_dirs

    def start_background(self) -> None:
        """Start watchdog observers on each directory."""
        # TODO(week 1):
        # from watchdog.observers import Observer
        # observer = Observer()
        # for d in self.watch_dirs:
        #     observer.schedule(self, str(d), recursive=True)
        # observer.start()
        raise NotImplementedError("Vinayak — week 1 deliverable")

    def on_modified(self, event) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in SUPPORTED_FILE_TYPES:
            return
        self._process(path)

    def on_created(self, event) -> None:
        self.on_modified(event)

    def _process(self, path: Path) -> None:
        """Extract text and pass to the pipeline."""
        # TODO(week 1):
        # 1. text = extract_text(path)
        # 2. compute MD5 hash
        # 3. check if hash already in store — skip if identical
        # 4. embed via embedder.encode(text)
        # 5. store.save(MemoryRecord)
        raise NotImplementedError("Vinayak — week 1 deliverable")


def extract_text(path: Path) -> str:
    """Extract text from supported file types."""
    # TODO(week 1):
    # if path.suffix == ".pdf": use pdfplumber
    # if path.suffix == ".docx": use python-docx
    # if path.suffix in (".txt", ".md"): read directly
    raise NotImplementedError("Vinayak — week 1 deliverable")

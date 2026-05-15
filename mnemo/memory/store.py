"""
mnemo/memory/store.py
Owner: Vinayak

SQLite + sqlite-vec memory store. Thread-safe.
Single source of truth for everything Mnemo remembers.

Both layers (Vinayak's capture pipeline, Vedansh's query engine) read/write here.
"""

import logging
import sqlite3
import threading
import time
from typing import Optional

import numpy as np

from mnemo.config import DB_PATH
from mnemo.schema import (
    SCHEMA_SQL,
    MemoryRecord,
    QuerySource,
    MemoryType,
    RAW_TEXT_RETENTION_DAYS,
)

log = logging.getLogger(__name__)


class MemoryStore:
    def __init__(self) -> None:
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.Lock()

    def open(self) -> None:
        """Open the SQLite connection, load sqlite-vec, run schema."""
        # TODO(week 1):
        # self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        # import sqlite_vec
        # sqlite_vec.load(self._conn)
        # self._conn.executescript(SCHEMA_SQL)
        raise NotImplementedError("Vinayak — week 1 deliverable")

    # ─── Write ─────────────────────────────────────────────────

    def save_memory(self, record: MemoryRecord, embedding: np.ndarray) -> int:
        """Insert a memory + its embedding. Returns the new memory_id."""
        # TODO(week 1):
        # with self._lock:
        #   1. INSERT INTO memories (...) VALUES (...) RETURNING id
        #   2. INSERT INTO embeddings (memory_id, vector) VALUES (?, ?)
        #   3. Use float32 .tobytes() for the vector blob
        raise NotImplementedError("Vinayak — week 1 deliverable")

    def save_activity(self, app_name: str, window_title: str) -> None:
        """Insert an activity log entry. No embedding."""
        # TODO(week 3): simple INSERT into activity_log
        raise NotImplementedError("Vinayak — week 3 deliverable")

    # ─── Read ──────────────────────────────────────────────────

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int,
        type_filter: Optional[list[MemoryType]] = None,
    ) -> list[QuerySource]:
        """
        Vector similarity search.
        Returns top_k QuerySource records ordered by similarity DESC.
        """
        # TODO(week 2):
        # Use sqlite-vec's vec_distance_cosine or KNN
        # JOIN embeddings → memories
        # If type_filter, add WHERE type IN (...)
        # Return as list of QuerySource dicts (include similarity)
        raise NotImplementedError("Vinayak — week 2 deliverable")

    def find_by_hash(self, content_hash: str) -> Optional[int]:
        """Lookup memory_id by content_hash. Used for file dedup."""
        # TODO(week 1)
        raise NotImplementedError("Vinayak — week 1 deliverable")

    # ─── Maintenance ───────────────────────────────────────────

    def purge_expired_raw_text(self) -> int:
        """
        Run on startup. NULLs out raw_text past its expiry.
        Summaries and embeddings remain intact.
        """
        # TODO(week 2):
        # UPDATE memories SET raw_text = NULL
        # WHERE raw_text_expires < ? AND raw_text IS NOT NULL
        # RETURNING COUNT(*)
        raise NotImplementedError("Vinayak — week 2 deliverable")

    def close(self) -> None:
        if self._conn:
            self._conn.close()

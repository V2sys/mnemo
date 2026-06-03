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

import mnemo.config
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
        self._has_vec = False

    def open(self) -> None:
        """Open the SQLite connection, load sqlite-vec, run schema."""
        mnemo.config.ensure_dirs()
        self._conn = sqlite3.connect(mnemo.config.DB_PATH, check_same_thread=False)
        
        try:
            import sqlite_vec
            sqlite_vec.load(self._conn)
            self._has_vec = True
        except ImportError:
            log.warning("sqlite_vec not found. Falling back to numpy for vector search.")
        except Exception as e:
            log.warning(f"Failed to load sqlite_vec: {e}. Falling back to numpy for vector search.")

        self._conn.executescript(SCHEMA_SQL)
        self._conn.execute("PRAGMA journal_mode=WAL")

    # ─── Write ─────────────────────────────────────────────────

    def save_memory(self, record: MemoryRecord, embedding: np.ndarray) -> int:
        """Insert a memory + its embedding. Returns the new memory_id."""
        with self._lock:
            cursor = self._conn.cursor()
            
            raw_text_expires = int(time.time()) + RAW_TEXT_RETENTION_DAYS * 86400
            
            cursor.execute(
                """
                INSERT INTO memories (type, source, content_hash, raw_text, raw_text_expires, summary, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["type"],
                    record["source"],
                    record["content_hash"],
                    record["raw_text"],
                    raw_text_expires,
                    record["summary"],
                    record["timestamp"],
                    record["metadata"]
                )
            )
            memory_id = cursor.lastrowid
            
            vector_blob = embedding.astype(np.float32).tobytes()
            cursor.execute(
                "INSERT INTO embeddings (memory_id, vector) VALUES (?, ?)",
                (memory_id, vector_blob)
            )
            
            self._conn.commit()
            return memory_id

    def save_activity(self, app_name: str, window_title: str) -> None:
        """Insert an activity log entry. No embedding."""
        with self._lock:
            self._conn.execute(
                "INSERT INTO activity_log (app_name, window_title, timestamp) VALUES (?, ?, ?)",
                (app_name, window_title, int(time.time()))
            )
            self._conn.commit()

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
        with self._lock:
            cursor = self._conn.cursor()
            query_blob = query_vector.astype(np.float32).tobytes()
            
            if self._has_vec:
                base_query = "SELECT m.type, m.summary, m.timestamp, vec_distance_cosine(e.vector, ?) as similarity, m.raw_text FROM embeddings e JOIN memories m ON e.memory_id = m.id"
                params = [query_blob]
            else:
                base_query = "SELECT m.type, m.summary, m.timestamp, e.vector as vec_blob, m.raw_text FROM embeddings e JOIN memories m ON e.memory_id = m.id"
                params = []
                
            if type_filter is not None and len(type_filter) > 0:
                placeholders = ",".join("?" * len(type_filter))
                base_query += f" WHERE m.type IN ({placeholders})"
                params.extend(type_filter)
                
            if self._has_vec:
                base_query += " ORDER BY similarity ASC LIMIT ?"
                params.append(top_k)
                
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
            results: list[QuerySource] = []
            if self._has_vec:
                for r in rows:
                    summary_val = r[1]
                    raw_text_val = r[4]
                    if not summary_val or summary_val == "pending":
                        summary_val = (raw_text_val or "")[:500] + ("..." if raw_text_val and len(raw_text_val) > 500 else "")
                        
                    results.append({
                        "type": r[0],
                        "summary": summary_val,
                        "timestamp": r[2],
                        "similarity": float(r[3])
                    })
            else:
                scored_rows = []
                for r in rows:
                    v = np.frombuffer(r[3], dtype=np.float32)
                    sim = 1.0 - np.dot(query_vector, v)
                    
                    summary_val = r[1]
                    raw_text_val = r[4]
                    if not summary_val or summary_val == "pending":
                        summary_val = (raw_text_val or "")[:500] + ("..." if raw_text_val and len(raw_text_val) > 500 else "")
                        
                    scored_rows.append((sim, {
                        "type": r[0],
                        "summary": summary_val,
                        "timestamp": r[2]
                    }))
                scored_rows.sort(key=lambda x: x[0])
                for sim, item in scored_rows[:top_k]:
                    item["similarity"] = float(sim)
                    results.append(item)
                    
            return results

    def find_by_hash(self, content_hash: str) -> Optional[int]:
        """Lookup memory_id by content_hash. Used for file dedup."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT id FROM memories WHERE content_hash = ? LIMIT 1", (content_hash,))
            row = cursor.fetchone()
            return row[0] if row else None

    # ─── Maintenance ───────────────────────────────────────────

    def purge_expired_raw_text(self) -> int:
        """
        Run on startup. NULLs out raw_text past its expiry.
        Summaries and embeddings remain intact.
        """
        with self._lock:
            cursor = self._conn.cursor()
            current_time = int(time.time())
            cursor.execute(
                "UPDATE memories SET raw_text = NULL WHERE raw_text_expires < ? AND raw_text IS NOT NULL",
                (current_time,)
            )
            count = cursor.rowcount
            self._conn.commit()
            log.info(f"Purged {count} expired raw text records.")
            return count

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

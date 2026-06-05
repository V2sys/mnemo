"""
mnemo/schema.py

SHARED CONTRACTS — owned jointly by Vinayak & Vedansh.

DO NOT modify this file without discussing with the other developer.
Any change here ripples through both layers and can silently break things.

All data shapes, enums, and tunable thresholds live here. Both layers
import from here. Neither layer defines its own version of anything below.
"""

from typing import Literal, TypedDict

# ─────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────

MemoryType = Literal["file", "screenshot", "activity"]
ResponseType = Literal["answer", "action", "not_found"]
ActionType = Literal["file_open", "app_launch", "system_command"]

MEMORY_TYPES: tuple[MemoryType, ...] = ("file", "screenshot", "activity")
RESPONSE_TYPES: tuple[ResponseType, ...] = ("answer", "action", "not_found")
ACTION_TYPES: tuple[ActionType, ...] = ("file_open", "app_launch", "system_command")


# ─────────────────────────────────────────────────────────────────
# Tunable thresholds
# ─────────────────────────────────────────────────────────────────

# Search
SIMILARITY_THRESHOLD: float = 0.4
TOP_K_DEFAULT: int = 3

# Embeddings — all-MiniLM-L6-v2 output dimension
EMBEDDING_DIM: int = 384

# Summarization
FILE_SUMMARY_CHAR_THRESHOLD: int = 1500     # Only summarize files larger than this
SCREENSHOT_ALWAYS_SUMMARIZE: bool = True    # OCR text is always messy
SUMMARY_MAX_CHARS: int = 500

# Raw text retention
RAW_TEXT_RETENTION_DAYS: int = 7            # Auto-purged; summary + embedding kept

# Activity monitoring
ACTIVITY_POLL_INTERVAL_SEC: int = 2

# Screenshot deduplication
SCREENSHOT_HASH_DIFF_THRESHOLD: float = 0.2  # 20% perceptual difference required

# Not-found behaviour — always return closest as low-confidence
NOT_FOUND_FALLBACK: bool = True

# Supported file types for indexing
SUPPORTED_FILE_TYPES: tuple[str, ...] = (".pdf", ".docx", ".txt", ".md")


# ─────────────────────────────────────────────────────────────────
# Data contracts — between Vinayak's and Vedansh's layers
# ─────────────────────────────────────────────────────────────────

class FileCapture(TypedDict):
    """Vinayak's file_watcher → embedder. Internal to Vinayak's layer."""
    type: MemoryType            # "file"
    path: str
    content: str
    timestamp: int              # Unix epoch seconds


class ScreenshotCapture(TypedDict):
    """Vinayak's screenshot.py → Vedansh's summarizer."""
    type: MemoryType            # "screenshot"
    image_bytes: bytes          # mss capture serialized
    ocr_text: str               # already extracted by Vinayak
    app_name: str
    window_title: str
    timestamp: int


class MemoryRecord(TypedDict):
    """Final shape stored in SQLite. Anyone writing to store.py uses this."""
    type: MemoryType
    source: str                  # file path, or "app_name - window_title"
    content_hash: str            # MD5 of raw_text, used for dedup
    raw_text: str | None      # nullable after RAW_TEXT_RETENTION_DAYS
    raw_text_expires: int        # Unix timestamp
    summary: str | None       # None for activity, may be None for short files
    timestamp: int
    metadata: str                # JSON string


class QueryRequest(TypedDict):
    """UI → Vedansh's query_engine."""
    query: str
    top_k: int                              # default TOP_K_DEFAULT
    type_filter: list[MemoryType] | None # None = all types


class QuerySource(TypedDict):
    """A single retrieved memory shown to the user as a source."""
    type: MemoryType
    source: str
    summary: str
    timestamp: int
    similarity: float


class ActionPayload(TypedDict):
    """When response_type == 'action', this is what the router executes."""
    type: ActionType
    target: str                  # path, app name, or command


class QueryResponse(TypedDict):
    """Vedansh's query_engine → UI. The shape UI knows how to render."""
    response_type: ResponseType
    text: str
    sources: list[QuerySource]
    action: ActionPayload | None
    confidence: Literal["high", "low"]   # "low" when below SIMILARITY_THRESHOLD


# ─────────────────────────────────────────────────────────────────
# SQL schema — created on first run
# ─────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memories (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    type              TEXT NOT NULL,
    source            TEXT,
    content_hash      TEXT,
    raw_text          TEXT,
    raw_text_expires  INTEGER,
    summary           TEXT,
    timestamp         INTEGER NOT NULL,
    metadata          TEXT
);

CREATE INDEX IF NOT EXISTS idx_memories_type      ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_hash      ON memories(content_hash);
CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp);
CREATE INDEX IF NOT EXISTS idx_memories_expires   ON memories(raw_text_expires);

CREATE TABLE IF NOT EXISTS embeddings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id  INTEGER NOT NULL,
    vector     BLOB NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_embeddings_memory ON embeddings(memory_id);

CREATE TABLE IF NOT EXISTS activity_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name      TEXT NOT NULL,
    window_title  TEXT NOT NULL,
    timestamp     INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp);
"""

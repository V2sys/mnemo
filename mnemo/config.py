"""
mnemo/config.py

Runtime paths and user-configurable settings.
Anything that might change between machines or users goes here.
"""

import os
from pathlib import Path

# Base directory for all Mnemo runtime data
MNEMO_HOME = Path(os.environ.get("MNEMO_HOME", Path.home() / ".mnemo"))

# Subdirectories
DATA_DIR = MNEMO_HOME / "data"
MODELS_DIR = MNEMO_HOME / "models"
LOGS_DIR = MNEMO_HOME / "logs"

# Database
DB_PATH = DATA_DIR / "mnemo.db"

# Model paths — both devs need these on disk; see docs/setup.md for download
PHI3_MODEL_PATH = MODELS_DIR / "phi-3-mini-4k-instruct-q4.gguf"
EMBEDDING_MODEL_PATH = MODELS_DIR / "all-MiniLM-L6-v2.onnx"
EMBEDDING_TOKENIZER_PATH = MODELS_DIR / "all-MiniLM-L6-v2-tokenizer.json"

# Hotkey
SUMMON_HOTKEY = "ctrl+space"
SCREENSHOT_HOTKEY = "ctrl+shift+space"

# Indexing — directories to watch (Vinayak: expose this in UI later)
WATCH_DIRS: tuple[Path, ...] = (
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Desktop",
)

# Activity mode default — "focus" (hotkey only) or "memory" (passive)
DEFAULT_MODE = "focus"


def ensure_dirs() -> None:
    """Create runtime directories if they don't exist. Called on startup."""
    for d in (MNEMO_HOME, DATA_DIR, MODELS_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)

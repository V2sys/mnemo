"""
tests/test_checkpoint4.py
Vinayak's Week 4 Checkpoint Test.
"""

import os
import sys
import time
import shutil
import tempfile
import logging
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mnemo import config
from mnemo.capture.file_watcher import FileWatcher
from mnemo.memory.store import MemoryStore
from mnemo.memory.embedder import Embedder

# Configure logging to be quiet
logging.basicConfig(level=logging.ERROR)

def run_tests():
    print("\nStarting Week 4 Checkpoint Tests...")
    
    tmp = Path(tempfile.mkdtemp())
    original_db_path = config.DB_PATH
    
    results_map = {
        "TEST 1": "FAIL",
        "TEST 2": "FAIL",
        "TEST 3": "FAIL"
    }

    try:
        config.DB_PATH = tmp / "week4.db"
        store = MemoryStore()
        store.open()
        
        embedder = Embedder()
        try:
            embedder.load()
        except FileNotFoundError:
            print("SKIPPING tests requiring Embedder (models not found)")
            return

        watcher = FileWatcher(
            watch_dirs=(tmp,),
            store=store,
            embedder=embedder,
            summarizer=None
        )

        # ──────────────────────────────────────────────────────────────
        # TEST 1: Bulk indexing works
        # ──────────────────────────────────────────────────────────────
        print("\n[TEST 1] Testing bulk indexing...")
        for i in range(5):
            f = tmp / f"test_{i}.txt"
            f.write_text(f"This is test document {i} about artificial intelligence.")
            
        watcher.bulk_index_directory()
        
        cursor = store._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories WHERE type='file'")
        count = cursor.fetchone()[0]
        assert count == 5, f"Expected 5 indexed files, got {count}"
        
        # Dedup check
        watcher.bulk_index_directory()
        cursor.execute("SELECT COUNT(*) FROM memories WHERE type='file'")
        count_after = cursor.fetchone()[0]
        assert count_after == 5, f"Dedup failed — expected 5, got {count_after}"

        results_map["TEST 1"] = "PASS"
        print("TEST 1 PASSED — bulk indexing indexed 5 files, dedup blocked duplicates")

        # ──────────────────────────────────────────────────────────────
        # TEST 2: Large files are skipped
        # ──────────────────────────────────────────────────────────────
        print("\n[TEST 2] Testing large file handling...")
        large_file = tmp / "large_file.txt"
        # Create an 11MB file by writing 11 million 'A's
        large_file.write_text("A" * (11 * 1024 * 1024))
        
        watcher.bulk_index_directory()
        
        cursor.execute("SELECT COUNT(*) FROM memories WHERE source=?", (str(large_file),))
        count = cursor.fetchone()[0]
        assert count == 0, "Large file was incorrectly indexed"

        results_map["TEST 2"] = "PASS"
        print("TEST 2 PASSED — large files correctly skipped")

        # ──────────────────────────────────────────────────────────────
        # TEST 3: Broken files don't crash bulk index
        # ──────────────────────────────────────────────────────────────
        print("\n[TEST 3] Testing broken file handling...")
        broken_dir = tmp / "broken"
        broken_dir.mkdir()
        
        broken_file = broken_dir / "broken.pdf"
        broken_file.write_bytes(b"garbage bytes not a pdf")
        
        for i in range(3):
            valid = broken_dir / f"valid_{i}.txt"
            valid.write_text(f"Valid file {i}")
            
        watcher.watch_dirs = (broken_dir,)
        # This should complete without raising an exception
        watcher.bulk_index_directory()
        
        cursor.execute("SELECT COUNT(*) FROM memories WHERE source LIKE ?", (f"%valid_%.txt",))
        count = cursor.fetchone()[0]
        assert count == 3, f"Expected 3 valid files indexed, got {count}"

        results_map["TEST 3"] = "PASS"
        print("TEST 3 PASSED — broken files skipped, valid files indexed")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        store.close()
        config.DB_PATH = original_db_path
        shutil.rmtree(tmp)

        # Print Summary Box
        box_width = 44
        print("\n  " + "╔" + "═" * (box_width - 2) + "╗")
        print("  ║" + "WEEK 4 CHECKPOINT — DONE".center(box_width - 2) + "║")
        print("  " + "╠" + "═" * (box_width - 2) + "╣")
        print(f"  ║  TEST 1  Bulk indexing             {results_map['TEST 1']:>4}  ║")
        print(f"  ║  TEST 2  Skip large files          {results_map['TEST 2']:>4}  ║")
        print(f"  ║  TEST 3  Skip broken files         {results_map['TEST 3']:>4}  ║")
        print("  " + "╚" + "═" * (box_width - 2) + "╝")

if __name__ == "__main__":
    run_tests()

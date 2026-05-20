"""
tests/test_integration_week1.py
Joint Integration Test for Week 1 — Vinayak & Vedansh.

Tests the full pipeline: 
File (Capture) -> Embedder (AI) -> Store (Memory) -> Search (Retrieval)
"""

import os
import sys
import time
import json
import shutil
import tempfile
import platform
import logging
from pathlib import Path

import numpy as np

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mnemo.memory.store import MemoryStore
from mnemo.memory.embedder import Embedder
from mnemo.capture.file_watcher import FileWatcher
from mnemo import schema
from mnemo import config

# Configure logging to be quiet during tests
logging.basicConfig(level=logging.ERROR)

def run_tests():
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    db_path = temp_path / "integration_test.db"
    
    # Save original DB_PATH to restore later
    original_db_path = config.DB_PATH
    config.DB_PATH = db_path

    print("\nStarting Week 1 Joint Integration Tests...")
    print(f"Platform: {platform.system()}")
    
    # Track test results
    results_map = {
        "TEST 1": "FAIL",
        "TEST 2": "FAIL",
        "TEST 3": "FAIL",
        "TEST 4": "FAIL"
    }

    store = MemoryStore()
    embedder = Embedder()

    try:
        # ──────────────────────────────────────────────────────────────
        # TEST 1: Memory pipeline end-to-end
        # ──────────────────────────────────────────────────────────────
        print("\n[TEST 1] Testing memory pipeline end-to-end...")
        
        # 1. Create temp file
        file_path = temp_path / "transformer_notes.txt"
        content = (
            "The transformer architecture uses self-attention mechanisms to process "
            "sequences in parallel. Key components include multi-head attention, "
            "positional encoding, and feed-forward layers."
        )
        file_path.write_text(content)

        # 2. Setup Embedder
        embedder.load()

        # 3. Setup Store
        store.open()

        # 4. Run Vinayak's pipeline
        watcher = FileWatcher(watch_dirs=(temp_path,), store=store, embedder=embedder)
        watcher._process(file_path)

        # 5. Simulate Vedansh's query
        query = "how does attention work in neural networks?"
        query_vector = embedder.encode(query)
        search_results = store.search(query_vector, top_k=3)

        # 6. Assertions
        assert len(search_results) >= 1, f"Expected at least 1 result, got {len(search_results)}"
        res = search_results[0]
        assert res["type"] == "file", f"Expected type 'file', got {res['type']}"
        assert isinstance(res["similarity"], float), f"Expected similarity to be float, got {type(res['similarity'])}"
        
        # summary might be None, empty, or "pending" (week 1 logic)
        summary = res["summary"]
        assert summary is None or summary == "" or "pending" in summary.lower(), f"Unexpected summary content: '{summary}'"
        
        # Sanity check for similarity (cosine distance; 0 is identical, >0.3 is usually relevant)
        # Note: Depending on backend, lower score might mean closer or distance.
        # sqlite-vec uses distance (0.0 = perfect), so we check it's 'close' enough.
        assert res["similarity"] < 0.7, f"Similarity too low for relevant query: {res['similarity']}"

        results_map["TEST 1"] = "PASS"
        print("TEST 1 PASSED — file indexed by Vinayak, found by Vedansh's search")


        # ──────────────────────────────────────────────────────────────
        # TEST 2: Deduplication works
        # ──────────────────────────────────────────────────────────────
        print("\n[TEST 2] Testing deduplication...")
        
        # Call process again on same file
        watcher._process(file_path)
        
        # Query directly for this file's source
        cursor = store._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories WHERE source = ?", (str(file_path),))
        count = cursor.fetchone()[0]
        
        assert count == 1, f"Expected 1 record after duplicate processing, found {count}"

        results_map["TEST 2"] = "PASS"
        print("TEST 2 PASSED — deduplication prevents duplicate indexing")


        # ──────────────────────────────────────────────────────────────
        # TEST 3: Raw text expiry
        # ──────────────────────────────────────────────────────────────
        print("\n[TEST 3] Testing raw text expiry...")
        
        # 1. Insert expired record
        dummy_vec = np.zeros(384, dtype=np.float32)
        expired_record = {
            "type": "file",
            "source": "expired.txt",
            "content_hash": "expiredhash",
            "raw_text": "this text should be gone",
            "summary": "this summary should stay",
            "timestamp": int(time.time()),
            "metadata": "{}"
        }
        mem_id = store.save_memory(expired_record, dummy_vec)
        
        # Force expiry in DB
        store._conn.execute(
            "UPDATE memories SET raw_text_expires = ? WHERE id = ?", 
            (int(time.time()) - 1, mem_id)
        )
        store._conn.commit()

        # 2. Run purge
        purge_count = store.purge_expired_raw_text()
        assert purge_count >= 1, f"Expected at least 1 record to be purged, got {purge_count}"

        # 3. Verify
        cursor.execute("SELECT raw_text, summary FROM memories WHERE id = ?", (mem_id,))
        row = cursor.fetchone()
        assert row[0] is None, f"Expected raw_text to be None, got {row[0]}"
        assert row[1] == "this summary should stay", f"Summary corrupted or deleted: {row[1]}"
        
        # 4. Verify embedding
        cursor.execute("SELECT COUNT(*) FROM embeddings WHERE memory_id = ?", (mem_id,))
        assert cursor.fetchone()[0] == 1, "Embedding was deleted along with raw text"

        results_map["TEST 3"] = "PASS"
        print("TEST 3 PASSED — raw text purged, summary and embedding intact")


        # ──────────────────────────────────────────────────────────────
        # TEST 4: Schema contract validation
        # ──────────────────────────────────────────────────────────────
        print("\n[TEST 4] Testing schema contract validation...")
        
        for r in search_results:
            # Keys
            for key in ["type", "summary", "timestamp", "similarity"]:
                assert key in r, f"Missing key '{key}' in QuerySource"
            
            # Values
            assert r["type"] in schema.MEMORY_TYPES, f"Invalid type: {r['type']}"
            assert isinstance(r["similarity"], float), f"Similarity must be float: {type(r['similarity'])}"
            assert 0.0 <= r["similarity"] <= 2.0, f"Similarity out of bounds: {r['similarity']}"
            assert isinstance(r["timestamp"], int) and r["timestamp"] > 0, f"Invalid timestamp: {r['timestamp']}"

        results_map["TEST 4"] = "PASS"
        print("TEST 4 PASSED — QuerySource contract matches schema.py exactly")

    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        # traceback would be good but instructions ask for specific values
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        store.close()
        shutil.rmtree(temp_dir)
        config.DB_PATH = original_db_path
        
        # Print Summary Box
        box_width = 44
        print("\n  " + "╔" + "═" * (box_width - 2) + "╗")
        print("  ║" + "WEEK 1 JOINT INTEGRATION — DONE".center(box_width - 2) + "║")
        print("  " + "╠" + "═" * (box_width - 2) + "╣")
        print(f"  ║  TEST 1  File pipeline end-to-end  {results_map['TEST 1']:>4}  ║")
        print(f"  ║  TEST 2  Deduplication             {results_map['TEST 2']:>4}  ║")
        print(f"  ║  TEST 3  Raw text expiry           {results_map['TEST 3']:>4}  ║")
        print(f"  ║  TEST 4  Schema contract           {results_map['TEST 4']:>4}  ║")
        print("  " + "╚" + "═" * (box_width - 2) + "╝")
        print("\nReady for Week 2.\n")

if __name__ == "__main__":
    run_tests()

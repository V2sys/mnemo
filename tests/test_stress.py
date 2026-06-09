"""
tests/test_stress.py
Stress testing Mnemo's memory, capture, and retrieval layers.
"""

import os
import sys
import time
import shutil
import tempfile
import threading
import statistics
import platform
import logging
from pathlib import Path

import numpy as np
import psutil

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mnemo import config, schema
from mnemo.memory.store import MemoryStore
from mnemo.memory.embedder import Embedder
from mnemo.capture.file_watcher import FileWatcher
from mnemo.capture.activity import ActivityMonitor

# Configure logging to be quiet
logging.basicConfig(level=logging.ERROR)

def run_stress_tests():
    print("\nStarting Mnemo Stress Tests...")
    print(f"Platform: {platform.system()}")

    tmp = Path(tempfile.mkdtemp())
    original_db_path = config.DB_PATH
    
    results = {
        "test1": "FAIL",
        "test2": "FAIL",
        "test3": "FAIL",
        "test4": "FAIL",
        "test5": "FAIL",
        "query_avg": 0,
        "query_p95": 0,
        "write_time": 0,
        "ram_delta": 0
    }

    try:
        # ──────────────────────────────────────────────────────────────
        # STRESS TEST 1: Concurrent writes
        # ──────────────────────────────────────────────────────────────
        print("\n[STRESS TEST 1] Concurrent writes (100 total)...")
        config.DB_PATH = tmp / "stress.db"
        store = MemoryStore()
        store.open()
        
        embedder = Embedder()
        try:
            embedder.load()
        except FileNotFoundError:
            print("SKIPPING tests requiring Embedder (models not found)")
            return

        errors = []
        write_count = [0]
        write_lock = threading.Lock()

        def write_worker(worker_id: int, n: int):
            for i in range(n):
                try:
                    vec = np.random.rand(384).astype(np.float32)
                    vec = vec / np.linalg.norm(vec)
                    record = {
                        "type": "file",
                        "source": f"worker{worker_id}_doc{i}.txt",
                        "content_hash": f"hash_{worker_id}_{i}",
                        "raw_text": f"Document {i} from worker {worker_id} " * 10,
                        "raw_text_expires": int(time.time()) + 86400,
                        "summary": f"Summary from worker {worker_id}",
                        "timestamp": int(time.time()),
                        "metadata": "{}"
                    }
                    store.save_memory(record, vec)
                    with write_lock:
                        write_count[0] += 1
                except Exception as e:
                    errors.append(f"Worker {worker_id} write {i}: {e}")

        threads = [threading.Thread(target=write_worker, args=(i, 20)) for i in range(5)]
        t0 = time.time()
        for t in threads: t.start()
        for t in threads: t.join()
        results["write_time"] = time.time() - t0

        assert len(errors) == 0, f"Concurrent write errors:\n" + "\n".join(errors)
        assert write_count[0] == 100, f"Expected 100 writes, got {write_count[0]}"

        cursor = store._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories")
        db_count = cursor.fetchone()[0]
        assert db_count == 100, f"DB has {db_count} records, expected 100"

        results["test1"] = "PASS"
        print(f"STRESS TEST 1 PASSED — 100 concurrent writes in {results['write_time']:.2f}s")

        # ──────────────────────────────────────────────────────────────
        # STRESS TEST 2: Rapid sequential queries
        # ──────────────────────────────────────────────────────────────
        print("\n[STRESS TEST 2] Rapid queries (30 queries against 50 docs)...")
        topics = [
            "machine learning neural networks deep learning",
            "python programming functions classes objects",
            "database sql queries joins transactions",
            "windows operating system processes memory",
            "natural language processing transformers attention",
        ]
        for i in range(50):
            text = topics[i % len(topics)] + f" document number {i} " * 5
            vec = embedder.encode(text)
            record = {
                "type": "file",
                "source": f"doc_{i}.txt",
                "content_hash": f"qhash_{i}",
                "raw_text": text,
                "raw_text_expires": int(time.time()) + 86400,
                "summary": None,
                "timestamp": int(time.time()),
                "metadata": "{}"
            }
            store.save_memory(record, vec)

        queries = [
            "how do neural networks learn?",
            "python object oriented programming",
            "how to join two database tables",
            "windows process management",
            "what is the attention mechanism?",
        ] * 6

        latencies = []
        for q in queries:
            t0 = time.time()
            qvec = embedder.encode(q)
            search_results = store.search(qvec, top_k=3)
            latencies.append(time.time() - t0)
            assert len(search_results) > 0, f"No results for: {q}"

        results["query_avg"] = statistics.mean(latencies) * 1000
        results["query_p95"] = sorted(latencies)[int(0.95 * len(latencies))] * 1000
        
        assert results["query_avg"] < 500, f"Average query too slow: {results['query_avg']:.0f}ms"
        assert results["query_p95"] < 1000, f"P95 too slow: {results['query_p95']:.0f}ms"

        results["test2"] = "PASS"
        print(f"STRESS TEST 2 PASSED — avg={results['query_avg']:.0f}ms p95={results['query_p95']:.0f}ms")

        # ──────────────────────────────────────────────────────────────
        # STRESS TEST 3: Bulk file drop
        # ──────────────────────────────────────────────────────────────
        print("\n[STRESS TEST 3] Bulk file drop (20 files)...")
        tmp_watch = Path(tempfile.mkdtemp())
        config.DB_PATH = tmp / "bulk_test.db"
        store2 = MemoryStore()
        store2.open()

        watcher = FileWatcher(watch_dirs=(tmp_watch,), store=store2, embedder=embedder, summarizer=None)

        errors = []
        for i in range(20):
            f = tmp_watch / f"bulk_{i}.txt"
            f.write_text(f"Bulk file {i} about topic {i % 5}. " * 20)
            try:
                watcher._process(f)
            except Exception as e:
                errors.append(f"File {i}: {e}")

        assert len(errors) == 0, f"Bulk index errors: {errors}"
        
        cursor2 = store2._conn.cursor()
        cursor2.execute("SELECT COUNT(*) FROM memories WHERE type='file'")
        assert cursor2.fetchone()[0] == 20

        # Dedup test
        for i in range(20):
            f = tmp_watch / f"bulk_{i}.txt"
            watcher._process(f)
        cursor2.execute("SELECT COUNT(*) FROM memories WHERE type='file'")
        assert cursor2.fetchone()[0] == 20

        store2.close()
        shutil.rmtree(tmp_watch)
        results["test3"] = "PASS"
        print("STRESS TEST 3 PASSED — 20 files indexed and deduped")

        # ──────────────────────────────────────────────────────────────
        # STRESS TEST 4: Large document
        # ──────────────────────────────────────────────────────────────
        print("\n[STRESS TEST 4] Large document handling (50K chars)...")
        big_text = ("The transformer model processes sequences using multi-head self-attention mechanisms. ") * 600
        vec = embedder.encode(big_text[:512])
        record = {
            "type": "file",
            "source": "big_doc.txt",
            "content_hash": "bighash",
            "raw_text": big_text,
            "raw_text_expires": int(time.time()) - 1,
            "summary": "A large document about transformers",
            "timestamp": int(time.time()),
            "metadata": "{}"
        }
        mem_id = store.save_memory(record, vec)
        
        # Force expiry in DB for purge test (save_memory sets it to future)
        store._conn.execute("UPDATE memories SET raw_text_expires = ? WHERE id = ?", (int(time.time()) - 1, mem_id))
        store._conn.commit()

        qvec = embedder.encode("transformer attention")
        search_results = store.search(qvec, top_k=1)
        assert any(r.get("summary") == "A large document about transformers" for r in search_results)

        purged = store.purge_expired_raw_text()
        assert purged >= 1
        
        cursor.execute("SELECT raw_text, summary FROM memories WHERE id=?", (mem_id,))
        row = cursor.fetchone()
        assert row[0] is None
        assert row[1] == "A large document about transformers"

        results["test4"] = "PASS"
        print("STRESS TEST 4 PASSED — 50K char doc indexed and purged")

        # ──────────────────────────────────────────────────────────────
        # STRESS TEST 5: Activity monitor stability
        # ──────────────────────────────────────────────────────────────
        print("\n[STRESS TEST 5] Activity monitor stability (10s run)...")
        config.DB_PATH = tmp / "activity_stress.db"
        store3 = MemoryStore()
        store3.open()

        process = psutil.Process(os.getpid())
        ram_before = process.memory_info().rss / 1e6

        monitor = ActivityMonitor(store=store3)
        monitor.set_enabled(True)
        
        # Test if we are on Windows for meaningful results
        is_windows = platform.system() == "Windows"
        
        monitor.start_background()
        time.sleep(10)
        monitor.shutdown()
        
        if monitor._thread:
            monitor._thread.join(timeout=3)
            assert not monitor._thread.is_alive(), "Activity monitor thread did not stop cleanly"

        ram_after = process.memory_info().rss / 1e6
        results["ram_delta"] = ram_after - ram_before
        
        # On Linux it skips writing entries but we still test the thread/leak
        if is_windows:
            cursor3 = store3._conn.cursor()
            cursor3.execute("SELECT COUNT(*) FROM activity_log")
            assert cursor3.fetchone()[0] >= 1, "No activity entries logged"
        
        assert results["ram_delta"] < 20, f"Possible memory leak: +{results['ram_delta']:.1f}MB"
        
        store3.close()
        results["test5"] = "PASS"
        print(f"STRESS TEST 5 PASSED — ran 10s, RAM delta={results['ram_delta']:.1f}MB")

    except Exception as e:
        print(f"\n❌ STRESS TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        store.close()
        config.DB_PATH = original_db_path
        shutil.rmtree(tmp)

        # Print Final Summary Box
        box_width = 52
        print("\n  " + "╔" + "═" * (box_width - 2) + "╗")
        print("  ║" + "MNEMO STRESS TEST RESULTS".center(box_width - 2) + "║")
        print("  " + "╠" + "═" * (box_width - 2) + "╣")
        print(f"  ║  TEST 1  Concurrent writes (100)          {results['test1']:>4}  ║")
        print(f"  ║  TEST 2  Query latency (30 queries)       {results['test2']:>4}  ║")
        print(f"  ║  TEST 3  Bulk file index + dedup (20)     {results['test3']:>4}  ║")
        print(f"  ║  TEST 4  Large document (50K chars)       {results['test4']:>4}  ║")
        print(f"  ║  TEST 5  Activity monitor 10s             {results['test5']:>4}  ║")
        print("  " + "╠" + "═" * (box_width - 2) + "╣")
        print(f"  ║  Query avg latency:          {results['query_avg']:>7.0f}ms              ║")
        print(f"  ║  Query p95 latency:          {results['query_p95']:>7.0f}ms              ║")
        print(f"  ║  Concurrent write time:      {results['write_time']:>7.2f}s               ║")
        print(f"  ║  Activity RAM delta:         {results['ram_delta']:>7.1f}MB              ║")
        print("  " + "╚" + "═" * (box_width - 2) + "╝\n")

if __name__ == "__main__":
    run_stress_tests()

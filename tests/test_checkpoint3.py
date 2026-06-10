"""
tests/test_checkpoint3.py
Vinayak's Week 3 Checkpoint Test.
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
from mnemo.capture.activity import ActivityMonitor
from mnemo.memory.store import MemoryStore
from mnemo.schema import ACTIVITY_POLL_INTERVAL_SEC

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def run_tests():
    tmp = Path(tempfile.mkdtemp())
    original_db_path = config.DB_PATH
    
    print("\nStarting Week 3 Checkpoint Tests...")
    
    results_map = {
        "TEST 1": "FAIL",
        "TEST 2": "FAIL",
        "TEST 3": "FAIL",
        "TEST 4": "FAIL"
    }

    try:
        # ──────────────────────────────────────────────────────────────
        # TEST 1 & 2: Activity Monitor
        # ──────────────────────────────────────────────────────────────
        print("\n[TEST 1] Testing activity monitor logging...")
        config.DB_PATH = tmp / "activity_test.db"
        store = MemoryStore()
        store.open()
        
        monitor = ActivityMonitor(store=store)
        monitor.set_enabled(True)
        
        # We might be on Linux, so we need to handle the case where win32gui is missing
        try:
            import win32gui
            monitor.start_background()
            # Wait for at least one poll cycle
            time.sleep(ACTIVITY_POLL_INTERVAL_SEC * 2 + 0.5)
            monitor.shutdown()

            # Check activity_log has at least one entry
            cursor = store._conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM activity_log")
            count = cursor.fetchone()[0]
            if count >= 1:
                results_map["TEST 1"] = "PASS"
                print(f"TEST 1 PASSED — activity monitor logged {count} events")
                
                # Check the entry has valid fields
                cursor.execute("SELECT app_name, window_title, timestamp FROM activity_log LIMIT 1")
                row = cursor.fetchone()
                assert isinstance(row[0], str) and len(row[0]) > 0
                assert isinstance(row[2], int) and row[2] > 0
                
                # TEST 2: No duplicates
                print("\n[TEST 2] Testing activity deduplication...")
                monitor2 = ActivityMonitor(store=store)
                monitor2.set_enabled(True)
                monitor2._last_window = (row[0], row[1]) # Simulate same window
                monitor2.start_background()
                time.sleep(ACTIVITY_POLL_INTERVAL_SEC * 2)
                monitor2.shutdown()
                
                cursor.execute("SELECT COUNT(*) FROM activity_log WHERE window_title = ?", (row[1],))
                count_after = cursor.fetchone()[0]
                if count_after == 1:
                    results_map["TEST 2"] = "PASS"
                    print("TEST 2 PASSED — no duplicate entries for unchanged window")
                else:
                    print(f"TEST 2 FAILED — duplicate entries found: {count_after}")
            else:
                print("TEST 1 FAILED — no activity entries logged")
        except ImportError:
            results_map["TEST 1"] = "SKIP (Linux)"
            results_map["TEST 2"] = "SKIP (Linux)"
            print("TEST 1 & 2 SKIPPED — pywin32 not available on this platform")

        # ──────────────────────────────────────────────────────────────
        # TEST 3: sqlite_vec loading
        # ──────────────────────────────────────────────────────────────
        print("\n[TEST 3] Testing sqlite_vec load authorization...")
        config.DB_PATH = tmp / "vec_test.db"
        store3 = MemoryStore()
        try:
            store3.open()
            # If we get here without "not authorized" exception, it's good
            assert hasattr(store3, '_has_vec')
            results_map["TEST 3"] = "PASS"
            print(f"TEST 3 PASSED — sqlite_vec available: {store3._has_vec}")
        except Exception as e:
            print(f"TEST 3 FAILED — Error loading sqlite_vec: {e}")
        finally:
            store3.close()

        # ──────────────────────────────────────────────────────────────
        # TEST 4: Phi-3 load/unload
        # ──────────────────────────────────────────────────────────────
        print("\n[TEST 4] Testing Phi-3 load/unload lifecycle...")
        if not config.PHI3_MODEL_PATH.exists():
            results_map["TEST 4"] = "SKIP (Model Missing)"
            print("TEST 4 SKIPPED — Phi-3 model file not found")
        else:
            try:
                from mnemo.ai.phi3 import Phi3Engine
                phi3 = Phi3Engine()
                phi3.load()
                assert phi3.is_loaded, "Phi-3 should be loaded"
                print("      Model loaded.")
                
                phi3.unload()
                assert not phi3.is_loaded, "Phi-3 should be unloaded"
                print("      Model unloaded.")
                
                # Reload and verify it works
                phi3.load()
                assert phi3.is_loaded
                print("      Model reloaded.")
                
                result = phi3.generate("Say OK")
                assert len(result) > 0
                phi3.unload()
                results_map["TEST 4"] = "PASS"
                print("TEST 4 PASSED — Phi-3 lifecycle verified")
            except Exception as e:
                print(f"TEST 4 FAILED — Error: {e}")

    finally:
        config.DB_PATH = original_db_path
        shutil.rmtree(tmp)

    # ──────────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────────
    box_width = 44
    print("\n  " + "╔" + "═" * (box_width - 2) + "╗")
    print("  ║" + "WEEK 3 CHECKPOINT — DONE".center(box_width - 2) + "║")
    print("  " + "╠" + "═" * (box_width - 2) + "╣")
    print(f"  ║  TEST 1  Activity logging          {results_map['TEST 1']:>4}  ║")
    print(f"  ║  TEST 2  Activity Dedup            {results_map['TEST 2']:>4}  ║")
    print(f"  ║  TEST 3  sqlite_vec authorized     {results_map['TEST 3']:>4}  ║")
    print(f"  ║  TEST 4  Phi-3 Load/Unload         {results_map['TEST 4']:>4}  ║")
    print("  " + "╚" + "═" * (box_width - 2) + "╝")

if __name__ == "__main__":
    run_tests()

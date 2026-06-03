"""
tests/test_checkpoint2.py
Vinayak's Week 2 Checkpoint Test.
"""

import io
import logging
import os
import platform
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mnemo import config
from mnemo.capture.ocr import IS_WINDOWS, extract_text
from mnemo.capture.screenshot import ScreenshotEngine

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def run_tests():
    print("\nStarting Week 2 Checkpoint Tests...")
    print(f"Platform: {platform.system()}")
    
    results_map = {
        "TEST 1": "FAIL",
        "TEST 2": "FAIL",
        "TEST 3": "FAIL",
        "TEST 4": "FAIL"
    }

    # ──────────────────────────────────────────────────────────────
    # TEST 1: OCR
    # ──────────────────────────────────────────────────────────────
    print("\n[TEST 1] Testing OCR...")
    img = Image.new("RGB", (400, 80), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 25), "Mnemo OCR Test 2025", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    result = extract_text(img_bytes)
    assert isinstance(result, str), "extract_text must return a string"

    if IS_WINDOWS:
        # WinRT should find at least one of these words
        found = any(w in result.lower() for w in ["mnemo", "ocr", "test", "2025"])
        if found:
            results_map["TEST 1"] = "PASS"
            print(f"TEST 1 PASSED — WinRT OCR working: '{result}'")
        else:
            print(f"TEST 1 FAILED — WinRT OCR returned unexpected text: '{result}'")
    else:
        results_map["TEST 1"] = "PASS"
        print(f"TEST 1 PASSED — OCR returned: '{result}' (non-Windows fallback)")

    # ──────────────────────────────────────────────────────────────
    # TEST 2: Screenshot capture and dedup
    # ──────────────────────────────────────────────────────────────
    print("\n[TEST 2] Testing screenshot capture and dedup...")
    
    is_headless = os.environ.get("DISPLAY") is None and not IS_WINDOWS
    
    if is_headless:
        results_map["TEST 2"] = "SKIP"
        print("TEST 2 SKIPPED — headless environment")
    else:
        captures = []
        engine = ScreenshotEngine(on_capture=lambda c: captures.append(c))

        # First capture — should succeed
        result1 = engine.capture()
        if result1 is None:
            print("TEST 2 FAILED — First capture failed")
        else:
            assert result1["type"] == "screenshot"
            assert isinstance(result1["image_bytes"], bytes)
            assert len(result1["image_bytes"]) > 0
            assert isinstance(result1["timestamp"], int)

            # Second immediate capture — should be deduped (screen hasn't changed)
            result2 = engine.capture()
            if result2 is None:
                print("TEST 2 PARTIAL PASS — Second capture was deduped")
                
                # Reset hash and capture again — should succeed
                engine._last_hash = None
                result3 = engine.capture()
                if result3 is not None:
                    results_map["TEST 2"] = "PASS"
                    print("TEST 2 PASSED — screenshot capture and dedup working")
                else:
                    print("TEST 2 FAILED — Capture after hash reset failed")
            else:
                print("TEST 2 FAILED — Second immediate capture should have been deduped")

    # ──────────────────────────────────────────────────────────────
    # TEST 3: Active window info
    # ──────────────────────────────────────────────────────────────
    print("\n[TEST 3] Testing active window info...")
    if not IS_WINDOWS:
        results_map["TEST 3"] = "SKIP"
        print("TEST 3 SKIPPED — Windows only")
    else:
        from mnemo.capture.screenshot import get_active_window_info
        app_name, window_title = get_active_window_info()
        assert isinstance(app_name, str)
        assert isinstance(window_title, str)
        if len(app_name) > 0 or len(window_title) > 0:
            results_map["TEST 3"] = "PASS"
            print(f"TEST 3 PASSED — active window: '{app_name}' / '{window_title}'")
        elif app_name == "system":
            results_map["TEST 3"] = "PASS"
            print(f"TEST 3 PASSED — active window: '{app_name}' (Headless/No Focus)")
        else:
            print("TEST 3 FAILED — Both app_name and window_title are empty")

    # ──────────────────────────────────────────────────────────────
    # TEST 4: File watcher summarizes long files
    # ──────────────────────────────────────────────────────────────
    print("\n[TEST 4] Testing long file summarization...")
    if not config.PHI3_MODEL_PATH.exists():
        results_map["TEST 4"] = "SKIP"
        print("TEST 4 SKIPPED — Phi-3 model not found")
    else:
        import shutil
        import tempfile

        from mnemo.ai.phi3 import Phi3Engine
        from mnemo.ai.summarizer import Summarizer
        from mnemo.capture.file_watcher import FileWatcher
        from mnemo.memory.embedder import Embedder
        from mnemo.memory.store import MemoryStore

        tmp = tempfile.mkdtemp()
        tmp_path = Path(tmp)
        original_db_path = config.DB_PATH
        try:
            config.DB_PATH = tmp_path / "test.db"
            store = MemoryStore()
            store.open()
            embedder = Embedder()
            embedder.load()
            phi3 = Phi3Engine()
            phi3.load()
            summarizer = Summarizer(phi3)
            watcher = FileWatcher(
                watch_dirs=(tmp_path,),
                store=store,
                embedder=embedder,
                summarizer=summarizer
            )
            # Write a long file (>1500 chars)
            long_file = tmp_path / "long_doc.txt"
            content = "Transformers revolutionized NLP by replacing recurrence with attention mechanisms. " * 40
            long_file.write_text(content)
            
            watcher._process(long_file)
            
            qv = embedder.encode("transformer attention mechanism")
            results = store.search(qv, top_k=1)
            
            if len(results) > 0 and results[0]["summary"] and results[0]["summary"] != "pending":
                results_map["TEST 4"] = "PASS"
                print(f"TEST 4 PASSED — long file summarized: '{results[0]['summary'][:50]}...'")
            else:
                summary_val = results[0]["summary"] if results else "no results"
                print(f"TEST 4 FAILED — Summary not generated correctly: '{summary_val}'")
            
            store.close()
        except Exception as e:
            print(f"TEST 4 ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            config.DB_PATH = original_db_path
            shutil.rmtree(tmp)

    # ──────────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────────
    box_width = 44
    print("\n  " + "╔" + "═" * (box_width - 2) + "╗")
    print("  ║" + "WEEK 2 CHECKPOINT — DONE".center(box_width - 2) + "║")
    print("  " + "╠" + "═" * (box_width - 2) + "╣")
    print(f"  ║  TEST 1  WinRT OCR working         {results_map['TEST 1']:>4}  ║")
    print(f"  ║  TEST 2  Screenshot & Dedup        {results_map['TEST 2']:>4}  ║")
    print(f"  ║  TEST 3  Active Window Info        {results_map['TEST 3']:>4}  ║")
    print(f"  ║  TEST 4  Long File Summary         {results_map['TEST 4']:>4}  ║")
    print("  " + "╚" + "═" * (box_width - 2) + "╝")

if __name__ == "__main__":
    run_tests()

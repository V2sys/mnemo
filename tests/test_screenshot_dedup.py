import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mnemo.capture.screenshot import ScreenshotEngine
import mss

def on_capture(capture):
    print(f"\n--- CAPTURE CALLBACK TRIGGERED ---")
    print(f"App: {capture['app_name']}")
    print(f"Title: {capture['window_title']}")
    print(f"OCR Text length: {len(capture['ocr_text'])}")
    print(f"OCR Preview: {capture['ocr_text'][:100]}...")

def test_screenshot():
    print("Testing ScreenshotEngine...")
    engine = ScreenshotEngine(on_capture)
    
    print("\n1. Taking first screenshot...")
    cap1 = engine.capture()
    if cap1:
        print("First screenshot captured successfully.")
    else:
        print("First screenshot skipped (unexpected).")
        
    print("\n2. Waiting 2 seconds then taking second screenshot (should be identical/skipped)...")
    time.sleep(2)
    cap2 = engine.capture()
    if cap2 is None:
        print("Second screenshot skipped due to deduplication (EXPECTED BEHAVIOR).")
    else:
        print("Second screenshot captured (unexpected if screen didn't change).")
        
if __name__ == "__main__":
    test_screenshot()
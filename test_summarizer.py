import sys
import os
import time

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from mnemo.ai.phi3 import Phi3Engine, inference_pool
from mnemo.ai.summarizer import Summarizer

def test_summary():
    print("1. Loading LLM Engine...")
    engine = Phi3Engine()
    engine.load()
    
    print("\n2. Initializing Summarizer...")
    summarizer = Summarizer(engine)
    
    # This simulates raw, messy OCR text pulled from a screenshot
    fake_ocr_text = """
    From: vinayak@v2systems.com
    To: vedansh@v2systems.com
    Subject: Hackathon Architecture Changes
    Hey Vedansh, I was looking at the threading model. I think we need to make sure 
    the watchdog doesn't block the main thread. Also, don't forget to push the 
    CustomTkinter changes to the repo before 5 PM tomorrow. 
    Cheers, Vinayak.
    """
    
    print("\n3. Sending raw OCR text to Summarizer (simulating screenshot capture)...")
    print(f"Raw Text:\n{fake_ocr_text.strip()}\n")
    
    start_time = time.time()
    
    # We submit it to the thread pool just like Vinayak's screenshot pipeline will do
    future = inference_pool.submit(summarizer.summarize, fake_ocr_text)
    summary = future.result()
    
    elapsed = time.time() - start_time
    
    print(f"--- GENERATED SUMMARY ({elapsed:.2f} seconds) ---")
    print(summary)
    print("---------------------------------------------")

if __name__ == "__main__":
    test_summary()

import sys
import os
from pathlib import Path

# Add mnemo to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from mnemo.ai.phi3 import Phi3Engine, inference_pool

def test_phi3():
    print("Initializing engine...")
    engine = Phi3Engine()
    
    print("Loading model into memory (this might take a few seconds)...")
    engine.load()
    
    prompt = "<|user|>\nPlease summarize this text: 'The mitochondria is the powerhouse of the cell.'<|end|>\n<|assistant|>\n"
    print(f"\nSending prompt:\n{prompt}")
    
    print("Generating response...")
    # We use the thread pool just like the architecture specifies
    future = inference_pool.submit(engine.generate, prompt=prompt, max_tokens=50)
    result = future.result()
    
    print("\n--- Output ---")
    print(result)
    print("--------------\n")
    print("Test passed! Checkpoint 1 LLM goal achieved.")

if __name__ == "__main__":
    test_phi3()

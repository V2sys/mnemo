import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mnemo.ai.phi3 import Phi3Engine
from mnemo.memory.embedder import Embedder
from mnemo.memory.store import MemoryStore
from mnemo.ai.query_engine import QueryEngine
import mnemo.config as config
import tempfile

def test_engine():
    print("Setting up test environment...")
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    config.DB_PATH = temp_path / "test_db.sqlite"
    
    print("1. Loading Phi-3 Engine...")
    phi3 = Phi3Engine()
    phi3.load()
    
    print("2. Loading Embedder...")
    embedder = Embedder()
    embedder.load()
    
    print("3. Opening Memory Store...")
    store = MemoryStore()
    store.open()
    
    print("4. Inserting fake memory into database...")
    # Add a memory about a meeting
    record = {
        "type": "file",
        "source": "meeting_notes.txt",
        "content_hash": "hash123",
        "raw_text": "Meeting with Sarah. She wants the new UI deployed by Friday.",
        "summary": "Meeting notes indicating Sarah requested the new UI deployment by Friday.",
        "timestamp": 1234567890,
        "metadata": "{}"
    }
    vec = embedder.encode(record["summary"])
    store.save_memory(record, vec)
    
    print("\n5. Initializing Query Engine...")
    engine = QueryEngine(phi3, embedder, store)
    
    print("\n--- TEST A: ANSWER Intent ---")
    query_a = {"query": "What did Sarah want done by Friday?"}
    print(f"User asking: '{query_a['query']}'")
    response_a = engine.handle(query_a)
    print(f"Intent classified as: {response_a['response_type']}")
    print(f"Phi-3 Answer:\n{response_a['text']}")
    
    print("\n--- TEST B: ACTION Intent ---")
    query_b = {"query": "Open notepad for me"}
    print(f"User asking: '{query_b['query']}'")
    response_b = engine.handle(query_b)
    print(f"Intent classified as: {response_b['response_type']}")
    print(f"Action Payload: {response_b['action']}")
    
if __name__ == "__main__":
    test_engine()
import sys
import time
from pathlib import Path

import numpy as np

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

import mnemo.config as config
from mnemo.capture.file_watcher import extract_text
from mnemo.memory.embedder import Embedder
from mnemo.memory.store import MemoryStore


def test_embedder():
    print("Testing Embedder...")
    e = Embedder()
    e.load()
    vec = e.encode("test document about machine learning")
    assert vec.shape == (384,), f"Expected shape (384,), got {vec.shape}"
    assert vec.dtype == np.float32, f"Expected float32, got {vec.dtype}"
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-5, f"Expected norm ~ 1.0, got {norm}"
    print("Embedder: PASS")

def test_store():
    print("Testing MemoryStore...")
    old_path = config.DB_PATH
    config.DB_PATH = config.DATA_DIR / "test_mnemo.db"
    if config.DB_PATH.exists():
        config.DB_PATH.unlink()
        
    store = MemoryStore()
    store.open()
    
    vec = np.random.rand(384).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    
    record = {
        "type": "file",
        "source": "test.txt",
        "content_hash": "testhash",
        "raw_text": "hello",
        "raw_text_expires": int(time.time()) - 100,
        "summary": "test",
        "timestamp": int(time.time()),
        "metadata": "{}"
    }
    
    mem_id = store.save_memory(record, vec)
    assert mem_id is not None
    
    results = store.search(vec, top_k=1)
    assert len(results) == 1
    
    found_id = store.find_by_hash("testhash")
    assert found_id == mem_id
    
    # Manually expire the record to test purge
    store._conn.execute("UPDATE memories SET raw_text_expires = ? WHERE id = ?", (int(time.time()) - 100, mem_id))
    store._conn.commit()
    
    count = store.purge_expired_raw_text()
    assert count == 1
    
    store.close()
    if config.DB_PATH.exists():
        config.DB_PATH.unlink()
    config.DB_PATH = old_path
    print("MemoryStore: PASS")

def test_file_watcher_extract():
    print("Testing file_watcher extract_text...")
    test_file = Path("test_extract.txt")
    test_file.write_text("hello extract")
    text = extract_text(test_file)
    assert text == "hello extract"
    test_file.unlink()
    
    missing_text = extract_text(Path("missing_file.pdf"))
    assert missing_text == ""
    print("FileWatcher Extract: PASS")

if __name__ == "__main__":
    test_embedder()
    test_store()
    test_file_watcher_extract()
    print("\nAll Week 1 checks passed. Ready for joint integration test.")

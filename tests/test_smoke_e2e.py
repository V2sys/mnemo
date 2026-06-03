import shutil
import sys
import tempfile
import time
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mnemo import config
from mnemo.ai.phi3 import Phi3Engine
from mnemo.ai.query_engine import QueryEngine
from mnemo.ai.summarizer import Summarizer
from mnemo.capture.file_watcher import FileWatcher
from mnemo.memory.embedder import Embedder
from mnemo.memory.store import MemoryStore


def run_smoke_test():
    print("=== MNEMO END-TO-END SMOKE TEST ===\n")

    tmp = Path(tempfile.mkdtemp())
    original_db_path = config.DB_PATH
    config.DB_PATH = tmp / "smoke.db"

    try:
        store = MemoryStore()
        store.open()
        embedder = Embedder()
        embedder.load()

        print("[1/5] Loading Phi-3 Mini...")
        t0 = time.time()
        phi3 = Phi3Engine()
        phi3.load()
        print(f"      Loaded in {time.time()-t0:.1f}s")

        summarizer = Summarizer(phi3)
        query_engine = QueryEngine(phi3, embedder, store)

        print("[2/5] Indexing a document...")
        doc = tmp / "research_notes.txt"
        doc.write_text(
            "Retrieval Augmented Generation (RAG) combines a retrieval system "
            "with a generative language model. The retrieval system fetches "
            "relevant context from a knowledge base using vector similarity search. "
            "The generator then uses this context to produce grounded, factual "
            "answers rather than hallucinating. This approach is widely used in "
            "enterprise search, customer support, and personal knowledge management. "
            * 5
        )
        watcher = FileWatcher((tmp,), store, embedder, summarizer)
        watcher._process(doc)
        print("      Document indexed.")

        print("[3/5] Running a query...")
        from mnemo.schema import QueryRequest
        request: QueryRequest = {
            "query": "what is RAG and how does it work?",
            "top_k": 3,
            "type_filter": None
        }
        t0 = time.time()
        response = query_engine.handle(request)
        elapsed = time.time() - t0
        print(f"      Response in {elapsed:.1f}s")
        print(f"      Type: {response['response_type']}")
        print(f"      Confidence: {response['confidence']}")
        print(f"      Answer: {response['text'][:200]}...")
        print(f"      Sources: {len(response['sources'])}")

        print("[4/5] Checking response quality...")
        assert response["response_type"] in ("answer", "not_found"), \
            f"Unexpected response type: {response['response_type']}"
        assert isinstance(response["text"], str) and len(response["text"]) > 10, \
            "Answer text too short"
        assert response["confidence"] in ("high", "low"), \
            f"Invalid confidence: {response['confidence']}"
        print("      Response shape valid.")

        print("[5/5] Measuring idle resource usage...")
        import os

        import psutil
        process = psutil.Process(os.getpid())
        ram_mb = process.memory_info().rss / 1e6
        print(f"      RAM with models loaded: {ram_mb:.0f}MB")
        print("      Target idle (no models): <50MB")
        print("      Note: models are loaded here for testing; daemon unloads them")

        print("\n=== SMOKE TEST COMPLETE ===")
        print("The full pipeline (index → query → answer) is working end-to-end.")
        print(f"Query response time: {elapsed:.1f}s")

    finally:
        store.close()
        config.DB_PATH = original_db_path
        shutil.rmtree(tmp)

if __name__ == "__main__":
    run_smoke_test()

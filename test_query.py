import sys
import os

# Add mnemo to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from mnemo.ai.phi3 import Phi3Engine
from mnemo.ai.query_engine import QueryEngine
from mnemo.memory.embedder import Embedder
from mnemo.memory.store import MemoryStore
from mnemo.schema import QueryRequest

def test_query():
    print("1. Initializing Memory Store...")
    store = MemoryStore()
    store.open()

    print("2. Initializing Embedder...")
    embedder = Embedder()
    embedder.load()

    print("3. Initializing LLM...")
    phi3 = Phi3Engine()
    phi3.load()

    print("4. Initializing Query Engine...")
    query_engine = QueryEngine(phi3=phi3, embedder=embedder, store=store)

    query_text = input("\nWhat would you like to ask Mnemo? (e.g. 'tell me about the README file')\n> ")
    if not query_text.strip():
        print("Empty query. Exiting.")
        return

    request: QueryRequest = {
        "query": query_text,
        "top_k": 3,
        "type_filter": None
    }

    print(f"\nProcessing query: '{query_text}'...")
    response = query_engine.handle(request)

    print("\n--- Response ---")
    print(f"Intent classified as: {response['response_type'].upper()}")
    print(f"Confidence: {response['confidence'].upper()}")
    print(f"\nAnswer:\n{response['text']}")
    print("\nSources retrieved:")
    for i, src in enumerate(response['sources']):
        print(f"  [{i+1}] {src['type'].upper()} ({src.get('source', 'Unknown')}): {src['summary'][:100]}...")
    print("----------------\n")
    
    store.close()

if __name__ == "__main__":
    test_query()

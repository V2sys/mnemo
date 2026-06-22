import psutil
import os
import gc
import time
import statistics
import tempfile
import shutil
from pathlib import Path
import subprocess

# Disable verbose logs for cleaner output during benchmarking
import logging
logging.getLogger("mnemo").setLevel(logging.WARNING)

proc = psutil.Process(os.getpid())

def ram_mb():
    return proc.memory_info().rss / 1e6

print("═══════════════════════════════════════════════════════")
print("BENCHMARK 1 — Memory footprint at each lifecycle stage")
print("═══════════════════════════════════════════════════════")

# Stage 1: bare Python process
baseline = ram_mb()
print(f"Bare Python:              {baseline:.1f}MB")

# Stage 2: after store + embedder loaded (true idle state)
from mnemo import config
config.ensure_dirs()
from mnemo.memory.store import MemoryStore
from mnemo.memory.embedder import Embedder
store = MemoryStore(); store.open()
embedder = Embedder(); embedder.load()
idle = ram_mb()
print(f"Store + Embedder (idle):  {idle:.1f}MB")

# Stage 3: after Phi-3 loaded (active state)
from mnemo.ai.phi3 import Phi3Engine
phi3 = Phi3Engine()
phi3.load()
active = ram_mb()
print(f"Phi-3 loaded (active):    {active:.1f}MB")

# Stage 4: after Phi-3 unloaded (back to idle)
phi3.unload()
gc.collect()
time.sleep(1)
after_unload = ram_mb()
print(f"After unload:             {after_unload:.1f}MB")
print(f"RAM freed by unload:      {active - after_unload:.1f}MB")


print("\n═══════════════════════════════════════════════════════")
print("BENCHMARK 2 — Phi-3 load time (3 runs, take average)")
print("═══════════════════════════════════════════════════════")

load_times = []
for i in range(3):
    phi3 = Phi3Engine()
    t0 = time.time()
    phi3.load()
    load_times.append(time.time() - t0)
    phi3.unload()
    gc.collect()
    time.sleep(1)

avg_load = sum(load_times) / len(load_times)
print(f"Phi-3 load time:          {load_times}")
print(f"Phi-3 load avg:           {avg_load:.2f}s")


print("\n═══════════════════════════════════════════════════════")
print("BENCHMARK 3 — Embedding latency (50 runs)")
print("═══════════════════════════════════════════════════════")

texts = [
    "the quick brown fox jumps over the lazy dog",
    "transformer architecture uses self-attention",
    "retrieval augmented generation combines search and generation",
    "python programming language object oriented",
    "windows operating system process management",
] * 10  # 50 total

times = []
for text in texts:
    t0 = time.time()
    embedder.encode(text)
    times.append((time.time() - t0) * 1000)

print(f"Embed latency avg:        {statistics.mean(times):.1f}ms")
print(f"Embed latency p95:        {sorted(times)[47]:.1f}ms")
print(f"Embed latency max:        {max(times):.1f}ms")


print("\n═══════════════════════════════════════════════════════")
print("BENCHMARK 4 — Semantic search latency (30 queries)")
print("═══════════════════════════════════════════════════════")

# Index 20 documents first
topics = [
    "machine learning neural networks",
    "python programming",
    "database management",
    "windows system administration",
    "natural language processing",
]
for i in range(20):
    text = topics[i % 5] + f" document {i} " * 10
    vec = embedder.encode(text)
    record = {
        "type": "file",
        "source": f"bench_{i}.txt",
        "content_hash": f"bench_hash_{i}",
        "raw_text": text,
        "raw_text_expires": int(time.time()) + 86400,
        "summary": None,
        "timestamp": int(time.time()),
        "metadata": "{}"
    }
    store.save_memory(record, vec)

queries = [
    "how do neural networks learn?",
    "python functions and classes",
    "SQL database queries",
    "Windows processes and memory",
    "attention mechanism transformers",
] * 6  # 30 queries

search_times = []
for q in queries:
    t0 = time.time()
    qvec = embedder.encode(q)
    results = store.search(qvec, top_k=3)
    search_times.append((time.time() - t0) * 1000)

print(f"Search latency avg:       {statistics.mean(search_times):.1f}ms")
print(f"Search latency p95:       {sorted(search_times)[28]:.1f}ms")
print(f"Search latency max:       {max(search_times):.1f}ms")


print("\n═══════════════════════════════════════════════════════")
print("BENCHMARK 5 — Full RAG query time (5 real queries)")
print("═══════════════════════════════════════════════════════")

phi3.load()

from mnemo.ai.query_engine import QueryEngine
from mnemo.schema import QueryRequest

qe = QueryEngine(phi3, embedder, store)

test_queries = [
    "how do neural networks learn from data?",
    "what is the difference between SQL and NoSQL?",
    "explain attention mechanisms in transformers",
    "how does python handle memory management?",
    "what are the key components of an operating system?",
]

rag_times = []
rag_results = []

for q in test_queries:
    t0 = time.time()
    request = QueryRequest(query=q, top_k=3, type_filter=None)
    response = qe.handle(request)
    elapsed = time.time() - t0
    rag_times.append(elapsed)
    rag_results.append({
        "query": q,
        "response_type": response["response_type"],
        "confidence": response["confidence"],
        "answer_length": len(response["text"]),
        "time": elapsed
    })
    print(f"  Q: {q[:50]}")
    print(f"  A: {response['text'][:100]}...")
    print(f"  Time: {elapsed:.2f}s | Confidence: {response['confidence']}")
    print()

print(f"RAG query avg:            {statistics.mean(rag_times):.2f}s")
print(f"RAG query min:            {min(rag_times):.2f}s")
print(f"RAG query max:            {max(rag_times):.2f}s")

phi3.unload()


print("\n═══════════════════════════════════════════════════════")
print("BENCHMARK 6 — File indexing throughput")
print("═══════════════════════════════════════════════════════")

tmp = Path(tempfile.mkdtemp())

# Create 10 files of varying sizes
sizes = [100, 500, 1000, 2000, 5000, 100, 500, 1000, 2000, 5000]
for i, size in enumerate(sizes):
    f = tmp / f"bench_file_{i}.txt"
    f.write_text("word " * size)

from mnemo.memory.store import MemoryStore as S2
from mnemo import config as cfg
import tempfile as tf2
tmp_db = Path(tf2.mkdtemp()) / "bench.db"
original_db_path = cfg.DB_PATH
cfg.DB_PATH = tmp_db
store2 = S2(); store2.open()
from mnemo.capture.file_watcher import FileWatcher
watcher = FileWatcher(
    watch_dirs=(tmp,),
    store=store2,
    embedder=embedder,
    summarizer=None
)

t0 = time.time()
watcher.bulk_index_directory()
index_time = time.time() - t0

print(f"Indexed 10 files in:      {index_time:.2f}s")
print(f"Avg per file:             {(index_time/10)*1000:.0f}ms")

store2.close()
shutil.rmtree(tmp)
try:
    tmp_db.parent.rmdir()
except Exception:
    pass
cfg.DB_PATH = original_db_path


print("\n═══════════════════════════════════════════════════════")
print("BENCHMARK 7 — GPU VRAM usage (if GPU available)")
print("═══════════════════════════════════════════════════════")

def get_vram_mb():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        return int(result.stdout.strip())
    except Exception:
        return None

vram_before = get_vram_mb()
phi3_gpu = Phi3Engine()
phi3_gpu.load()
vram_after = get_vram_mb()
phi3_gpu.unload()

if vram_before is not None:
    print(f"VRAM before Phi-3:        {vram_before}MB")
    print(f"VRAM after Phi-3 load:    {vram_after}MB")
    print(f"VRAM used by Phi-3:       {vram_after - vram_before}MB")
else:
    print("VRAM measurement: nvidia-smi not available")

store.close()

# Mnemo — Resource Benchmarks

Measured on Windows 11, Python 3.12, CPU-only inference.
No GPU required.

## Memory Usage

| State | RAM Usage |
|---|---|
| Idle (store + embedder only) | 173.2MB |
| Active (Phi-3 loaded) | ~2000.0MB |
| After idle unload (5min) | 173.2MB |
| RAM freed by unload | ~1826.8MB |

Phi-3 unloads automatically after 5 minutes of inactivity,
returning memory usage to the idle state.

## Latency

| Operation | Time |
|---|---|
| App startup to ready | ~1.5s |
| Phi-3 model load | ~2.5s |
| Semantic search (numpy fallback) | 23ms |
| Text embedding (single) | 16ms |
| Full query (embed + search + synthesize) | ~4.0s |

## vs. Alternatives

| Tool | Idle RAM | Offline? | Semantic Search? |
|---|---|---|---|
| Mnemo (idle) | 173MB | Yes | Yes |
| Microsoft Copilot | ~450MB | No | No |
| Windows Search | ~150MB | Yes | No |

## Hardware Tested

- CPU: Intel Core i7 (or equivalent)
- RAM: 16GB
- OS: Windows 11
- Storage: SSD

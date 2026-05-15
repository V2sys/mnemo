# Mnemo

A lightweight, memory-first personal AI agent for Windows.

Mnemo runs silently in the system tray, builds a semantic memory of your workflow, and lets you query it in natural language. Privacy-first, fully on-device, no cloud.

> Submission for Samsung ennovateX AX Hackathon 2026 — Problem #3: Context-Aware, Adaptive Memory Solution for Mobile Agentic Systems.

---

## Team — V2Labs

| Member | Role | Layer |
|---|---|---|
| Vinayak Tyagi | Memory & Capture | Daemon, hotkey, file watcher, screenshot capture, OCR, activity monitor, embeddings, SQLite store |
| Vedansh Sharma | Intelligence & Interface | Phi-3 integration, summarization, query engine, action router, overlay UI |

Both — Manipal University Jaipur.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│         System Tray Daemon (~20MB idle)     │
└────┬───────────┬────────────┬───────────────┘
     │           │            │
  Hotkey      File         Activity
  Handler     Watcher      Monitor
     │           │            │
     ▼           ▼            ▼
┌─────────────────────────────────────────────┐
│           Memory Layer (SQLite + vec)       │
│   files · screenshots · activity timeline   │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│       Query Engine + Phi-3 Mini             │
│   intent → retrieve → synthesize → respond  │
└──────────────────┬──────────────────────────┘
                   ▼
            Overlay UI (CustomTkinter)
```

---

## Tech Stack

| Component | Library |
|---|---|
| System tray | pystray |
| Global hotkey | keyboard |
| File watcher | watchdog |
| Screenshot | mss |
| OCR | pywinrt (Windows native) |
| PDF / DOCX | pdfplumber, python-docx |
| Activity monitor | pywin32 |
| Image dedup | ImageHash |
| Embeddings | onnxruntime + all-MiniLM-L6-v2 (ONNX) |
| Vector store | SQLite + sqlite-vec |
| LLM | llama-cpp-python (Vulkan/DirectML backend) |
| LLM model | Phi-3 Mini (MIT) |
| UI | CustomTkinter |

All models are open weight (MIT or Apache 2.0). No proprietary APIs.

---

## Setup

**Requirements:** Windows 10/11, Python 3.10+

```bash
git clone https://github.com/v2labs/mnemo.git
cd mnemo
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Download the Phi-3 Mini GGUF model (~2GB) into `./models/`:
```bash
# instructions in docs/setup.md
```

Run:
```bash
python -m mnemo
```

---

## Project Structure

```
mnemo/
├── mnemo/
│   ├── __main__.py          # Entry point
│   ├── config.py            # Paths, constants
│   ├── schema.py            # SHARED CONTRACTS — do not modify alone
│   │
│   ├── daemon/              # Vinayak
│   │   ├── tray.py
│   │   └── hotkey.py
│   │
│   ├── capture/             # Vinayak
│   │   ├── file_watcher.py
│   │   ├── screenshot.py
│   │   ├── ocr.py
│   │   └── activity.py
│   │
│   ├── memory/              # Vinayak
│   │   ├── embedder.py
│   │   └── store.py
│   │
│   ├── ai/                  # Vedansh
│   │   ├── phi3.py
│   │   ├── summarizer.py
│   │   └── query_engine.py
│   │
│   ├── actions/             # Vedansh
│   │   └── router.py
│   │
│   └── ui/                  # Vedansh
│       ├── overlay.py
│       └── results.py
│
├── docs/                    # Design notes, schema, threading model
├── tests/                   # Unit tests
├── models/                  # Downloaded GGUF models (gitignored)
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Development Workflow

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for branching strategy, schema rules, and weekly checkpoints.

**Critical rule:** Never modify `mnemo/schema.py` without discussing with the other dev first.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

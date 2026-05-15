# Contributing — V2Labs Internal

This document is for **Vinayak** and **Vedansh** only. Workflow, rules, and the contracts that keep our two halves from drifting apart.

---

## Branching

- `main` — protected. Never commit directly. Only PR merges.
- `dev` — integration branch. Merge feature branches here first, test together, then PR to `main`.
- `feature/<area>` — your working branches.

**Vinayak's branches:**
- `feature/daemon`, `feature/file-watcher`, `feature/screenshot`, `feature/ocr`, `feature/activity`, `feature/embedder`, `feature/store`

**Vedansh's branches:**
- `feature/phi3`, `feature/summarizer`, `feature/query-engine`, `feature/action-router`, `feature/overlay`, `feature/results`

Open PRs to `dev`, the other person reviews. PR to `main` only at end-of-week checkpoints, both must approve.

---

## Schema Rules

`mnemo/schema.py` is the **only place** for shared data shapes and tunables.

- Both layers import from here. Neither layer redefines anything here.
- Want to change a TypedDict, an enum, or a threshold? Discuss first. Document the change in commit message.
- Adding new fields to a TypedDict is fine. Renaming or removing is not — coordinate.

---

## Threading Rules

| Thread | Owner | What |
|---|---|---|
| Main | Vedansh | CustomTkinter UI — Tkinter REQUIRES this |
| Tray | Vinayak | pystray system tray icon |
| File watcher | Vinayak | watchdog observers |
| Activity monitor | Vinayak | pywin32 polling loop |
| Phi-3 pool (1 worker) | Vedansh | All LLM inference goes here |
| Hotkey | Vinayak | `keyboard` library — registers global hooks |

**Rules:**
1. Never touch the Tkinter root from any thread except main. Use `root.after(0, callable)` to come back to main thread.
2. Never call `phi3_engine.generate()` directly. Always go through `inference_pool.submit()`.
3. Vinayak's threads never call into `mnemo.ai.*` directly — only via callbacks the main wiring sets up.
4. SQLite connection in `store.py` uses a Lock — both layers share it, hold the lock briefly.

---

## Weekly Checkpoints

### Week 1 — Foundation (May 16–22)
**Vinayak:**
- [ ] Tray icon shows in system tray
- [ ] Hotkey (Ctrl+Space) prints "summon" to console
- [ ] File watcher detects .txt changes, prints extracted text
- [ ] `schema.py` reviewed and locked

**Vedansh:**
- [ ] Phi-3 Mini loads, returns text for a hardcoded prompt (CPU)
- [ ] CustomTkinter overlay window opens and closes
- [ ] Dev environment fully working on his machine

**Joint test (end of week):** Vinayak's `embedder.encode()` produces a vector, `store.save_memory()` writes it. Vedansh's `store.search()` retrieves it. Manual scripts ok — proves the contract works.

### Week 2 — Core Memory (May 23–29)
**Vinayak:**
- [ ] File watcher → embedder → store fully automated
- [ ] PDF and DOCX extraction working
- [ ] Screenshot capture via mss working with ImageHash dedup
- [ ] Windows OCR (`pywinrt`) returning text from screenshots

**Vedansh:**
- [ ] Summarizer accepts OCR text, returns Phi-3 summary
- [ ] Query engine: receives text, embeds, searches, returns top-k
- [ ] Vulkan/DirectML backend attempted (doc results either way)

**Joint test:** Modify a .pdf → ask "what was in that pdf about X" → get a real answer.

### Week 3 — Intelligence (May 30–Jun 5)
**Vinayak:**
- [ ] Activity monitor live (opt-in)
- [ ] `purge_expired_raw_text` job runs on startup
- [ ] Performance check: idle RAM under 50MB?

**Vedansh:**
- [ ] Full query engine: intent classify + retrieve + synthesize
- [ ] Not-found fallback returns closest with low confidence
- [ ] Action parsing returns ActionPayload dict

**Joint test:** End-to-end via Python scripts (no UI yet). Three queries, three correct answers.

### Week 4 — Interface (Jun 6–12)
**Vinayak:**
- [ ] Resource benchmarks documented
- [ ] Bulk indexing on first run for WATCH_DIRS works

**Vedansh:**
- [ ] Overlay UI fully wired to query engine
- [ ] Action router executes file_open and app_launch
- [ ] Hotkey → UI opens → query → result, in under 3 seconds

**Joint test:** Cold start, demo scenario start to finish via UI only.

### Week 5 — Polish (Jun 13–19)
- [ ] Bug fixes from daily use
- [ ] Edge cases handled
- [ ] (Optional) Whisper Tiny voice input
- [ ] Demo scenario rehearsed
- [ ] Resource numbers documented

### Week 6 — Submit (Jun 20–22)
- [ ] Test on a clean machine
- [ ] Demo video recorded
- [ ] Phase 2 submission document written
- [ ] Submitted by Jun 22

---

## Daily Workflow

- 10-min sync at start of day. Slack/Discord/whatever you use.
- Push to your feature branch at least once a day.
- If you change anything in `schema.py`, ping the other person immediately.
- If something is blocking you, say so the same day. Don't sit on it.

---

## Code Style

- Run `ruff check` before pushing.
- Type hints on public functions.
- Module docstring at the top, owner clearly marked.
- No print() in committed code — use `logging.getLogger(__name__)`.

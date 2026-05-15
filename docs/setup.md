# Setup Notes

## One-time model downloads

After `pip install -r requirements.txt`, both devs need these files in `~/.mnemo/models/`:

### Phi-3 Mini (GGUF, quantized)

Download from HuggingFace:
- File: `Phi-3-mini-4k-instruct-q4.gguf`
- Repo: `microsoft/Phi-3-mini-4k-instruct-gguf`
- Size: ~2.3 GB
- Save as: `~/.mnemo/models/phi-3-mini-4k-instruct-q4.gguf`

### all-MiniLM-L6-v2 (ONNX)

- File: `model.onnx`
- Repo: `sentence-transformers/all-MiniLM-L6-v2`
- Size: ~80 MB
- Save as: `~/.mnemo/models/all-MiniLM-L6-v2.onnx`

Tokenizer:
- File: `tokenizer.json` from same repo
- Save as: `~/.mnemo/models/all-MiniLM-L6-v2-tokenizer.json`

---

## llama-cpp-python with Vulkan / DirectML

The prebuilt PyPI wheel is CPU-only. For GPU acceleration on integrated graphics:

### Vulkan (cross-vendor, recommended)

```bash
pip uninstall llama-cpp-python -y
$env:CMAKE_ARGS="-DGGML_VULKAN=on"
pip install llama-cpp-python --no-cache-dir --upgrade --force-reinstall
```

Needs Vulkan SDK installed.

### DirectML (Windows native)

```bash
pip uninstall llama-cpp-python -y
$env:CMAKE_ARGS="-DGGML_DIRECTML=on"
pip install llama-cpp-python --no-cache-dir --upgrade --force-reinstall
```

If neither builds, fall back to CPU — expect 5–15 s per response. Document which backend you ended up using.

---

## sqlite-vec on Windows

If `pip install sqlite-vec` fails:

```bash
pip install sqlite-vec --pre
```

Or download the prebuilt `.dll` from the sqlite-vec releases and load manually. See `mnemo/memory/store.py` open() docstring.

---

## Admin permissions

The `keyboard` library may need admin/elevated permissions on some Windows configs for global hotkeys. If hotkeys aren't firing, run the terminal as admin during dev.

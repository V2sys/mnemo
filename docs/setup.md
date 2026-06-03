# Setup Notes

> [!CAUTION]
> ⚠️ **Python 3.14 is NOT supported.** Use **Python 3.12** (`.venv312`). `llama-cpp-python` and other core dependencies are currently incompatible with 3.14 on Windows.

## Quick Start (Windows)

1. **Install Python 3.12** from [python.org](https://www.python.org/downloads/).
2. **Create and Activate Virtual Environment**:
   ```powershell
   py -3.12 -m venv .venv312
   .venv312\Scripts\activate
   ```
3. **Install Dependencies**:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   # If llama-cpp-python fails to build, use pre-built CPU wheels:
   pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
   ```
4. **Download Models**:
   Run the helper script (requires `huggingface-hub`):
   ```powershell
   python download_models_hf.py
   ```
5. **Run Mnemo**:
   ```powershell
   python -m mnemo
   ```

---

## One-time model downloads

The following files are required in `~/.mnemo/models/`:

### Phi-3 Mini (GGUF, quantized)
- **Repo**: `microsoft/Phi-3-mini-4k-instruct-gguf`
- **File**: `Phi-3-mini-4k-instruct-q4.gguf`
- **Path**: `~/.mnemo/models/phi-3-mini-4k-instruct-q4.gguf`

### all-MiniLM-L6-v2 (ONNX)
- **Repo**: `sentence-transformers/all-MiniLM-L6-v2`
- **File**: `onnx/model.onnx` -> `~/.mnemo/models/all-MiniLM-L6-v2.onnx`
- **Tokenizer**: `tokenizer.json` -> `~/.mnemo/models/all-MiniLM-L6-v2-tokenizer.json`

---

## llama-cpp-python with Vulkan / DirectML

The default `pip install` may require a compiler. For GPU acceleration on Windows:

### Vulkan (Recommended)
Requires [Vulkan SDK](https://vulkan.lunarg.com/).
```powershell
$env:CMAKE_ARGS="-DGGML_VULKAN=on"
pip install llama-cpp-python --no-cache-dir --force-reinstall
```

### DirectML
```powershell
$env:CMAKE_ARGS="-DGGML_DIRECTML=on"
pip install llama-cpp-python --no-cache-dir --force-reinstall
```

---

## sqlite-vec on Windows

If `pip install sqlite-vec` fails to load at runtime, you may need to download the `.dll` manually from the [releases page](https://github.com/asg017/sqlite-vec/releases) and place it in your site-packages or local path.

---

## Admin permissions

The `keyboard` library requires **Administrator/Elevated permissions** on Windows to capture global hotkeys. Always run your terminal as Admin during development.

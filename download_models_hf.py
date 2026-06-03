import os
from pathlib import Path
from huggingface_hub import hf_hub_download

# Base directory for all Mnemo runtime data
MNEMO_HOME = Path.home() / ".mnemo"
MODELS_DIR = MNEMO_HOME / "models"

def download_models():
    print(f"Ensuring models directory exists: {MODELS_DIR}")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Phi-3 Mini (GGUF)
    print("\nDownloading Phi-3 Mini (GGUF)...")
    hf_hub_download(
        repo_id="microsoft/Phi-3-mini-4k-instruct-gguf",
        filename="Phi-3-mini-4k-instruct-q4.gguf",
        local_dir=MODELS_DIR,
        local_dir_use_symlinks=False
    )
    # Rename to match config if necessary (hf_hub_download might keep original name)
    # config.py: PHI3_MODEL_PATH = MODELS_DIR / "phi-3-mini-4k-instruct-q4.gguf"
    # The file on HF is "Phi-3-mini-4k-instruct-q4.gguf"
    phi3_path = MODELS_DIR / "Phi-3-mini-4k-instruct-q4.gguf"
    target_phi3 = MODELS_DIR / "phi-3-mini-4k-instruct-q4.gguf"
    if phi3_path.exists() and not target_phi3.exists():
        phi3_path.rename(target_phi3)

    # 2. all-MiniLM-L6-v2 (ONNX)
    print("\nDownloading all-MiniLM-L6-v2 (ONNX)...")
    hf_hub_download(
        repo_id="sentence-transformers/all-MiniLM-L6-v2",
        filename="onnx/model.onnx",
        local_dir=MODELS_DIR,
        local_dir_use_symlinks=False
    )
    # Move and rename to match config
    # config.py: EMBEDDING_MODEL_PATH = MODELS_DIR / "all-MiniLM-L6-v2.onnx"
    onnx_path = MODELS_DIR / "onnx" / "model.onnx"
    target_onnx = MODELS_DIR / "all-MiniLM-L6-v2.onnx"
    if onnx_path.exists():
        if target_onnx.exists():
            target_onnx.unlink()
        onnx_path.rename(target_onnx)
        (MODELS_DIR / "onnx").rmdir()

    print("\nDownloading all-MiniLM-L6-v2 (Tokenizer)...")
    hf_hub_download(
        repo_id="sentence-transformers/all-MiniLM-L6-v2",
        filename="tokenizer.json",
        local_dir=MODELS_DIR,
        local_dir_use_symlinks=False
    )
    # Rename to match config
    # config.py: EMBEDDING_TOKENIZER_PATH = MODELS_DIR / "all-MiniLM-L6-v2-tokenizer.json"
    tok_path = MODELS_DIR / "tokenizer.json"
    target_tok = MODELS_DIR / "all-MiniLM-L6-v2-tokenizer.json"
    if tok_path.exists():
        if target_tok.exists():
            target_tok.unlink()
        tok_path.rename(target_tok)

    print("\nAll models downloaded successfully.")

if __name__ == "__main__":
    download_models()

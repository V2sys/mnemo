import sys
from huggingface_hub import hf_hub_download
import logging

logging.basicConfig(level=logging.INFO)

print("Downloading Phi-3-mini-4k-instruct-q4.gguf... This may take a few minutes for 2.4GB.")
try:
    path = hf_hub_download(
        repo_id="microsoft/Phi-3-mini-4k-instruct-gguf",
        filename="Phi-3-mini-4k-instruct-q4.gguf",
        local_dir=r"C:\Users\vedan\.mnemo\models",
        local_dir_use_symlinks=False
    )
    print(f"Success! Downloaded to {path}")
except Exception as e:
    print(f"Error: {e}")

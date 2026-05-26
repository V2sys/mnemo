import os
import shutil
from huggingface_hub import hf_hub_download

os.makedirs(r"C:\Users\vedan\.mnemo\models", exist_ok=True)

tok_path = hf_hub_download(repo_id="sentence-transformers/all-MiniLM-L6-v2", filename="tokenizer.json")
shutil.copy(tok_path, r"C:\Users\vedan\.mnemo\models\all-MiniLM-L6-v2-tokenizer.json")

model_path = hf_hub_download(repo_id="sentence-transformers/all-MiniLM-L6-v2", filename="onnx/model.onnx")
shutil.copy(model_path, r"C:\Users\vedan\.mnemo\models\all-MiniLM-L6-v2.onnx")

print("Downloaded embedder models successfully!")

import os
import sys
import urllib.request
from pathlib import Path

# Add mnemo to path so we can import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "mnemo")))
from mnemo.config import ensure_dirs, PHI3_MODEL_PATH

def download_file(url: str, dest: Path) -> None:
    print(f"Downloading {url} to {dest}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response, open(dest, 'wb') as out_file:
            # We don't have tqdm, so let's do a simple progress print
            file_size = int(response.info().get("Content-Length", 0))
            chunk_size = 1024 * 1024 * 5 # 5 MB
            downloaded = 0
            
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if file_size > 0:
                    percent = downloaded / file_size * 100
                    print(f"\rProgress: {downloaded/(1024*1024):.2f} MB / {file_size/(1024*1024):.2f} MB ({percent:.1f}%)", end="")
                else:
                    print(f"\rProgress: {downloaded/(1024*1024):.2f} MB downloaded", end="")
            print("\nDownload complete!")
    except Exception as e:
        print(f"\nFailed to download: {e}")
        if dest.exists():
            dest.unlink() # remove partial file

if __name__ == "__main__":
    ensure_dirs()
    
    url = "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
    
    if PHI3_MODEL_PATH.exists():
        print(f"Model already exists at {PHI3_MODEL_PATH}")
    else:
        download_file(url, PHI3_MODEL_PATH)

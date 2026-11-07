import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from huggingface_hub import hf_hub_download
from config import MODEL_REPO_ID, MODEL_FILENAME, MODELS_DIR, MODEL_PATH

def download_gguf_model(repo_id: str = None, filename: str = None) -> Path:
    """Download local GGUF model from Hugging Face Hub if not already present."""
    repo_id = repo_id or MODEL_REPO_ID
    filename = filename or MODEL_FILENAME
    target_path = MODELS_DIR / filename

    print("=" * 60)
    print("Local LLM Downloader (ITU AI for Good Architecture)")
    print("=" * 60)
    print(f"Repository: {repo_id}")
    print(f"Filename  : {filename}")
    print(f"Directory : {MODELS_DIR}")

    if target_path.exists():
        print(f"\n[OK] Model already present: {target_path}")
        print(f"Size: {target_path.stat().st_size / (1024 * 1024):.2f} MB")
        return target_path

    print("\nDownloading GGUF model from Hugging Face Hub...")
    print("Note: This is a public model, no Hugging Face token is required.")
    
    downloaded = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=str(MODELS_DIR)
    )
    print(f"\n[SUCCESS] Download completed: {downloaded}")
    return Path(downloaded)

if __name__ == "__main__":
    download_gguf_model()

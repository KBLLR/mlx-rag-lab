import argparse
import os
from pathlib import Path
from mlx_lm.utils import load

def download_mlx_model(model_id: str):
    print(f"[INFO] Attempting to download MLX model: {model_id}...")
    try:
        # mlx_lm.utils.load handles downloading and caching automatically.
        # It returns the model and tokenizer, but also stores the model locally.
        # The actual path can be inferred from huggingface_hub's cache.
        model, tokenizer = load(model_id, lazy=True) # lazy=True to avoid loading weights into memory if not needed
        
        # Determine the local cache path for the model
        # This is a common pattern for Hugging Face models
        from huggingface_hub import snapshot_download
        local_path = snapshot_download(repo_id=model_id)

        print(f"[INFO] Model '{model_id}' downloaded and cached successfully.")
        print(f"[INFO] Local path: {local_path}")
        return local_path
    except Exception as e:
        print(f"[ERROR] Failed to download model '{model_id}': {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download MLX-compatible models from Hugging Face Hub.")
    parser.add_argument(
        "--model-id",
        type=str,
        required=True,
        help="The Hugging Face model ID (e.g., mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit)"
    )
    args = parser.parse_args()
    download_mlx_model(args.model_id)

#!/usr/bin/env python3
"""
Download GPT-OSS 20B MXFP4 model weights to mlx-models/ directory.

Usage:
    python scripts/download_gpt_oss_20b.py

    # Or via uv:
    uv run python scripts/download_gpt_oss_20b.py
"""

from pathlib import Path
from huggingface_hub import snapshot_download

# Define the base directory for MLX models within our repo
MLX_MODELS_DIR = Path("./mlx-models/")

# Model configuration
MODEL_REPO_ID = "mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx"
LOCAL_MODEL_NAME = "gpt-oss-20b-mxfp4"


def download_gpt_oss_20b():
    """Download GPT-OSS 20B model weights to local directory."""
    print(f"🔽 Downloading GPT-OSS 20B MXFP4 from {MODEL_REPO_ID}...")
    print(f"📁 Target directory: mlx-models/{LOCAL_MODEL_NAME}/")
    print(f"📦 Expected size: ~12 GB\n")

    local_dir = MLX_MODELS_DIR / LOCAL_MODEL_NAME
    local_dir.mkdir(parents=True, exist_ok=True)

    # Download all necessary files for MLX models
    try:
        downloaded_path = snapshot_download(
            repo_id=MODEL_REPO_ID,
            allow_patterns=[
                "*.json",           # config files
                "*.safetensors",    # model weights
                "*.model",          # tokenizer model
                "*.txt",            # vocab files
                "tokenizer*",       # all tokenizer files
                "*.tiktoken",       # tiktoken files if present
                "*.bin",            # backup weight format
            ],
            local_dir=local_dir,
            local_dir_use_symlinks=False,  # Copy files directly (no symlinks)
        )

        print(f"\n✅ Successfully downloaded {MODEL_REPO_ID}")
        print(f"📂 Location: {downloaded_path}")
        print(f"\n💡 To use this model:")
        print(f"   - Via RAG CLI: --model-id {local_dir.resolve()}")
        print(f"   - Via MLX Lab: Select 'GPT-OSS 20B' from the RAG models menu")

        return downloaded_path

    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print(f"\n🔧 Troubleshooting:")
        print(f"   - Check internet connection")
        print(f"   - Verify model exists: https://huggingface.co/{MODEL_REPO_ID}")
        print(f"   - Ensure sufficient disk space (~12 GB)")
        raise


if __name__ == "__main__":
    download_gpt_oss_20b()

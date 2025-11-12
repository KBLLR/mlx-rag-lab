"""
Initialize global settings for the `rag` package.

We keep Hugging Face downloads inside `mlx-models/.hf-cache` (ignored from Git)
to preserve the local-first workflow and avoid polluting the user home cache.
We also disable Hugging Face's multiprocessing downloader to prevent the
macOS/Python 3.12 `fds_to_keep` fork/lock crash when Textual loads models in
background threads.
"""

from __future__ import annotations

import os
from pathlib import Path

# Resolve repo root (src/rag/__init__.py -> repo/)
REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO_ROOT / "mlx-models" / ".hf-cache"
CACHE_ROOT.mkdir(parents=True, exist_ok=True)

# Ensure all HF downloads stay within mlx-models/
os.environ.setdefault("HF_HOME", str(CACHE_ROOT))
os.environ.setdefault("HF_HUB_CACHE", str(CACHE_ROOT))

# Avoid thread_map + multiprocessing issues on macOS/Python 3.12
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_DISABLE_MULTIPROCESSING", "1")

# Expose useful constants for other modules if needed.
HF_CACHE_DIR = CACHE_ROOT

__all__ = ["HF_CACHE_DIR"]

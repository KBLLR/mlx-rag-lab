from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _make_runner(module_name: str) -> Callable[[], None]:
    """Import one CLI when its script runs, not when this module is imported.

    Eager imports made every console script depend on every app. A missing
    module in one app (rag.models.qwen_reranker) crashed all twelve.
    """

    def runner() -> None:
        os.environ.setdefault("PYTHONPATH", str(ROOT / "src"))
        module = importlib.import_module(module_name)
        module.main()

    return runner


mlxlab_main = _make_runner("apps.mlxlab_cli")
rag_cli_main = _make_runner("apps.rag_cli")
chat_cli_main = _make_runner("apps.chat_cli")
voice_chat_cli_main = _make_runner("apps.voice_chat_cli")
sts_avatar_cli_main = _make_runner("apps.sts_avatar_cli")
flux_cli_main = _make_runner("apps.flux_cli")
bench_cli_main = _make_runner("apps.bench_cli")
musicgen_cli_main = _make_runner("apps.musicgen_cli")
whisper_cli_main = _make_runner("apps.whisper_cli")
ingest_cli_main = _make_runner("apps.ingest_cli")
ingest_rooms_cli_main = _make_runner("apps.ingest_rooms_cli")
classify_cli_main = _make_runner("apps.classify_cli")

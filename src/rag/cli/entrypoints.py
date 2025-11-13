from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps import bench_cli as bench_cli_module
from apps import chat_cli as chat_cli_module
from apps import classify_cli as classify_cli_module
from apps import flux_cli as flux_cli_module
from apps import ingest_cli as ingest_cli_module
from apps import mlxlab_cli as mlxlab_cli_module
from apps import musicgen_cli as musicgen_cli_module
from apps import rag_cli as rag_cli_module
from apps import sts_avatar_cli as sts_avatar_cli_module
from apps import voice_chat_cli as voice_chat_cli_module
from apps import whisper_cli as whisper_cli_module


def _make_runner(func: Callable[[], None]) -> Callable[[], None]:
    def runner() -> None:
        os.environ.setdefault("PYTHONPATH", str(ROOT / "src"))
        func()

    return runner


mlxlab_main = _make_runner(mlxlab_cli_module.main)
rag_cli_main = _make_runner(rag_cli_module.main)
chat_cli_main = _make_runner(chat_cli_module.main)
voice_chat_cli_main = _make_runner(voice_chat_cli_module.main)
sts_avatar_cli_main = _make_runner(sts_avatar_cli_module.main)
flux_cli_main = _make_runner(flux_cli_module.main)
bench_cli_main = _make_runner(bench_cli_module.main)
musicgen_cli_main = _make_runner(musicgen_cli_module.main)
whisper_cli_main = _make_runner(whisper_cli_module.main)
ingest_cli_main = _make_runner(ingest_cli_module.main)
classify_cli_main = _make_runner(classify_cli_module.main)

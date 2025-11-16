"""Common fixtures for RAG-focused tests."""

from __future__ import annotations

from typing import Iterable, Sequence

import pytest

try:
    import mlx.core as mx
    MLX_AVAILABLE = True
except (ImportError, OSError):
    # MLX not available or shared library missing - use numpy fallback
    import numpy as np
    MLX_AVAILABLE = False


def _text_to_vector(text: str) -> list[float]:
    if not text:
        return [0.0, 0.0, 0.0, 0.0]
    encoded = text.encode("utf-8")
    length = len(text)
    byte_sum = sum(encoded) % 997
    vowels = sum(1 for c in text.lower() if c in "aeiou")
    unique_tokens = len({token.strip(".,!?").lower() for token in text.split() if token})
    return [float(length), float(byte_sum), float(vowels), float(unique_tokens or 1)]


class _StubModel:
    """Deterministic embedding stub so tests do not hit HuggingFace downloads."""

    def run(self, input_text: str | Sequence[str]):
        texts: Iterable[str]
        if isinstance(input_text, str):
            texts = [input_text]
        else:
            texts = input_text
        vectors = [_text_to_vector(t) for t in texts]
        if MLX_AVAILABLE:
            return mx.array(vectors, dtype=mx.float32)
        else:
            return np.array(vectors, dtype=np.float32)


@pytest.fixture(autouse=True)
def stub_embedding_model(monkeypatch):
    """Patch rag.retrieval.vdb.Model with a deterministic stub for tests."""
    import rag.retrieval.vdb as vdb_module

    monkeypatch.setattr(vdb_module, "Model", _StubModel)
    yield

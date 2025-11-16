"""Common fixtures for RAG-focused tests."""

from __future__ import annotations

from typing import Iterable, Sequence

import mlx.core as mx
import pytest


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

    def __init__(self):
        self.model_id = "deterministic-stub"
        self.embedding_dim = 4

    def run(self, input_text: str | Sequence[str]) -> mx.array:
        texts: Iterable[str]
        if isinstance(input_text, str):
            texts = [input_text]
        else:
            texts = input_text
        vectors = [_text_to_vector(t) for t in texts]
        return mx.array(vectors, dtype=mx.float32)


@pytest.fixture(autouse=True)
def stub_embedding_model(monkeypatch):
    """Patch load_embedding_model to return a deterministic stub for tests."""
    import rag.retrieval.embedding as embedding_module

    # Replace load_embedding_model to always return the stub
    def _load_stub():
        return _StubModel()

    monkeypatch.setattr(embedding_module, "load_embedding_model", _load_stub)
    yield

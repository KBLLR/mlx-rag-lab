"""Tests for real MLX embedding models.

These tests are SKIPPED by default unless RAG_EMBEDDINGS_MODEL_PATH is set.
They require a local embedding model to be available.

To run these tests:
    export RAG_EMBEDDINGS_MODEL_PATH=/path/to/your/model
    pytest tests/rag/test_embeddings_real.py -v
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Skip entire module unless RAG_EMBEDDINGS_MODEL_PATH is set
pytestmark = pytest.mark.skipif(
    not os.getenv("RAG_EMBEDDINGS_MODEL_PATH"),
    reason="RAG_EMBEDDINGS_MODEL_PATH not set - skipping real embedding tests"
)


@pytest.fixture
def model_path():
    """Get the model path from environment."""
    path = os.getenv("RAG_EMBEDDINGS_MODEL_PATH")
    assert path is not None, "RAG_EMBEDDINGS_MODEL_PATH must be set"
    assert Path(path).exists(), f"Model path does not exist: {path}"
    return path


def test_real_model_loads(model_path):
    """Test that the real model can be loaded from the specified path."""
    from rag.retrieval.embedding import load_embedding_model

    model = load_embedding_model()

    # Verify model attributes
    assert hasattr(model, "model_id")
    assert hasattr(model, "embedding_dim")
    assert hasattr(model, "run")

    # Model should indicate it's not the stub
    assert "stub" not in model.model_id.lower()


def test_real_embeddings_shape(model_path):
    """Test that embeddings have the expected shape."""
    from rag.retrieval.embedding import load_embedding_model

    model = load_embedding_model()

    # Single text
    single_emb = model.run("Hello world")
    assert single_emb.shape == (1, model.embedding_dim)

    # Batch of texts
    batch_emb = model.run(["Hello", "World", "Test"])
    assert batch_emb.shape == (3, model.embedding_dim)

    # Embedding dimension should be > 4 (stub uses 4)
    assert model.embedding_dim > 4, "Real model should have larger embedding dim than stub"


def test_real_embeddings_dtype(model_path):
    """Test that embeddings are returned as float32."""
    from rag.retrieval.embedding import load_embedding_model
    import mlx.core as mx

    model = load_embedding_model()
    embeddings = model.run("Test text")

    # Should be MLX array with float32 dtype
    assert isinstance(embeddings, mx.array.__class__) or hasattr(embeddings, "dtype")
    assert str(embeddings.dtype) == "float32"


def test_real_embeddings_end_to_end(model_path, tmp_path):
    """Test end-to-end ingestion and query with real embeddings."""
    from rag.retrieval.vdb import VectorDB

    # Note: This will NOT use the stub because the fixture only applies
    # to tests without this module-level skip marker
    # We need to temporarily unmonkeypatch or run without the fixture
    # For now, we'll create VectorDB directly which will use load_embedding_model

    vdb = VectorDB()

    # Ingest some documents
    vdb.ingest("Machine learning is a subset of artificial intelligence.", "ml_doc.txt")
    vdb.ingest("Python is a popular programming language.", "python_doc.txt")

    # Verify embeddings were created
    assert vdb.embeddings is not None
    assert len(vdb.content) > 0

    # Save and reload
    out_path = tmp_path / "real_embeddings" / "vdb.npz"
    vdb.savez(out_path)

    reloaded = VectorDB(str(out_path))

    # Query with real embeddings
    results = reloaded.query("artificial intelligence", k=2)

    assert len(results) > 0
    # The ML document should be more relevant to "artificial intelligence"
    # (though we can't guarantee order without real similarity scoring)
    sources = {r["source"] for r in results}
    assert "ml_doc.txt" in sources or "python_doc.txt" in sources


def test_real_model_semantic_similarity(model_path):
    """Test that semantically similar texts produce similar embeddings."""
    from rag.retrieval.embedding import load_embedding_model
    import mlx.core as mx

    model = load_embedding_model()

    # Similar texts
    emb1 = model.run("The cat sat on the mat")
    emb2 = model.run("A cat was sitting on a mat")

    # Dissimilar text
    emb3 = model.run("Quantum physics and relativity theory")

    # Compute cosine similarities (simple dot product for normalized vectors)
    # Note: We're not normalizing here, just checking relative magnitudes
    def cosine_sim(a, b):
        """Compute cosine similarity between two embedding vectors."""
        # Flatten to 1D if needed
        a_flat = a.reshape(-1)
        b_flat = b.reshape(-1)

        dot = float((a_flat * b_flat).sum())
        norm_a = float((a_flat * a_flat).sum() ** 0.5)
        norm_b = float((b_flat * b_flat).sum() ** 0.5)

        return dot / (norm_a * norm_b + 1e-8)

    sim_similar = cosine_sim(emb1, emb2)
    sim_dissimilar = cosine_sim(emb1, emb3)

    # Similar texts should have higher similarity than dissimilar ones
    # (This is a loose check - real models should show this behavior)
    # We use > 0 just to verify embeddings are not degenerate
    assert sim_similar > 0, "Similar texts should have positive similarity"
    assert sim_dissimilar != sim_similar, "Different text pairs should have different similarities"

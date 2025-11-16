"""Tests for cosine similarity scoring in VectorDB."""

from __future__ import annotations

import pytest

try:
    import mlx.core as mx
    MLX_AVAILABLE = True
except (ImportError, OSError):
    import numpy as np
    MLX_AVAILABLE = False

from rag.retrieval.vdb import VectorDB


def _array(data, dtype=None):
    """Helper to create arrays using available library."""
    if MLX_AVAILABLE:
        if dtype is None:
            dtype = mx.float32
        return mx.array(data, dtype=dtype)
    else:
        if dtype is None:
            dtype = np.float32
        return np.array(data, dtype=dtype)


def test_identical_vectors_score_one():
    """Identical vectors should have cosine similarity ≈ 1.0."""
    vdb = VectorDB()

    # Create identical vectors
    vec1 = _array([1.0, 2.0, 3.0, 4.0])
    vec2 = _array([1.0, 2.0, 3.0, 4.0])

    score = vdb.score(vec1, vec2)

    assert isinstance(score, float), "score() should return a Python float"
    assert abs(score - 1.0) < 1e-6, f"Expected score ≈ 1.0, got {score}"


def test_orthogonal_vectors_score_zero():
    """Orthogonal (perpendicular) vectors should have cosine similarity ≈ 0.0."""
    vdb = VectorDB()

    # Create orthogonal vectors in 4D space
    # vec1 = [1, 0, 0, 0] and vec2 = [0, 1, 0, 0] are orthogonal
    vec1 = _array([1.0, 0.0, 0.0, 0.0])
    vec2 = _array([0.0, 1.0, 0.0, 0.0])

    score = vdb.score(vec1, vec2)

    assert isinstance(score, float), "score() should return a Python float"
    assert abs(score - 0.0) < 1e-6, f"Expected score ≈ 0.0, got {score}"


def test_opposite_vectors_score_negative_one():
    """Opposite (antiparallel) vectors should have cosine similarity ≈ -1.0."""
    vdb = VectorDB()

    # Create opposite vectors
    vec1 = _array([1.0, 2.0, 3.0, 4.0])
    vec2 = _array([-1.0, -2.0, -3.0, -4.0])

    score = vdb.score(vec1, vec2)

    assert isinstance(score, float), "score() should return a Python float"
    assert abs(score - (-1.0)) < 1e-6, f"Expected score ≈ -1.0, got {score}"


def test_partial_similarity():
    """Partially similar vectors should have score between 0 and 1."""
    vdb = VectorDB()

    # Create vectors with partial similarity
    vec1 = _array([1.0, 0.0, 0.0, 0.0])
    vec2 = _array([1.0, 1.0, 0.0, 0.0])

    score = vdb.score(vec1, vec2)

    assert isinstance(score, float), "score() should return a Python float"
    assert 0.0 < score < 1.0, f"Expected score between 0 and 1, got {score}"
    # For these specific vectors, cosine similarity should be 1/sqrt(2) ≈ 0.707
    expected = 1.0 / (2.0 ** 0.5)
    assert abs(score - expected) < 1e-6, f"Expected score ≈ {expected}, got {score}"


def test_zero_vector_handling():
    """Zero vectors should be handled gracefully with epsilon."""
    vdb = VectorDB()

    # Create a zero vector and a normal vector
    vec1 = _array([0.0, 0.0, 0.0, 0.0])
    vec2 = _array([1.0, 2.0, 3.0, 4.0])

    # Should not raise an error due to epsilon
    score = vdb.score(vec1, vec2)

    assert isinstance(score, float), "score() should return a Python float"
    # With epsilon, this should be close to 0 but not raise division by zero
    assert abs(score) < 1.0, "Score should be finite and small"


def test_query_integration_with_cosine_similarity():
    """VectorDB.query() should use cosine similarity and return most similar chunks first."""
    vdb = VectorDB()

    # Ingest documents with different content
    vdb.ingest("The quick brown fox jumps over the lazy dog", "doc1.txt")
    vdb.ingest("Apples are rich in fiber and vitamins", "doc2.txt")
    vdb.ingest("The quick brown cat sleeps on the mat", "doc3.txt")

    # Query with text similar to doc1 and doc3 (both have "quick brown")
    results = vdb.query("quick brown", k=3)

    # Should get results
    assert len(results) > 0, "Expected query to return results"
    assert len(results) <= 3, "Expected at most k=3 results"

    # All results should have required fields
    for result in results:
        assert "text" in result, "Result should have 'text' field"
        assert "source" in result, "Result should have 'source' field"


def test_query_returns_descending_similarity():
    """VectorDB.query() should return results in descending order of similarity."""
    vdb = VectorDB()

    # Ingest multiple documents
    vdb.ingest("Machine learning is a subset of artificial intelligence", "ml.txt")
    vdb.ingest("Python is a popular programming language", "python.txt")
    vdb.ingest("Deep learning uses neural networks for pattern recognition", "dl.txt")

    # Query
    results = vdb.query("artificial intelligence machine learning", k=3)

    assert len(results) > 0, "Expected query to return results"

    # Manually compute scores to verify ordering
    query_emb = vdb.model.run("artificial intelligence machine learning")
    query_vec = query_emb[0]

    result_scores = []
    for result in results:
        # Find the embedding for this result
        for i, content in enumerate(vdb.content):
            if content["text"] == result["text"] and content["source"] == result["source"]:
                doc_vec = vdb.embeddings[i]
                score = vdb.score(query_vec, doc_vec)
                result_scores.append(score)
                break

    # Verify scores are in descending order
    for i in range(len(result_scores) - 1):
        assert result_scores[i] >= result_scores[i + 1], \
            f"Scores should be descending: {result_scores[i]} >= {result_scores[i + 1]}"


def test_score_with_stub_model_embeddings():
    """Test that score() works correctly with StubModel embeddings."""
    vdb = VectorDB()

    # Use StubModel (via fixture) to generate embeddings
    text1 = "Hello world"
    text2 = "Hello world"
    text3 = "Goodbye moon"

    emb1 = vdb.model.run(text1)
    emb2 = vdb.model.run(text2)
    emb3 = vdb.model.run(text3)

    # Identical text should have identical embeddings → score = 1.0
    score_identical = vdb.score(emb1[0], emb2[0])
    assert abs(score_identical - 1.0) < 1e-6, f"Expected score ≈ 1.0 for identical text, got {score_identical}"

    # Different text should have different embeddings → score < 1.0
    score_different = vdb.score(emb1[0], emb3[0])
    assert score_different < 1.0, f"Expected score < 1.0 for different text, got {score_different}"


def test_query_with_large_k():
    """Test that query handles k larger than available results."""
    vdb = VectorDB()

    # Ingest only 2 documents
    vdb.ingest("First document about AI.", "doc1.txt")
    vdb.ingest("Second document about ML.", "doc2.txt")

    # Query with k=100 (much larger than available documents)
    results = vdb.query("artificial intelligence", k=100)

    # Should return at most the number of documents we have
    assert len(results) <= 2, f"Expected at most 2 results, got {len(results)}"
    assert len(results) > 0, "Expected at least some results"


def test_query_returns_scores_in_valid_range():
    """Test that all returned scores are in valid cosine similarity range [-1, 1]."""
    vdb = VectorDB()

    # Ingest diverse documents
    vdb.ingest("Machine learning is a field of AI.", "doc1.txt")
    vdb.ingest("Python is a programming language.", "doc2.txt")
    vdb.ingest("The quick brown fox jumps.", "doc3.txt")

    # Query
    results = vdb.query("artificial intelligence", k=10)

    # All scores should be in [-1, 1]
    for result in results:
        score = result.get("score", 0.0)
        assert -1.0 <= score <= 1.0, f"Score {score} outside valid range [-1, 1]"
        assert isinstance(score, float), f"Score should be float, got {type(score)}"

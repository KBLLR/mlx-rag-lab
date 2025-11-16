"""Tests for metadata-aware query filtering in VectorDB."""

from __future__ import annotations

from pathlib import Path

import pytest

from rag.retrieval.vdb import VectorDB


def test_single_key_filter():
    """Test filtering with a single metadata key."""
    vdb = VectorDB()
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc1.txt", {"author": "alice"})
    vdb.ingest("Bananas provide potassium and quick energy.", "doc2.txt", {"author": "bob"})
    vdb.ingest("Carrots contain beta-carotene for eye health.", "doc3.txt", {"author": "alice"})

    # Query with filter for author=alice
    results = vdb.query("nutrition", k=10, metadata_filter={"author": "alice"})

    # Should only return alice's documents
    assert len(results) > 0, "Expected at least one result"
    for result in results:
        assert result["metadata"]["author"] == "alice", f"Expected author=alice, got {result['metadata'].get('author')}"
        assert result["source"] in ["doc1.txt", "doc3.txt"], f"Unexpected source: {result['source']}"


def test_multi_key_and_filter():
    """Test filtering with multiple metadata keys (AND logic)."""
    vdb = VectorDB()
    vdb.ingest("Physics paper on quantum mechanics.", "doc1.txt", {"author": "alice", "category": "physics"})
    vdb.ingest("Chemistry paper on organic compounds.", "doc2.txt", {"author": "bob", "category": "chemistry"})
    vdb.ingest("Physics paper on thermodynamics.", "doc3.txt", {"author": "alice", "category": "physics"})
    vdb.ingest("Biology paper on genetics.", "doc4.txt", {"author": "alice", "category": "biology"})

    # Query with filter for author=alice AND category=physics
    results = vdb.query("science", k=10, metadata_filter={"author": "alice", "category": "physics"})

    # Should only return alice's physics papers
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    for result in results:
        assert result["metadata"]["author"] == "alice"
        assert result["metadata"]["category"] == "physics"
        assert result["source"] in ["doc1.txt", "doc3.txt"]


def test_filter_missing_metadata_field():
    """Test filtering when some documents are missing the filter field."""
    vdb = VectorDB()
    vdb.ingest("Document with author metadata.", "doc1.txt", {"author": "alice"})
    vdb.ingest("Document without author metadata.", "doc2.txt", {"category": "physics"})
    vdb.ingest("Another document with author.", "doc3.txt", {"author": "bob"})

    # Query with filter for author=alice
    results = vdb.query("document", k=10, metadata_filter={"author": "alice"})

    # Should only return doc1 (doc2 doesn't have author field)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    assert results[0]["source"] == "doc1.txt"
    assert results[0]["metadata"]["author"] == "alice"


def test_filter_matches_nothing():
    """Test filtering with criteria that match no documents."""
    vdb = VectorDB()
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc1.txt", {"author": "alice"})
    vdb.ingest("Bananas provide potassium and quick energy.", "doc2.txt", {"author": "bob"})

    # Query with filter that matches nothing
    results = vdb.query("nutrition", k=10, metadata_filter={"author": "charlie"})

    # Should return empty results
    assert len(results) == 0, f"Expected 0 results, got {len(results)}"


def test_filter_with_no_metadata():
    """Test filtering when no documents have metadata."""
    vdb = VectorDB()
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc1.txt")
    vdb.ingest("Bananas provide potassium and quick energy.", "doc2.txt")

    # Query with filter on documents without metadata
    results = vdb.query("nutrition", k=10, metadata_filter={"author": "alice"})

    # Should return empty results (no docs have author field)
    assert len(results) == 0, f"Expected 0 results, got {len(results)}"


def test_query_without_filter():
    """Test that query without filter returns all results as before."""
    vdb = VectorDB()
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc1.txt", {"author": "alice"})
    vdb.ingest("Bananas provide potassium and quick energy.", "doc2.txt", {"author": "bob"})
    vdb.ingest("Carrots contain beta-carotene for eye health.", "doc3.txt", {"author": "alice"})

    # Query without filter
    results = vdb.query("nutrition", k=10)

    # Should return all documents (up to k)
    assert len(results) > 0, "Expected results without filter"
    # Should have results from different authors
    authors = {result["metadata"].get("author") for result in results}
    assert len(authors) > 1, "Expected results from multiple authors"


def test_filtering_with_stub_model():
    """Test filtering with StubModel embeddings (deterministic)."""
    vdb = VectorDB()

    # Ingest documents with different metadata
    vdb.ingest("Machine learning is a subset of AI.", "ml.txt", {"topic": "ai", "level": "intro"})
    vdb.ingest("Deep learning uses neural networks.", "dl.txt", {"topic": "ai", "level": "advanced"})
    vdb.ingest("Python is a programming language.", "py.txt", {"topic": "programming", "level": "intro"})

    # Filter for topic=ai
    results = vdb.query("artificial intelligence", k=10, metadata_filter={"topic": "ai"})

    assert len(results) == 2, f"Expected 2 AI results, got {len(results)}"
    for result in results:
        assert result["metadata"]["topic"] == "ai"
        assert result["source"] in ["ml.txt", "dl.txt"]

    # Filter for topic=ai AND level=intro
    results = vdb.query("artificial intelligence", k=10, metadata_filter={"topic": "ai", "level": "intro"})

    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    assert results[0]["source"] == "ml.txt"
    assert results[0]["metadata"]["topic"] == "ai"
    assert results[0]["metadata"]["level"] == "intro"


def test_filtering_returns_scores():
    """Test that filtered results include similarity scores."""
    vdb = VectorDB()
    vdb.ingest("Machine learning is a subset of AI.", "ml.txt", {"author": "alice"})
    vdb.ingest("Deep learning uses neural networks.", "dl.txt", {"author": "alice"})

    # Query with filter
    results = vdb.query("artificial intelligence", k=10, metadata_filter={"author": "alice"})

    # Should include scores
    assert len(results) > 0, "Expected results"
    for result in results:
        assert "score" in result, "Result should include score"
        assert isinstance(result["score"], float), "Score should be a float"
        assert -1.0 <= result["score"] <= 1.0, f"Score should be in [-1, 1], got {result['score']}"


def test_filtering_preserves_ranking():
    """Test that filtering preserves similarity-based ranking."""
    vdb = VectorDB()

    # All documents have the same metadata
    vdb.ingest("Machine learning is a subset of artificial intelligence.", "doc1.txt", {"category": "ai"})
    vdb.ingest("Deep learning uses neural networks for pattern recognition.", "doc2.txt", {"category": "ai"})
    vdb.ingest("Python is a popular programming language.", "doc3.txt", {"category": "ai"})

    # Query for AI-related content with filter
    results = vdb.query("artificial intelligence machine learning", k=10, metadata_filter={"category": "ai"})

    assert len(results) > 0, "Expected results"

    # Verify results are in descending order by score
    scores = [r["score"] for r in results]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], f"Scores should be descending: {scores[i]} >= {scores[i + 1]}"


def test_metadata_persistence_with_filter(tmp_path: Path):
    """Test that metadata filtering works after save/reload."""
    vdb = VectorDB()
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc1.txt", {"author": "alice", "year": "2023"})
    vdb.ingest("Bananas provide potassium and quick energy.", "doc2.txt", {"author": "bob", "year": "2024"})

    # Save to disk
    out_path = tmp_path / "test_collection" / "vdb.npz"
    vdb.savez(out_path)

    # Reload from disk
    reloaded = VectorDB(str(out_path))

    # Query with filter should work on reloaded VectorDB
    results = reloaded.query("nutrition", k=10, metadata_filter={"author": "alice"})

    assert len(results) == 1, f"Expected 1 result after reload, got {len(results)}"
    assert results[0]["metadata"]["author"] == "alice"
    assert results[0]["metadata"]["year"] == "2023"
    assert results[0]["source"] == "doc1.txt"


def test_empty_filter_returns_all():
    """Test that passing None or empty dict as filter returns all results."""
    vdb = VectorDB()
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc1.txt", {"author": "alice"})
    vdb.ingest("Bananas provide potassium and quick energy.", "doc2.txt", {"author": "bob"})

    # Query with None filter
    results_none = vdb.query("nutrition", k=10, metadata_filter=None)
    assert len(results_none) > 0, "Expected results with None filter"

    # Query with empty dict filter
    results_empty = vdb.query("nutrition", k=10, metadata_filter={})
    assert len(results_empty) > 0, "Expected results with empty filter"

    # Both should return the same results
    assert len(results_none) == len(results_empty), "None and empty filter should return same results"


def test_filter_respects_k_limit():
    """Test that filtering still respects the k limit."""
    vdb = VectorDB()

    # Ingest many documents with same metadata
    for i in range(10):
        vdb.ingest(f"Document number {i} about nutrition and health.", f"doc{i}.txt", {"category": "health"})

    # Query with filter and k=3
    results = vdb.query("nutrition", k=3, metadata_filter={"category": "health"})

    # Should return at most k results
    assert len(results) <= 3, f"Expected at most 3 results, got {len(results)}"


def test_filter_with_special_characters():
    """Test filtering with metadata values containing special characters."""
    vdb = VectorDB()
    vdb.ingest("Document about MLX.", "doc1.txt", {"author": "alice@example.com", "tag": "MLX/AI"})
    vdb.ingest("Document about Python.", "doc2.txt", {"author": "bob@example.com", "tag": "Python/Dev"})

    # Query with filter containing special characters
    results = vdb.query("technology", k=10, metadata_filter={"author": "alice@example.com"})

    assert len(results) > 0, "Expected results"
    assert results[0]["metadata"]["author"] == "alice@example.com"
    assert results[0]["metadata"]["tag"] == "MLX/AI"

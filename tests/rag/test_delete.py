"""Tests for VectorDB deletion functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from rag.retrieval.vdb import VectorDB


def test_delete_by_source(tmp_path: Path):
    """Test deleting chunks by source document name."""
    vdb = VectorDB()
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc_apples.txt")
    vdb.ingest("Bananas provide potassium and quick energy.", "doc_bananas.txt")

    # Verify both documents are present
    assert len(vdb.content) > 0
    sources = {chunk["source"] for chunk in vdb.content}
    assert "doc_apples.txt" in sources
    assert "doc_bananas.txt" in sources

    # Delete one document
    deleted_count = vdb.delete({"source": "doc_apples.txt"})
    assert deleted_count > 0

    # Verify deletion
    remaining_sources = {chunk["source"] for chunk in vdb.content}
    assert "doc_apples.txt" not in remaining_sources
    assert "doc_bananas.txt" in remaining_sources

    # Query should never return deleted document
    results = vdb.query("apples fiber", k=10)
    for chunk in results:
        assert chunk["source"] != "doc_apples.txt", "Deleted document should not be in results"


def test_delete_persists_to_disk(tmp_path: Path):
    """Test that deletions persist when saved and reloaded."""
    vdb = VectorDB()
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc_apples.txt")
    vdb.ingest("Bananas provide potassium and quick energy.", "doc_bananas.txt")

    out_path = tmp_path / "demo" / "vdb.npz"
    vdb.savez(out_path)

    # Reload and delete
    reloaded = VectorDB(str(out_path))
    deleted_count = reloaded.delete({"source": "doc_apples.txt"})
    assert deleted_count > 0

    # Save again
    reloaded.savez(out_path)

    # Reload again and verify deletion persisted
    final = VectorDB(str(out_path))
    sources = {chunk["source"] for chunk in final.content}
    assert "doc_apples.txt" not in sources
    assert "doc_bananas.txt" in sources


def test_delete_nonexistent_source():
    """Test deleting with filter that matches nothing."""
    vdb = VectorDB()
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc_apples.txt")

    deleted_count = vdb.delete({"source": "nonexistent.txt"})
    assert deleted_count == 0
    assert len(vdb.content) > 0  # Original content unchanged


def test_delete_empty_filter():
    """Test that empty filter criteria returns 0 deletions."""
    vdb = VectorDB()
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc_apples.txt")

    deleted_count = vdb.delete({})
    assert deleted_count == 0
    assert len(vdb.content) > 0  # Original content unchanged


def test_delete_all_chunks():
    """Test deleting all chunks from the database."""
    vdb = VectorDB()
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc_apples.txt")

    initial_count = len(vdb.content)
    assert initial_count > 0

    deleted_count = vdb.delete({"source": "doc_apples.txt"})
    assert deleted_count == initial_count

    # Verify database is empty
    assert len(vdb.content) == 0
    assert vdb.embeddings is None


def test_delete_with_multiple_criteria():
    """Test deleting with multiple filter criteria (all must match)."""
    vdb = VectorDB()
    # Note: Currently chunks only have "text" and "source" fields
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc_apples.txt")
    vdb.ingest("Bananas provide potassium and quick energy.", "doc_bananas.txt")

    # This should match nothing because "source" doesn't match both
    deleted_count = vdb.delete({"source": "doc_apples.txt", "text": "Bananas"})
    assert deleted_count == 0

    # All chunks should remain
    assert len(vdb.content) > 0

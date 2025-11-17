"""Contract tests for the /rag_stats endpoint."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rag.api.main import app
from rag.api.schemas import StatsResponse
from rag.retrieval.vdb import VectorDB


client = TestClient(app)


@pytest.fixture
def test_collection(tmp_path: Path) -> str:
    """Create a test collection with some data."""
    from rag.config.settings import get_settings

    settings = get_settings()
    original_path = settings.index_root_path

    # Use tmp_path for testing
    settings.index_root_path = tmp_path
    collection_name = "test_stats_collection"

    # Create a VectorDB with test data
    vdb = VectorDB()
    vdb.ingest("First test document about machine learning.", "doc1.txt", {"author": "alice"})
    vdb.ingest("Second test document about deep learning.", "doc2.txt", {"author": "bob"})

    # Save the collection
    index_path = tmp_path / collection_name / "vdb.npz"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    vdb.savez(str(index_path))

    yield collection_name

    # Restore original path
    settings.index_root_path = original_path


def test_stats_contract_fields(test_collection: str):
    """Test that /rag_stats endpoint returns all expected fields."""
    response = client.get(f"/rag_stats?collection={test_collection}")
    assert response.status_code == 200

    payload = response.json()
    model = StatsResponse(**payload)

    # Check all expected fields are present
    expected_keys = {
        "collection",
        "num_chunks",
        "num_documents",
        "embedding_model",
        "embedding_dim",
        "index_path",
        "created_at",
        "updated_at",
        "request_id",
    }
    assert set(payload.keys()) == expected_keys

    # Validate field types
    assert isinstance(model.collection, str)
    assert isinstance(model.num_chunks, int)
    assert isinstance(model.num_documents, int)
    assert isinstance(model.embedding_model, str)
    assert model.embedding_dim is None or isinstance(model.embedding_dim, int)
    assert model.index_path is None or isinstance(model.index_path, str)
    assert model.created_at is None or isinstance(model.created_at, str)
    assert model.updated_at is None or isinstance(model.updated_at, str)
    assert model.request_id is None or isinstance(model.request_id, str)


def test_stats_with_request_id(test_collection: str):
    """Test that /rag_stats endpoint respects X-Request-ID header."""
    test_request_id = "test-stats-456"
    response = client.get(
        f"/rag_stats?collection={test_collection}", headers={"X-Request-ID": test_request_id}
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["request_id"] == test_request_id


def test_stats_nonexistent_collection():
    """Test that /rag_stats returns 404 for nonexistent collection."""
    response = client.get("/rag_stats?collection=nonexistent_collection")
    assert response.status_code == 404

    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "IndexNotFoundError"


def test_stats_chunk_and_document_counts(test_collection: str):
    """Test that chunk and document counts are accurate."""
    response = client.get(f"/rag_stats?collection={test_collection}")
    assert response.status_code == 200

    payload = response.json()
    # We ingested 2 documents
    assert payload["num_documents"] == 2
    # We should have at least 2 chunks (one per document minimum)
    assert payload["num_chunks"] >= 2


def test_stats_timestamps(test_collection: str):
    """Test that timestamps are in ISO 8601 format."""
    response = client.get(f"/rag_stats?collection={test_collection}")
    assert response.status_code == 200

    payload = response.json()
    # Timestamps should be ISO 8601 strings if present
    if payload["created_at"]:
        assert "T" in payload["created_at"]
        assert "Z" in payload["created_at"] or "+" in payload["created_at"]
    if payload["updated_at"]:
        assert "T" in payload["updated_at"]
        assert "Z" in payload["updated_at"] or "+" in payload["updated_at"]

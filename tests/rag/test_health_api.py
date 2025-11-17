"""Contract checks for the FastAPI /health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from rag.api.main import app
from rag.api.schemas import HealthResponse


client = TestClient(app)


def test_health_contract_stable():
    """Test that /health endpoint returns expected fields."""
    response = client.get("/health")
    assert response.status_code == 200

    payload = response.json()
    model = HealthResponse(**payload)

    # Check status values
    assert model.status in ["ok", "degraded", "error"]
    assert model.tier == "3B"
    assert isinstance(model.models_loaded, bool)
    assert isinstance(model.index_available, bool)

    # Check all expected fields are present
    expected_keys = {"status", "tier", "models_loaded", "embedding_model", "index_available", "request_id"}
    assert set(payload.keys()) == expected_keys

    # request_id should be present
    assert model.request_id is not None
    assert len(model.request_id) > 0


def test_health_with_request_id():
    """Test that /health endpoint respects X-Request-ID header."""
    test_request_id = "test-request-123"
    response = client.get("/health", headers={"X-Request-ID": test_request_id})
    assert response.status_code == 200

    payload = response.json()
    assert payload["request_id"] == test_request_id


def test_health_index_availability():
    """Test that /health endpoint reports index availability."""
    response = client.get("/health")
    assert response.status_code == 200

    payload = response.json()
    # index_available should be a boolean
    assert isinstance(payload["index_available"], bool)

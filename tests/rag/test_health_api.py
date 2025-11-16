"""Contract checks for the FastAPI /health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from rag.api.main import app
from rag.api.schemas import HealthResponse


client = TestClient(app)


def test_health_contract_stable():
    response = client.get("/health")
    assert response.status_code == 200

    payload = response.json()
    model = HealthResponse(**payload)

    assert model.status == "ok"
    assert model.tier == "3B"
    assert set(payload.keys()) == {"status", "tier", "models_loaded", "embedding_model"}

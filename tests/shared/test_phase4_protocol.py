"""Unit tests for Phase-4 protocol models.

Tests validation, serialization, and deserialization of all
Phase-4 protocol models used in Smart Campus integration.
"""

import pytest
from pydantic import ValidationError

from shared.phase4_protocol import (
    RAGQueryRequest,
    RAGResult,
    RAGContext,
    RoomQueryRequest,
    RoomQueryResponse,
    EntityContextRequest,
    ErrorResponse,
)


class TestRAGQueryRequest:
    """Tests for RAGQueryRequest model."""

    def test_minimal_valid_request(self):
        """Test minimal valid request with only required fields."""
        request = RAGQueryRequest(
            query="How does MLX work?",
            collection="technical_docs",
        )
        assert request.query == "How does MLX work?"
        assert request.collection == "technical_docs"
        assert request.k == 5  # Default
        assert request.threshold == 0.5  # Default
        assert request.requestId is None
        assert request.source is None
        assert request.timestamp is None

    def test_full_request_with_all_fields(self):
        """Test request with all optional fields populated."""
        request = RAGQueryRequest(
            requestId="req_123",
            source="smart-campus",
            timestamp="2025-11-20T12:00:00Z",
            query="How does Peace room handle noise?",
            collection="rooms",
            k=10,
            threshold=0.7,
            filter={"room_id": "peace", "section": "rules"},
        )
        assert request.requestId == "req_123"
        assert request.source == "smart-campus"
        assert request.timestamp == "2025-11-20T12:00:00Z"
        assert request.k == 10
        assert request.threshold == 0.7
        assert request.filter == {"room_id": "peace", "section": "rules"}

    def test_invalid_k_value(self):
        """Test that k must be within valid range."""
        with pytest.raises(ValidationError) as exc_info:
            RAGQueryRequest(
                query="test",
                collection="test",
                k=0,  # Invalid: must be >= 1
            )
        assert "greater than or equal to 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            RAGQueryRequest(
                query="test",
                collection="test",
                k=101,  # Invalid: must be <= 100
            )
        assert "less than or equal to 100" in str(exc_info.value)

    def test_invalid_threshold_value(self):
        """Test that threshold must be within [-1, 1] range."""
        with pytest.raises(ValidationError) as exc_info:
            RAGQueryRequest(
                query="test",
                collection="test",
                threshold=-1.5,  # Invalid: must be >= -1
            )
        assert "greater than or equal to -1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            RAGQueryRequest(
                query="test",
                collection="test",
                threshold=1.5,  # Invalid: must be <= 1
            )
        assert "less than or equal to 1" in str(exc_info.value)

    def test_json_serialization(self):
        """Test model can be serialized to JSON."""
        request = RAGQueryRequest(
            requestId="req_123",
            query="test query",
            collection="test_collection",
        )
        json_str = request.model_dump_json()
        assert "req_123" in json_str
        assert "test query" in json_str
        assert "test_collection" in json_str


class TestRAGResult:
    """Tests for RAGResult model."""

    def test_valid_result(self):
        """Test valid result with all fields."""
        result = RAGResult(
            text="The Peace room is a quiet study space.",
            score=0.87,
            metadata={"room_id": "peace", "source_file": "peace.json"},
        )
        assert result.text == "The Peace room is a quiet study space."
        assert result.score == 0.87
        assert result.metadata["room_id"] == "peace"

    def test_result_without_metadata(self):
        """Test result with no metadata."""
        result = RAGResult(
            text="Sample text",
            score=0.5,
        )
        assert result.text == "Sample text"
        assert result.score == 0.5
        assert result.metadata is None

    def test_invalid_score_range(self):
        """Test that score must be within [-1, 1] range."""
        with pytest.raises(ValidationError) as exc_info:
            RAGResult(text="test", score=1.5)
        assert "less than or equal to 1" in str(exc_info.value)


class TestRAGContext:
    """Tests for RAGContext model."""

    def test_valid_context(self):
        """Test valid RAG context with results."""
        context = RAGContext(
            collection="rooms",
            query="peace: What are the rules?",
            results=[
                RAGResult(text="Rule 1: Maintain silence", score=0.9),
                RAGResult(text="Rule 2: Use headphones", score=0.85),
            ],
            latencyMs=23.4,
            requestId="req_123",
        )
        assert context.collection == "rooms"
        assert len(context.results) == 2
        assert context.latencyMs == 23.4
        assert context.requestId == "req_123"

    def test_empty_results(self):
        """Test context with empty results list."""
        context = RAGContext(
            collection="rooms",
            query="nonexistent query",
            results=[],
            latencyMs=10.0,
        )
        assert len(context.results) == 0
        assert context.requestId is None


class TestRoomQueryRequest:
    """Tests for RoomQueryRequest model."""

    def test_valid_request(self):
        """Test valid room query request."""
        request = RoomQueryRequest(
            requestId="req_123",
            source="smart-campus",
            timestamp="2025-11-20T12:00:00Z",
            room="peace",
            query="What are the rules?",
        )
        assert request.requestId == "req_123"
        assert request.source == "smart-campus"
        assert request.room == "peace"
        assert request.query == "What are the rules?"
        assert request.type == "room_query"  # Default
        assert request.includeRag is True  # Default
        assert request.includeEntities is False  # Default

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError) as exc_info:
            RoomQueryRequest(
                requestId="req_123",
                source="smart-campus",
                # Missing: timestamp, room, query
            )
        error_str = str(exc_info.value)
        assert "timestamp" in error_str
        assert "room" in error_str
        assert "query" in error_str

    def test_custom_flags(self):
        """Test custom includeRag and includeEntities flags."""
        request = RoomQueryRequest(
            requestId="req_123",
            source="smart-campus",
            timestamp="2025-11-20T12:00:00Z",
            room="peace",
            query="What are the rules?",
            includeRag=False,
            includeEntities=True,
        )
        assert request.includeRag is False
        assert request.includeEntities is True


class TestRoomQueryResponse:
    """Tests for RoomQueryResponse model."""

    def test_minimal_response(self):
        """Test minimal response with required fields only."""
        response = RoomQueryResponse(
            requestId="req_123",
            room="peace",
            answer="The Peace room requires silence.",
            latencyMs=20.1,
        )
        assert response.requestId == "req_123"
        assert response.room == "peace"
        assert response.answer == "The Peace room requires silence."
        assert response.latencyMs == 20.1
        assert response.entities == []  # Default
        assert response.ragContext is None
        assert response.modelUsed == "rag-only"  # Default

    def test_response_with_rag_context(self):
        """Test response with RAG context included."""
        rag_context = RAGContext(
            collection="rooms",
            query="peace: rules",
            results=[RAGResult(text="Maintain silence", score=0.9)],
            latencyMs=15.0,
        )
        response = RoomQueryResponse(
            requestId="req_123",
            room="peace",
            answer="The Peace room requires silence.",
            ragContext=rag_context,
            latencyMs=20.1,
        )
        assert response.ragContext is not None
        assert response.ragContext.collection == "rooms"
        assert len(response.ragContext.results) == 1

    def test_response_with_entities(self):
        """Test response with entity information."""
        response = RoomQueryResponse(
            requestId="req_123",
            room="peace",
            answer="Room has temperature sensor.",
            entities=[
                {"entity_id": "sensor.peace_temperature", "state": "22.5°C"},
            ],
            latencyMs=18.0,
        )
        assert len(response.entities) == 1
        assert response.entities[0]["entity_id"] == "sensor.peace_temperature"


class TestEntityContextRequest:
    """Tests for EntityContextRequest model."""

    def test_valid_request(self):
        """Test valid entity context request."""
        request = EntityContextRequest(
            requestId="req_456",
            source="smart-campus",
            timestamp="2025-11-20T12:00:00Z",
            entityId="sensor.peace_temperature",
        )
        assert request.requestId == "req_456"
        assert request.entityId == "sensor.peace_temperature"
        assert request.k == 3  # Default
        assert request.threshold == 0.5  # Default
        assert request.room is None

    def test_request_with_room_scope(self):
        """Test entity request with room scoping."""
        request = EntityContextRequest(
            requestId="req_456",
            source="smart-campus",
            timestamp="2025-11-20T12:00:00Z",
            entityId="sensor.peace_temperature",
            room="peace",
            k=5,
            threshold=0.7,
        )
        assert request.room == "peace"
        assert request.k == 5
        assert request.threshold == 0.7

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError) as exc_info:
            EntityContextRequest(
                requestId="req_456",
                # Missing: source, timestamp, entityId
            )
        error_str = str(exc_info.value)
        assert "source" in error_str
        assert "timestamp" in error_str
        assert "entityId" in error_str


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_valid_error_response(self):
        """Test valid error response."""
        error = ErrorResponse(
            error={
                "code": "IndexNotFoundError",
                "message": "Collection 'rooms' does not exist",
                "status_code": 404,
            }
        )
        assert error.error["code"] == "IndexNotFoundError"
        assert error.error["status_code"] == 404

    def test_json_serialization(self):
        """Test error response serialization."""
        error = ErrorResponse(
            error={
                "code": "InvalidRequestError",
                "message": "Invalid threshold value",
                "status_code": 400,
            }
        )
        json_str = error.model_dump_json()
        assert "InvalidRequestError" in json_str
        assert "400" in json_str

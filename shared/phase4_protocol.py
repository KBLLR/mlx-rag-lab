"""Phase-4 Protocol Definitions for RAG Provider Integration.

This module defines the contract between Tier-2 orchestrators (gen-idea-lab)
and Tier-3B RAG providers (mlx-rag-lab) for Smart Campus integration.

Key principles:
- Request ID propagation for distributed tracing
- Latency measurement on all operations
- Structured metadata for filtering and attribution
- Room-aware and entity-aware query patterns
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# RAG Query Models (Enhanced)
# ============================================================================


class RAGQueryRequest(BaseModel):
    """Enhanced RAG query request with Phase-4 tracing fields.

    This extends the basic RAG query with orchestrator-level metadata
    for request tracing, source identification, and timing.
    """

    requestId: Optional[str] = Field(
        None,
        description="Request ID for distributed tracing across services",
        examples=["req_550e8400-e29b-41d4-a716-446655440000"],
    )
    source: Optional[str] = Field(
        None,
        description="Source system identifier (e.g., 'smart-campus', 'avatar')",
        examples=["smart-campus", "avatar", "orchestrator"],
    )
    timestamp: Optional[str] = Field(
        None,
        description="Request timestamp in ISO 8601 format",
        examples=["2025-11-20T12:00:00Z"],
    )
    query: str = Field(
        ...,
        description="Query text to search for in the collection",
        examples=["How does Peace room handle noise?"],
    )
    collection: str = Field(
        ...,
        description="Collection name to query",
        examples=["rooms", "campus_classroom_data", "general_knowledge"],
    )
    k: int = Field(
        5,
        description="Number of results to retrieve",
        ge=1,
        le=100,
    )
    threshold: Optional[float] = Field(
        0.5,
        description="Minimum cosine similarity threshold (range: -1 to 1)",
        ge=-1.0,
        le=1.0,
        examples=[0.5, 0.6, 0.85],
    )
    filter: Optional[Dict[str, str]] = Field(
        None,
        description="Metadata filter criteria (AND logic for multiple keys)",
        examples=[{"room_id": "peace", "section": "rules"}],
    )


class RAGResult(BaseModel):
    """Single retrieved chunk result from RAG query."""

    text: str = Field(
        ...,
        description="Chunk text content",
    )
    score: float = Field(
        ...,
        description="Cosine similarity score (range: -1 to 1, L2-normalized)",
        ge=-1.0,
        le=1.0,
        examples=[0.87, 0.92, 0.65],
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Chunk metadata (room_id, source_file, tags, etc.)",
        examples=[
            {
                "room_id": "peace",
                "source_file": "room-personality-peace.json",
                "section": "personality",
            }
        ],
    )


class RAGContext(BaseModel):
    """RAG context response containing retrieved chunks and metadata.

    This is the standard return type for all RAG operations,
    providing both results and tracing information.
    """

    collection: str = Field(
        ...,
        description="Collection that was queried",
        examples=["rooms"],
    )
    query: str = Field(
        ...,
        description="Original query text (may be rewritten)",
        examples=["peace: Explain the atmosphere and rules"],
    )
    results: List[RAGResult] = Field(
        ...,
        description="Retrieved chunks ranked by similarity score",
    )
    latencyMs: float = Field(
        ...,
        description="Query execution latency in milliseconds",
        examples=[23.4, 45.2, 18.7],
    )
    requestId: Optional[str] = Field(
        None,
        description="Request ID for tracing (echoed from request)",
        examples=["req_550e8400-e29b-41d4-a716-446655440000"],
    )


# ============================================================================
# Room Query Models (Smart Campus)
# ============================================================================


class RoomQueryRequest(BaseModel):
    """Room-aware query request for Smart Campus integration.

    This specialized request type allows querying room-specific
    knowledge with optional RAG context and entity information.
    """

    requestId: str = Field(
        ...,
        description="Request ID for distributed tracing",
        examples=["req_123"],
    )
    source: str = Field(
        ...,
        description="Source system identifier",
        examples=["smart-campus"],
    )
    timestamp: str = Field(
        ...,
        description="Request timestamp in ISO 8601 format",
        examples=["2025-11-20T12:00:00Z"],
    )
    type: str = Field(
        default="room_query",
        description="Request type identifier",
        examples=["room_query"],
    )
    room: str = Field(
        ...,
        description="Room identifier (e.g., 'peace', 'focus', 'collab')",
        examples=["peace", "focus", "collab"],
    )
    query: str = Field(
        ...,
        description="User question about the room",
        examples=["What are the rules of this room?", "Explain the atmosphere"],
    )
    includeRag: bool = Field(
        True,
        description="Whether to include RAG context in response",
    )
    includeEntities: bool = Field(
        False,
        description="Whether to include entity information in response",
    )


class RoomQueryResponse(BaseModel):
    """Room query response with answer, RAG context, and optional entities.

    This response provides a comprehensive view of room-specific information,
    combining RAG results with structured answers.
    """

    requestId: str = Field(
        ...,
        description="Request ID (echoed from request)",
        examples=["req_123"],
    )
    room: str = Field(
        ...,
        description="Room identifier",
        examples=["peace"],
    )
    answer: str = Field(
        ...,
        description="Generated answer about the room (from RAG or LLM)",
        examples=["The Peace room is a quiet study space that requires silence..."],
    )
    entities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Entity information (if includeEntities=true)",
        examples=[
            [
                {
                    "entity_id": "sensor.peace_temperature",
                    "description": "Temperature sensor for the Peace room",
                }
            ]
        ],
    )
    ragContext: Optional[RAGContext] = Field(
        None,
        description="RAG context with retrieved chunks (if includeRag=true)",
    )
    latencyMs: float = Field(
        ...,
        description="Total request latency in milliseconds",
        examples=[20.1, 35.4, 12.8],
    )
    modelUsed: str = Field(
        default="rag-only",
        description="Model used for answer generation",
        examples=["rag-only", "mlx-phi3", "deterministic"],
    )


# ============================================================================
# Entity Context Models (Smart Campus)
# ============================================================================


class EntityContextRequest(BaseModel):
    """Entity-specific context request for Smart Campus entities.

    This request type retrieves RAG context specific to a given entity
    (e.g., sensor, device, automation) with optional room scoping.
    """

    requestId: str = Field(
        ...,
        description="Request ID for distributed tracing",
        examples=["req_456"],
    )
    source: str = Field(
        ...,
        description="Source system identifier",
        examples=["smart-campus"],
    )
    timestamp: str = Field(
        ...,
        description="Request timestamp in ISO 8601 format",
        examples=["2025-11-20T12:00:00Z"],
    )
    entityId: str = Field(
        ...,
        description="Entity identifier (e.g., 'sensor.peace_temperature')",
        examples=["sensor.peace_temperature", "light.focus_main", "automation.collab_welcome"],
    )
    room: Optional[str] = Field(
        None,
        description="Optional room scope to filter results",
        examples=["peace", "focus"],
    )
    k: int = Field(
        3,
        description="Number of results to retrieve",
        ge=1,
        le=100,
    )
    threshold: Optional[float] = Field(
        0.5,
        description="Minimum cosine similarity threshold (range: -1 to 1)",
        ge=-1.0,
        le=1.0,
    )


# ============================================================================
# Utility Models
# ============================================================================


class ErrorResponse(BaseModel):
    """Standardized error response for Phase-4 APIs."""

    error: Dict[str, Any] = Field(
        ...,
        description="Error details",
        examples=[
            {
                "code": "IndexNotFoundError",
                "message": "Collection 'rooms' does not exist",
                "status_code": 404,
            }
        ],
    )

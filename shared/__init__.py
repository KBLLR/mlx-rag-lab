"""Shared protocol definitions for Phase-4 cross-service integration.

This module provides standardized Pydantic models for RAG queries,
room-aware queries, and entity context requests/responses.
"""

from shared.phase4_protocol import (
    # RAG Query Models
    RAGQueryRequest,
    RAGResult,
    RAGContext,
    # Room Query Models
    RoomQueryRequest,
    RoomQueryResponse,
    # Entity Context Models
    EntityContextRequest,
)

__all__ = [
    "RAGQueryRequest",
    "RAGResult",
    "RAGContext",
    "RoomQueryRequest",
    "RoomQueryResponse",
    "EntityContextRequest",
]

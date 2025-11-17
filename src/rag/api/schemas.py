"""Pydantic schemas for RAG API request/response models.

This module defines all data models used in the RAG API endpoints.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Health Check Schemas
class HealthResponse(BaseModel):
    """Health check response model (Phase-4 contract)."""

    ok: bool = Field(..., description="Whether service is operational", example=True)
    latency_ms: float = Field(..., description="Health check latency in milliseconds", example=12.5)
    tier: str = Field(..., description="Service tier identifier", example="3B")
    models_loaded: bool = Field(
        ..., description="Whether embedding models are loaded", example=True
    )
    embedding_model: Optional[str] = Field(
        None, description="Currently loaded embedding model ID", example="all-MiniLM-L6-v2"
    )
    index_available: bool = Field(
        ..., description="Whether index storage is accessible", example=True
    )
    request_id: Optional[str] = Field(
        None, description="Request ID for tracing", example="550e8400-e29b-41d4-a716-446655440000"
    )


# RAG Upsert Schemas (Document Ingestion)
class Document(BaseModel):
    """Document to be ingested into the RAG system."""

    content: str = Field(..., description="Pre-extracted document text content")
    source: str = Field(..., description="Document source identifier (filename, URL, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata for filtering/attribution"
    )


class UpsertRequest(BaseModel):
    """Request body for document ingestion endpoint."""

    documents: List[Document] = Field(..., description="List of documents to ingest")
    collection: str = Field(..., description="Collection name", example="technical_docs")


class UpsertResponse(BaseModel):
    """Response for successful document ingestion."""

    chunks_added: int = Field(..., description="Number of chunks added to index", example=142)
    documents_processed: int = Field(..., description="Number of documents processed", example=3)
    collection: str = Field(..., description="Collection name", example="technical_docs")
    index_path: Optional[str] = Field(
        None, description="Path to the vector index file", example="var/indexes/technical_docs/vdb.npz"
    )
    latency_ms: float = Field(..., description="Operation latency in milliseconds", example=234.5)
    request_id: Optional[str] = Field(
        None, description="Request ID for tracing", example="550e8400-e29b-41d4-a716-446655440000"
    )


# RAG Query Schemas (Retrieval)
class ChunkResult(BaseModel):
    """Single retrieved chunk result."""

    text: str = Field(..., description="Chunk text content")
    source: str = Field(..., description="Source document identifier")
    score: float = Field(
        ...,
        description="Cosine similarity score in range [-1, 1] (L2-normalized embeddings)",
        example=0.87,
        ge=-1.0,
        le=1.0
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk metadata if available")


class QueryRequest(BaseModel):
    """Request body for query endpoint."""

    query: str = Field(..., description="Query text", example="How does MLX handle embeddings?")
    collection: str = Field(..., description="Collection name to query", example="technical_docs")
    k: int = Field(5, description="Number of chunks to retrieve", ge=1, le=100)
    threshold: Optional[float] = Field(
        0.5,
        description="Minimum cosine similarity threshold in range [-1, 1]. Typical values: 0.3 (broad), 0.6 (moderate), 0.85 (strict)",
        ge=-1.0,
        le=1.0
    )
    filter: Optional[Dict[str, str]] = Field(
        None, description="Metadata filter criteria (AND logic for multiple keys)", example={"author": "alice", "category": "physics"}
    )


class QueryResponse(BaseModel):
    """Response for successful query."""

    results: List[ChunkResult] = Field(..., description="Retrieved chunks ranked by relevance")
    query: str = Field(..., description="Original query text")
    collection: str = Field(..., description="Collection queried")
    latency_ms: float = Field(..., description="Query latency in milliseconds", example=45.2)
    request_id: Optional[str] = Field(
        None, description="Request ID for tracing", example="550e8400-e29b-41d4-a716-446655440000"
    )


# RAG Stats Schemas
class StatsResponse(BaseModel):
    """Response with collection statistics."""

    collection: str = Field(..., description="Collection name", example="technical_docs")
    num_chunks: int = Field(..., description="Total number of chunks in index", example=352)
    num_documents: int = Field(..., description="Number of source documents", example=12)
    embedding_model: str = Field(
        ..., description="Embedding model used", example="deterministic-stub"
    )
    embedding_dim: Optional[int] = Field(
        None, description="Embedding vector dimensions", example=4
    )
    index_path: Optional[str] = Field(
        None, description="Path to the vector index file", example="var/indexes/technical_docs/vdb.npz"
    )
    created_at: Optional[str] = Field(
        None, description="Index creation timestamp (ISO 8601)", example="2025-11-16T10:30:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp (ISO 8601)", example="2025-11-16T14:22:00Z"
    )
    latency_ms: float = Field(..., description="Stats operation latency in milliseconds", example=8.3)
    request_id: Optional[str] = Field(
        None, description="Request ID for tracing", example="550e8400-e29b-41d4-a716-446655440000"
    )


# RAG Delete Schemas
class DeleteRequest(BaseModel):
    """Request body for delete endpoint."""

    filter: Dict[str, Any] = Field(..., description="Filter criteria for deletion")
    collection: str = Field(..., description="Collection name", example="technical_docs")


class DeleteResponse(BaseModel):
    """Response for successful deletion."""

    deleted_count: int = Field(..., description="Number of documents deleted", example=5)
    collection: str = Field(..., description="Collection name", example="technical_docs")
    latency_ms: float = Field(..., description="Delete operation latency in milliseconds", example=15.7)
    request_id: Optional[str] = Field(
        None, description="Request ID for tracing", example="550e8400-e29b-41d4-a716-446655440000"
    )

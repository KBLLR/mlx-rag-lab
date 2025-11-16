"""Pydantic schemas for RAG API request/response models.

This module defines all data models used in the RAG API endpoints.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Health Check Schemas
class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status", example="ok")
    tier: str = Field(..., description="Service tier identifier", example="3B")
    models_loaded: bool = Field(
        ..., description="Whether embedding models are loaded", example=True
    )
    embedding_model: Optional[str] = Field(
        None, description="Currently loaded embedding model ID", example="all-MiniLM-L6-v2"
    )


# RAG Upsert Schemas (Document Ingestion)
class Document(BaseModel):
    """Document to be ingested into the RAG system."""

    content: str = Field(..., description="Pre-extracted document text content")
    source: str = Field(..., description="Document source identifier (filename, URL, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata for filtering/attribution"
    )


class UpsertOptions(BaseModel):
    """Options for document ingestion."""

    chunk_size: Optional[int] = Field(None, description="Token size for text chunks", example=256)
    chunk_overlap: Optional[int] = Field(
        None, description="Overlap tokens between chunks", example=50
    )


class RagUpsertRequest(BaseModel):
    """Request body for document ingestion endpoint."""

    documents: List[Document] = Field(..., description="List of documents to ingest")
    bank_name: str = Field(..., description="Knowledge bank name", example="technical_docs")
    options: Optional[UpsertOptions] = Field(None, description="Ingestion options")


class RagUpsertResponse(BaseModel):
    """Response for successful document ingestion."""

    chunks_added: int = Field(..., description="Number of chunks added to index", example=142)
    documents_processed: int = Field(..., description="Number of documents processed", example=3)
    bank_name: str = Field(..., description="Knowledge bank name", example="technical_docs")
    index_path: Optional[str] = Field(
        None, description="Path to created index", example="var/indexes/technical_docs/vdb.npz"
    )


# RAG Query Schemas (Retrieval)
class QueryOptions(BaseModel):
    """Options for retrieval queries."""

    top_k: int = Field(5, description="Number of chunks to retrieve", ge=1, le=100)
    rerank: bool = Field(False, description="Whether to apply reranking (if available)")
    threshold: Optional[float] = Field(
        None, description="Minimum similarity threshold (0-1)", ge=0.0, le=1.0
    )


class ChunkResult(BaseModel):
    """Single retrieved chunk result."""

    text: str = Field(..., description="Chunk text content")
    source: str = Field(..., description="Source document identifier")
    score: float = Field(..., description="Similarity score", example=0.87)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk metadata if available")


class RagQueryRequest(BaseModel):
    """Request body for query endpoint."""

    query: str = Field(..., description="Query text", example="How does MLX handle embeddings?")
    bank_name: str = Field(..., description="Knowledge bank to query", example="technical_docs")
    options: Optional[QueryOptions] = Field(None, description="Query options")


class RagQueryResponse(BaseModel):
    """Response for successful query."""

    results: List[ChunkResult] = Field(..., description="Retrieved chunks ranked by relevance")
    query: str = Field(..., description="Original query text")
    bank_name: str = Field(..., description="Knowledge bank queried")


# RAG Stats Schemas
class RagStatsResponse(BaseModel):
    """Response with knowledge bank statistics."""

    bank_name: str = Field(..., description="Knowledge bank name", example="technical_docs")
    num_chunks: int = Field(..., description="Total number of chunks in index", example=352)
    num_documents: int = Field(..., description="Number of source documents", example=12)
    chunk_size: int = Field(..., description="Chunk size in tokens", example=256)
    chunk_overlap: int = Field(..., description="Overlap tokens between chunks", example=50)
    embedding_model: str = Field(
        ..., description="Embedding model used", example="all-MiniLM-L6-v2"
    )
    embedding_dim: Optional[int] = Field(
        None, description="Embedding vector dimensions", example=384
    )
    created_at: Optional[str] = Field(
        None, description="Index creation timestamp", example="2025-11-16T10:30:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp", example="2025-11-16T14:22:00Z"
    )

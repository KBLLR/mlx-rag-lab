"""RAG API route handlers for document ingestion, retrieval, and management."""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from rag.api.exceptions import IndexNotFoundError, InvalidRequestError
from rag.api.schemas import (
    ChunkResult,
    DeleteRequest,
    DeleteResponse,
    QueryRequest,
    QueryResponse,
    StatsResponse,
    UpsertRequest,
    UpsertResponse,
)
from rag.config.settings import get_settings
from rag.retrieval.vdb import VectorDB

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


def _get_index_path(collection: str) -> Path:
    """Get the path to a collection's vector index.

    Args:
        collection: Collection name

    Returns:
        Path to the vector index file
    """
    return settings.index_root_path / collection / "vdb.npz"


def _collection_exists(collection: str) -> bool:
    """Check if a collection exists.

    Args:
        collection: Collection name

    Returns:
        True if collection exists, False otherwise
    """
    return _get_index_path(collection).exists()


@router.post("/rag_query", response_model=QueryResponse, tags=["RAG"])
async def query(
    request: QueryRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    """Query a collection for relevant documents (Phase-4 contract).

    Retrieves the top-k most relevant chunks from the specified collection
    based on semantic similarity to the query text.

    Args:
        request: Query request with query text, collection name, k, and threshold (Phase-4 enhanced)
        x_request_id: Optional request ID for tracing (header-based, deprecated in favor of body)

    Returns:
        QueryResponse with ranked chunks and latency

    Raises:
        404: Collection does not exist
        500: Query execution failed
    """
    import time

    # Start latency measurement
    start_time = time.perf_counter()

    # Generate request_id if not provided (Phase-4: prefer body, then header, then generate)
    request_id = request.requestId or x_request_id or str(uuid.uuid4())

    logger.info(
        f"Query request for collection '{request.collection}' "
        f"(k={request.k}, threshold={request.threshold}) "
        f"[request_id={request_id}]"
    )

    # Check if collection exists
    if not _collection_exists(request.collection):
        raise IndexNotFoundError(f"Collection '{request.collection}' does not exist")

    try:
        # Load the vector DB
        index_path = _get_index_path(request.collection)
        vdb = VectorDB(str(index_path))

        # Perform the query with optional metadata filter
        results = vdb.query(request.query, k=request.k, metadata_filter=request.filter)

        # Filter by threshold if specified
        if request.threshold is not None:
            filtered_results = []
            for result in results:
                # VectorDB now returns scores in the result dict
                if result.get("score", 0.0) >= request.threshold:
                    filtered_results.append(result)
            results = filtered_results

        # Convert to response format
        chunk_results = [
            ChunkResult(
                text=r["text"],
                source=r["source"],
                score=r.get("score", 0.0),  # Use actual similarity score from VectorDB
                metadata=r.get("metadata"),
            )
            for r in results
        ]

        # Measure latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Query returned {len(chunk_results)} results in {latency_ms:.2f}ms [request_id={request_id}]"
        )

        return QueryResponse(
            results=chunk_results,
            query=request.query,
            collection=request.collection,
            latency_ms=latency_ms,
            request_id=request_id,
        )

    except Exception as e:
        logger.error(
            f"Query failed for collection '{request.collection}': {e} "
            f"[request_id={request_id}]"
        )
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@router.post("/rag_upsert", response_model=UpsertResponse, tags=["RAG"])
async def upsert(
    request: UpsertRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    """Ingest documents into a collection (Phase-4 contract).

    Creates or updates a collection with the provided documents.
    Documents are chunked and embedded automatically.

    Args:
        request: Upsert request with documents and collection name
        x_request_id: Optional request ID for tracing

    Returns:
        UpsertResponse with ingestion statistics and latency

    Raises:
        400: Invalid request (empty documents, etc.)
        500: Ingestion failed
    """
    import time

    # Start latency measurement
    start_time = time.perf_counter()

    # Generate request_id if not provided
    request_id = x_request_id or str(uuid.uuid4())

    logger.info(
        f"Upsert request for collection '{request.collection}' "
        f"with {len(request.documents)} documents "
        f"[request_id={request_id}]"
    )

    if not request.documents:
        raise InvalidRequestError("No documents provided")

    try:
        # Load existing index if it exists, otherwise create new one
        index_path = _get_index_path(request.collection)
        if index_path.exists():
            vdb = VectorDB(str(index_path))
        else:
            vdb = VectorDB()

        # Track statistics
        total_chunks = 0

        # Ingest each document
        for doc in request.documents:
            if not doc.content.strip():
                logger.warning(
                    f"Skipping empty document from source '{doc.source}' "
                    f"[request_id={request_id}]"
                )
                continue

            # Count chunks before ingestion
            chunks_before = len(vdb.content) if vdb.content else 0

            # Ingest the document with metadata
            vdb.ingest(doc.content, doc.source, doc.metadata)

            # Count chunks after ingestion
            chunks_after = len(vdb.content) if vdb.content else 0
            total_chunks += chunks_after - chunks_before

        # Save the updated index
        # Ensure parent directory exists
        index_path.parent.mkdir(parents=True, exist_ok=True)
        vdb.savez(str(index_path))

        # Measure latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Upserted {len(request.documents)} documents "
            f"({total_chunks} chunks) to collection '{request.collection}' in {latency_ms:.2f}ms "
            f"[request_id={request_id}]"
        )

        return UpsertResponse(
            chunks_added=total_chunks,
            documents_processed=len(request.documents),
            collection=request.collection,
            index_path=str(index_path),
            latency_ms=latency_ms,
            request_id=request_id,
        )

    except Exception as e:
        logger.error(
            f"Upsert failed for collection '{request.collection}': {e} "
            f"[request_id={request_id}]"
        )
        raise HTTPException(status_code=500, detail=f"Upsert failed: {str(e)}")


@router.post("/rag_delete", response_model=DeleteResponse, tags=["RAG"])
async def delete(
    request: DeleteRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    """Delete documents from a collection based on filter criteria (Phase-4 contract).

    Args:
        request: Delete request with filter and collection name
        x_request_id: Optional request ID for tracing

    Returns:
        DeleteResponse with deletion count and latency

    Raises:
        404: Collection does not exist
        400: Invalid filter criteria
        500: Delete operation failed
    """
    import time

    # Start latency measurement
    start_time = time.perf_counter()

    # Generate request_id if not provided
    request_id = x_request_id or str(uuid.uuid4())

    logger.info(
        f"Delete request for collection '{request.collection}' "
        f"with filter {request.filter} "
        f"[request_id={request_id}]"
    )

    # Check if collection exists
    if not _collection_exists(request.collection):
        raise IndexNotFoundError(f"Collection '{request.collection}' does not exist")

    # Validate filter criteria
    if not request.filter:
        raise InvalidRequestError("Filter criteria cannot be empty")

    try:
        # Load the vector DB
        index_path = _get_index_path(request.collection)
        vdb = VectorDB(str(index_path))

        # Perform deletion
        deleted_count = vdb.delete(request.filter)

        # Persist changes if any deletions occurred
        if deleted_count > 0:
            vdb.savez(str(index_path))

        # Measure latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Deleted {deleted_count} chunks from collection '{request.collection}' in {latency_ms:.2f}ms "
            f"[request_id={request_id}]"
        )

        return DeleteResponse(
            deleted_count=deleted_count,
            collection=request.collection,
            latency_ms=latency_ms,
            request_id=request_id,
        )

    except Exception as e:
        logger.error(
            f"Delete failed for collection '{request.collection}': {e} "
            f"[request_id={request_id}]"
        )
        raise HTTPException(status_code=500, detail=f"Delete operation failed: {str(e)}")


@router.get("/rag_stats", response_model=StatsResponse, tags=["RAG"])
async def stats(
    collection: str,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    """Get statistics about a collection (Phase-4 contract).

    Args:
        collection: Collection name (query parameter)
        x_request_id: Optional request ID for tracing

    Returns:
        StatsResponse with collection statistics and latency

    Raises:
        404: Collection does not exist
        500: Failed to read statistics
    """
    import time

    # Start latency measurement
    start_time = time.perf_counter()

    # Generate request_id if not provided
    request_id = x_request_id or str(uuid.uuid4())

    logger.info(
        f"Stats request for collection '{collection}' " f"[request_id={request_id}]"
    )

    # Check if collection exists
    if not _collection_exists(collection):
        raise IndexNotFoundError(f"Collection '{collection}' does not exist")

    try:
        # Load the vector DB to get statistics
        index_path = _get_index_path(collection)
        vdb = VectorDB(str(index_path))

        # Count unique sources for num_documents
        unique_sources = set()
        if vdb.content:
            for item in vdb.content:
                unique_sources.add(item.get("source", "unknown"))

        num_chunks = len(vdb.content) if vdb.content else 0
        num_documents = len(unique_sources)

        # Get embedding dimensions
        embedding_dim = None
        if vdb.embeddings is not None:
            try:
                embedding_dim = vdb.embeddings.shape[1]
            except Exception:
                embedding_dim = None

        # Get file timestamps
        created_at = None
        updated_at = None
        if index_path.exists():
            try:
                stat = index_path.stat()
                # Use modification time as updated_at
                updated_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                # Use creation time as created_at (or mtime if ctime not available)
                created_at = datetime.fromtimestamp(
                    getattr(stat, 'st_birthtime', stat.st_mtime), tz=timezone.utc
                ).isoformat()
            except Exception:
                pass

        # Measure latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Stats for collection '{collection}': "
            f"{num_chunks} chunks, {num_documents} documents in {latency_ms:.2f}ms "
            f"[request_id={request_id}]"
        )

        return StatsResponse(
            collection=collection,
            num_chunks=num_chunks,
            num_documents=num_documents,
            embedding_model=vdb.model.model_id if hasattr(vdb.model, "model_id") else "unknown",
            embedding_dim=embedding_dim,
            index_path=str(index_path),
            created_at=created_at,
            updated_at=updated_at,
            latency_ms=latency_ms,
            request_id=request_id,
        )

    except Exception as e:
        logger.error(
            f"Failed to get stats for collection '{collection}': {e} "
            f"[request_id={request_id}]"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to read collection stats: {str(e)}"
        )

"""Room-specific RAG API routes for Smart Campus integration (Phase-4).

These endpoints provide room-aware and entity-aware query capabilities
specifically designed for Smart Campus room management.
"""

import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from rag.api.exceptions import IndexNotFoundError, InvalidRequestError
from rag.config.settings import get_settings
from rag.retrieval.vdb import VectorDB

# Import protocol models from shared/
try:
    from shared.phase4_protocol import (
        RoomQueryRequest,
        RoomQueryResponse,
        EntityContextRequest,
        RAGContext,
        RAGResult,
    )
except ImportError:
    # Fallback if shared/ is not in path
    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[4]
    if str(ROOT / "shared") not in sys.path:
        sys.path.insert(0, str(ROOT / "shared"))
    from phase4_protocol import (
        RoomQueryRequest,
        RoomQueryResponse,
        EntityContextRequest,
        RAGContext,
        RAGResult,
    )

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["Rooms"])


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


@router.post("/query_room", response_model=RoomQueryResponse, tags=["Rooms"])
async def query_room(
    request: RoomQueryRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    """Query room-specific knowledge with RAG context (Phase-4 Smart Campus).

    This endpoint provides room-aware RAG queries optimized for Smart Campus.
    It queries the 'rooms' collection with optional query rewriting for better
    context matching.

    Args:
        request: Room query request with room ID, query text, and options
        x_request_id: Optional request ID for tracing (header-based, optional)

    Returns:
        RoomQueryResponse with answer, RAG context, and optional entity info

    Raises:
        400: Invalid request or rooms collection not configured
        404: Rooms collection does not exist
        500: Query execution failed
    """
    import time

    # Start latency measurement
    start_time = time.perf_counter()

    # Use request_id from body (Phase-4 standard)
    request_id = request.requestId

    logger.info(
        f"Room query request for room '{request.room}' "
        f"(includeRag={request.includeRag}, includeEntities={request.includeEntities}) "
        f"[request_id={request_id}]"
    )

    # Use the 'rooms' collection
    collection = "rooms"

    # Check if rooms collection exists
    if not _collection_exists(collection):
        raise IndexNotFoundError(
            f"Rooms collection does not exist. "
            f"Please ingest room data first using: uv run ingest-rooms-cli --rooms-dir <path>"
        )

    try:
        rag_context = None
        entities = []

        # Execute RAG query if requested
        if request.includeRag:
            # Load the vector DB
            index_path = _get_index_path(collection)
            vdb = VectorDB(str(index_path))

            # Rewrite query to include room name for better context matching
            # Format: "room_name: user_query"
            rewritten_query = f"{request.room}: {request.query}"

            logger.debug(
                f"Rewritten query: '{rewritten_query}' "
                f"[request_id={request_id}]"
            )

            # Perform the query with room_id filter
            results = vdb.query(
                rewritten_query,
                k=5,  # Default k for room queries
                metadata_filter={"room_id": request.room},
            )

            # Apply threshold filtering (default: 0.6 for room queries)
            threshold = 0.6
            filtered_results = []
            for result in results:
                if result.get("score", 0.0) >= threshold:
                    filtered_results.append(result)

            # Convert to RAGResult format
            rag_results = [
                RAGResult(
                    text=r["text"],
                    score=r.get("score", 0.0),
                    metadata=r.get("metadata"),
                )
                for r in filtered_results
            ]

            # Measure RAG latency
            rag_latency = (time.perf_counter() - start_time) * 1000

            # Build RAG context
            rag_context = RAGContext(
                collection=collection,
                query=rewritten_query,
                results=rag_results,
                latencyMs=rag_latency,
                requestId=request_id,
            )

            logger.info(
                f"RAG query returned {len(rag_results)} results "
                f"[request_id={request_id}]"
            )

        # Handle entity inclusion if requested
        if request.includeEntities:
            # Query for entities associated with this room
            # Filter by room_id and section='entity'
            index_path = _get_index_path(collection)
            vdb = VectorDB(str(index_path))

            entity_results = vdb.query(
                f"{request.room} entities",
                k=10,
                metadata_filter={"room_id": request.room, "section": "entity"},
            )

            # Extract entity information from results
            for result in entity_results:
                metadata = result.get("metadata", {})
                entity_id = metadata.get("entity_id")
                if entity_id:
                    entities.append({
                        "entity_id": entity_id,
                        "description": result.get("text", ""),
                        "metadata": metadata,
                    })

            logger.info(
                f"Found {len(entities)} entities for room '{request.room}' "
                f"[request_id={request_id}]"
            )

        # Generate answer from RAG context
        # For now, use a deterministic approach: concatenate top results
        # In production, you could use a local LLM for better summarization
        answer = _generate_answer_from_rag(request.query, rag_context, request.room)

        # Measure total latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Room query completed in {latency_ms:.2f}ms "
            f"[request_id={request_id}]"
        )

        return RoomQueryResponse(
            requestId=request_id,
            room=request.room,
            answer=answer,
            entities=entities,
            ragContext=rag_context,
            latencyMs=latency_ms,
            modelUsed="rag-only",  # No LLM used, just RAG deterministic
        )

    except Exception as e:
        logger.error(
            f"Room query failed for room '{request.room}': {e} "
            f"[request_id={request_id}]"
        )
        raise HTTPException(status_code=500, detail=f"Room query execution failed: {str(e)}")


@router.post("/entity_context", response_model=RAGContext, tags=["Rooms"])
async def entity_context(
    request: EntityContextRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    """Get RAG context for a specific entity (Phase-4 Smart Campus).

    This endpoint retrieves RAG context specific to a given entity
    (e.g., sensor, device, automation) with optional room scoping.

    Args:
        request: Entity context request with entity ID and optional room filter
        x_request_id: Optional request ID for tracing (header-based, optional)

    Returns:
        RAGContext with entity-specific chunks and metadata

    Raises:
        404: Rooms collection does not exist
        500: Query execution failed
    """
    import time

    # Start latency measurement
    start_time = time.perf_counter()

    # Use request_id from body (Phase-4 standard)
    request_id = request.requestId

    logger.info(
        f"Entity context request for '{request.entityId}' "
        f"(room={request.room}, k={request.k}) "
        f"[request_id={request_id}]"
    )

    # Use the 'rooms' collection
    collection = "rooms"

    # Check if rooms collection exists
    if not _collection_exists(collection):
        raise IndexNotFoundError(
            f"Rooms collection does not exist. "
            f"Please ingest room data first using: uv run ingest-rooms-cli --rooms-dir <path>"
        )

    try:
        # Load the vector DB
        index_path = _get_index_path(collection)
        vdb = VectorDB(str(index_path))

        # Build metadata filter
        metadata_filter = {"entity_id": request.entityId}
        if request.room:
            metadata_filter["room_id"] = request.room

        # Query using entity_id as the query text
        results = vdb.query(
            request.entityId,
            k=request.k,
            metadata_filter=metadata_filter,
        )

        # Apply threshold filtering
        threshold = request.threshold if request.threshold is not None else 0.5
        filtered_results = []
        for result in results:
            if result.get("score", 0.0) >= threshold:
                filtered_results.append(result)

        # Convert to RAGResult format
        rag_results = [
            RAGResult(
                text=r["text"],
                score=r.get("score", 0.0),
                metadata=r.get("metadata"),
            )
            for r in filtered_results
        ]

        # Measure latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Entity context returned {len(rag_results)} results in {latency_ms:.2f}ms "
            f"[request_id={request_id}]"
        )

        return RAGContext(
            collection=collection,
            query=request.entityId,
            results=rag_results,
            latencyMs=latency_ms,
            requestId=request_id,
        )

    except Exception as e:
        logger.error(
            f"Entity context query failed for '{request.entityId}': {e} "
            f"[request_id={request_id}]"
        )
        raise HTTPException(
            status_code=500, detail=f"Entity context query execution failed: {str(e)}"
        )


def _generate_answer_from_rag(query: str, rag_context: Optional[RAGContext], room: str) -> str:
    """Generate a deterministic answer from RAG context.

    This is a simple deterministic approach. In production, you could use
    a local LLM (e.g., MLX Phi-3) for better summarization.

    Args:
        query: User's query
        rag_context: RAG context with retrieved chunks
        room: Room identifier

    Returns:
        Generated answer string
    """
    if not rag_context or not rag_context.results:
        return f"No information found about {room} room for query: {query}"

    # Build answer from top results
    answer_parts = []
    answer_parts.append(f"Based on {room} room information:")

    for i, result in enumerate(rag_context.results[:3], 1):
        # Extract relevant portion of text (strip room prefix if present)
        text = result.text
        # Remove the "Room: X" prefix if present
        if "\n\n" in text:
            text = text.split("\n\n", 1)[1] if len(text.split("\n\n")) > 1 else text

        answer_parts.append(f"\n{i}. {text[:200]}{'...' if len(text) > 200 else ''}")

    return "\n".join(answer_parts)

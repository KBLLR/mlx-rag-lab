"""Fusion API routes for profile-based RAG queries.

These routes provide a higher-level interface for Tier-2 orchestrators
(gen-idea-lab) and tool backends (mlx-openai-server, Smart Campus).

Key differences from low-level /rag_* routes:
- Uses profile_id instead of explicit collection names
- Applies profile-specific defaults (k, threshold)
- Validates metadata filters against profile schema
- Designed for cross-service integration
"""

import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from rag.api.exceptions import IndexNotFoundError, InvalidRequestError
from rag.api.profiles import get_profile, list_profiles, profile_exists
from rag.api.schemas import (
    ChunkResult,
    FusionQueryRequest,
    FusionQueryResponse,
    FusionTrace,
    ProfileInfo,
    ProfilesResponse,
)
from rag.config.settings import get_settings
from rag.retrieval.vdb import VectorDB

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/v1/fusion", tags=["Fusion"])


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


@router.post("/query", response_model=FusionQueryResponse, tags=["Fusion"])
async def fusion_query(
    request: FusionQueryRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    """Query a profile for relevant documents (Fusion API).

    This is the primary entry point for Tier-2 orchestrators and tool backends.
    It provides a higher-level interface than /rag_query, using profile_id
    instead of explicit collection names.

    Args:
        request: Fusion query request with profile_id, query, and optional filters
        x_request_id: Optional request ID for tracing

    Returns:
        FusionQueryResponse with ranked chunks, trace metadata, and latency

    Raises:
        400: Profile not found or invalid request
        404: Profile's collection does not exist
        500: Query execution failed
    """
    import time

    # Start latency measurement
    start_time = time.perf_counter()

    # Generate request_id if not provided
    request_id = x_request_id or str(uuid.uuid4())

    logger.info(
        f"Fusion query request for profile '{request.profile_id}' "
        f"[request_id={request_id}]"
    )

    # Validate profile exists
    if not profile_exists(request.profile_id):
        raise InvalidRequestError(
            f"Profile '{request.profile_id}' not found. "
            f"Available profiles: {list(p.profile_id for p in list_profiles())}"
        )

    # Get profile configuration
    profile = get_profile(request.profile_id)

    # Merge filters: explicit filters + classroom_id shortcut
    filters = request.filters or {}
    if request.classroom_id and "classroom_id" not in filters:
        filters["classroom_id"] = request.classroom_id

    # Apply profile defaults
    k = request.top_k if request.top_k is not None else profile.default_k
    threshold = request.threshold if request.threshold is not None else profile.default_threshold

    logger.info(
        f"Profile '{profile.profile_id}' → collection '{profile.collection}' "
        f"(k={k}, threshold={threshold}, filters={filters}) "
        f"[request_id={request_id}]"
    )

    # Check if collection exists
    if not _collection_exists(profile.collection):
        raise IndexNotFoundError(
            f"Collection '{profile.collection}' for profile '{profile.profile_id}' does not exist"
        )

    try:
        # Load the vector DB
        index_path = _get_index_path(profile.collection)
        vdb = VectorDB(str(index_path))

        # Perform the query with filters
        results = vdb.query(request.query, k=k, metadata_filter=filters if filters else None)

        # Filter by threshold
        if threshold is not None:
            filtered_results = []
            for result in results:
                if result.get("score", 0.0) >= threshold:
                    filtered_results.append(result)
            results = filtered_results

        # Convert to response format
        chunk_results = [
            ChunkResult(
                text=r["text"],
                source=r["source"],
                score=r.get("score", 0.0),
                metadata=r.get("metadata"),
            )
            for r in results
        ]

        # Measure latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        # Build trace metadata
        trace = FusionTrace(
            profile_id=profile.profile_id,
            collection_used=profile.collection,
            latency_ms=latency_ms,
            filters_applied=filters if filters else None,
        )

        logger.info(
            f"Fusion query returned {len(chunk_results)} results in {latency_ms:.2f}ms "
            f"[request_id={request_id}]"
        )

        return FusionQueryResponse(
            results=chunk_results,
            trace=trace,
            tokens=None,  # TODO: Calculate token count for results
            request_id=request_id,
        )

    except Exception as e:
        logger.error(
            f"Fusion query failed for profile '{request.profile_id}': {e} "
            f"[request_id={request_id}]"
        )
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@router.get("/profiles", response_model=ProfilesResponse, tags=["Fusion"])
async def list_available_profiles(
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    """List all available RAG profiles.

    Returns information about all configured profiles, including
    their collection mappings, default settings, and metadata schemas.

    Args:
        x_request_id: Optional request ID for tracing

    Returns:
        ProfilesResponse with list of available profiles
    """
    import uuid as uuid_lib

    # Generate request_id if not provided
    request_id = x_request_id or str(uuid_lib.uuid4())

    logger.debug(f"Listing available profiles [request_id={request_id}]")

    profiles = list_profiles()
    profile_infos = [
        ProfileInfo(
            profile_id=p.profile_id,
            collection=p.collection,
            default_k=p.default_k,
            default_threshold=p.default_threshold,
            metadata_schema=p.metadata_schema,
            description=p.description,
        )
        for p in profiles
    ]

    return ProfilesResponse(profiles=profile_infos, request_id=request_id)

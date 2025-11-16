"""FastAPI application for MLX RAG Engine (Tier 3B).

This module provides the main FastAPI application instance with:
- Health check endpoint
- CORS middleware for local development
- Structured logging
- Exception handling
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from rag.api.exceptions import RagException
from rag.api.routes import rag
from rag.api.schemas import HealthResponse
from rag.models.model import Model

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global model instance (loaded at startup)
_embedding_model: Optional[Model] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    global _embedding_model

    logger.info("Starting MLX RAG Engine API (Tier 3B)")

    # Initialize embedding model
    try:
        logger.info("Loading embedding model...")
        _embedding_model = Model()
        logger.info(f"Embedding model loaded: {_embedding_model.model_id}")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        _embedding_model = None

    yield

    logger.info("Shutting down MLX RAG Engine API")
    _embedding_model = None


# Create FastAPI application instance
app = FastAPI(
    title="MLX RAG Engine",
    description="Tier 3B: Stateless RAG engine with document ingestion, retrieval, and stats",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(rag.router, tags=["RAG"])


# Exception Handlers
@app.exception_handler(RagException)
async def rag_exception_handler(request: Request, exc: RagException):
    """Handle all RAG-specific exceptions.

    Args:
        request: The incoming request that triggered the exception
        exc: The RAG exception that was raised

    Returns:
        JSONResponse with error details and appropriate status code
    """
    logger.error(f"RAG Exception: {exc.detail} (status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.__class__.__name__,
                "message": exc.detail,
                "status_code": exc.status_code,
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions.

    This is a catch-all handler for any exceptions not covered by
    specific handlers. It prevents internal errors from leaking
    implementation details to clients.

    Args:
        request: The incoming request that triggered the exception
        exc: The exception that was raised

    Returns:
        JSONResponse with generic error message and 500 status
    """
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "InternalServerError",
                "message": "An internal server error occurred",
                "status_code": 500,
            }
        },
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(x_request_id: Optional[str] = Header(None, alias="X-Request-ID")):
    """Health check endpoint.

    Returns the current status of the RAG engine, including whether
    embedding models are loaded and ready to process requests.

    Returns:
        HealthResponse: Health status with model loading state
    """
    import uuid
    from pathlib import Path
    from rag.config.settings import get_settings

    # Generate request_id if not provided
    request_id = x_request_id or str(uuid.uuid4())

    logger.debug(f"Health check requested [request_id={request_id}]")

    models_loaded = _embedding_model is not None
    embedding_model = _embedding_model.model_id if _embedding_model else None

    # Check if index storage is accessible
    index_available = True
    try:
        settings = get_settings()
        index_root = settings.index_root_path
        # Ensure index root exists and is writable
        index_root.mkdir(parents=True, exist_ok=True)
        # Try to access it
        list(index_root.iterdir())
    except Exception as e:
        logger.warning(f"Index storage not accessible: {e}")
        index_available = False

    # Determine overall status
    status = "ok"
    if not models_loaded:
        status = "degraded"
    if not index_available:
        status = "error" if not models_loaded else "degraded"

    return HealthResponse(
        status=status,
        tier="3B",
        models_loaded=models_loaded,
        embedding_model=embedding_model,
        index_available=index_available,
        request_id=request_id,
    )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint providing API information."""
    return {
        "name": "MLX RAG Engine",
        "tier": "3B",
        "version": "0.1.0",
        "docs_url": "/docs",
        "health_url": "/health",
    }

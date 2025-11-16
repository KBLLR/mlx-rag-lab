"""FastAPI application for MLX RAG Engine (Tier 3B).

This module provides the main FastAPI application instance with:
- Health check endpoint
- CORS middleware for local development
- Structured logging
- Exception handling
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from rag.api.exceptions import RagException
from rag.api.schemas import HealthResponse

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    logger.info("Starting MLX RAG Engine API (Tier 3B)")
    yield
    logger.info("Shutting down MLX RAG Engine API")


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
async def health_check():
    """Health check endpoint.

    Returns the current status of the RAG engine, including whether
    embedding models are loaded and ready to process requests.

    Returns:
        HealthResponse: Health status with model loading state
    """
    logger.debug("Health check requested")

    # TODO: Add actual model loading check in Phase 1 Task (P1-1)
    return HealthResponse(
        status="ok",
        tier="3B",
        models_loaded=False,  # Placeholder until Model class is implemented
        embedding_model=None,  # Will be populated when Model is implemented
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

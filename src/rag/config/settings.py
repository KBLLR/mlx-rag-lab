"""Environment-based configuration for MLX RAG Engine.

This module provides centralized configuration management using Pydantic settings.
All configuration values can be overridden via environment variables.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden by setting environment variables with
    the same name (case-insensitive). For example:
        INDEX_ROOT_PATH=/custom/path uvicorn rag.api.main:app

    Settings can also be loaded from a .env file in the project root.
    """

    # Vector Index Storage
    INDEX_ROOT_PATH: str = Field(
        default="var/indexes",
        description="Root directory for vector index storage",
    )

    # Embedding Model Configuration
    EMBEDDING_MODEL_ID: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace model ID or local path for embeddings",
    )

    # Index Cache Management
    MAX_INDEX_CACHE_SIZE: int = Field(
        default=3,
        description="Maximum number of knowledge banks to keep in memory",
        ge=1,
        le=50,
    )

    # Chunking Configuration
    CHUNK_SIZE: int = Field(
        default=256,
        description="Default chunk size in tokens",
        ge=50,
        le=2048,
    )

    CHUNK_OVERLAP: int = Field(
        default=50,
        description="Default overlap between chunks in tokens",
        ge=0,
        le=512,
    )

    # Logging Configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # API Configuration
    API_HOST: str = Field(
        default="0.0.0.0",
        description="API server host",
    )

    API_PORT: int = Field(
        default=8000,
        description="API server port",
        ge=1024,
        le=65535,
    )

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra environment variables
        case_sensitive=False,  # Allow lowercase env vars
    )

    @property
    def index_root_path(self) -> Path:
        """Return INDEX_ROOT_PATH as a Path object."""
        return Path(self.INDEX_ROOT_PATH)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    This function creates a singleton Settings instance that is cached
    for the lifetime of the application. Subsequent calls return the
    same instance.

    Returns:
        Settings: Application settings instance
    """
    return Settings()

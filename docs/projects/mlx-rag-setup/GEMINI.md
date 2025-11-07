# mlx-RAG Setup - Gemini AI Assistant Guide

This `GEMINI.md` file serves as a high-level entry point for AI assistant interactions within the `mlx-RAG Setup` project. It provides essential context and directs the AI to more detailed documentation.

## Project Overview

`mlx-RAG` is a local-first Retrieval-Augmented Generation (RAG) system built on Apple Silicon using the MLX framework. It allows users to ingest documents, create a local vector database with MLX-based embeddings, and query it using a local MLX-powered Large Language Model (LLM). This setup guide focuses on establishing the foundational components for this system.

## Key Documentation Files

For detailed instructions, context, and project-specific documentation, please refer to the following files:

*   [`README.md`](README.md): High-level project overview and setup instructions.
*   [`SITEMAP.md`](SITEMAP.md): A human-friendly overview of the repository structure.
*   [`DEVELOPMENT_GUIDELINES.md`](../../DEVELOPMENT_GUIDELINES.md): Comprehensive guidelines for development practices, artifact management, and release procedures for the main `mlx-RAG` project.
*   [`AUDIT-log.md`](AUDIT-log.md): Checklist and criteria for assessing the project's "good state" for the `mlx-RAG Setup`.
*   [`tasks.md`](tasks.md): A ledger for tracking all project tasks and their status for the `mlx-RAG Setup`.

## AI Assistant Specific Instructions

*   **Prioritize changes** within the `src/rag` and `src/libs` directories for core RAG system components.
*   **Model artifacts** are located in the `models/` directory.
*   **Dependency management** is handled exclusively by `uv` and `pyproject.toml`.
*   **Always refer to existing documentation** (especially `README.md`, `SITEMAP.md`, and `AUDIT-log.md`) for context before making changes.
*   **When refactoring**, ensure backward compatibility with existing APIs, especially `MLXModelEngine` and `VectorDB`.

## Dependency Management

Dependencies are managed exclusively via `uv` and `pyproject.toml`.
*   To install core runtime dependencies: `uv sync`
*   To install development dependencies: `uv sync --dev`

## Building and Running

*   **Downloading Models**: `uv run python -m rag.cli.download_model --model-id <HUGGING_FACE_MODEL_ID>`
*   **Creating a Vector Database**: `uv run python -m rag.ingestion.create_vdb --pdf <PATH_TO_YOUR_PDF_FILE> --vdb models/indexes/vdb.npz`
*   **Querying the Vector Database**: `uv run python -m rag.retrieval.query_vdb --question "<YOUR_QUESTION>" --vdb models/indexes/vdb.npz`
*   **Interactive RAG CLI**: `uv run python -m rag.cli.interactive_rag`
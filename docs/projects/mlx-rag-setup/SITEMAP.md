# SITEMAP — mlx-RAG Source Overview

_Last generated: 2025-11-05_

This sitemap provides a **human-friendly** overview of the `mlx-RAG` monorepo structure, helping developers and AI agents quickly locate relevant files and understand the project layout.

## Top-Level Directories

*   `/src` — Core Python source code for the RAG pipeline and shared libraries.
    *   `/src/rag` — Main RAG package.
        *   `/src/rag/config` — Configuration files (e.g., `config.json`).
        *   `/src/rag/ingestion` — Data ingestion and vectorization pipelines (e.g., `create_vdb.py`).
        *   `/src/rag/retrieval` — Retrieval and vector database utilities (e.g., `vdb.py`, `query_vdb.py`).
        *   `/src/rag/models` — Model-facing code (e.g., `model.py` for embedding models).
        *   `/src/rag/cli` — User-facing command-line interfaces (e.g., `interactive_rag.py`).
    *   `/src/libs` — Project-owned reusable utilities.
        *   `/src/libs/mlx_core` — Thin adapters and helpers for MLX / local model APIs (e.g., `model_engine.py`).
        *   `/src/libs/utils` — Shared utilities (logging, I/O helpers).
*   `/models` — Model artifacts and indices (ignored by Git).
    *   `/models/mlx-models` — Local MLX-ready models (e.g., Phi-3, Llasa, Whisper).
    *   `/models/embeddings` — Embedding artifacts (e.g., `gte-embeddings-model.npz`).
    *   `/models/indexes` — Vector database index files (e.g., `combined_vdb.npz`).
    *   `/models/lora` — LoRA training datasets and scripts.
*   `/apps` — Native client applications and UI code (e.g., iOS, macOS, UI components).
*   `/third_party` — Vendored or external projects and libraries.
*   `/experiments` — Experimental or prototype code and assets.
*   `/var` — Local logs and generated outputs (ignored by Git).
    *   `/var/logs` — Log files.
    *   `/var/outputs` — Generated artifacts and temporary results.
    *   `/var/source_docs` — Local PDF documents for ingestion (ignored by Git).
*   `/config` — Environment-level configuration (e.g., `requirements.txt`, `env.example`).
*   `/docs` — Project documentation (this file, `README.md`, `GEMINI.md`, `DEVELOPMENT_GUIDELINES.md`, `AUDIT-log.md`, `tasks.md`).

## Root-Level Files

*   `/pyproject.toml` — Canonical Python project definition (managed by `uv`).
*   `/uv.lock` — Locked dependency versions.
*   `/LICENSE` — Project license.
*   `/.gitignore` — Specifies files and directories to be ignored by Git.
*   `/README.md` — High-level project overview.
*   `/GEMINI.md` — AI assistant / MCP configuration and context.

## Developer Notes

*   Keep paths **relative to the repo root**.
*   Auto-generated files (build artifacts, downloaded models, VDBs) should **not** be hand-edited; regenerate or re-download instead.
*   For detailed development guidelines, refer to `docs/DEVELOPMENT_GUIDELINES.md`.

> For a fully expanded view (e.g., file-level detail), tools can be used to list directories recursively.

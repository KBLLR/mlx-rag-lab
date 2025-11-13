# SITEMAP — MLX Data Pipeline Source Overview

_Last generated: 2025-11-07_

This sitemap provides a **human-friendly** overview of the `mlx-data-pipeline` project structure, helping developers and AI agents quickly locate relevant files and understand the project layout.

## Top-Level Directories

*   `/src` — Core Python source code for the data pipeline.
    *   `/src/data_ingestion` — Modules for ingesting various data types (e.g., `pdf_loader.py`, `jsonl_loader.py`).
    *   `/src/data_processing` — Modules for transforming and preparing data using `mlx.data` (e.g., `chunking.py`, `embedding_generation.py`).
    *   `/src/data_schemas` — Definitions of data schemas (e.g., `document_schema.py`, `training_sample_schema.py`).
    *   `/src/vdb_integration` — Modules for interacting with the Vector Database (e.g., `vdb_builder.py`, `vdb_updater.py`).
    *   `/src/retrieval_strategies` — Implementations of various retrieval methods (e.g., `vector_search.py`, `hybrid_search.py`).
    *   `/src/performance_testing` — Scripts and utilities for benchmarking the pipeline (e.g., `ingestion_benchmarks.py`, `retrieval_benchmarks.py`).
*   `/data` — Sample data, raw inputs, or processed outputs (ignored by Git).
    *   `/data/raw` — Raw input data (e.g., PDFs, JSONL files).
    *   `/data/processed` — Intermediate or final processed data.
*   `/config` — Configuration files for the data pipeline.
*   `/docs` — Project documentation (this file, `README.md`, `GEMINI.md`, `AUDIT-log.md`, `tasks.md`).
    *   `/docs/future-features` — Placeholder for future feature ideas.
    *   `/docs/qa` — Quality Assurance checklists.
    *   `/docs/sessions` — Session logs for development work.

## Root-Level Files

*   `/README.md` — High-level project overview and setup instructions.
*   `/SITEMAP.md` — This human-friendly overview of the repository structure.
*   `/AUDIT-log.md` — Checklist and criteria for assessing the project's "good state."
*   `/GEMINI.md` — AI assistant / MCP configuration and context for this project.
*   `/tasks.md` — A ledger for tracking all project tasks and their status.

## Developer Notes

*   Keep paths **relative to the repo root**.
*   Prioritize the use of `mlx.data` for efficient data loading and processing.
*   Ensure modularity to support diverse data sources and future MLX projects.

> For a fully expanded view (e.g., file-level detail), tools can be used to list directories recursively.
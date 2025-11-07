# MLX Data Pipeline - Gemini AI Assistant Guide

This `GEMINI.md` file serves as a high-level entry point for AI assistant interactions within the `MLX Data Pipeline` project. It provides essential context and directs the AI to more detailed documentation.

## Project Overview

The `mlx-data-pipeline` project aims to provide a generic and extensible data pipeline solution for the `mlx-RAG` monorepo. Its purpose is to handle diverse data sources, including RAG documents (e.g., PDFs), training datasets for LoRA, Flux, and other future MLX projects. The pipeline will emphasize efficient data loading using `mlx.data`, modular design, and robust data quality checks.

## Key Documentation Files

For detailed instructions, context, and project-specific documentation, please refer to the following files:

*   [`README.md`](README.md): High-level project overview and setup instructions.
*   [`SITEMAP.md`](SITEMAP.md): A human-friendly overview of the repository structure.
*   [`AUDIT-log.md`](AUDIT-log.md): Checklist and criteria for assessing the project's "good state."
*   [`GEMINI.md`](GEMINI.md): This AI assistant / MCP configuration and context file.
*   [`tasks.md`](tasks.md): A ledger for tracking all project tasks and their status.

## AI Assistant Specific Instructions

*   **Prioritize modularity and extensibility** to support various data sources and future MLX projects.
*   **Leverage `mlx.data`** for all data loading and processing tasks, focusing on efficient pipeline construction (e.g., using `prefetch`).
*   **Emphasize data schema definition** and data quality checks throughout the pipeline.
*   **Integrate seamlessly with the existing `VectorDB`** for embedding storage and retrieval.
*   **Conduct thorough performance testing** for ingestion and retrieval components.
*   **Refer to official MLX documentation** ([https://ml-explore.github.io/mlx/build/html/index.html](https://ml-explore.github.io/mlx/build/html/index.html)) and `ml-explore/mlx-examples` for data handling best practices.

## Dependency Management

Dependencies will include `mlx`, `mlx-lm` (for embedding models), `unstructured[pdf]` (for PDF ingestion), and potentially other data-specific libraries. `uv` is the preferred dependency manager.

*   To install core MLX: `pip install mlx`
*   To install MLX for LLMs: `pip install mlx-lm`
*   For PDF processing: `pip install unstructured[pdf]`

## Building and Running

This project will involve running Python scripts for data ingestion, processing, VDB building, and retrieval. There are no complex build steps beyond installing the necessary Python packages.

*   **Data Ingestion Scripts**: Run scripts to ingest data from various sources.
*   **VDB Building Scripts**: Execute scripts to build or update the Vector Database.
*   **Retrieval Test Scripts**: Run scripts to test different retrieval strategies.
*   **Performance Benchmarks**: Execute scripts to measure pipeline performance.
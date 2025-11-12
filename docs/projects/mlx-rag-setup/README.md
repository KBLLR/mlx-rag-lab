# MLX-RAG Project Setup Guide

This document provides comprehensive instructions for setting up, installing dependencies, and getting started with the `mlx-RAG` project. It covers prerequisites, installation, vector database creation, and querying.

## 1. Project Overview

`mlx-RAG` is a local-first Retrieval-Augmented Generation (RAG) system built on Apple Silicon using the MLX framework. It allows users to ingest documents, create a local vector database with MLX-based embeddings, and query it using a local MLX-powered Large Language Model (LLM).

## 2. Prerequisites

Before you begin, ensure you have the following:

*   **Apple Silicon Mac**: The MLX framework is optimized for Apple Silicon. This project is designed to run on compatible hardware.
*   **Python 3.9+**: The project requires Python 3.9 or newer.
*   **`uv`**: The project uses `uv` for efficient dependency management. If you don't have `uv` installed, you can install it via `pipx`:
    ```bash
    pipx install uv
    ```

## 3. Installation

Follow these steps to set up the project and install its dependencies:

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone https://github.com/your-org/mlx-RAG.git
    cd mlx-RAG
    ```
    *(Note: Replace `https://github.com/your-org/mlx-RAG.git` with the actual repository URL if different.)*

2.  **Install core runtime dependencies** using `uv`:
    ```bash
    uv sync
    ```

3.  **Install development dependencies** (optional, but recommended for contributors):
    ```bash
    uv sync --dev
    ```

## 4. Model Management

The `mlx-RAG` system relies on local MLX-compatible models for embeddings and LLM generation. A utility script is provided to download these models from the Hugging Face Hub.

### Downloading Models

Use the `download_model.py` script to acquire MLX-compatible models:

```bash
uv run python -m rag.cli.download_model --model-id <HUGGING_FACE_MODEL_ID>
```

**Example (for an LLM):**

```bash
uv run python -m rag.cli.download_model --model-id mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit
```

**Example (for an embedding model, if not already provided):**

```bash
uv run python -m rag.cli.download_model --model-id BAAI/bge-large-en-v1.5-mlx
```

*   Replace `<HUGGING_FACE_MODEL_ID>` with the desired model ID from Hugging Face.
*   Downloaded models are typically cached in `~/.cache/huggingface/hub`.

## 5. Creating a Vector Database (VDB)

You can now build indexes either from a specific set of PDFs or by pointing at your knowledge-bank root folder.

### Single Index from Specific PDFs

```bash
uv run python -m rag.ingestion.create_vdb \
  --pdfs var/source_docs/mlx/*.pdf \
  --vdb models/indexes/combined_vdb.npz
```

*   `--pdfs` accepts individual files and/or directories (all nested PDFs are included).
*   The `--vdb` argument sets the output `.npz` path; a companion `.meta.json` file is written automatically.

### One Index per Knowledge Bank

```bash
uv run python -m rag.ingestion.create_vdb \
  --banks-root var/source_docs \
  --output-dir models/indexes \
  --mlx-batch-size 4 --mlx-prefetch 8
```

This iterates over every immediate subfolder inside `var/source_docs/` (e.g., `agentic-design`, `mlx`, `generative-music`) and writes one VDB under `models/indexes/<bank>/vdb.npz` plus metadata describing the documents, chunking parameters, and timestamp. The command requires the `mlx-data` package, so make sure you’ve run `uv add mlx-data` beforehand.

> Tip: tweak `--mlx-batch-size` / `--mlx-prefetch` to fine-tune throughput. The pipeline always relies on `mlx.data`, so ensure `uv add mlx-data` has been run in your environment.
## 6. Querying the Vector Database

Once your vector database is created, you can query it using the `query_vdb.py` script:

```bash
uv run python -m rag.retrieval.query_vdb --question "<YOUR_QUESTION>" --vdb models/indexes/vdb.npz
```

If you generated per-bank indexes, supply the bank name instead of a direct `.npz` path:

```bash
uv run python -m rag.retrieval.query_vdb \
  --question "What is MLX?" \
  --bank agentic-design \
  --indexes-dir models/indexes
```

*   Replace `<YOUR_QUESTION>` with the question you want to ask.
*   Ensure the `--vdb` argument (or `--bank`) points to your created vector database.

## 7. Verification Steps

To verify your setup:

1.  Run `uv sync` and ensure no errors are reported.
2.  Successfully download an MLX model using `rag.cli.download_model`.
3.  Create a vector database from a sample PDF using `rag.ingestion.create_vdb`.
4.  Query the created vector database using `rag.retrieval.query_vdb` and observe relevant responses.

If you encounter any issues, refer to the `DEVELOPMENT_GUIDELINES.md` for troubleshooting or consult the project maintainers.

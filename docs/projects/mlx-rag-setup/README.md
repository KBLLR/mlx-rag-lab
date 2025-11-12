# MLX-RAG Project Setup Guide

This document provides comprehensive instructions for setting up, installing dependencies, and getting started with the `mlx-RAG` project. It covers prerequisites, installation, vector database creation, and querying.

## 1. Project Overview

`mlx-RAG` is a local-first Retrieval-Augmented Generation (RAG) system built on Apple Silicon using the MLX framework. It allows users to ingest documents, create a local vector database with MLX-based embeddings, and query it using a local MLX-powered Large Language Model (LLM).

## RAG v0.1 Milestone

The first milestone focuses on proving a stable, fully local workflow. RAG v0.1 will:
- **RAG-013** – persist chunk-level source metadata and surface citations in answers.
- **RAG-014** – define a native MLX reranker interface powered by MLX LMs (e.g., Qwen/mxbai).
- **RAG-015** – replace the legacy CrossEncoder references in `interactive_rag` with the new MLX reranker.
- **RAG-016** – document a reliable smoke scenario (sample corpus + `create_vdb` + `interactive_rag`) that runs on a single Apple Silicon machine.
- **RAG-017** – add minimal VectorDB save/load + ranking tests that avoid heavy ML downloads or Metal requirements.

See RAG-013 / RAG-014 / RAG-015 / RAG-016 / RAG-017 in `tasks.md` for the canonical wording and status of each work item.

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

To create a vector database from your documents, use the `create_vdb.py` script. This example uses a PDF file.

```bash
uv run python -m rag.ingestion.create_vdb --pdf <PATH_TO_YOUR_PDF_FILE> --vdb models/indexes/vdb.npz
```

**Example:**

```bash
uv run python -m rag.ingestion.create_vdb --pdf var/source_docs/my_document.pdf --vdb models/indexes/vdb.npz
```

*   Replace `<PATH_TO_YOUR_PDF_FILE>` with the absolute or relative path to your PDF document.
*   The `--vdb` argument specifies the output path for your vector database index.

## 6. Querying the Vector Database

Once your vector database is created, you can query it using the `query_vdb.py` script:

```bash
uv run python -m rag.retrieval.query_vdb --question "<YOUR_QUESTION>" --vdb models/indexes/vdb.npz
```

**Example:**

```bash
uv run python -m rag.retrieval.query_vdb --question "What is MLX?" --vdb models/indexes/vdb.npz
```

*   Replace `<YOUR_QUESTION>` with the question you want to ask.
*   Ensure the `--vdb` argument points to your created vector database.

## 7. Verification Steps

To verify your setup:

1.  Run `uv sync` and ensure no errors are reported.
2.  Successfully download an MLX model using `rag.cli.download_model`.
3.  Create a vector database from a sample PDF using `rag.ingestion.create_vdb`.
4.  Query the created vector database using `rag.retrieval.query_vdb` and observe relevant responses.

If you encounter any issues, refer to the `DEVELOPMENT_GUIDELINES.md` for troubleshooting or consult the project maintainers.

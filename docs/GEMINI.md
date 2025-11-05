# MLX RAG Project Overview

This project implements a local-first Retrieval-Augmented Generation (RAG) system on Apple Silicon, built on top of the MLX framework. It's structured as a monorepo, aiming for "one clean RAG stack, many clients."

## Core Idea

The RAG system follows these steps:
1.  **Ingest documents**: PDFs or other text documents are ingested into a custom vector database using MLX-based embeddings.
2.  **Store embeddings locally**: Embeddings are stored as lightweight `npz` indexes.
3.  **Query with a local LLM**: The system uses a local LLM, running fully on-device via MLX, to answer queries.

By default, the project uses:
*   **Embedding model**: `gte-large` (converted to MLX format).
*   **LLM for generation**: `mlx-community/NeuralBeagle14-7B-4bit-mlx`.

These models can be swapped for any MLX-supported embedding + LLM pair.

## Repository Layout

The repository is structured as follows:

*   **`docs/`**: High-level documentation.
*   **`.gemini/`**: AI assistant / MCP configuration.
*   **`src/`**:
    *   **`rag/`**: Core RAG Python package.
        *   **`config/`**: RAG configuration files (model paths, index locations).
        *   **`ingestion/`**: PDF/text ingestion and vector DB building.
        *   **`retrieval/`**: Vector DB, similarity search, query strategies.
        *   **`models/`**: Model wrappers and MLX integration.
        *   **`cli/`**: Command-line entrypoints.
    *   **`libs/`**: Shared utilities.
        *   **`mlx_core/`**: Thin adapters around MLX / MLX-LM / model helpers.
        *   **`utils/`**: Shared utilities (logging, I/O, misc helpers).
*   **`models/`**: Model artifacts and indices.
    *   **`mlx-models/`**: Local model folders (LLMs, encoders) in MLX format.
    *   **`embeddings/`**: Embedding artifacts (e.g., GTE NPZ files).
    *   **`indexes/`**: Vector DB index files (e.g., `vdb.npz`).
    *   **`lora/`**: LoRA datasets and training artifacts.
*   **`apps/`**: Native client applications and UI experiments.
    *   **`ios/`**: iOS / vision / RAG clients.
    *   **`macos/`**: macOS-specific apps.
    *   **`ui-components/`**: Shared UI building blocks.
*   **`third_party/`**: Vendored libraries and external projects.
*   **`experiments/`**: Prototypes, sandboxes, scratch experiments.
*   **`var/`**:
    *   **`logs/`**: Local logs.
    *   **`outputs/`**: Generated outputs / artifacts.
*   **`config/`**: Environment and dependency configuration.
*   **`pyproject.toml`**: Canonical Python project definition (managed by `uv`).
*   **`uv.lock`**: Locked dependency versions.
*   **`LICENSE`**: Project license.

## Building and Running

### Installation

The project uses `uv` for dependency management. The core dependencies are defined in `pyproject.toml`.

To install the core runtime dependencies:

```bash
uv sync
```

To install development dependencies (including `pytest`, `ruff`, `mypy`):

```bash
uv sync --dev
```

### Creating a Vector Database

To create a vector database from a PDF file (e.g., `flash_attention.pdf`), run:

```bash
python3 src/rag/ingestion/create_vdb.py --pdf flash_attention.pdf --vdb models/indexes/vdb.npz
```

### Querying the Database

Once the vector database is created, you can query it with a question:

```bash
python3 src/rag/retrieval/query_vdb.py --question "what is flash attention?" --vdb models/indexes/vdb.npz
```

## Development Conventions

*   **Coding Style**: Pythonic style, leveraging `mlx` for array operations and neural network definitions.
*   **Model Loading**: Models are loaded from Hugging Face Hub, with pre-converted MLX weights for the embedding model.
*   **PDF Processing**: `unstructured` library is used for robust PDF content extraction.
*   **Vector Database**: Custom `VectorDB` implementation for managing embeddings and content chunks.
*   **Dependency Management**: `uv` is used for managing Python dependencies, with `pyproject.toml` as the canonical source of truth.
*   **Project Structure**: Adherence to the monorepo layout described above, with `src/rag` and `src/libs` as the primary focus for core logic.
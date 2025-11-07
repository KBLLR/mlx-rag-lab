# MLX RAG

Local-first Retrieval-Augmented Generation (RAG) on Apple Silicon, built on top of [MLX](https://github.com/ml-explore/mlx) and MLX-compatible models from the [Hugging Face Hub](https://huggingface.co/).

This repository started from the original [`mlx-rag` example](https://github.com/vegaluisjose/mlx-rag) and has evolved into a monorepo that groups:

- A Python RAG core (`src/rag`)
- Shared utilities for MLX and data workflows (`src/libs`)
- Local model artifacts (`models/`)
- Native clients and UI experiments (`apps/`)
- Vendored / reference libraries (`third_party/`)

The goal is: **one clean RAG stack, many clients**, all optimized for Apple Silicon.

---

## Core idea

1. **Ingest documents** (e.g. PDFs) into a custom vector database using MLX-based embeddings.
2. **Store embeddings locally** as lightweight `npz` indexes.
3. **Query with a local LLM**, running fully on-device via MLX.

By default, the project is configured around:

- **Embedding model**: [`gte-large`](https://huggingface.co/thenlper/gte-large) converted to MLX format (or compatible GTE variants).
- **LLM for generation**: [`mlx-community/NeuralBeagle14-7B-4bit-mlx`](https://huggingface.co/mlx-community/NeuralBeagle14-7B-4bit-mlx) as a fast, quantized MLX model.

You can swap these for any MLX-supported embedding + LLM pair with minimal changes.

---

## Repository layout



This repo is intentionally structured so tools (and humans) know where to look:



```txt

mlx-RAG/

  docs/                # High-level documentation (this README, architecture notes, etc.)

  .gemini/             # AI assistant / MCP configuration (optional, tool-specific)

  src/

    rag/               # Core RAG package (Python)

      config/          # RAG config files (model paths, index locations, etc.)

      ingestion/       # PDF/text ingestion & vector DB building

      retrieval/       # Vector DB, similarity search, query strategies

      models/          # Model wrappers & MLX integration

      cli/             # Command-line entrypoints

    libs/

      mlx_core/        # Thin adapters around MLX / MLX-LM / model helpers

      utils/           # Shared utilities (logging, I/O, misc helpers)

  models/

    mlx-models/        # Local model folders (LLMs, encoders) in MLX format

    embeddings/        # Embedding artifacts (e.g. GTE NPZ files)

    indexes/           # Vector DB index files (e.g. vdb.npz)

    lora/              # LoRA datasets & training artefacts

  apps/

    ios/               # iOS / vision / RAG clients

    macos/             # macOS-specific apps

    ui-components/     # Shared UI building blocks

  third_party/         # Vendored libraries & external projects

  experiments/         # Prototypes, sandboxes, scratch experiments

  var/

    logs/              # Local logs (ignored in VCS)

    outputs/           # Generated outputs / artifacts

    source_docs/       # Local PDF documents for ingestion (ignored in VCS)

  config/              # Environment & dependency configuration

  pyproject.toml       # Canonical Python project definition (managed by uv)

  uv.lock              # Locked dependency versions

  LICENSE

```



### Key Documentation Files



*   [`docs/SITEMAP.md`](docs/SITEMAP.md): A human-friendly overview of the repository structure.

*   [`docs/DEVELOPMENT_GUIDELINES.md`](docs/DEVELOPMENT_GUIDELINES.md): Comprehensive guidelines for development practices, artifact management, and release procedures.

*   [`docs/AUDIT-log.md`](docs/AUDIT-log.md): Checklist and criteria for assessing the project's "good state."

*   [`docs/tasks.md`](docs/tasks.md): A ledger for tracking all project tasks and their status.





# MLX RAG

Local-first Retrieval-Augmented Generation (RAG) on Apple Silicon, built on top of [MLX](https://github.com/ml-explore/mlx) and MLX-compatible models from the [Hugging Face Hub](https://huggingface.co/).

This repository started from the original [`mlx-rag` example](https://github.com/vegaluisjose/mlx-rag) and has evolved into a monorepo that groups:

- A Python RAG core (`src/rag`)
- Shared utilities for MLX and data workflows (`src/libs`)
- Local model artifacts (`models/`)
- CLI-focused entrypoints and helpers (`apps/`)
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
├── apps/
│   ├── rag_cli.py
│   ├── flux_cli.py
│   ├── musicgen_cli.py
│   ├── voice_cli.py
│   └── bench_cli.py
├── benchmarks/
│   ├── flux/
│   ├── musicgen/
│   ├── flux_benchmark.py
│   └── prompt_evaluation.py
├── docs/
│   ├── README.md
│   ├── MLX-CORE.md
│   ├── models/
│   ├── profiling/
│   ├── projects/
│   └── tasks.md
├── experiments/
│   ├── benchmarking/
│   ├── dataset_generation/
│   └── ingestion/
├── lora/
├── mlx-models/
├── models/
│   └── indexes/
├── musicgen/
├── segment_anything/
├── speechcommands/
├── scripts/
│   ├── clean_models.py
│   └── model_manifest.py
├── src/
│   ├── __init__.py
│   └── rag/
├── tests/
│   ├── flux/
│   ├── models/
│   ├── musicgen/
│   └── test_flux_generation.py
├── utils/
│   └── convert_cross_encoder.py
├── var/
│   ├── benchmarking/
│   ├── music_output/
│   ├── source_docs/
│   └── static/
└── pyproject.toml
```

The legacy Textual TUI now lives under `archive/tui/` for historical reference; day-to-day experimentation happens via the CLIs in `apps/`.



### Key Documentation Files



*   [`docs/SITEMAP.md`](docs/SITEMAP.md): A human-friendly overview of the repository structure.

*   [`docs/DEVELOPMENT_GUIDELINES.md`](docs/DEVELOPMENT_GUIDELINES.md): Comprehensive guidelines for development practices, artifact management, and release procedures.

*   [`docs/AUDIT-log.md`](docs/AUDIT-log.md): Checklist and criteria for assessing the project's "good state."

*   [`docs/tasks.md`](docs/tasks.md): A ledger for tracking all project tasks and their status.

*   [`docs/COMMANDS_MANIFEST.md`](docs/COMMANDS_MANIFEST.md): Canonical collection of CLI commands grouped by app (Flux, MusicGen, RAG) for benchmarking and generation workflows.

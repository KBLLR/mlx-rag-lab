# mlx-RAG

This repository is a monorepo for experiments and applications built on top of MLX-based retrieval-augmented generation (RAG) on Apple silicon. It is a lab: MLX-powered RAG, Flux, MusicGen, and benchmarking experiments gathered in one repo, not a polished product.

## Project Overview

The core Python RAG pipeline lives under `src/` and is responsible for:
- Ingesting documents into vector databases
- Running retrieval and query workflows
- Integrating with local MLX models for inference

Additional directories such as `apps/`, `Libraries/`, and `Tools/` contain example apps, Swift libraries, and utilities that build on the MLX ecosystem.

## Features

*   **MLX-powered RAG:** Leverage Apple silicon for efficient local RAG operations.
*   **Modular Design:** Easily extendable architecture for various RAG components.
*   **Multimodal Capabilities:** (Future) Integration with models like Musicgen for audio generation, FLUX for images, and Llasa for voice.
*   **CLI Interface:** Interactive command-line tools for ingestion, querying, and model interaction.

## Setup and Installation

To get started with `mlx-RAG`, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/mlx-RAG.git
    cd mlx-RAG
    ```

2.  **Install `uv`:**
    This project uses `uv` for dependency management. If you don't have `uv` installed, you can get it via `pip`:
    ```bash
    pip install uv
    ```

3.  **Create and activate virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

4.  **Install dependencies:**
    ```bash
    uv sync
    ```

5.  **Download MLX Models:**
    Some components require pre-trained MLX models. Refer to `mlx-models/README.md` for instructions on how to download them.

## Usage

The lab exposes three main CLIs plus helper workflows:

- `rag-cli` – RAG over a local vector index; it reranks documents before calling `MLXModelEngine`. The CLI may trigger MLX/Metal `NSRangeException` when you hit real models.
- `flux-cli` – Flux text-to-image demo that wraps `rag.cli.flux_txt2image`.
- `bench-cli` – Dispatches the Flux benchmark runner or prompt evaluation workflow with familiar presets.

Every command is registered via `[project.scripts]` so you can run `uv run rag-cli ...` (or install the package to expose the entry points). The previous Textual-based TUI lives in `archive/tui/` and is not maintained; the CLI path is the canonical way forward.

For ingestion, benchmarking, or MusicGen experiments you still use the scripts under `src/rag/cli/`, `benchmarks/`, and `musicgen/` as documented in `docs/COMMANDS_MANIFEST.md`.

## Command-line entry points

After you run `uv sync` the project installs console scripts into `.venv/bin`:

- `rag-cli` – reranks retrieved chunks via `QwenReranker` and asks `MLXModelEngine` for the answer.
- `flux-cli` – thin wrapper around `rag.cli.flux_txt2image`/MLX Flux pipeline.
- `bench-cli` – dispatches the Flux benchmark runner or prompt evaluation workflow.

Example usage:

```bash
uv sync

# pure help (does not instantiate MLX)
uv run rag-cli --help

# Flux smoke test (touches MLX/Metal)
uv run flux-cli --prompt "lab smoke test" --steps 1 --image-size 256

# Benchmark CLI help and dispatcher
uv run bench-cli flux --help
```

The scripts are wired through `[project.scripts]` and the shim in `src/rag/cli/entrypoints.py`, so `uv run rag-cli` works even though the modules live under `apps/`.

## Contributing

We welcome contributions to `mlx-RAG`! Please see our [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Documentation

For comprehensive documentation, including architecture, development guidelines, and project sitemap, please visit the [`docs/` directory](docs/README.md).

# mlx-RAG

This repository is a monorepo for experiments and applications built on top of MLX-based retrieval-augmented generation (RAG) on Apple silicon.

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

Once set up, you can run various RAG components and tools. For example:

*   **Interactive RAG CLI:**
    ```bash
    uv run python -m rag.cli.interactive_rag
    ```

*   **Generate Music (with Musicgen):**
    ```bash
    uv run python -m rag.cli.generate_music --prompt "a short test melody" --duration 5
    ```

For more detailed usage examples and available commands, please refer to the `docs/README.md` and the `src/rag/cli/` directory.

## Contributing

We welcome contributions to `mlx-RAG`! Please see our [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Documentation

For comprehensive documentation, including architecture, development guidelines, and project sitemap, please visit the [`docs/` directory](docs/README.md).
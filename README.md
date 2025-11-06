# mlx-rag-lab

This repository is a monorepo for experiments and applications built on top of MLX-based retrieval-augmented generation (RAG) on Apple silicon.

The core Python RAG pipeline lives under `src/` and is responsible for:
- Ingesting documents into vector databases
- Running retrieval and query workflows
- Integrating with local MLX models for inference

Additional directories such as `apps/`, `Libraries/`, and `Tools/` contain example apps, Swift libraries, and utilities that build on the MLX ecosystem.

For detailed documentation, setup instructions, and usage examples, please refer to [`docs/README.md`](docs/README.md).

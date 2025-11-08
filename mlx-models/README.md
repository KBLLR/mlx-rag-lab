# MLX Models

This directory (`mlx-models/`) is used to store locally cached MLX model weights. These models are typically downloaded from Hugging Face and are essential for the functionality of various MLX-RAG components.

**Important:** This directory is configured in `.gitignore` to prevent accidental commits of large model files to the repository.

## Currently Used Models

*   **Musicgen Small:** `facebook/musicgen-small`
*   **Encodec 32kHz Float32:** `mlx-community/encodec-32khz-float32`

## Download Instructions

To download the necessary Musicgen and Encodec model weights, run the following CLI command from the project root:

```bash
uv run python -m rag.cli.download_musicgen_weights
```

This script will automatically download the models to this `mlx-models/` directory. Ensure you have an active `uv` environment and `huggingface_hub` installed.
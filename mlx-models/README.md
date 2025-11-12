# MLX Models

This directory (`mlx-models/`) is used to store locally cached MLX model weights. These models are typically downloaded from Hugging Face and are essential for the functionality of various MLX-RAG components.

**Important:** This directory is configured in `.gitignore` to prevent accidental commits of large model files to the repository.

## Metadata manifests

Each model now carries a lightweight metadata manifest under `mlx-models/manifests/<model>.manifest.json`. Use `scripts/model_manifest.py` to (re)generate these files after downloading or modifying weights:

```bash
# Refresh manifests for the Flux models without scanning large weight files
python scripts/model_manifest.py sync --models flux-schnell flux-dev --fast

# Show a quick summary table
python scripts/model_manifest.py show
```

The manifests capture provenance (source repo, quantization, LoRA fusion state) plus optional disk-usage stats so downstream tooling (e.g., cache cleanup) can make decisions without poking at large directories.

Pair manifests with the cleanup helper to prune stale weights or tidy the Hugging Face cache:

```bash
# Preview candidates filtered by tag/quantization (no deletions)
python scripts/clean_models.py preview --tags flux --quantization 4bit

# Forward to huggingface-cli for cache hygiene (respects $HF_HOME)
python scripts/clean_models.py hf --scan
```

## Currently Used Models

*   **Flux Schnell & Dev:** `black-forest-labs/FLUX.1-schnell`, `black-forest-labs/FLUX.1-dev`
*   **Flux Schnell (4-bit Quantized):** `mzbac/flux1.schnell.4bit.mlx`
*   **Musicgen Small:** `facebook/musicgen-small`
*   **Encodec 32kHz Float32:** `mlx-community/encodec-32khz-float32`
*   **Phi-3 Mini 4k UnsLoTh 4-bit:** `mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit`

## Download Instructions

To download the necessary models, use the `download_flux_models.py` script. For example:

```bash
# Download all models (default and quantized)
uv run python src/rag/cli/download_flux_models.py --model all

# Download only the 4-bit quantized schnell model
uv run python src/rag/cli/download_flux_models.py --model schnell --quantization 4bit
```

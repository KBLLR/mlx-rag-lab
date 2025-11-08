# Musicgen Module Usage Guide

This document provides instructions on setting up and using the Musicgen module within the MLX-RAG monorepo.

## 1. Model Weight Acquisition

To use the Musicgen module, you need to acquire the pre-trained MLX-compatible Musicgen model weights. While a direct download script is not yet implemented in this monorepo, the expected process (based on `mlx-examples`):

1.  **Download from Hugging Face:** Obtain the model weights (e.g., `facebook/musicgen-medium`) from Hugging Face. The `mlx-examples` repository typically provides a script or instructions for this.
2.  **Placement:** Place the downloaded model files (e.g., `model.safetensors`, `config.json`, `tokenizer.json`) into the `./models/mlx-models/musicgen-medium/` directory (or a similar structure following the `mlx-models/` convention).

## 2. Command-Line Interface (CLI) Usage

The Musicgen module provides a command-line interface for easy music generation.

### `generate_music.py`

This script allows you to generate music from a text prompt.

**Usage:**

```bash
uv run python -m rag.cli.generate_music --prompt "a calming piano melody" --duration 15 --output_dir "./var/music_output"
```

**Arguments:**

*   `--prompt` (str, required): The text description of the music to generate.
*   `--duration` (int, optional): The desired duration of the generated music in seconds. Default is `10`.
*   `--output_dir` (str, optional): The directory where the generated WAV file will be saved. Default is `./var/music_output`.

**Example:**

```bash
uv run python -m rag.cli.generate_music --prompt "upbeat electronic dance music" --duration 20
```

This will generate a 20-second electronic dance music track and save it to `./var/music_output/musicgen_upbeat_electronic_dance_music_20s.wav`.

## 3. Programmatic Usage (MusicgenAdapter)

For programmatic integration, you can use the `MusicgenAdapter` class:

```python
from libs.musicgen_core import MusicgenAdapter

# Initialize the adapter (model_path can be specified if different from default)
adapter = MusicgenAdapter(model_path="./models/mlx-models/musicgen-small")

# Generate music
text_prompt = "a serene orchestral piece"
duration = 30
output_filepath = adapter.generate_music(text_prompt, duration)

print(f"Generated music saved to: {output_filepath}")
```

## 4. Important Considerations

*   **Hardware:** Generating music with medium-sized Musicgen models (e.g., 1.5B parameters) typically requires a GPU with at least 16 GB of memory.
*   **Output:** Generated audio files are saved in WAV format.
*   **Dependencies:** Ensure your `uv` environment has `mlx` and any other necessary audio processing libraries installed (as specified by the `mlx-examples/musicgen` requirements).

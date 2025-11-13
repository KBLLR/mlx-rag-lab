# SITEMAP — mlx-RAG Voice App Source Overview

_Last generated: 2025-11-06_

This sitemap provides a **human-friendly** overview of the expected structure for the `mlx-RAG` Voice App, highlighting key components for MLX-based voice interaction.

## Top-Level Directories (Voice App Specific)

*   `/apps/voice_app` — Main directory for the Gradio-based voice application.
    *   `app.py` — The Gradio interface script.
    *   `requirements.txt` — Voice app specific Python dependencies (e.g., `gradio`, `librosa`, `soundfile`).
    *   `assets/` — Any UI assets, example audio files, or static content for the Gradio app.

*   `/src/libs/mlx_core` — Extended with MLX-compatible voice model engines.
    *   `mlx_llasa_engine.py` — Placeholder for `MLXLlasaEngine` (MLX-native Llasa-3B integration).
    *   `mlx_xcodec2_engine.py` — Placeholder for `MLXXCodec2Engine` (MLX-native XCodec2 integration).

*   `/models/mlx-models` — Expected location for MLX-converted Llasa-3B and XCodec2 model weights.

## Developer Notes

*   The primary challenge is converting `torch`-based Llasa-3B and XCodec2 models to MLX, or finding MLX-native equivalents.
*   All voice-related model weights and large audio assets should be ignored by Git and managed locally.
*   Refer to `docs/voice-app/tasks.md` for detailed action items and `docs/voice-app/AUDIT-log.md` for the current status and challenges.

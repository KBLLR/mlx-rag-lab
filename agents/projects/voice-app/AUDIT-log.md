# mlx-RAG Voice App — AUDIT Log

**Date:** 2025-11-06
**LLM Auditor:** Gemini CLI Agent
**Project:** mlx-RAG Voice App — Good State Checklist
**Author:** David Caballero
**Tags:** audit, checklist, readiness, project-state, mlx, voice, tts, stt, llasa, xcodec2

---

## Good State — Definition

The `mlx-RAG` Voice App project is in a **good state** when its foundational components for voice interaction are defined, and the path towards MLX-purist implementation is clear, adhering to the project's core philosophy.

### Criteria

1.  **MLX-Purism Adherence**: All core voice models (STT, TTS, Codec) are either MLX-native or have a clear, documented conversion path to MLX.
2.  **Model Integration**: Placeholder MLX-compatible engines (`MLXLlasaEngine`, `MLXXCodec2Engine`) are defined within `src/libs/mlx_core/`.
3.  **Interface Definition**: A placeholder Gradio application (`apps/voice_app/`) is structured to integrate with the MLX voice engines.
4.  **Documentation**: Setup, API, and operator notes for voice integration are current and reflect the project's MLX-first approach.
5.  **Dependencies**: Voice-specific dependencies are identified, and their MLX compatibility is assessed.
6.  **Version Control**: All voice-related code and documentation are correctly tracked, with non-MLX dependencies and large model files excluded via `.gitignore`.
7.  **Stakeholders**: Project owners and contributors are aware of the current state, MLX conversion challenges, and next milestones for voice integration.

---

## Actions Taken to Reach Good State (Session Log)

This section details the initial actions and assessments performed for the `mlx-RAG` Voice App project:

1.  **Project Scaffolding:**
    *   `docs/voice-app/` directory created by duplicating `docs/templates/project-template`.
    *   Initial `AUDIT-log.md`, `SITEMAP.md`, and `tasks.md` created for voice integration.

2.  **Initial Model Assessment (Llasa-3B & XCodec2):**
    *   User provided Gradio application code demonstrating `HKUSTAudio/Llasa-3B` (for TTS/voice cloning) and `HKUSTAudio/xcodec2` (for speech tokenization/decoding).
    *   **Challenge Identified:** The provided code relies heavily on `torch` for both Llasa-3B and XCodec2. This directly conflicts with the `mlx-RAG` project's strict MLX-purist mandate.
    *   **Decision:** Direct implementation of the `torch`-based Gradio app is deferred. The immediate focus shifts to documenting the MLX conversion challenge and creating MLX-compatible placeholders.

3.  **Placeholder MLX Voice Engines (Planned):**
    *   **Plan:** Create `src/libs/mlx_core/mlx_llasa_engine.py` for an `MLXLlasaEngine` (to handle MLX-compatible Llasa-3B).
    *   **Plan:** Create `src/libs/mlx_core/mlx_xcodec2_engine.py` for an `MLXXCodec2Engine` (to handle MLX-compatible XCodec2).

4.  **Placeholder Voice Gradio Application (Planned):**
    *   **Plan:** Create `apps/voice_app/app.py` as a placeholder Gradio interface that would utilize the MLX voice engines once they are implemented.

---

## Agent Note

This `AUDIT-log.md` outlines the initial setup and critical challenge for the `mlx-RAG` Voice App: the need to convert or find MLX-native versions of Llasa-3B and XCodec2. Future development will focus on addressing this MLX compatibility gap. Refer to `docs/voice-app/tasks.md` for detailed action items.

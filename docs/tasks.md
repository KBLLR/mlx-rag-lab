# Task Ledger for mlx-RAG

Track all work for the `mlx-RAG` project here. Keep the table **sorted by priority** (top = highest).

## Backlog
| ID    | Title                                            | Description                                                   | Priority | Owner | Notes                                                  |
|-------|--------------------------------------------------|---------------------------------------------------------------|----------|-------|--------------------------------------------------------|
| RAG-001 | Implement AudioSTTManager                        | Integrate MLX Whisper for speech-to-text functionality.       | High     |       |                                                        |
| HYG-001 | Create Repo Hygiene Project Template             | Duplicate project template for best practices for public repos. | High     |       | Includes License, README, CONTRIBUTING, CODEOWNERS, SECURITY, CHANGELOG, GITIGNORE, CI/CD, DOCS, LICENSING, CODESTYLE, TESTING, SECRETS, DATA, LOCALDEV. |
| RAG-002 | Implement VoiceOutputManager                     | Integrate MLX Llasa for text-to-speech/speech-to-speech.      | High     |       | Requires research on Llasa API.                        |
| RAG-003 | Create RAG Orchestrator                          | Develop a module to coordinate STT, VDB query, and LLM gen.   | High     |       |                                                        |
| RAG-004 | Enhance User Experience for Interactive CLI      | Improve input parsing, error messages, and output formatting. | Medium   |       | Consider rich library for better terminal experience.  |
| RAG-005 | Implement Hybrid Retrieval Strategy              | Combine vector search with keyword-based search.              | Medium   |       | Requires changes in `VectorDB.query`.                  |
| RAG-006 | Improve JSON Output Grounding & Citations        | Ensure LLM strictly adheres to JSON format and accurate citing. | Medium   |       | May require prompt engineering and/or `outlines` integration. |
| RAG-007 | Integrate Vision Models (mlx-vlm)                | Add support for multi-modal queries with image inputs.        | Low      |       | Requires `mlx-vlm` installation and `MLXModelEngine` updates. |
| RAG-008 | Implement Speculative Decoding (optional)        | Integrate a draft model for faster generation.                | Low      |       | Requires a working draft model and `mlx-lm` support.   |
| MG-009  | Add property & API tests for EncodecModel        | Test EncodecModel.from_pretrained, properties, and round-trip encode/decode. | High     |       |                                                        |
| MG-010  | Add stricter MusicgenAdapter tests               | Extend tests for duration, prompts, and invalid inputs.       | High     |       |                                                        |
| MG-011  | Add regression test for Encodec drift            | Ensure EncodecModel.decode signatures match expected contract. | Medium   |       |                                                        |
| MG-012  | Document Musicgen duration semantics             | Explicitly document 50 steps/sec rule and provide examples.   | Medium   |       |                                                        |
| MG-013  | Create Musicgen CLI / script entrypoint          | Develop a CLI for MusicgenAdapter with various arguments.     | Medium   |       |                                                        |
| MG-014  | Expose Musicgen model choices via config         | Implement config/env-based selection for model sizes.         | Low      |       | Optional: add benchmark script.                        |
| MG-015  | Track MLX upstream for stereo & melody support   | Monitor MLX for stereo/melody variants and plan integration.  | Low      |       |                                                        |
| MG-016  | Define Musicgen model caching & download strategy| Document model storage, check/download utility.               | Low      |       |                                                        |
| MG-017  | Define RAG / system integration hooks            | Create AudioGenerator interface for MusicgenAdapter.          | Low      |       |                                                        |
| MG-018  | Define Musicgen Configuration Schema             | Create Python dataclass/Pydantic model for Musicgen config (model, generation, prompt). | High     |       |                                                        |
| MG-019  | Implement Musicgen Preset Loading                | Develop logic to load and merge default, style, role, and quality presets. | High     |       |                                                        |
| MG-020  | Refactor MusicgenAdapter for Config              | Update MusicgenAdapter to accept and utilize the new configuration object. | High     |       |                                                        |
| MG-021  | Implement Musicgen CLI Entrypoint                | Create a CLI command (e.g., `rag musicgen generate`) using the adapter and config. | Medium   |       |                                                        |
| MG-022  | Integrate Musicgen into RAG Output Flow (Basic)  | Develop a basic flow for RAG answer to trigger Musicgen background track. | Medium   |       |                                                        |
| MG-023  | Implement Loudness Normalization                 | Add optional loudness normalization step in MusicgenAdapter or utils.py. | Low      |       |                                                        |
| MG-024  | Document Musicgen Configuration & Presets        | Create detailed documentation for Musicgen config schema and presets. | Low      |       |                                                        |
| MG-025  | Explore Two-Step CFG (Stub)                      | Add placeholder or initial investigation for `two_step_cfg`.  | Low      |       |                                                        |
| MG-026  | Implement Prompt Reflection Logging              | Log Musicgen generation details for future RAG context.       | Low      |       |                                                        |
| MG-027  | Design Music Catalog Metadata Schema             | Define schema for storing generated tracks with structured metadata. | Low      |       |                                                        |

## In Progress
| ID | Title | Started (YYYY-MM-DD) | Owner | Notes |
|----|-------|----------------------|-------|-------|

## Review / QA
| ID | Title | PR / Branch | Reviewer | Notes |
|----|-------|--------------|----------|-------|

## Done
| ID    | Title                                            | Completed (YYYY-MM-DD) | Outcome |
|-------|--------------------------------------------------|------------------------|---------|
| RAG-013 | Implement Cross-Encoder Re-ranking               | 2025-11-07             | Implemented Qwen2-based reranker using mlx_lm. |
| MG-008  | Integrate and activate Musicgen module           | 2025-11-08             | Successfully integrated MLX Musicgen for text-to-music generation, resolving attribute and duration issues. |
| HYG-001 | Create Repo Hygiene Project Template             | 2025-11-08             | Implemented best practices for public repository hygiene, including licensing, documentation, code style, and CI/CD. |
> Add/remove columns if needed, but keep the section order (Backlog → In Progress → Review/QA → Done) so other agents/tools can parse it.

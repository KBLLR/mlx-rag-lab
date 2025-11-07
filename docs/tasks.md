# Task Ledger for mlx-RAG

Track all work for the `mlx-RAG` project here. Keep the table **sorted by priority** (top = highest).

## Backlog
| ID    | Title                                            | Description                                                   | Priority | Owner | Notes                                                  |
|-------|--------------------------------------------------|---------------------------------------------------------------|----------|-------|--------------------------------------------------------|
| RAG-001 | Implement AudioSTTManager                        | Integrate MLX Whisper for speech-to-text functionality.       | High     |       |                                                        |
| RAG-002 | Implement VoiceOutputManager                     | Integrate MLX Llasa for text-to-speech/speech-to-speech.      | High     |       | Requires research on Llasa API.                        |
| RAG-003 | Create RAG Orchestrator                          | Develop a module to coordinate STT, VDB query, and LLM gen.   | High     |       |                                                        |
| RAG-004 | Enhance User Experience for Interactive CLI      | Improve input parsing, error messages, and output formatting. | Medium   |       | Consider rich library for better terminal experience.  |
| RAG-005 | Implement Hybrid Retrieval Strategy              | Combine vector search with keyword-based search.              | Medium   |       | Requires changes in `VectorDB.query`.                  |
| RAG-006 | Improve JSON Output Grounding & Citations        | Ensure LLM strictly adheres to JSON format and accurate citing. | Medium   |       | May require prompt engineering and/or `outlines` integration. |
| RAG-007 | Integrate Vision Models (mlx-vlm)                | Add support for multi-modal queries with image inputs.        | Low      |       | Requires `mlx-vlm` installation and `MLXModelEngine` updates. |
| RAG-008 | Implement Speculative Decoding (optional)        | Integrate a draft model for faster generation.                | Low      |       | Requires a working draft model and `mlx-lm` support.   |

## In Progress
| ID | Title | Started (YYYY-MM-DD) | Owner | Notes |
|----|-------|----------------------|-------|-------|

## Review / QA
| ID | Title | PR / Branch | Reviewer | Notes |
|----|-------|--------------|----------|-------|

## Done
| ID | Title | Completed (YYYY-MM-DD) | Outcome |
|----|-------|------------------------|---------|

> Add/remove columns if needed, but keep the section order (Backlog → In Progress → Review/QA → Done) so other agents/tools can parse it.

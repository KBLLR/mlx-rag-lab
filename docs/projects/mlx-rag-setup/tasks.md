# Task Ledger for mlx-RAG

Track all work for the `mlx-RAG` project here. Keep the table **sorted by priority** (top = highest).

**Note**: The `Research Notes` field is mandatory for all new tasks. Refer to `DEVELOPMENT_GUIDELINES.md` for details.

## Backlog
| ID    | Title                                            | Description                                                   | Priority | Owner | Research Notes | Notes                                                  |
|-------|--------------------------------------------------|---------------------------------------------------------------|----------|-------|----------------|--------------------------------------------------------|
| RAG-013 | Implement citations and source metadata          | Persist chunk-level source metadata in the index and surface citations in answers once reranking is in place. | High     | TBD   |                | Ensures answers can cite origins even before broader UX polish. |
| RAG-015 | Replace legacy CrossEncoder in interactive_rag   | Remove references to the missing CrossEncoder/mlx_compat modules and wire `interactive_rag` to the MLX LM reranker so reranking works end-to-end. | High     | TBD   |                | Blocks reliable demos until reranking path is fixed.   |
| RAG-016 | Define RAG v0.1 smoke scenario                   | Create a tiny demo corpus and a documented workflow (create_vdb + interactive_rag) that reliably runs on a single Apple Silicon machine with MLX. | High     | TBD   |                | Establishes the acceptance bar for “RAG v0.1”.         |
| RAG-017 | Add minimal RAG unit tests                       | Add tests for VectorDB save/load and basic ranking that avoid downloads/Metal so they can run in macOS CI. | High     | TBD   |                | Provides a sanity net without heavy MLX requirements.  |
| RAG-011 | Create RAG Pipeline Benchmarking Script          | Develop a script to measure retrieval accuracy and latency under varying load conditions. | High     | TBD   |                | Use a small ground-truth dataset for accuracy testing. |
| RAG-009 | Improve Document Parsing and Chunking            | Explore advanced strategies for PDF parsing and text chunking to enhance retrieval quality. | High     | TBD   |                | Investigate libraries beyond basic PDF reading.        |
| RAG-005 | Implement Hybrid Retrieval Strategy              | Combine vector search with keyword-based search.              | Medium   | TBD   |                | Requires changes in `VectorDB.query`.                  |
| RAG-006 | Improve JSON Output Grounding & Citations        | Ensure LLM strictly adheres to JSON format and accurate citing. | Medium   | TBD   |                | May require prompt engineering and/or `outlines` integration. |
| RAG-010 | Implement Automated Document/VDB Quality Checks  | Develop automated tests to validate the quality of ingested documents and the vector database. | Low      | TBD   |                | Ensure data integrity and retrieval effectiveness.     |
| RAG-012 | Add Document Summaries to `list-docs`            | Enhance the `list-docs` command to show a brief, AI-generated summary for each document. | Medium   | TBD   |                | This would likely involve a separate LLM call per document during ingestion. |
| RAG-014 | Define native MLX reranker interface             | Introduce a small reranker interface and implement an MLX LM-based reranker (e.g., Qwen or mxbai) as the default backend. | Medium   | TBD   |                | Replaces the placeholder cross-encoder with an MLX-native path. |

## In Progress
| ID | Title | Started (YYYY-MM-DD) | Owner | Notes |
|----|-------|----------------------|-------|-------|

## Review / QA
| ID | Title | PR / Branch | Reviewer | Notes |
|----|-------|--------------|----------|-------|

## Done
| ID    | Title                                            | Completed (YYYY-MM-DD) | Outcome                                                                                                   |
|-------|--------------------------------------------------|------------------------|-----------------------------------------------------------------------------------------------------------|
| RAG-013 | Implement Re-ranking and Source Citations        | 2025-11-07             | Landed a placeholder cross-encoder reranker plus basic per-chunk source tracking; current RAG-013 backlog item supersedes this with MLX reranker + richer citation support. |
| RAG-004 | Enhance User Experience for Interactive CLI      | 2025-11-07             | Refactored CLI with Typer and Rich; implemented streaming generation for a responsive user experience. |

# Task Ledger for mlx-RAG

Track all work for the `mlx-RAG` project here. Keep the table **sorted by priority** (top = highest).

**Note**: The `Research Notes` field is mandatory for all new tasks. Refer to `DEVELOPMENT_GUIDELINES.md` for details.

## Backlog
| ID    | Title                                            | Description                                                   | Priority | Owner | Research Notes | Notes                                                  |
|-------|--------------------------------------------------|---------------------------------------------------------------|----------|-------|----------------|--------------------------------------------------------|
| RAG-013 | Implement Re-ranking and Source Citations        | Add a cross-encoder re-ranking step to improve retrieval accuracy and modify the VDB to track and cite the source document for each chunk. | High     |       |                | This will address issues with ambiguous questions and incorrect sourcing. |
| RAG-011 | Create RAG Pipeline Benchmarking Script          | Develop a script to measure retrieval accuracy and latency under varying load conditions. | High     |       |                | Use a small ground-truth dataset for accuracy testing. |
| RAG-009 | Improve Document Parsing and Chunking            | Explore advanced strategies for PDF parsing and text chunking to enhance retrieval quality. | High     |       |                | Investigate libraries beyond basic PDF reading.        |
| RAG-005 | Implement Hybrid Retrieval Strategy              | Combine vector search with keyword-based search.              | Medium   |       |                | Requires changes in `VectorDB.query`.                  |
| RAG-006 | Improve JSON Output Grounding & Citations        | Ensure LLM strictly adheres to JSON format and accurate citing. | Medium   |       |                | May require prompt engineering and/or `outlines` integration. |
| RAG-010 | Implement Automated Document/VDB Quality Checks  | Develop automated tests to validate the quality of ingested documents and the vector database. | Low      |       |                | Ensure data integrity and retrieval effectiveness.     |
| RAG-012 | Add Document Summaries to `list-docs`            | Enhance the `list-docs` command to show a brief, AI-generated summary for each document. | Medium   |       |                | This would likely involve a separate LLM call per document during ingestion. |
| RAG-014 | Implement Native MLX Cross-Encoder               | Replace the placeholder re-ranking logic with a functional, native MLX cross-encoder. | Medium   |       |                | This will involve adapting a BERT model from mlx-examples or fine-tuning. |

## In Progress
| ID | Title | Started (YYYY-MM-DD) | Owner | Notes |
|----|-------|----------------------|-------|-------|

## Review / QA
| ID | Title | PR / Branch | Reviewer | Notes |
|----|-------|--------------|----------|-------|

## Done
| ID    | Title                                            | Completed (YYYY-MM-DD) | Outcome                                                                                                   |
|-------|--------------------------------------------------|------------------------|-----------------------------------------------------------------------------------------------------------|
| RAG-013 | Implement Re-ranking and Source Citations        | 2025-11-07             | Implemented accurate source tracking per chunk and integrated a (placeholder) cross-encoder re-ranking step. |
| RAG-004 | Enhance User Experience for Interactive CLI      | 2025-11-07             | Refactored CLI with Typer and Rich; implemented streaming generation for a responsive user experience. |
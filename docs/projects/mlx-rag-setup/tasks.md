# Task Ledger for mlx-RAG

Track all work for the `mlx-RAG` project here. Keep the table **sorted by priority** (top = highest).

## Backlog
| ID    | Title                                            | Description                                                   | Priority | Owner | Notes                                                  |
|-------|--------------------------------------------------|---------------------------------------------------------------|----------|-------|--------------------------------------------------------|
| RAG-004 | Enhance User Experience for Interactive CLI      | Improve input parsing, error messages, and output formatting. | High     |       | Consider rich library for better terminal experience; explore `mlx-lm`'s `stream_generate` for reduced latency. |
| RAG-009 | Improve Document Parsing and Chunking            | Explore advanced strategies for PDF parsing and text chunking to enhance retrieval quality. | High     |       | Investigate libraries beyond basic PDF reading.        |
| RAG-005 | Implement Hybrid Retrieval Strategy              | Combine vector search with keyword-based search.              | Medium   |       | Requires changes in `VectorDB.query`.                  |
| RAG-006 | Improve JSON Output Grounding & Citations        | Ensure LLM strictly adheres to JSON format and accurate citing. | Medium   |       | May require prompt engineering and/or `outlines` integration. |
| RAG-010 | Implement Automated Document/VDB Quality Checks  | Develop automated tests to validate the quality of ingested documents and the vector database. | Low      |       | Ensure data integrity and retrieval effectiveness.     |

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
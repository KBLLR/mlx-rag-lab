# Task Ledger for MLX Data Pipeline

Track all work for the `MLX Data Pipeline` project here. Keep the table **sorted by priority** (top = highest).

**Note**: The `Research Notes` field is mandatory for all new tasks. Refer to `DEVELOPMENT_GUIDELINES.md` for details.

## Backlog
| ID    | Title                                            | Description                                                   | Priority | Owner | Research Notes | Notes                                                  |
|-------|--------------------------------------------------|---------------------------------------------------------------|----------|-------|----------------|--------------------------------------------------------|
| MDP-001 | Define Generic Data Schemas                      | Define flexible data schemas (e.g., for documents, training samples) using Pydantic to ensure data quality and consistency. | High     |       |                | Schemas should be extensible for future data types.    |
| MDP-002 | Implement Modular Data Ingestion Framework       | Develop a modular framework for ingesting data from various sources (PDFs, JSONL, custom formats). | High     |       |                | Leverage `unstructured[pdf]` for PDFs; ensure extensibility. |
| MDP-003 | Integrate `mlx.data` for Efficient Processing    | Implement data loading and transformation pipelines using `mlx.data`, focusing on `prefetch`, `batch`, and `key_transform`. | High     |       |                | Optimize for throughput and memory efficiency.         |
| MDP-004 | Build and Update Vector Database (VDB)           | Develop modules for building and incrementally updating the `VectorDB` with embeddings and metadata from processed data. | High     |       |                | Ensure efficient embedding generation with MLX models. |
| MDP-005 | Implement and Test Retrieval Strategies          | Implement and test various retrieval strategies, including vector search and hybrid search, evaluating relevance and performance. | Medium   |       |                | Integrate with existing `VectorDB` query mechanisms.   |
| MDP-006 | Establish Performance Benchmarks                 | Define and implement benchmarks for measuring data ingestion speed, VDB building time, retrieval latency, and memory usage. | Medium   |       |                | Use these benchmarks for optimization efforts.         |
| MDP-007 | Implement Data Quality and Validation Checks     | Integrate automated data quality and validation checks at various stages of the pipeline. | Medium   |       |                | Prevent bad data from impacting downstream models.     |
| MDP-008 | Develop Data Versioning Strategy                 | Explore and implement a strategy for versioning data and data pipelines to ensure reproducibility. | Low      |       |                | Consider DVC or similar tools if appropriate.          |
| MDP-009 | Prototype `mlx.data` Pipelines for Document Banks | Build a reference pipeline that loads per-bank documents via `mlx.data`, chunks them, and emits samples ready for embedding. | High | Codex | Reviewed MLX docs (`mlx.data` samples-as-dicts paradigm) and project README outlining need for streaming ingestion. | Feeds the new per-bank VDB workflow. |
| MDP-010 | Add Google Drive Connector Layer                 | Implement a document provider that syncs curated Drive folders into the ingestion pipeline. | Medium | Codex | Need Drive API creds, evaluate `pydrive2`, ensure outputs land in `var/source_docs/<bank>` before MLX ingestion. | Enables remote knowledge banks. |

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

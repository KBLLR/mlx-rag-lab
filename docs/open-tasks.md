# Consolidated Open Tasks (Generated 2025-11-16)

This document aggregates every backlog item currently defined under `docs/projects/*/tasks.md` while the repository is pinned to commit `4865e01`.
If a project lacks a `tasks.md` file (or still contains only placeholder content), it is called out separately.

## Projects With Active Backlogs

### mlx-rag-setup
| ID | Priority | Title | Description / Notes |
|----|----------|-------|----------------------|
| RAG-013 | High | Implement citations and source metadata | Persist chunk-level source metadata in the index and surface citations in answers once reranking is in place. |
| RAG-015 | High | Replace legacy CrossEncoder in interactive_rag | Remove references to the missing CrossEncoder/mlx_compat modules and wire `interactive_rag` to the MLX LM reranker so reranking works end-to-end. |
| RAG-016 | High | Define RAG v0.1 smoke scenario | Create a tiny demo corpus and a documented workflow (create_vdb + interactive_rag) that reliably runs on a single Apple Silicon machine with MLX. |
| RAG-017 | High | Add minimal RAG unit tests | Add tests for VectorDB save/load and basic ranking that avoid downloads/Metal so they can run in macOS CI. |
| RAG-011 | High | Create RAG Pipeline Benchmarking Script | Measure retrieval accuracy & latency with a ground-truth dataset. |
| RAG-009 | High | Improve Document Parsing and Chunking | Explore better PDF parsing/chunking strategies. |
| RAG-005 | Medium | Implement Hybrid Retrieval Strategy | Combine vector and keyword search inside `VectorDB.query`. |
| RAG-006 | Medium | Improve JSON Output Grounding & Citations | Harden JSON prompt/formatting so answers cite sources reliably. |
| RAG-012 | Medium | Add Document Summaries to `list-docs` | Show brief AI summaries for each ingested document. |
| RAG-010 | Low | Implement Automated Document/VDB Quality Checks | Add validation to ingestion + retrieval artifacts. |
| RAG-014 | Medium | Define native MLX reranker interface | Introduce a small reranker interface and implement an MLX LM-based reranker (e.g., Qwen or mxbai) as the default backend. |

RAG-013 through RAG-017 collectively define the “RAG v0.1” milestone: a citation-aware MLX reranking pipeline, an updated interactive CLI, a reproducible smoke scenario, and minimal tests. See `docs/projects/mlx-rag-setup/tasks.md` for full wording and status.

### mlx-data-pipeline
| ID | Priority | Title | Description / Notes |
|----|----------|-------|----------------------|
| MDP-001 | High | Define Generic Data Schemas | Use Pydantic schemas for documents/training samples. |
| MDP-002 | High | Implement Modular Data Ingestion Framework | Support multiple source formats with reusable modules. |
| MDP-003 | High | Integrate `mlx.data` for Efficient Processing | Build streaming pipelines using `shuffle`, `batch`, `prefetch`, etc. |
| MDP-004 | High | Build and Update Vector Database (VDB) | Support incremental updates with MLX embeddings + metadata. |
| MDP-009 | High | Define shared document schema between ingestion and VDB | Introduce a shared schema (Pydantic model or dataclass) for document chunks so ingestion and VectorDB share a single definition, enabling future `mlx.data` streaming pipelines. |
| MDP-005 | Medium | Implement and Test Retrieval Strategies | Evaluate vector + hybrid retrieval approaches. |
| MDP-006 | Medium | Establish Performance Benchmarks | Track ingestion, VDB build, and retrieval latency metrics. |
| MDP-007 | Medium | Implement Data Quality and Validation Checks | Guard against bad inputs throughout the pipeline. |
| MDP-008 | Low | Develop Data Versioning Strategy | Design reproducible data/version management (DVC or similar). |

### voice-app
| ID | Priority | Title | Description / Notes |
|----|----------|-------|----------------------|
| P-001 | Medium | Example task | Placeholder entry; project scope still undefined. |

### mlx-setup
_No open backlog items. Last recorded work (MLX-000 … MLX-008) is marked complete._

### rollback-reflection
| ID | Priority | Title | Description / Notes |
|----|----------|-------|----------------------|
| RRB-002 | Medium | Maintain `open-tasks.md` | Re-run this consolidation after any significant backlog change. |
| RRB-003 | Medium | Plan remediation sprint | Decide which regressions to fix first now that we’re on `4865e01`. |

## Projects Missing Task Ledgers
The following directories under `docs/projects/` do not contain a `tasks.md` file (or contain only metadata files). Consider adding one so future rollups stay complete:
- `app-starter/`
- `container-research/`
- `flux-benchmark/`
- `flux-setup/`
- `s3-integration/`
- `user-priorities/`

## Maintenance Notes
- Update this file whenever any project backlog changes (see RRB-002).
- If a project adds new task sections (In Progress, Review), feel free to mirror them here, but keep the focus on *open* work.
- Generated manually on 2025-11-16 by scanning `find docs/projects -name tasks.md`.

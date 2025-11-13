# Vision Pipeline Task Ledger

Track every task for the vision pipeline project. Keep the table sorted by priority (top = highest). Move items between sections as they progress.

## Backlog

| ID | Title | Description | Priority | Owner | Notes |
|----|-------|-------------|----------|-------|-------|
| VP-001 | Audit Phi-3-Vision-MLX code | Review existing code in `mlx-models/Phi-3-Vision-MLX/` to understand APIs | High | | Prerequisite for wrappers |
| VP-002 | Create phi3_vision_backend.py | Raw MLX model loading / forward pass wrapper | High | | Backend layer |
| VP-003 | Create phi3_vision_embedder.py | High-level embedding API for RAG with normalized I/O | High | | RAG integration layer |
| VP-004 | Refactor rag-cli to subcommands | Add `text`, `vision`, `multimodal` subcommands to existing CLI | High | | Architecture decision #1 |
| VP-005 | Create src/rag/vision/ module | New module for vision-specific RAG logic | High | | Module structure |
| VP-006 | Implement image input handling | Support local files, URLs → normalized local paths | High | | Phase 1 core feature |
| VP-007 | Create image_vdb.npz structure | Define schema and implement storage for image embeddings | High | | Architecture decision #2 |
| VP-008 | Implement vision ingestion | CLI command to ingest images and build image_vdb.npz | High | | `rag-cli vision --ingest` |
| VP-009 | Implement vision query | CLI command to query with text + optional image context | High | | `rag-cli vision --query` |
| VP-010 | Multimodal retrieval logic | Merge text + image search results with optional reranking | Medium | | Cross-modal search |
| VP-011 | Add multimodal mode | Hybrid mode querying both text_vdb and image_vdb | Medium | | `rag-cli multimodal` |
| VP-012 | Batch image processing | Process multiple images in single ingestion command | Medium | | Efficiency feature |
| VP-013 | Image URL download/cache | Download remote images to `var/images/cache/` | Medium | | Phase 1 feature |
| VP-014 | Format validation | Validate `.png`, `.jpg`, `.jpeg`, `.webp` support | Medium | | Input validation |
| VP-015 | Add vision to mlxlab CLI | Add vision pipeline option to main `mlxlab` menu | Low | | UX consistency |
| VP-016 | PDF→image ingestion | Extract PDF pages as images for vision ingestion | Low | | Phase 2 feature |
| VP-017 | Base64 image support | Support base64-encoded images (API/programmatic only) | Low | | Phase 2 feature |
| VP-018 | LoRA fine-tuning CLI | Interface for fine-tuning Phi-3-Vision on custom datasets | Low | | Phase 3 - advanced |
| VP-019 | Documentation | Add usage examples and command reference to docs | Medium | | User-facing docs |
| VP-020 | ASCII art header | Create colorful header for vision mode | Low | | Visual consistency |

## In Progress
| ID | Title | Started | Owner | Notes |
|----|-------|---------|-------|-------|

## Review / QA
| ID | Title | PR / Branch | Reviewer | Notes |
|----|-------|-------------|----------|-------|

## Done
| ID | Title | Completed | Outcome |
|----|-------|-----------|---------|

## Notes

### Architecture (from decisions)
- **Integration**: Subcommands in rag-cli (`text`, `vision`, `multimodal`), NOT separate binary
- **Storage**: Split indexes (`text_vdb.npz`, `image_vdb.npz`, `multimodal_meta.json`)
- **Model wrapper**: Thin local wrapper around Phi-3-Vision-MLX backend
- **Formats**: Phase 1: `.png`, `.jpg`, `.jpeg`, `.webp` + URLs

### Module Structure
```
src/rag/
  text/              # existing text RAG
  vision/            # new vision RAG module
    __init__.py
    embedder.py      # uses phi3_vision_embedder
    ingestion.py     # build image_vdb
    retrieval.py     # query image_vdb
  shared/            # configs, VectorDB helpers
  models/
    phi3_vision_backend.py   # raw model
    phi3_vision_embedder.py  # high-level API
```

### CLI Interface
```bash
# Ingest images
uv run rag-cli vision --ingest path/to/images/ https://example.com/fig.png

# Query with text only
uv run rag-cli vision --query "Show me charts about revenue"

# Query with image context
uv run rag-cli vision --query "Explain this" --query-image chart.png

# Multimodal (text + image indexes)
uv run rag-cli multimodal --query "Find similar documents"
```

### Dependencies
- Phi-3-Vision-MLX library (already in `mlx-models/Phi-3-Vision-MLX/`)
- MLX framework (~0.29.3)
- Pillow (already available)
- requests (for URL downloads)

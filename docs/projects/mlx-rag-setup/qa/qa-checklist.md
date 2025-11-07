# QA Checklist — mlx-RAG Setup

> Duplicate this file per QA run and attach to the session log / PR summary.

## Metadata
- **Build / Commit**: `<hash>`
- **Environment**: `<local / staging / prod>`
- **Tester**: `<name>`
- **Date**: `<YYYY-MM-DD>`

## Pre-flight
- [ ] `uv sync` completes without errors.
- [ ] All necessary MLX models are downloaded.
- [ ] Session log created (`docs/projects/mlx-rag-setup/sessions/`)

## Critical Paths

### 1. Dependency Installation
- [ ] `uv sync` successfully installs all dependencies.

### 2. Model Download
- [ ] `uv run python -m rag.cli.download_model --model-id mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit` successfully downloads the model.
- [ ] Downloaded model files are present in `mlx-models/`.

### 3. Vector Database Creation
- [ ] A sample PDF is placed in `var/source_docs/`.
- [ ] `uv run python -m rag.ingestion.create_vdb --pdf var/source_docs/sample.pdf --vdb models/indexes/vdb.npz` successfully creates the VDB.
- [ ] `models/indexes/vdb.npz` and `models/indexes/vdb.meta.json` are created.

### 4. Vector Database Query
- [ ] `uv run python -m rag.retrieval.query_vdb --question "What is MLX?" --vdb models/indexes/vdb.npz` returns a relevant response.

### 5. Interactive RAG CLI
- [ ] `uv run python -m rag.cli.interactive_rag` starts successfully.
- [ ] `ask <question>` command works as expected.
- [ ] `list_docs` command lists ingested documents.
- [ ] `rebuild_vdb` command successfully rebuilds the VDB.

## Regression / Smoke Notes
-

## Follow-up Issues
- [ ] Logged in `docs/projects/mlx-rag-setup/tasks.md` (IDs: …)

## Sign-off
- ✅ / ⚠️ / ❌  — *Tester signature*
# Launcher Planning Session — 2025-11-15

## Summary

- Reviewed existing `apps/rag_cli.py`, `apps/flux_cli.py`, `apps/bench_cli.py`, ingestion helpers, and the documented paths under `models/indexes/`, `outputs/flux/`, and `var/`. Confirmed that CLI entrypoints are runnable and that `uv sync` plus helper tests pass.
- Drafted the `launcher` project scaffold (`docs/projects/launcher/`) with README, tasks, and session notes so future agents can track the CLI-lab batch effort.
- Identified the need for a simple launcher (`apps/lab_cli.py`), path flags for ingestion/batch, and documentation updates (README, COMMANDS_MANIFEST, LAB_STATUS).

## Next Actions

1. Implement `apps/lab_cli.py` with `rag-batch`, `flux-batch`, `bench`, and `ingest` commands that accept the proposed path defaults.
2. Update `src/rag/ingestion/create_vdb.py` to expose `--input-dir`, `--pattern`, and `--output-index` flags so the launcher can call it programmatically.
3. Keep documenting the lab story (README + docs) and mark which flows are stable vs Metal-sensitive.

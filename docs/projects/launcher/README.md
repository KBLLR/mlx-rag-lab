# Launcher Project

This project tracks the “lab launcher” effort: a batch-friendly CLI that wires together the existing `rag-cli`, `flux-cli`, `bench-cli`, and ingestion helpers under a single entry point. The launcher keeps the repo CLI-first, exposes clear path defaults, and guides operators straight to the workflows that actually work on Metal macOS.

## Project Goals

1. Build a lightweight launcher (`apps/lab_cli.py`) that accepts modes such as `ingest`, `rag-batch`, `flux-batch`, and `bench`.
2. Standardize input/output paths (`var/source_docs/`, `models/indexes/`, `outputs/flux/`, `benchmarks/results/`, `var/music_output/`).
3. Document the lab status (stable vs. Metal-sensitive) and keep the tasks/hand-offs aligned.

## Resources

- CLI scaffolding lives under `apps/`.
- RAG ingestion helper: `src/rag/ingestion/create_vdb.py`.
- Flux generation: `apps/flux_cli.py`, `rag.cli.flux_txt2image`.
- Benchmarks: `benchmarks/flux_benchmark.py`, `benchmarks/results/`.
- Musicgen helpers: `musicgen/generate.py` and `docs/LAB_STATUS.md` for the Metal caveat.

## Next Steps

- Continue wiring path flags into the launcher (see `apps/lab_cli.py` once created).
- Keep `docs/LAB_STATUS.md`, `docs/COMMANDS_MANIFEST.md`, and `docs/HANDOFFS.md` in sync with the CLI behaviors.
- Add stub-friendly tests under `tests/cli/` and `tests/flux/`.

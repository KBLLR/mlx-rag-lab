# Handoff Log

## Project Snapshot
- **Goal**: Maintain a local-first MLX RAG lab that covers ingestion, retrieval, Flux benchmarking, and lightweight ML experiments (Musicgen, BytePhi, etc.).
- **Key entry points**:
  * `docs/README.md`, `docs/MLX-CORE.md`, `docs/DEVELOPMENT_GUIDELINES.md` — high-level architecture, workflow rules.
  * `docs/projects/*` — per-initiative folders (`flux-setup`, `mlx-data-pipeline`, `user-priorities`, etc.) containing tasks and sessions.
  * Recent additions: `src/rag/ingestion/create_vdb.py` (mlx.data ingestion), `src/rag/cli/rag_tui.py`, `benchmarks/flux/bench_flux.py`, `benchmarks/flux/prompts.py`.
- **Agent workflow (loop until compact)**:
  1. Read `docs/HANDOFFS.md` (this file) to understand the latest state.
  2. Greet the user, ask if there’s any context to resume or clarify.
  3. Review relevant project docs/tasks (`docs/projects/.../tasks.md`, sessions).
  4. Execute work with proper session logs (per project) and update tasks.
  5. Before completing your cycle, summarize in a new handoff entry (include alias/codename, summary, next steps).

## Entry: 2025-11-10 — "Lyric" (Agent codename: `FluxLearn-TUI`)

**Summary**
- Finished implementing the MLX-native ingestion path (`create_vdb.py` now requires `mlx-data` and exposes batch/prefetch knobs).
- Delivered Textual-based RAG TUI (`uv run python -m rag.cli.rag_tui --vdb-path models/indexes/vdb.npz`) and documented usage.
- Rebuilt the Flux benchmarking stack under `benchmarks/flux/` with prompt presets, LoRA/fuse support, and JSON metadata (`bench_flux.py` + `prompts.py`).

**Next Agent To-Do**
1. Add per-model metadata manifests (quantization, LoRA fusion info) inside `mlx-models/…` so we can audit/clean weights safely.
2. Provide a cleanup helper (e.g., `scripts/clean_models.py`) that leverages `hf cache rm/prune` guidance for Hugging Face caches.
3. Extend `src/rag/cli/flux_txt2image.py` to accept non-square `--image-size` (e.g., `512x768`) as the new runner already supports strings.

**Notes**
- All Flux benchmarks assume weights already exist locally; set `HF_HOME` if you want the HF cache elsewhere.
- Keep using `PYTHONPATH=src …` until we formalize packaging (`uv pip install -e .`).
- LoRA adapters live under `models-mlx/lora/`; fused outputs should go in separate subfolders to preserve full‑precision bases.

## Entry: 2025-11-11 — "Octave" (Agent codename: `ModelCustodian`)

**Summary**
- Added manifest + cleanup tooling so every Flux weight directory now has provenance metadata (`scripts/model_manifest.py`, `scripts/clean_models.py`, `mlx-models/manifests/*.json`).
- Documented the workflow inside `mlx-models/README.md` and logged repo-hygiene + flux-setup sessions/tasks for traceability.
- Extended `src/rag/cli/flux_txt2image.py` so operators can pass non-square `--image-size` values like `512x768`, matching the benchmark runner’s interface.
- Introduced a Typer-based launcher (`uv run python -m rag.cli.app_launcher`) that surfaces RAG TUI, Flux presets, and MusicGen commands via a single menu.
- Hardened RAG tooling: `rag.cli.rag_tui` now uses `argparse`, and global `rag` init sets `HF_HOME=/mlx-models/.hf-cache` plus disables HF Hub multiprocessing so downloads stay inside the repo and avoid macOS/Python 3.12 FD crashes.
- Spun up the `container-research` project (branch `apple-container`, committed) to track Apple’s new “Container” framework for native Docker-like workflows; tasks/logs reference The Register, Linuxiac, and `apple/container` GitHub releases.

**Next Agent To-Do**
1. Extend the manifest registry to other models (Musicgen, Phi-3, etc.) and wire in lightweight tests that mock MLX imports.
2. Teach `benchmarks/flux/prompts.py` / docs about typical portrait ratios (e.g., 3:4, 9:16) and add presets for them.
3. Explore a CI-safe shim for importing MLX helpers (so we can unit-test `parse_image_size_arg` without Metal) or split helpers into a dedicated module without heavy dependencies.

**Notes**
- `scripts/clean_models.py preview --compute-size` walks entire model directories—expect a short pause for large checkpoints.
- `python scripts/model_manifest.py sync --fast` only updates metadata; rerun without `--fast` to capture disk usage before cleanup.

## Entry: 2025-11-12 — "Echo" (Agent codename: `FluxCustodian`)

**Summary**
- Extended the registry so Phi-3 (unsloth instruct 4-bit) plus MusicGen Small and its Encodec dependency live in `docs/models/model_registry.json`, highlighted Phi-3 in `mlx-models/README.md`, and regenerated manifests with `scripts/model_manifest.py sync` for those assets.
- Added `tests/flux/test_flux_txt2image_helpers.py` alongside `tests/conftest.py` so helper logic can be exercised without touching MTX-heavy dependencies; pytest now passes.
- Shifted the repo to a CLI-focused lab: created `apps/rag_cli.py`, `apps/flux_cli.py`, and `apps/bench_cli.py`, wired them into `[project.scripts]`, archived `src/rag/cli/rag_tui.py` in `archive/tui/`, and refreshed docs/manifest/tasks to describe the new shape while keeping `HF_HUB_DISABLE_PROGRESS_BARS=1` baked into `rag.models.model.Model`.
- The old `ValueError: bad value(s) in fds_to_keep` path is now covered via the HF env var, but VectorDB still aborts with a Metal `NSRangeException` before that lock bug manifests unless the weights are pre-cached on a Metal-capable machine.

**Next Agent To-Do**
1. Verify the new CLI story (RS/CLI tasks) end-to-end: confirm `rag-cli`, `flux-cli`, and `bench-cli` run via `uv`/`rag-cli` entry points and update `docs/tasks.md` as needed when new commands are added.
2. Keep the HF Hub/manifest guidance (RH-003) current; remind operators that `HF_HUB_DISABLE_PROGRESS_BARS=1` is still set before downloads and link to `archive/tui/rag_tui.py` for historical context.
3. Track any future Metal/NSRange issues when building vector DBs—run the CLI on a GPU-backed Mac (or with pre-downloaded caches) before assuming the lock bug is resolved.

**Notes**
- `tests/conftest.py` now prepends `src`, so helper tests import `rag.cli.flux_txt2image` and stubbed `rag.models.flux` instead of pulling real MLX modules.
- The archived Textual `rag_tui` lives under `archive/tui/rag_tui.py`; day-to-day experimentation should stay within the new `apps/` CLIs.

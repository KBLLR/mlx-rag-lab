# Lab Status

This doc describes what works reliably today, what depends on a friendly Metal/MLX environment, and what is still experimental.

-## Stable / Working

- macOS + Python 3.12 CI installs dependencies via `uv sync` (the workflow now runs on `macos-15`).
- CLI entry points `rag-cli`, `flux-cli`, and `bench-cli` are wired via `[project.scripts]` and the shim in `src/rag/cli/entrypoints.py`; running `uv run rag-cli --help` works on macOS.
- Dependency / import sanity checks:
  - `uv sync` (Python 3.12)
  - `uv run python -m compileall src apps`
  - `PYTHONPATH=./src uv run pytest tests/flux/test_flux_txt2image_helpers.py`
- Model registry + manifest tooling (`scripts/model_manifest.py`, manifests under `mlx-models/manifests/`, cleanup helper) keeps ad-hoc weights documented.

## Working, but environment-sensitive

- Running `rag-cli` with real MLX models touches Metal (NSRangeException risk on some machines). Start with `--help` or stubbed inputs before letting long prompts load models.
- `flux-cli` still relies on the full Flux pipeline (Metal-heavy). Keep prompts small or run on a known-good Mac GPU.
- Any other MLX-backed RAG / VectorDB flows that instantiate the model engine will hit the same hardware sensitivities; the CLI path surfaces the issue rather than hiding it.

## WIP / Experimental

- Full end-to-end RAG with freshly downloaded MLX models and new Metal drivers (the NSRangeException remains the gating bug).
- Additional CLIs (MusicGen, voice, etc.) are conceptually in `apps/` but not yet fully coverage-tested; treat them as experimental unless their tests pass without Metal interactions.

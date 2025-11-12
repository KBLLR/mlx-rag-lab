# Task Ledger for mlx-RAG

Track every task for this experimental MLX lab. Keep sections grouped by focus area and prioritize rows within each table (top = highest).

## Repo shape
| ID | Title | Description | Priority | Owner | Notes |
|----|-------|-------------|----------|-------|-------|
| RS-01 | Create apps/ directory | Consolidate runtime CLIs under `apps/` and treat every entry point as a focused script. | High | | |
| RS-02 | Archive Textual/TUI code | Move `src/rag/cli/rag_tui.py` (and any UI-only modules) into `archive/tui/` so the working tree stays CLI-first. | High | | |
| RS-03 | Drop TUI-only dependencies | Remove `textual` from production deps and trim lockfiles so the lab stays lean. | Medium | | |
| RS-04 | Restore vanilla multiprocessing | Remove `multiprocessing.set_start_method("fork")` clusters that only existed for the TUI runner. | Medium | | |

## CLIs
| ID | Title | Description | Priority | Owner | Notes |
|----|-------|-------------|----------|-------|-------|
| CLI-01 | Implement apps/rag_cli.py | Build a REPL-style RAG CLI that loads `VectorDB`, reranks with `QwenReranker`, and generates answers via `MLXModelEngine`. | High | | |
| CLI-02 | Implement apps/flux_cli.py | Wrap `rag.cli.flux_txt2image` behind a lightweight CLI so prompt-to-image flows live under `apps/`. | High | | |
| CLI-03 | Implement apps/bench_cli.py | Dispatch existing `benchmarks.flux_benchmark` and `benchmarks.prompt_evaluation` runners from a single CLI. | Medium | | |
| CLI-04 | Wire CLI scripts | Add `[project.scripts]` entries for `rag-cli`, `flux-cli`, and `bench-cli` in `pyproject.toml`. | Medium | | |
| CLI-05 | (Optional) Add musicgen/voice CLIs | Expose MusicGen and Whisper demos once the basic CLIs stabilize. | Low | | |

## MLX / RAG core
| ID | Title | Description | Priority | Owner | Notes |
|----|-------|-------------|----------|-------|-------|
| CORE-01 | Keep src/rag UI-free | Ensure `src/rag` contains only ingestion, retrieval, and model wrappers—no Textual/Rich UI side effects. | High | | |
| CORE-02 | Prefer mlx-models/ + models/indexes/ | All loaders should default to local paths (`MLX_MODELS_DIR`, `models/indexes/`) before hitting HF Hub. | High | | |
| CORE-03 | Document HF_HUB_DISABLE_PROGRESS_BARS | Keep the HF env var guidance scoped to CLI entry points so downloads remain predictable. | Medium | | |

## Benchmarks & training
| ID | Title | Description | Priority | Owner | Notes |
|----|-------|-------------|----------|-------|-------|
| BENCH-01 | Document bench-cli usage | Explain how to run the benchmark dispatcher and where JSON/metric outputs land. | Medium | | |
| TRAIN-01 | Document LoRA training | Cover LoRA fine-tuning inputs/outputs under `lora/`. | Low | | |
| TRAIN-02 | Connect experiments → indexes | Describe how `experiments/` ingestion scripts feed `models/indexes/` artifacts. | Low | | |

## Docs
| ID | Title | Description | Priority | Owner | Notes |
|----|-------|-------------|----------|-------|-------|
| DOC-01 | Reframe docs/README.md | Declare the repo as a CLI-first MLX lab (rag-cli, flux-cli, bench-cli) with no active TUI. | High | | |
| DOC-02 | Note TUI removal in handoffs | Record the “TUI era” archive and CLI reset in `docs/HANDOFFS.md`. | High | | |
| DOC-03 | Sync docs/tasks.md | Keep this ledger in sync with the RS/CLI/CORE/BENCH/TRAIN tasks defined above. | High | | |

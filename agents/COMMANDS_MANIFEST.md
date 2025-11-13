# Command Manifest (Flux • MusicGen • RAG)

Central index of the high-signal commands used across the MLX-RAG lab. Entries are grouped per app so you can skim for benchmarking vs. generation scenarios without digging through individual READMEs. All commands assume you run them from the repo root with `uv` installed; prepend `PYTHONPATH=src` only if noted elsewhere.

> **Contributing:** When you add a new CLI or workflow, append the relevant command block under its app section so this manifest stays the single source of truth.

---

## Apps (CLIs)

| Scenario | Command | Notes |
| --- | --- | --- |
| **rag-cli question loop** | ```bash\nrag-cli --vdb-path models/indexes/vdb.npz --model-id mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit\n``` | Interactive loop that reranks the top chunks with `QwenReranker` before asking `MLXModelEngine`. |
| **flux-cli prompt run** | ```bash\nflux-cli --prompt "a sci-fi skyline" --steps 8 --image-size 512x512\n``` | Wraps `rag.cli.flux_txt2image` with a simpler interface plus output directory defaults. |
| **bench-cli dispatcher** | ```bash\nbench-cli flux```<br>```bash\nbench-cli prompt``` | Dispatches the Flux benchmark runner or the prompt evaluation workflow. |

### CLI entrypoints

| Command | Module | Notes |
| --- | --- | --- |
| `rag-cli` | `apps.rag_cli:main` | Entry point uses `rag.cli.entrypoints:rag_cli_main` to set `PYTHONPATH` before invoking the CLI. |
| `flux-cli` | `apps.flux_cli:main` | Wraps the Flux CLI via `rag.cli.entrypoints:flux_cli_main`. |
| `bench-cli` | `apps.bench_cli:main` | Dispatches bench runners via `rag.cli.entrypoints:bench_cli_main`. |

---

## Flux (image generation & benchmarking)

| Scenario | Command | Notes |
| --- | --- | --- |
| **Base generation (square)** | ```bash\nuv run python src/rag/cli/flux_txt2image.py \\\n  \"a cinematic photo of an astronaut riding a horse\" \\\n  --model schnell --steps 4 --n-images 1 --image-size 512 \\\n  --output outputs/flux/base\n``` | Uses the default schnell weights; outputs grids under `outputs/flux/base`. |
| **Portrait / rectangular render** | ```bash\nuv run python src/rag/cli/flux_txt2image.py \\\n  \"studio portrait of a person\" \\\n  --model dev --image-size 512x768 --steps 8 \\\n  --n-images 2 --output outputs/flux/portrait\n``` | `--image-size` accepts `WxH` strings (new CLI behavior). |
| **LoRA generation (no fuse)** | ```bash\nuv run python src/rag/cli/flux_txt2image.py \\\n  \"a photo of <sks> dog on the beach\" \\\n  --model dev --adapter models-mlx/lora/dragon-v1.safetensors \\\n  --prompt \"a photo of <sks> dog on the beach\" \\\n  --image-size 640 --steps 6\n``` | Keeps the adapter separate (no `--fuse-adapter`) so base weights remain untouched. |
| **LoRA fused run** | ```bash\nuv run python src/rag/cli/flux_txt2image.py \\\n  \"hyper-detailed dragon sculpture\" \\\n  --model dev --adapter models-mlx/lora/dragon-v1.safetensors \\\n  --fuse-adapter --no-t5-padding --image-size 768 --steps 10\n``` | Temporarily fuses the adapter for faster iteration; pair with manifests + cleanup script before/after. |
| **Benchmark – generic** | ```bash\nuv run python benchmarks/flux/bench_flux.py \\\n  --model both --steps 4 --repeats 3 --warmup 1 \\\n  --prompt-key astronaut_horse --image-size 512\n``` | Runs both schnell & dev; outputs latency/memory summary (optionally add `--json-out`). |
| **Benchmark – “Schnell Pic” preset** | ```bash\nuv run python benchmarks/flux/bench_flux.py \\\n  --model schnell --steps 4 --repeats 3 --warmup 1 \\\n  --prompt-key schnell_pic --image-size 512\n``` | Targets the fast schnell weights only. |
| **Benchmark – LoRA fuse stress** | ```bash\nuv run python benchmarks/flux/bench_flux.py \\\n  --model dev \\\n  --adapter models-mlx/lora/dragon-v1.safetensors \\\n  --fuse-adapter --no-t5-padding \\\n  --prompt-key lora_subject \\\n  --steps 4 --repeats 3 --warmup 1 --image-size 512\n``` | Exercises adapter fusion inside the benchmark runner. |
| **Benchmark – Pro Portrait** | ```bash\nuv run python benchmarks/flux/bench_flux.py \\\n  --model dev --prompt-key pro_portrait \\\n  --image-size 1024 --steps 4 --repeats 3 --warmup 1\n``` | Higher-resolution portrait baseline; ensure VRAM is sufficient. |
| **Benchmark – custom models dir** | ```bash\nuv run python benchmarks/flux/bench_flux.py \\\n  --model both --models-dir /Users/<you>/mlx-RAG/mlx-models \\\n  --prompt-key astronaut_horse --steps 4 --repeats 3 --warmup 1\n``` | Sets `MLX_MODELS_DIR` implicitly so runs use pre-downloaded weights. |

---

## MusicGen (audio generation)

| Scenario | Command | Notes |
| --- | --- | --- |
| **Quick 15 s clip** | ```bash\nuv run python -m rag.cli.generate_music \\\n  --prompt \"a calming piano melody\" --duration 15 \\\n  --output-dir ./var/music_output\n``` | Uses default `musicgen-small`; produces WAV files in the specified directory. |
| **Longer EDM sample** | ```bash\nuv run python -m rag.cli.generate_music \\\n  --prompt \"upbeat electronic dance music\" \\\n  --duration 30 --model-size medium --seed 1234\n``` | Explicitly chooses the `medium` checkpoint and sets a deterministic seed. |
| **Batch-friendly folder** | ```bash\nuv run python -m rag.cli.generate_music \\\n  --prompt \"lofi study beats\" --duration 20 \\\n  --output-dir ./var/music_output/lofi --model-size large\n``` | Keep outputs organized per experiment by pointing `--output-dir` to unique folders. |

> MusicGen currently supports WAV output only; the CLI guards against unsupported formats (see `src/rag/cli/generate_music.py`).

---

## RAG (vector DB ingestion, querying, and UIs)

| Scenario | Command | Notes |
| --- | --- | --- |
| **Download an MLX model** | ```bash\nuv run python -m rag.cli.download_model \
  --model-id mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit
``` | General-purpose helper for caching LLMs locally; repeat for embeddings or domain models. |
| **Build a vector DB from PDFs** | ```bash\nuv run python -m rag.ingestion.create_vdb \
  --pdf var/source_docs/sample.pdf \
  --vdb models/indexes/vdb.npz --chunk-size 512 --overlap 128
``` | Adjust chunk parameters per corpus size; ensure `models/indexes/` exists. |
| **Batch ingest (folder)** | ```bash\nuv run python -m rag.ingestion.create_vdb \
  --pdf-dir Data/manuals --glob "*.pdf" \
  --vdb models/indexes/manuals.npz
``` | Uses the folder glob mode for bulk ingestion. |
| **Query an existing VDB** | ```bash\nuv run python -m rag.retrieval.query_vdb \
  --question "What is MLX?" \
  --vdb models/indexes/vdb.npz --top-k 4
``` | Returns the top matches plus answer text; tweak `--top-k` per use case. |
| **rag-cli question loop** | ```bash\nrag-cli --vdb-path models/indexes/vdb.npz --model-id mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit
``` | Primary CLI that reranks retrieved context before asking `MLXModelEngine`. |
| **Rich-powered CLI** | ```bash\nuv run python -m rag.cli.interactive_rag \
  --vdb models/indexes/vdb.npz --model-id mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit
``` | Legacy Rich interface; still available if you want richer progress/status indicators. |
| **Archived Textual TUI** | _see `archive/tui/rag_tui.py`_ | The Textual UI has been archived for reference; this lab now favors CLI-first workflows. |


---

### Keeping This Manifest Fresh

- When adding new presets or workflows, append another table row inside the relevant section (Flux, MusicGen, RAG). Keep command blocks copy-paste ready.
- If an app grows beyond these categories, start a new top-level section (e.g., **Voice**, **Benchmarks**) to maintain clarity.
- Pair this manifest with `scripts/model_manifest.py` + `scripts/clean_models.py` when introducing new weight directories so operators can reproducibly run the commands above.

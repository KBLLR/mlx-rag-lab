# mlx‑RAG · Apple Silicon Tool Suite

mlx‑RAG is a lab of **MLX-first workflows** for Apple silicon. It bundles Speech‑to‑Speech avatars, live voice chat, RAG, Flux text‑to‑image, benchmarking, and ingestion utilities into one CLI-driven toolkit. Every pipeline runs locally on Metal (no cloud dependency) while staying close to upstream projects like **mlx-lm**, **Hugging Face Transformers**, Kokoro TTS, and WhisperX.

---

## What’s inside

| Domain | Pipelines & Models | Highlights |
| --- | --- | --- |
| **Voice / STS** | `sts-avatar-cli` (WhisperX → GPT‑OSS 20B → Kokoro TTS + visemes) | Ready Player Me visemes, diarization folders, push-to-talk mic capture (via Voice Chat app) |
| **Live Voice Chat** | `voice-chat-cli` (Whisper, GPT‑OSS, Marvis/Kokoro) | Hold‑space recording with VU meter, instant playback, optional transcript saving |
| **Retrieval & RAG** | `rag-cli`, ingestion scripts | Vector DB creation, Qwen reranker integration, scripted workflows for terminal automation |
| **Imaging** | `flux-cli`, `bench-cli flux …` | Flux text‑to‑image presets, benchmark harness with repeatable prompts |
| **Music / Audio** | MusicGen helpers under `apps/musicgen_cli.py` | Local melody experiments (see docs/projects/) |
| **Lab Orchestration** | `mlxlab_cli.py` | Rich menu for launching every pipeline with curated defaults |

_Model roster_: GPT-OSS 20B (mlx-community), Phi‑3 Mini, Kokoro voices (54), Marvis TTS, Whisper & WhisperX MLX forks, Qwen reranker, Flux checkpoints, MusicGen + Encodec. Download recipes live in `mlx-models/README.md`.

---

## Quick start

```bash
git clone https://github.com/your-username/mlx-RAG.git
cd mlx-RAG
pip install uv                      # once
uv venv && source .venv/bin/activate
uv sync                             # installs deps + console scripts

# Launch the lab menu (voice chat, STS avatar, RAG, Flux…)
uv run mlxlab
```

CLIs are wired via `[project.scripts]`, so `uv run voice-chat-cli --help` “just works”. See `docs/` for pipeline specifics and `mlx-models/README.md` for weight download tips (GPT‑OSS, Kokoro, Flux, etc.).

---

## Terminal-first workflows

- **Voice Chat** – Hold SPACE to record, release to send. Whisper transcribes, GPT‑OSS answers, Kokoro/Marvis speaks, audio auto-plays and is saved under `var/voice_chat/response_*`.
- **Speech-to-Speech Avatar** – Point to input audio (`var/source_audios`), get diarized transcripts, responses, `visemes.json`, and `speakers.json` for each turn. Designed for Ready Player Me / Three.js / Unity avatars.
- **RAG CLI** – `uv run rag-cli --vdb-path var/indexes/foo.npz` queries your vector DB, reranks with Qwen, formats answers with source snippets.
- **Flux / Bench** – `uv run flux-cli --prompt "retro mac" --steps 4` for quick renders, or `uv run bench-cli flux --preset portrait` to capture timing and outputs.
- **Automation ready** – Every pipeline prints clear paths (audio, JSON, transcripts) so you can wire them into shell scripts, Hazel automations, or Shortcuts.

Upcoming niceties: richer per-app layouts (Rich panels), saved presets, batch workflows for ingestion/cleanup, and Apple Shortcuts shims for “hands-free” launching.

---

## Roadmap snapshot

- **Benchmarking**: keep extending `bench-cli` for reproducible Flux/MusicGen timings on M1–M4. Results feed into docs/benchmarks/.
- **Workflow automation**: per-app config files + templated runs (e.g., “daily RAG ingest”, “voice memo → STS folder”).
- **Rich UI**: structured console layouts (progress bars, speaker panels, VU meters) across all CLIs, not just voice chat.
- **Data plumbing**: scripted cleanup for model caches, ingestion manifests, HF offline mirrors.

Follow progress in `agents/HANDOFFS.md` where each agent logs their alias + next steps.

---

## Credits & acknowledgements

- **Apple MLX / mlx-lm** for the core model runtimes and reference Whisper code (see `examples/whisper` subtree).
- **Hugging Face** for hosting GPT-OSS, Kokoro, Flux, WhisperX, and reranker checkpoints that power this lab.
- **Community projects** like Kokoro TTS, Marvis TTS, WhisperX-MLX, MusicGen, and Qwen reranker that we integrate via upstream APIs.

mlx‑RAG is not a polished product—it’s a fast-moving experimentation lab meant to squeeze every drop of performance from Apple silicon. Contributions, docs, and ideas are welcome (see [CONTRIBUTING.md](CONTRIBUTING.md)).

Enjoy the lab, keep your models local, and let the terminal be your control room. 🎛️

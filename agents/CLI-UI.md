• # Project CLI Overview

  mlxlab is the umbrella launcher for every MLX/RAG workflow in this repo. When you run uv run mlxlab (or the installed mlxlab script), it boots apps/mlxlab_cli.py,
  clears the terminal, prints an ASCII banner, and renders an InquirerPy select menu. Each menu entry either opens a configuration wizard (built with InquirerPy prompts
  plus Rich console output) or dispatches a direct action (show cache, clean memory, etc.). Once a pipeline is configured, the CLI prints the composed uv run … command
  and, on confirmation, executes it via subprocess.run.

  ## Entry Points

  | File / Function | Purpose |
  | --- | --- |
  | src/rag/cli/entrypoints.py:mlxlab_main() | Lightweight runner that ensures PYTHONPATH=src and calls apps.mlxlab_cli.main(). Similar wrappers exist for each pipeline
  CLI (chat_cli_main, voice_chat_cli_main, etc.), so every script can be invoked via uv run <name>-cli. |
  | apps/mlxlab_cli.py:main() | Installs SIGINT handler, calls main_menu(), and handles any uncaught exceptions. |
  | apps/mlxlab_cli.py:main_menu() | Core event loop. Builds the menu with InquirerPy.select, clears the screen between loops, and routes selections to configuration
  helpers (configure_chat, configure_voice_chat, etc.), utility views (show_models_menu, show_cache_info), or inline actions (cleanup, exit). |

  ## Menu Structure

  (Current labels contain emojis; these will need redesign per new guidelines.)

  | Label (current) | Internal id | Handler/Command | Location |
  | --- | --- | --- | --- |
  | 💬 Chat - Conversational AI | chat | run_pipeline("chat") → configure_chat() → builds uv run chat-cli --model-id … | apps/mlxlab_cli.py:1719-1744, config at apps/
  mlxlab_cli.py:1176-1254 |
  | 🗣️  Voice Chat - Text to Speech | voice_chat | configure_voice_chat() → uv run voice-chat-cli --chat-model … [--live] | apps/mlxlab_cli.py:1256-1348 |
  | 🎭 STS Avatar - Speech to Speech | sts_avatar | configure_sts_avatar() → uv run sts-avatar-cli … (diarization options, voice mapping) | apps/mlxlab_cli.py:1337-
  1544 |
  | 🔍 RAG - Question Answering | rag | configure_rag() → uv run rag-cli --vdb-path … | apps/mlxlab_cli.py (see rg 'def configure_rag' around lines ~820) |
  | 📚 Ingest - Build Vector Index | ingest | configure_ingest() → uv run ingest-cli … | same file, ~line 640+ |
  | 🏷️  Classify - Text Classification | classify | configure_classify() → uv run classify-cli … | ~line 720 |
  | 🎨 Flux - Image Generation | flux | configure_flux() → uv run flux-cli --prompt … | ~line 560 |
  | 🎵 MusicGen - Audio Generation | musicgen | configure_musicgen() → uv run musicgen-cli --prompt … (now supports prompt presets via --prompt-preset) | ~line 960 |
  | 🎙️  Whisper - Speech-to-Text | whisper | configure_whisper() → uv run whisper-cli --model … | ~line 400 |
  | 📊 Benchmark - Performance Testing | bench | No wizard yet. Prints notice and default command uv run bench-cli --help. | apps/mlxlab_cli.py:1687-1704 |
  | 🧪 Generators - Dataset Tools | generators | configure_generators() → sub-menu currently offering “Q&A Dataset (MLX models)” which calls run_qa_dataset_generator()
  in the same file, ultimately invoking generate_qa_dataset() from experiments/dataset_generation/generate_qa_dataset.py. | apps/mlxlab_cli.py:1560-1690 |
  | 📥 Download Models | download | Calls download_model() to fetch HF weights into mlx-models/. | ~line 110 |
  | 📦 View Available Models | models | show_models_menu(); lists curated model options defined in MODELS. | ~line 300 |
  | 💾 View HuggingFace Cache | cache | show_cache_info() prints cache stats via Rich table. | apps/mlxlab_cli.py:294-341 |
  | 🗑️  Delete Cached Models | delete | delete_cached_models() (interactive removal). | ~line 360 |
  | 💻 System Information | system | show_system_info() (hardware summary; uses Rich). | ~line 430 |
  | 🧹 Clean Memory (MLX) | cleanup | Inline gc.collect() with status message. | apps/mlxlab_cli.py:1784-1794 |
  | 🚪 Exit | exit | Breaks loop after farewell. | apps/mlxlab_cli.py:1747-1755 |

  (You’ll remove/rework emojis in the next iteration.)

  ## UI and Styling

  Files importing Rich and their roles:

  - apps/mlxlab_cli.py: Global console = Console() (line ~34), ASCII banner show_header(), colored text, Panel, Table, Progress, and verbose emoji usage throughout
    configuration helpers. No shared theme—styles are inline strings ("bold cyan", "dim", etc.). ASCII art stored in PIPELINE_HEADERS.
  - apps/chat_cli.py: Uses Console, Panel, Markdown for help panels, history dumps, and cleanup messages.
  - apps/voice_chat_cli.py: Console and Panel.fit for pipeline summary; console.print handles all recorder status cues (recording, silence warnings).
  - apps/sts_avatar_cli.py: Console, Panel, Progress (for audio processing), Table for available audio listing.
  - apps/classify_cli.py: Rich console output for result tables and progress bars.
  - experiments/dataset_generation/generate_qa_dataset.py: Console plus Progress spinner/bars for MLX-based Q/A generation.
  - experiments/ingestion/build_vdb_from_generated_dataset.py & experiments/benchmarking/retrieval_benchmark.py: use Rich for progress/log reporting during data prep
    and benchmarking.
  - src/rag/ingestion/create_vdb.py, src/rag/cli/interactive_rag.py, src/rag/cli/utils.py: utility scripts that print status via Rich (tables, log panels).
  - Emojis currently appear in banner headings, menu labels, config prompts, and inline status icons (✅, 🧹, etc.).

  There is no centralized theme or layout helper—every module instantiates its own Console and hardcodes colors and icons.

  ## Pipelines and Commands

  | Menu label | Script / Module | Entry function | Rich usage / notes |
  | --- | --- | --- | --- |
  | Chat | apps/chat_cli.py | main() (invoked from chat_cli_main) | Rich console + panels; command parser built with argparse; maintains history and optional JSON
  logging. |
  | Voice Chat | apps/voice_chat_cli.py | main() | Rich console/panels plus sounddevice/pynput; live VU meter and recording status messages. |
  | STS Avatar | apps/sts_avatar_cli.py | main() | Heavy Rich usage (console, Panel, Progress) for pipeline status and folder summaries. |
  | RAG | apps/rag_cli.py | main() | Plain stdout (no Rich); prompts user via input() loop; prints JSON/strings. |
  | Ingest | apps/ingest_cli.py | main() | (Not shown above, but invoked via entrypoints) handles document ingestion; typically prints status via Rich (check import). |
  | Classify | apps/classify_cli.py | main() | Rich tables for classification summaries. |
  | Flux | apps/flux_cli.py | main() | Wraps text-to-image runner; minimal Rich usage (mostly prints). |
  | MusicGen | apps/musicgen_cli.py | main() | Pure argparse + print; now supports prompt preset management but no Rich styling yet. |
  | Whisper | apps/whisper_cli.py | main() | Basic logging, no Rich components. |
  | Benchmark | apps/bench_cli.py | main() | Launches benchmarking scripts (progress output handled inside benchmarks/). |
  | Generators (Q&A) | experiments/dataset_generation/generate_qa_dataset.py | generate_qa_dataset() | Rich Progress spinner, console info. |
  | Utility actions | apps/mlxlab_cli.py (functions show_models_menu, show_cache_info, etc.) | N/A | Use Rich Table, Panel, direct console.print. |

  ## Suggested Integration Points

  - Global console/layout/theme: The single source of truth should live in apps/mlxlab_cli.py where console = Console() is currently defined (top of file). Replace
    that with a helper (e.g., from rag.cli.ui import get_console) and optionally instantiate a Rich Layout inside main_menu() or show_header(). This module already owns
    banner rendering and menu orchestration, so it’s the natural “UI shell”.
  - Centralized theme helpers: Create a new module (e.g., src/rag/cli/ui.py) exporting a configured Console, reusable Panel styles, and banner text. apps/mlxlab_cli.py,
    plus downstream CLIs (chat_cli, voice_chat_cli, etc.), can import the shared theme instead of defining colors/emojis inline.
  - UI Settings branch: Add a new Choice("ui_settings", name="UI Settings") under the “OTHER” separator inside main_menu() (around apps/mlxlab_cli.py:1735). Handle it
    near the existing elif action == "cleanup" block (add elif action == "ui_settings": configure_ui_settings()), where configure_ui_settings() would eventually present
    toggles (theme variant, borders, glass effect). Keep the function in the same file initially, or move to the future ui.py.
  - Layout entry point: Implement layout initialization right after show_header() or wrap main_menu() with a with Live(layout, refresh_per_second=…) context so all views
    share the same Rich layout. Because main_menu already clears/redraws, this is the best place to intercept output.
  - Other modules: Once a global theme exists, update apps/chat_cli.py, apps/voice_chat_cli.py, and apps/sts_avatar_cli.py to import that theme instead of instantiating
    their own Console. This ensures future Rich-based components (dialogs, progress dashboards) look consistent.

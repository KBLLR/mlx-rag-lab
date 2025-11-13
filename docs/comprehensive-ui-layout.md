. Comprehensive UI layout analysis document

Here’s a ready-to-drop markdown doc you can commit as e.g.:

docs/ui/cli-layout-proposals.md
(or docs/ui/cli-layouts-2025.md, you decide how dramatic you want to be).

# MLX-RAG Lab CLI UI Layout Proposals

## 0. Context

This document summarizes a UI audit across **11 CLI apps** in the `mlx-RAG` lab and proposes a consistent set of **layout patterns** and **shared UI components**.

Goals:

- Unify interaction patterns across CLIs
- Make complex pipelines understandable at a glance
- Keep UX consistent with “lab console” mental model
- Prepare for future TUI / Rich-powered extensions

---

## 1. App Inventory & Categories

**CLI Apps:**

- `chat_cli.py`
- `rag_cli.py`
- `voice_chat_cli.py`
- `classify_cli.py`
- `mlxlab_cli.py`
- `ingest_cli.py`
- `whisper_cli.py`
- `musicgen_cli.py`
- `flux_cli.py`
- `bench_cli.py`
- `sts_avatar_cli.py`

**5 UI Pattern Categories:**

1. **Interactive Chat Loops**  
   - Apps: `chat_cli.py`, `rag_cli.py`, `voice_chat_cli.py`
2. **Data Presentation & Analysis**  
   - Apps: `classify_cli.py`
3. **Menu-Driven Navigation**  
   - Apps: `mlxlab_cli.py`
4. **Batch Processing with Progress**  
   - Apps: `ingest_cli.py`, `whisper_cli.py`, `musicgen_cli.py`, `flux_cli.py`
5. **Complex Interactive with File Selection**  
   - Apps: `sts_avatar_cli.py`

---

## 2. Pattern 1 – Interactive Chat Loops

**Apps:** `chat_cli.py`, `rag_cli.py`, `voice_chat_cli.py`  

**Current issues:**

- Input field scrolls with history
- Header/status info scrolls off-screen
- No clear separation between *context*, *answer*, and *commands*

### Proposed Layout

```text
┌─────────────────────────────────────┐
│ FIXED HEADER                       │
│ Model: GPT-OSS | Temp: 0.7         │
│ Tokens: 512 | Mode: RAG            │
├─────────────────────────────────────┤
│ SCROLLABLE CHAT HISTORY            │
│ • You: How does RAG work?          │
│ • Assistant: RAG combines...       │
│ • You: What about reranking?       │
│ • Assistant: Reranking uses...     │
│                                     │
│ ↓ (auto-scroll to bottom)          │
├─────────────────────────────────────┤
│ FIXED FOOTER INPUT                 │
│ You: █                             │
│ /help /history /clear /exit        │
└─────────────────────────────────────┘


Key behaviors:

Header is fixed: model, mode, token usage, optional latency

History scrolls independently, always focusing on latest exchange

Footer:

Prompt line

Inline help for slash commands

Extra for rag_cli.py:

Split the main area logically into:

Context Panel (sources, docs, chunks)

Answer Panel (final response)

Using Rich Layout:

┌───────────────┬─────────────────────┐
│ CONTEXT       │ ANSWER              │
│ (scroll)      │ (scroll)            │
└───────────────┴─────────────────────┘

3. Pattern 2 – Data Presentation & Analysis

App: classify_cli.py

Current issues:

Raw numeric scores, hard to interpret

Uniform distributions (e.g. ~0.12 everywhere) are not flagged as “low confidence”

Long file paths kill readability

Proposed Layout
┌─────────────────────────────────────┐
│ FIXED HEADER                       │
│ Mode: Emotion | VDB: grok-chat     │
├─────────────────────────────────────┤
│ SCROLLABLE RESULTS TABLE           │
│ ╔══════════════╦════════╦════════╗ │
│ ║ Text         ║ Source ║ Top 3  ║ │
│ ╠══════════════╬════════╬════════╣ │
│ ║ Monkey...    ║ grok…  ║ BARS   ║ │
│ ╚══════════════╩════════╩════════╝ │
│                                     │
│ [Confidence Chart Component]        │
│ ████░░ surprise (0.12)              │
│ ███░░ negative (0.12)               │
│                                     │
├─────────────────────────────────────┤
│ FIXED FOOTER STATS                 │
│ Total: 150 | Avg Conf: 0.12        │
│ ⚠ Low confidence detected          │
└─────────────────────────────────────┘

Proposed Components
3.1 Confidence Bar Chart
def render_confidence_bars(predictions: list[dict], max_width: int = 20) -> None:
    """Render horizontal bar chart for confidence scores."""
    for pred in predictions:
        label = pred["label"]
        score = pred["score"]
        filled = int(score * max_width)
        bar = "█" * filled + "░" * (max_width - filled)
        color = get_confidence_color(score)
        console.print(f"[{color}]{bar}[/{color}] {label} ({score:.2%})")

3.2 Smart Path Truncation
def truncate_source_path(path: str, max_len: int = 50) -> str:
    """Smart path truncation keeping important parts."""
    if len(path) <= max_len:
        return path

    parts = path.split("/")
    filename = parts[-1]

    if len(filename) > max_len - 10:
        return f".../{filename[: max_len - 13]}..."

    remaining = max_len - len(filename) - 4
    prefix = path[: remaining // 2]
    return f"{prefix}.../{filename}"

3.3 Low-Confidence Warning
import statistics

def show_confidence_warning(predictions: list[dict]) -> None:
    """Warn when predictions are too uniform (low confidence)."""
    scores = [p["score"] for p in predictions]
    if len(scores) < 2:
        return

    std_dev = statistics.stdev(scores)
    if std_dev < 0.05:
        console.print("[yellow]⚠ Low confidence: scores too uniform[/yellow]")
        console.print("[dim]Model is uncertain about this classification[/dim]")

4. Pattern 3 – Menu-Driven Navigation (MLX Lab)

App: mlxlab_cli.py

Problems identified

Too many flat options (18+ items)

Model/system/UI actions scattered across menu

Header can scroll out of view in some layouts

Global actions are conceptually separate but visually mixed

New Main Menu Layout
┌─────────────────────────────────────┐
│ FIXED HEADER – MLX LAB             │
│ System: M3 Max | RAM: 36GB         │
├─────────────────────────────────────┤
│            PIPELINES               │
│   💬 Chat                          │
│   🗣 Voice Chat                     │
│   🎭 STS Avatar                    │
│   🔍 RAG                           │
│   📚 Ingest                        │
│   🏷 Classify                      │
│   🎨 Flux                          │
│   🎵 MusicGen                      │
│   🎙 Whisper                       │
│   📊 Benchmark                     │
│                                    │
│            TOOLS                   │
│   📦 Models Management             │
│   💻 System Management             │
│                                    │
│            USER                    │
│   👤 User Menu                     │
├─────────────────────────────────────┤
│ FOOTER                             │
│ ↑↓ Navigate | Enter Select | Q Quit│
└─────────────────────────────────────┘

Grouped Views

Models Management

Download models

List available models

Show cache usage / locations

Delete cached models

System Management

Show system info (device, RAM, MLX env)

Memory / cache cleanup utilities

User Menu

UI settings (theme, verbosity, debug level)

Exit MLX Lab

These changes are already implemented on branch:

claude/ui-improvements-01BFX4GERN54LzhRA9UpE1Wt

5. Pattern 4 – Batch Processing with Progress

Apps: ingest_cli.py, whisper_cli.py, musicgen_cli.py, flux_cli.py

Current issues:

Logs and progress interleaved

No clear separation between “now”, “history”, and “controls”

It’s hard to know what is currently happening vs what just finished

Proposed Layout
┌──────────────────────────────────────────┐
│ FIXED HEADER                            │
│ Task: Ingest PDFs | Bank: papers        │
├──────────────────────────────────────────┤
│ CENTERED PROGRESS (FIXED)               │
│  Processing 45/150 files…               │
│  ████████████░░░░░░░░░ 30%              │
│                                          │
│  Current: quantum_physics.pdf           │
│  Speed: 2.3 files/sec                   │
│  ETA: 45 seconds                        │
│                                          │
│ [Scrollable Log Below]                  │
│  ✓ doc1.pdf → 234 chunks                │
│  ✓ doc2.pdf → 189 chunks                │
│  …                                      │
├──────────────────────────────────────────┤
│ FOOTER                                  │
│ Press Ctrl+C to cancel                  │
└──────────────────────────────────────────┘


Common elements across these apps:

Standardized progress bar component (Rich Progress)

“Current item” line

Short metrics: throughput, ETA

Scrollable log of completed items

6. Pattern 5 – Complex Interactive + File Selection

App: sts_avatar_cli.py

Current issues:

File selection is numeric only

Lack of persistent view of file list vs results

Multi-file pipelines are hard to visualize

Proposed Layout
┌─────────────────────────────────────┐
│ FIXED HEADER                       │
│ STS Avatar | Voice: af_bella       │
├──────────────┬─────────────────────┤
│ LEFT SIDEBAR │ MAIN AREA           │
│ 📁 Files     │ 🎤 Transcribing…    │
│ 1. a_01.wav  │ You said: "Hello"   │
│ 2. a_02.mp3  │                     │
│ 3. a_03.m4a  │ 💬 Assistant:       │
│ …            │  Hello! How are you?│
│              │                     │
│              │ 📁 Saved to:        │
│              │  responses/YYYYMMDD │
│              │   • audio.wav       │
│              │   • visemes.json    │
├──────────────┴─────────────────────┤
│ FOOTER INPUT                       │
│ Select file (1–N) or path: █       │
└─────────────────────────────────────┘


Components:

File Tree Component: list of available files with icons & sizes

Status Timeline: show pipeline stages (ingest → transcribe → synth → export)

Output Preview: simple textual preview (later: audio waveform)

7. Shared UI Component Library

To avoid duplicating logic and ASCII crimes everywhere, define a shared UI toolkit, e.g.:

apps/ui/common.py or apps/ui/components/*.py

Proposed building blocks:

Header / Footer helpers

render_header(title: str, meta: dict)

render_footer(hints: list[str])

Chat History Renderer

render_chat_history(messages: list[dict])

Progress Panel

render_task_progress(current, total, eta, speed)

Tables & Expandables

render_expandable_table(results: list[dict])

render_confidence_bars(predictions: list[dict])

Path helpers

truncate_source_path(path: str, max_len: int = 50)

Warnings

show_confidence_warning(predictions)

show_system_warning(message)

8. Summary by App
App	Layout Type	Key Needs
chat_cli	Fixed header/footer	Scrollable history, commands
rag_cli	Fixed header/footer	Context panel + answer panel
voice_chat_cli	Fixed header/footer	Audio status, timelines
classify_cli	Data presentation	Confidence bars, warnings
mlxlab_cli	Centered menu	Grouped actions, user menu
ingest_cli	Centered progress	Log scroll, progress summary
whisper_cli	Centered progress	Transcript view + progress
musicgen_cli	Centered progress	Render status + audio output
flux_cli	Centered progress	Image preview + status
bench_cli	Fixed table	Comparisons, summaries
sts_avatar_cli	Sidebar + main	File tree, pipeline timeline
9. Implementation Order

Done on claude/ui-improvements-01BFX4GERN54LzhRA9UpE1Wt:

mlxlab_cli.py main menu reorganization

classify_cli.py confidence visualization + warnings

Next recommended steps:

Extract shared UI helpers into apps/ui/

Apply chat layout to:

chat_cli.py

rag_cli.py

voice_chat_cli.py

Refactor batch apps to use unified progress/log layout

Implement file/tree panel for sts_avatar_cli.py

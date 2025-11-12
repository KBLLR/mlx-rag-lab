#!/usr/bin/env python3
"""
MLX Lab v2 - Interactive CLI for MLX pipelines
Unified interface with model management, quantization, and cache control.
"""

import gc
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional

from huggingface_hub import scan_cache_dir
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

# Pipeline metadata
PIPELINES = {
    "rag": {
        "name": "RAG - Question Answering",
        "description": "Ask questions over your local vector index",
        "emoji": "🔍",
        "command": "rag-cli",
    },
    "flux": {
        "name": "Flux - Image Generation",
        "description": "Generate images from text descriptions",
        "emoji": "🎨",
        "command": "flux-cli",
    },
    "musicgen": {
        "name": "MusicGen - Audio Generation",
        "description": "Create audio from text prompts",
        "emoji": "🎵",
        "command": "musicgen-cli",
    },
    "whisper": {
        "name": "Whisper - Speech-to-Text",
        "description": "Transcribe audio files to text",
        "emoji": "🎙️",
        "command": "whisper-cli",
    },
    "bench": {
        "name": "Benchmark - Performance Testing",
        "description": "Run benchmarks on MLX models",
        "emoji": "📊",
        "command": "bench-cli",
    },
}

# Correct model names with -mlx suffix
MODELS = {
    "whisper": {
        "full": [
            ("mlx-community/whisper-tiny-mlx", "~39MB", "Fastest, good for testing"),
            ("mlx-community/whisper-base-mlx", "~74MB", "Balanced speed/accuracy"),
            ("mlx-community/whisper-small-mlx", "~244MB", "Better accuracy"),
            ("mlx-community/whisper-medium-mlx", "~769MB", "High accuracy"),
            ("mlx-community/whisper-large-v3-mlx", "~1.5GB", "Best accuracy"),
            ("mlx-community/whisper-large-v3-turbo", "~809MB", "⚡ Latest turbo (Nov 2024)"),
            ("mlx-community/whisper-turbo", "~809MB", "⚡ Turbo variant (Oct 2024)"),
        ],
        "english_only": [
            ("mlx-community/whisper-tiny.en-mlx", "~39MB", "English-only, faster"),
            ("mlx-community/whisper-base.en-mlx", "~74MB", "English-only, faster"),
            ("mlx-community/whisper-small.en-mlx", "~244MB", "English-only, faster"),
        ],
        "quantized": [
            "4-bit (smaller, faster, slight quality loss)",
            "8-bit (good balance)",
            "2-bit (smallest, lowest quality)",
        ],
    },
    "musicgen": [("facebook/musicgen-small", "5.4GB", "Meta's text-to-audio model")],
    "flux": [
        ("schnell", "23GB", "Fast generation"),
        ("dev", "23GB", "Higher quality"),
    ],
    "rag": [
        ("Phi-3-mini-4k-instruct-4bit", "", "Quantized LLM"),
        ("mxbai-rerank-large-v2", "", "Cross-encoder reranker"),
    ],
}

LANGUAGES = [
    "English",
    "Spanish",
    "German",
    "French",
    "Italian",
    "Portuguese",
    "Dutch",
    "Russian",
    "Chinese",
    "Japanese",
    "Korean",
    "Auto-detect",
]


def show_header():
    """Display the MLX Lab header."""
    header = """
    ███╗   ███╗██╗     ██╗  ██╗    ██╗      █████╗ ██████╗
    ████╗ ████║██║     ╚██╗██╔╝    ██║     ██╔══██╗██╔══██╗
    ██╔████╔██║██║      ╚███╔╝     ██║     ███████║██████╔╝
    ██║╚██╔╝██║██║      ██╔██╗     ██║     ██╔══██║██╔══██╗
    ██║ ╚═╝ ██║███████╗██╔╝ ██╗    ███████╗██║  ██║██████╔╝
    ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝╚═════╝
    """
    console.print(f"[bold cyan]{header}[/bold cyan]")
    console.print(
        "[dim]Local-first MLX pipelines on Apple Silicon[/dim]\n", justify="center"
    )


def get_cache_info():
    """Get HuggingFace cache information."""
    try:
        cache_info = scan_cache_dir()
        return cache_info
    except Exception as e:
        console.print(f"[yellow]Could not scan cache: {e}[/yellow]")
        return None


def show_cache_info():
    """Display HuggingFace cache information."""
    console.print("\n[bold cyan]📦 HuggingFace Cache Information[/bold cyan]\n")

    cache_info = get_cache_info()
    if not cache_info:
        console.print("[red]Unable to access cache information[/red]")
        return

    # Overall stats
    total_size = cache_info.size_on_disk
    total_repos = len(cache_info.repos)

    table = Table(title="Cache Overview", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Cache Location", str(Path.home() / ".cache/huggingface/hub"))
    table.add_row("Total Size", f"{total_size / 1e9:.2f} GB")
    table.add_row("Total Repositories", str(total_repos))

    console.print(table)

    # List repos
    if total_repos > 0:
        console.print("\n[bold]Cached Models:[/bold]\n")

        repo_table = Table(show_header=True, header_style="bold cyan")
        repo_table.add_column("Repository", style="yellow", no_wrap=False)
        repo_table.add_column("Size", style="green", justify="right")
        repo_table.add_column("Revisions", style="blue", justify="right")

        for repo in sorted(cache_info.repos, key=lambda r: r.size_on_disk, reverse=True)[:20]:
            repo_name = repo.repo_id
            repo_size = f"{repo.size_on_disk / 1e9:.2f} GB"
            num_revisions = len(repo.revisions)

            repo_table.add_row(repo_name, repo_size, str(num_revisions))

        console.print(repo_table)

        if total_repos > 20:
            console.print(f"\n[dim]... and {total_repos - 20} more repositories[/dim]")

    input("\n[dim]Press Enter to continue...[/dim]")


def delete_cached_models():
    """Interactive model deletion from cache."""
    console.print("\n[bold yellow]⚠️  Model Deletion[/bold yellow]\n")

    cache_info = get_cache_info()
    if not cache_info or len(cache_info.repos) == 0:
        console.print("[yellow]No cached models found[/yellow]")
        input("\n[dim]Press Enter to continue...[/dim]")
        return

    # Let user select models to delete
    choices = []
    for repo in sorted(cache_info.repos, key=lambda r: r.size_on_disk, reverse=True):
        size_gb = repo.size_on_disk / 1e9
        choices.append(
            Choice(
                repo.repo_id,
                name=f"{repo.repo_id} ({size_gb:.2f} GB)",
            )
        )

    selected = inquirer.checkbox(
        message="Select models to DELETE (Space to select, Enter to confirm):",
        choices=choices,
        instruction="(Use arrow keys, Space to select, Enter to confirm)",
    ).execute()

    if not selected:
        console.print("[yellow]No models selected[/yellow]")
        input("\n[dim]Press Enter to continue...[/dim]")
        return

    # Calculate total size to free
    total_size = sum(
        repo.size_on_disk for repo in cache_info.repos if repo.repo_id in selected
    )

    console.print(f"\n[bold red]You are about to delete {len(selected)} model(s)[/bold red]")
    console.print(f"[bold]Total space to free: {total_size / 1e9:.2f} GB[/bold]\n")

    for model in selected:
        console.print(f"  • {model}")

    confirm = inquirer.confirm(
        message="\nAre you SURE you want to delete these models?",
        default=False,
    ).execute()

    if confirm:
        console.print("\n[bold]Deleting models...[/bold]\n")

        strategy = cache_info.delete_revisions(*[
            rev.commit_hash
            for repo in cache_info.repos
            if repo.repo_id in selected
            for rev in repo.revisions
        ])

        console.print(f"[green]✓ Deleted {len(selected)} model(s)[/green]")
        console.print(f"[green]✓ Freed {strategy.expected_freed_size / 1e9:.2f} GB[/green]")
    else:
        console.print("[yellow]Deletion cancelled[/yellow]")

    input("\n[dim]Press Enter to continue...[/dim]")


def download_model():
    """Interactive model download with progress."""
    console.print("\n[bold cyan]📥 Download Model[/bold cyan]\n")

    # Select pipeline
    pipeline_choice = inquirer.select(
        message="Select pipeline:",
        choices=[
            Choice("whisper", name="Whisper - Speech-to-Text"),
            Choice("musicgen", name="MusicGen - Audio Generation"),
        ],
        default="whisper",
    ).execute()

    if pipeline_choice == "whisper":
        # Select category
        category = inquirer.select(
            message="Select model category:",
            choices=[
                Choice("full", name="Full multilingual models"),
                Choice("english_only", name="English-only models (faster)"),
            ],
            default="full",
        ).execute()

        # Select specific model
        model_choices = [
            Choice(model[0], name=f"{model[0].split('/')[-1]} - {model[1]} - {model[2]}")
            for model in MODELS["whisper"][category]
        ]

        model_id = inquirer.select(
            message="Select model to download:",
            choices=model_choices,
        ).execute()

    elif pipeline_choice == "musicgen":
        model_id = "facebook/musicgen-small"

    console.print(f"\n[bold]Downloading: {model_id}[/bold]\n")
    console.print("[dim]This will download the model to ~/.cache/huggingface/hub[/dim]\n")

    confirm = inquirer.confirm(
        message="Start download?",
        default=True,
    ).execute()

    if confirm:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Downloading {model_id}...", total=None)

            try:
                from huggingface_hub import snapshot_download

                snapshot_download(repo_id=model_id, cache_dir=None)
                progress.update(task, completed=True)
                console.print(f"\n[green]✓ Downloaded {model_id}[/green]")
            except Exception as e:
                console.print(f"\n[red]✗ Download failed: {e}[/red]")

    input("\n[dim]Press Enter to continue...[/dim]")


def show_models_menu():
    """Show available models for each pipeline."""
    console.print("\n[bold cyan]📦 Available Models[/bold cyan]\n")

    # Whisper models
    console.print("[bold yellow]WHISPER - SPEECH-TO-TEXT[/bold yellow]")
    console.print("\n[bold]Full Multilingual Models:[/bold]")
    for model, size, desc in MODELS["whisper"]["full"]:
        console.print(f"  • {model.split('/')[-1]} - {size} - {desc}")

    console.print("\n[bold]English-Only Models (faster):[/bold]")
    for model, size, desc in MODELS["whisper"]["english_only"]:
        console.print(f"  • {model.split('/')[-1]} - {size} - {desc}")

    console.print("\n[bold]Quantized Options:[/bold]")
    for option in MODELS["whisper"]["quantized"]:
        console.print(f"  • {option}")

    console.print("\n[bold yellow]MUSICGEN - AUDIO GENERATION[/bold yellow]")
    for model, size, desc in MODELS["musicgen"]:
        console.print(f"  • {model} - {size} - {desc}")

    console.print("\n[dim]Total: 54+ Whisper variants available in mlx-community[/dim]")

    input("\n[dim]Press Enter to continue...[/dim]")


def show_system_info():
    """Display system information and resource usage."""
    import subprocess

    table = Table(title="System Information", show_header=True, header_style="bold magenta")
    table.add_column("Resource", style="cyan")
    table.add_column("Status", style="green")

    # Platform
    table.add_row("Platform", "macOS (Apple Silicon)")
    table.add_row("MLX Framework", "✓ Available")

    # Models directory
    models_path = Path("mlx-models")
    if models_path.exists():
        model_count = len(list(models_path.iterdir()))
        total_size = sum(
            sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
            for p in models_path.iterdir()
            if p.is_dir()
        )
        table.add_row("Local Models", f"{model_count} directories ({total_size / 1e9:.1f} GB)")
    else:
        table.add_row("Local Models", "Not found")

    # HuggingFace cache
    cache_info = get_cache_info()
    if cache_info:
        cache_size = cache_info.size_on_disk / 1e9
        cache_repos = len(cache_info.repos)
        table.add_row("HF Cache", f"{cache_repos} models ({cache_size:.1f} GB)")

    # Var directories
    var_path = Path("var")
    if var_path.exists():
        source_audios = (
            len(list((var_path / "source_audios").glob("*")))
            if (var_path / "source_audios").exists()
            else 0
        )
        transcripts = (
            len(list((var_path / "transcripts").glob("*")))
            if (var_path / "transcripts").exists()
            else 0
        )
        music_outputs = (
            len(list((var_path / "music_output").glob("*")))
            if (var_path / "music_output").exists()
            else 0
        )

        table.add_row("Source Audio Files", str(source_audios))
        table.add_row("Transcripts", str(transcripts))
        table.add_row("Generated Music", str(music_outputs))

    console.print(table)
    console.print()
    input("\n[dim]Press Enter to continue...[/dim]")


def configure_whisper():
    """Interactive configuration for Whisper pipeline."""
    console.print("\n[bold cyan]🎙️  Whisper Configuration[/bold cyan]\n")

    # Select audio files
    source_dir = Path("var/source_audios")
    if not source_dir.exists():
        console.print("[red]var/source_audios/ not found![/red]")
        return None

    audio_files = list(source_dir.glob("*"))
    audio_files = [
        f
        for f in audio_files
        if f.suffix.lower() in [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm"]
    ]

    if not audio_files:
        console.print("[red]No audio files found in var/source_audios/[/red]")
        return None

    console.print(f"[green]Found {len(audio_files)} audio files[/green]\n")

    # File selection
    file_choice = inquirer.select(
        message="Select audio file:",
        choices=[Choice("all", name="🎵 Transcribe all files"), Separator()]
        + [Choice(str(f), name=f"📄 {f.name}") for f in audio_files[:20]],
        default="all",
    ).execute()

    # Model category
    category = inquirer.select(
        message="Select model category:",
        choices=[
            Choice("full", name="Full multilingual models"),
            Choice("english_only", name="English-only models (faster)"),
        ],
        default="full",
    ).execute()

    # Model selection with correct names
    model_choices = [
        Choice(model[0], name=f"{model[0].split('/')[-1]} - {model[1]} - {model[2]}")
        for model in MODELS["whisper"][category]
    ]

    model = inquirer.select(
        message="Select Whisper model:",
        choices=model_choices,
        default=model_choices[0].value,
    ).execute()

    # Output format
    output_format = inquirer.select(
        message="Select output format:",
        choices=[
            Choice("txt", name="Plain text"),
            Choice("json", name="JSON with timestamps"),
            Choice("srt", name="SRT subtitles"),
            Choice("vtt", name="VTT subtitles"),
            Choice("all", name="All formats"),
        ],
        default="json",
    ).execute()

    # Language hint
    use_language = inquirer.confirm(
        message="Specify language hint? (faster processing)", default=False
    ).execute()

    language = None
    if use_language:
        language = inquirer.select(
            message="Select language:", choices=LANGUAGES, default="English"
        ).execute()

    # Build command
    files_arg = "var/source_audios/*" if file_choice == "all" else file_choice
    cmd_parts = [
        "uv run whisper-cli",
        files_arg,
        f"--model {model}",
        f"--output-format {output_format}",
        "--output-dir var/transcripts",
    ]

    if language and language != "Auto-detect":
        cmd_parts.append(f"--language {language}")

    return " ".join(cmd_parts)


def configure_musicgen():
    """Interactive configuration for MusicGen pipeline."""
    console.print("\n[bold cyan]🎵 MusicGen Configuration[/bold cyan]\n")

    prompt = inquirer.text(
        message="Enter music description:", default="upbeat electronic melody"
    ).execute()

    duration_choice = inquirer.select(
        message="Select duration:",
        choices=[
            Choice(300, name="~10 seconds (300 steps)"),
            Choice(500, name="~16 seconds (500 steps)"),
            Choice(900, name="~30 seconds (900 steps)"),
            Choice("custom", name="Custom..."),
        ],
        default=500,
    ).execute()

    if duration_choice == "custom":
        max_steps = inquirer.number(
            message="Enter number of steps (30 steps ≈ 1 second):",
            min_allowed=100,
            max_allowed=3000,
            default=500,
        ).execute()
    else:
        max_steps = duration_choice

    use_custom_name = inquirer.confirm(
        message="Use custom output filename?", default=False
    ).execute()

    output_arg = ""
    if use_custom_name:
        filename = inquirer.text(message="Enter filename (without extension):", default="music").execute()
        output_arg = f"--output var/music_output/{filename}.wav"
    else:
        output_arg = "--output-dir var/music_output --prefix musicgen"

    cmd = f'uv run musicgen-cli --prompt "{prompt}" --max-steps {max_steps} {output_arg}'
    return cmd


def configure_flux():
    """Interactive configuration for Flux pipeline."""
    console.print("\n[bold cyan]🎨 Flux Configuration[/bold cyan]\n")

    prompt = inquirer.text(
        message="Enter image description:", default="a beautiful landscape at sunset"
    ).execute()

    model = inquirer.select(
        message="Select Flux model:",
        choices=[
            Choice("schnell", name="Schnell - Fast generation"),
            Choice("dev", name="Dev - Higher quality"),
        ],
        default="schnell",
    ).execute()

    if model == "schnell":
        steps_default = 4
        steps_msg = "Steps (schnell works well with 4):"
    else:
        steps_default = 20
        steps_msg = "Steps (dev works well with 20-50):"

    steps = inquirer.number(
        message=steps_msg, min_allowed=1, max_allowed=100, default=steps_default
    ).execute()

    filename = inquirer.text(
        message="Enter output filename (without extension):", default="image"
    ).execute()

    cmd = f'uv run flux-cli --prompt "{prompt}" --model {model} --steps {steps} --output var/static/flux/{filename}.png'
    return cmd


def configure_rag():
    """Interactive configuration for RAG pipeline."""
    console.print("\n[bold cyan]🔍 RAG Configuration[/bold cyan]\n")

    vdb_path = Path("models/indexes/vdb.npz")
    if not vdb_path.exists():
        console.print("[red]Vector database not found at models/indexes/vdb.npz[/red]")
        console.print("[yellow]You need to ingest documents first.[/yellow]")
        return None

    use_reranker = inquirer.confirm(
        message="Use reranker? (slower but more accurate)", default=False
    ).execute()

    top_k = inquirer.number(
        message="Number of documents to retrieve:", min_allowed=1, max_allowed=20, default=5
    ).execute()

    max_tokens = inquirer.number(
        message="Max tokens for answer:", min_allowed=128, max_allowed=2048, default=512
    ).execute()

    cmd_parts = ["uv run rag-cli", f"--top-k {top_k}", f"--max-tokens {max_tokens}"]

    if not use_reranker:
        cmd_parts.append("--no-reranker")

    cmd = " ".join(cmd_parts)

    console.print(f"\n[green]Starting RAG CLI (interactive mode)[/green]")
    console.print(f"[dim]Command: {cmd}[/dim]\n")

    return cmd


def run_pipeline(pipeline_id: str):
    """Configure and run a pipeline."""
    pipeline = PIPELINES[pipeline_id]
    console.print(f"\n{pipeline['emoji']}  [bold]{pipeline['name']}[/bold]")
    console.print(f"[dim]{pipeline['description']}[/dim]\n")

    cmd = None
    if pipeline_id == "whisper":
        cmd = configure_whisper()
    elif pipeline_id == "musicgen":
        cmd = configure_musicgen()
    elif pipeline_id == "flux":
        cmd = configure_flux()
    elif pipeline_id == "rag":
        cmd = configure_rag()
    elif pipeline_id == "bench":
        console.print("[yellow]Benchmark CLI doesn't have interactive config yet[/yellow]")
        cmd = "uv run bench-cli --help"

    if cmd is None:
        input("\n[dim]Press Enter to return to main menu...[/dim]")
        return

    console.print(f"\n[bold]Command to execute:[/bold]")
    console.print(f"[cyan]{cmd}[/cyan]\n")

    confirm = inquirer.confirm(message="Execute this command?", default=True).execute()

    if confirm:
        console.print("\n[green]Executing...[/green]\n")
        try:
            subprocess.run(cmd, shell=True, check=True)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        except subprocess.CalledProcessError as e:
            console.print(f"\n[red]Command failed with exit code {e.returncode}[/red]")

        input("\n[dim]Press Enter to return to main menu...[/dim]")


def main_menu():
    """Display and handle the main menu."""
    while True:
        console.clear()
        show_header()

        action = inquirer.select(
            message="What would you like to do?",
            choices=[
                Separator("═══ PIPELINES ═══"),
                Choice("rag", name="🔍 RAG - Question Answering"),
                Choice("flux", name="🎨 Flux - Image Generation"),
                Choice("musicgen", name="🎵 MusicGen - Audio Generation"),
                Choice("whisper", name="🎙️  Whisper - Speech-to-Text"),
                Choice("bench", name="📊 Benchmark - Performance Testing"),
                Separator("═══ MODEL MANAGEMENT ═══"),
                Choice("download", name="📥 Download Models"),
                Choice("models", name="📦 View Available Models"),
                Choice("cache", name="💾 View HuggingFace Cache"),
                Choice("delete", name="🗑️  Delete Cached Models"),
                Separator("═══ SYSTEM ═══"),
                Choice("system", name="💻 System Information"),
                Choice("cleanup", name="🧹 Clean Memory (MLX)"),
                Separator("═══ OTHER ═══"),
                Choice("exit", name="🚪 Exit"),
            ],
            default="whisper",
        ).execute()

        if action == "exit":
            console.print("\n[cyan]👋 Goodbye![/cyan]\n")
            break
        elif action == "models":
            console.clear()
            show_header()
            show_models_menu()
        elif action == "cache":
            console.clear()
            show_header()
            show_cache_info()
        elif action == "delete":
            console.clear()
            show_header()
            delete_cached_models()
        elif action == "download":
            console.clear()
            show_header()
            download_model()
        elif action == "system":
            console.clear()
            show_header()
            show_system_info()
        elif action == "cleanup":
            console.print("\n[bold]🧹 Cleaning memory...[/bold]\n")
            gc.collect()
            console.print("[green]✓ Memory cleanup complete[/green]")
            input("\n[dim]Press Enter to continue...[/dim]")
        else:
            run_pipeline(action)


def cleanup_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    console.print("\n\n[yellow]🧹 Cleaning up...[/yellow]")
    gc.collect()
    console.print("[green]✅ Cleanup complete. Bye![/green]\n")
    sys.exit(0)


def main() -> None:
    """Entry point for mlxlab CLI."""
    signal.signal(signal.SIGINT, cleanup_handler)

    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[cyan]👋 Goodbye![/cyan]\n")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

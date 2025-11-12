#!/usr/bin/env python3
"""
MLX Lab - Interactive CLI for MLX pipelines
Unified interface for RAG, Flux, MusicGen, Whisper, and more.
"""

import gc
import signal
import sys
from pathlib import Path
from typing import Optional

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from rich.console import Console
from rich.panel import Panel
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

MODELS = {
    "musicgen": ["facebook/musicgen-small (5.4GB)"],
    "whisper": [
        "mlx-community/whisper-tiny (~39MB) - Fast, good for testing",
        "mlx-community/whisper-base (~74MB) - Balanced",
        "mlx-community/whisper-small (~244MB) - Better accuracy",
        "mlx-community/whisper-large-v3 (~1.5GB) - Best accuracy",
    ],
    "flux": ["schnell (23GB) - Fast", "dev (23GB) - High quality"],
    "rag": ["Phi-3-mini-4k-instruct-4bit", "mxbai-rerank-large-v2"],
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


def show_system_info():
    """Display system information and available models."""
    import subprocess

    table = Table(title="System Information", show_header=True, header_style="bold magenta")
    table.add_column("Resource", style="cyan")
    table.add_column("Status", style="green")

    # Get memory info on macOS
    try:
        vm_stat = subprocess.check_output(["vm_stat"]).decode()
        # Parse memory info (simplified)
        table.add_row("Platform", "macOS (Apple Silicon)")
        table.add_row("MLX Framework", "✓ Available")
    except Exception:
        table.add_row("Platform", "Unknown")

    # Check models directory
    models_path = Path("mlx-models")
    if models_path.exists():
        model_count = len(list(models_path.iterdir()))
        table.add_row("Local Models", f"{model_count} directories")
    else:
        table.add_row("Local Models", "Not found")

    # Check var directories
    var_path = Path("var")
    if var_path.exists():
        source_audios = len(list((var_path / "source_audios").glob("*"))) if (var_path / "source_audios").exists() else 0
        transcripts = len(list((var_path / "transcripts").glob("*"))) if (var_path / "transcripts").exists() else 0
        music_outputs = len(list((var_path / "music_output").glob("*"))) if (var_path / "music_output").exists() else 0

        table.add_row("Source Audio Files", str(source_audios))
        table.add_row("Transcripts", str(transcripts))
        table.add_row("Generated Music", str(music_outputs))

    console.print(table)
    console.print()


def show_models_menu():
    """Show available models for each pipeline."""
    console.print("\n[bold cyan]📦 Available Models by Pipeline[/bold cyan]\n")

    for pipeline, models in MODELS.items():
        console.print(f"[bold yellow]{pipeline.upper()}[/bold yellow]")
        for model in models:
            console.print(f"  • {model}")
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
    audio_files = [f for f in audio_files if f.suffix.lower() in [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm"]]

    if not audio_files:
        console.print("[red]No audio files found in var/source_audios/[/red]")
        return None

    # Show file count
    console.print(f"[green]Found {len(audio_files)} audio files[/green]\n")

    # File selection
    file_choice = inquirer.select(
        message="Select audio file:",
        choices=[
            Choice("all", name="🎵 Transcribe all files"),
            Separator(),
        ] + [Choice(str(f), name=f"📄 {f.name}") for f in audio_files[:20]],  # Limit to 20 for display
        default="all",
    ).execute()

    # Model selection
    model = inquirer.select(
        message="Select Whisper model:",
        choices=[
            Choice("mlx-community/whisper-tiny", name="Tiny (~39MB) - Fastest"),
            Choice("mlx-community/whisper-base", name="Base (~74MB) - Balanced"),
            Choice("mlx-community/whisper-small", name="Small (~244MB) - Better accuracy"),
            Choice("mlx-community/whisper-large-v3", name="Large-v3 (~1.5GB) - Best accuracy"),
        ],
        default="mlx-community/whisper-tiny",
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
            message="Select language:",
            choices=LANGUAGES,
            default="English",
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

    # Prompt
    prompt = inquirer.text(
        message="Enter music description:",
        default="upbeat electronic melody",
    ).execute()

    # Duration (in steps)
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

    # Output filename
    use_custom_name = inquirer.confirm(
        message="Use custom output filename?", default=False
    ).execute()

    output_arg = ""
    if use_custom_name:
        filename = inquirer.text(
            message="Enter filename (without extension):",
            default="music",
        ).execute()
        output_arg = f"--output var/music_output/{filename}.wav"
    else:
        output_arg = "--output-dir var/music_output --prefix musicgen"

    # Build command
    cmd = f'uv run musicgen-cli --prompt "{prompt}" --max-steps {max_steps} {output_arg}'
    return cmd


def configure_flux():
    """Interactive configuration for Flux pipeline."""
    console.print("\n[bold cyan]🎨 Flux Configuration[/bold cyan]\n")

    # Prompt
    prompt = inquirer.text(
        message="Enter image description:",
        default="a beautiful landscape at sunset",
    ).execute()

    # Model variant
    model = inquirer.select(
        message="Select Flux model:",
        choices=[
            Choice("schnell", name="Schnell - Fast generation"),
            Choice("dev", name="Dev - Higher quality"),
        ],
        default="schnell",
    ).execute()

    # Number of steps
    if model == "schnell":
        steps_default = 4
        steps_msg = "Steps (schnell works well with 4):"
    else:
        steps_default = 20
        steps_msg = "Steps (dev works well with 20-50):"

    steps = inquirer.number(
        message=steps_msg,
        min_allowed=1,
        max_allowed=100,
        default=steps_default,
    ).execute()

    # Output filename
    filename = inquirer.text(
        message="Enter output filename (without extension):",
        default="image",
    ).execute()

    # Build command
    cmd = f'uv run flux-cli --prompt "{prompt}" --model {model} --steps {steps} --output var/static/flux/{filename}.png'
    return cmd


def configure_rag():
    """Interactive configuration for RAG pipeline."""
    console.print("\n[bold cyan]🔍 RAG Configuration[/bold cyan]\n")

    # Check for VDB
    vdb_path = Path("models/indexes/vdb.npz")
    if not vdb_path.exists():
        console.print("[red]Vector database not found at models/indexes/vdb.npz[/red]")
        console.print("[yellow]You need to ingest documents first.[/yellow]")
        return None

    # Reranker option
    use_reranker = inquirer.confirm(
        message="Use reranker? (slower but more accurate)", default=False
    ).execute()

    # Top-k
    top_k = inquirer.number(
        message="Number of documents to retrieve:",
        min_allowed=1,
        max_allowed=20,
        default=5,
    ).execute()

    # Max tokens
    max_tokens = inquirer.number(
        message="Max tokens for answer:",
        min_allowed=128,
        max_allowed=2048,
        default=512,
    ).execute()

    # Build command
    cmd_parts = [
        "uv run rag-cli",
        f"--top-k {top_k}",
        f"--max-tokens {max_tokens}",
    ]

    if not use_reranker:
        cmd_parts.append("--no-reranker")

    cmd = " ".join(cmd_parts)

    console.print(f"\n[green]Starting RAG CLI (interactive mode)[/green]")
    console.print(f"[dim]Command: {cmd}[/dim]\n")

    return cmd


def run_pipeline(pipeline_id: str):
    """Configure and run a pipeline."""
    import subprocess

    pipeline = PIPELINES[pipeline_id]
    console.print(f"\n{pipeline['emoji']}  [bold]{pipeline['name']}[/bold]")
    console.print(f"[dim]{pipeline['description']}[/dim]\n")

    # Configure based on pipeline
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

    # Confirm execution
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
                Separator("═══ INFO ═══"),
                Choice("models", name="📦 View Available Models"),
                Choice("system", name="💻 System Information"),
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
        elif action == "system":
            console.clear()
            show_header()
            show_system_info()
            input("\n[dim]Press Enter to continue...[/dim]")
        else:
            # Run pipeline
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

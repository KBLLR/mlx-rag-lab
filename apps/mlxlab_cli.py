#!/usr/bin/env python3
"""
MLX Lab v2 - Interactive CLI for MLX pipelines
Unified interface with model management, quantization, and cache control.
"""

import gc
import shlex
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

from experiments.dataset_generation.generate_qa_dataset import (
    QAGenerationConfig,
    generate_qa_dataset,
)
from ui import get_console, Card, show_card_menu, run_ui_playground, APP_METADATA

console = get_console()

# Pipeline ASCII art headers
PIPELINE_HEADERS = {
    "rag": {
        "ascii": """
    ██████╗  █████╗  ██████╗
    ██╔══██╗██╔══██╗██╔════╝
    ██████╔╝███████║██║  ███╗
    ██╔══██╗██╔══██║██║   ██║
    ██║  ██║██║  ██║╚██████╔╝
    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝
        """,
        "color": "bold magenta",
    },
    "flux": {
        "ascii": """
    ███████╗██╗     ██╗   ██╗██╗  ██╗
    ██╔════╝██║     ██║   ██║╚██╗██╔╝
    █████╗  ██║     ██║   ██║ ╚███╔╝
    ██╔══╝  ██║     ██║   ██║ ██╔██╗
    ██║     ███████╗╚██████╔╝██╔╝ ██╗
    ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝
        """,
        "color": "bold cyan",
    },
    "musicgen": {
        "ascii": """
    ███╗   ███╗██╗   ██╗███████╗██╗ ██████╗
    ████╗ ████║██║   ██║██╔════╝██║██╔════╝
    ██╔████╔██║██║   ██║███████╗██║██║
    ██║╚██╔╝██║██║   ██║╚════██║██║██║
    ██║ ╚═╝ ██║╚██████╔╝███████║██║╚██████╗
    ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝ ╚═════╝
        """,
        "color": "bold green",
    },
    "whisper": {
        "ascii": """
    ██╗    ██╗██╗  ██╗██╗███████╗██████╗ ███████╗██████╗
    ██║    ██║██║  ██║██║██╔════╝██╔══██╗██╔════╝██╔══██╗
    ██║ █╗ ██║███████║██║███████╗██████╔╝█████╗  ██████╔╝
    ██║███╗██║██╔══██║██║╚════██║██╔═══╝ ██╔══╝  ██╔══██╗
    ╚███╔███╔╝██║  ██║██║███████║██║     ███████╗██║  ██║
     ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝
        """,
        "color": "bold yellow",
    },
    "bench": {
        "ascii": """
    ██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗
    ██╔══██╗██╔════╝████╗  ██║██╔════╝██║  ██║
    ██████╔╝█████╗  ██╔██╗ ██║██║     ███████║
    ██╔══██╗██╔══╝  ██║╚██╗██║██║     ██╔══██║
    ██████╔╝███████╗██║ ╚████║╚██████╗██║  ██║
    ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝
        """,
        "color": "bold red",
    },
    "ingest": {
        "ascii": """
    ██╗███╗   ██╗ ██████╗ ███████╗███████╗████████╗
    ██║████╗  ██║██╔════╝ ██╔════╝██╔════╝╚══██╔══╝
    ██║██╔██╗ ██║██║  ███╗█████╗  ███████╗   ██║
    ██║██║╚██╗██║██║   ██║██╔══╝  ╚════██║   ██║
    ██║██║ ╚████║╚██████╔╝███████╗███████║   ██║
    ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚══════╝   ╚═╝
        """,
        "color": "bold blue",
    },
    "classify": {
        "ascii": """
     ██████╗██╗      █████╗ ███████╗███████╗██╗███████╗██╗   ██╗
    ██╔════╝██║     ██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝
    ██║     ██║     ███████║███████╗███████╗██║█████╗   ╚████╔╝
    ██║     ██║     ██╔══██║╚════██║╚════██║██║██╔══╝    ╚██╔╝
    ╚██████╗███████╗██║  ██║███████║███████║██║██║        ██║
     ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝        ╚═╝
        """,
        "color": "bold bright_magenta",
    },
    "chat": {
        "ascii": """
     ██████╗██╗  ██╗ █████╗ ████████╗
    ██╔════╝██║  ██║██╔══██╗╚══██╔══╝
    ██║     ███████║███████║   ██║
    ██║     ██╔══██║██╔══██║   ██║
    ╚██████╗██║  ██║██║  ██║   ██║
     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝
        """,
        "color": "bold green",
    },
    "voice_chat": {
        "ascii": """
    ██╗   ██╗ ██████╗ ██╗ ██████╗███████╗
    ██║   ██║██╔═══██╗██║██╔════╝██╔════╝
    ██║   ██║██║   ██║██║██║     █████╗
    ╚██╗ ██╔╝██║   ██║██║██║     ██╔══╝
     ╚████╔╝ ╚██████╔╝██║╚██████╗███████╗
      ╚═══╝   ╚═════╝ ╚═╝ ╚═════╝╚══════╝
        """,
        "color": "bold bright_green",
    },
    "sts_avatar": {
        "ascii": """
    ███████╗████████╗███████╗     █████╗ ██╗   ██╗ █████╗ ████████╗ █████╗ ██████╗
    ██╔════╝╚══██╔══╝██╔════╝    ██╔══██╗██║   ██║██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗
    ███████╗   ██║   ███████╗    ███████║██║   ██║███████║   ██║   ███████║██████╔╝
    ╚════██║   ██║   ╚════██║    ██╔══██║╚██╗ ██╔╝██╔══██║   ██║   ██╔══██║██╔══██╗
    ███████║   ██║   ███████║    ██║  ██║ ╚████╔╝ ██║  ██║   ██║   ██║  ██║██║  ██║
    ╚══════╝   ╚═╝   ╚══════╝    ╚═╝  ╚═╝  ╚═══╝  ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝
        """,
        "color": "bold bright_cyan",
    },
}

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
    "ingest": {
        "name": "Ingest - Build Vector Index",
        "description": "Create vector database from documents",
        "emoji": "📚",
        "command": "ingest-cli",
    },
    "classify": {
        "name": "Classify - Text Classification",
        "description": "Sentiment analysis and text classification",
        "emoji": "🏷️",
        "command": "classify-cli",
    },
    "chat": {
        "name": "Chat - Conversational AI",
        "description": "Chat interface with GPT-OSS 20B or other LLMs",
        "emoji": "💬",
        "command": "chat-cli",
    },
    "voice_chat": {
        "name": "Voice Chat - Text to Speech",
        "description": "Chat with TTS audio responses (Marvis/Kokoro)",
        "emoji": "🗣️",
        "command": "voice-chat-cli",
    },
    "sts_avatar": {
        "name": "STS Avatar - Speech to Speech",
        "description": "Full voice pipeline with viseme output for avatars",
        "emoji": "🎭",
        "command": "sts-avatar-cli",
    },
}

# Correct model names with real available models
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
    },
    "musicgen": [
        ("facebook/musicgen-small", "~1.2GB", "300M params, fast generation"),
        ("facebook/musicgen-medium", "~4GB", "1.5B params, better quality"),
        ("facebook/musicgen-large", "~8GB", "3.3B params, best quality"),
        ("facebook/musicgen-melody", "~4GB", "Melody conditioning support"),
        ("facebook/musicgen-stereo-small", "~1.2GB", "Stereo output"),
        ("facebook/musicgen-stereo-medium", "~4GB", "Stereo output, better quality"),
        ("facebook/musicgen-stereo-large", "~8GB", "Stereo output, best quality"),
    ],
    "flux": [
        ("argmaxinc/mlx-FLUX.1-schnell", "~23GB", "Fast, 4-step generation"),
        ("argmaxinc/mlx-FLUX.1-schnell-4bit-quantized", "~6GB", "4-bit quantized, 75% smaller"),
        ("argmaxinc/mlx-FLUX.1-dev", "~23GB", "High quality, 20-50 steps"),
    ],
    "rag": [
        ("mlx-community/Phi-3-mini-4k-instruct-4bit", "~2.4GB", "Quantized LLM"),
        ("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx", "~12GB", "GPT-OSS 20B (MXFP4 4-bit)"),
        ("mlx-community/mxbai-rerank-large-v2", "~1.2GB", "Cross-encoder reranker"),
        ("mlx-community/Llama-3.2-3B-Instruct-4bit", "~1.9GB", "Alternative LLM"),
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
    console.print("[dim]Local-first MLX pipelines on Apple Silicon[/dim]\n", justify="left")


def get_cache_info():
    """Get HuggingFace cache information."""
    try:
        cache_info = scan_cache_dir()
        return cache_info
    except Exception as e:
        console.print(f"[yellow]Could not scan cache: {e}[/yellow]")
        return None


def is_model_cached(model_id: str) -> bool:
    """Check if a model is already cached."""
    cache_info = get_cache_info()
    if not cache_info:
        return False

    cached_repos = [repo.repo_id for repo in cache_info.repos]
    return model_id in cached_repos


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
    total_size = sum(repo.size_on_disk for repo in cache_info.repos if repo.repo_id in selected)

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

        strategy = cache_info.delete_revisions(
            *[
                rev.commit_hash
                for repo in cache_info.repos
                if repo.repo_id in selected
                for rev in repo.revisions
            ]
        )

        console.print(f"[green]✓ Deleted {len(selected)} model(s)[/green]")
        console.print(f"[green]✓ Freed {strategy.expected_freed_size / 1e9:.2f} GB[/green]")
    else:
        console.print("[yellow]Deletion cancelled[/yellow]")

    input("\n[dim]Press Enter to continue...[/dim]")


def download_model():
    """Interactive model download with progress and cache detection."""
    console.print("\n[bold cyan]📥 Download Model[/bold cyan]\n")

    # Select pipeline
    pipeline_choice = inquirer.select(
        message="Select pipeline:",
        choices=[
            Choice("whisper", name="Whisper - Speech-to-Text"),
            Choice("musicgen", name="MusicGen - Audio Generation"),
            Choice("flux", name="Flux - Image Generation"),
            Choice("rag", name="RAG - Language Models"),
        ],
        default="whisper",
    ).execute()

    model_id = None

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

        # Select specific model with cache status
        model_choices = []
        for model, size, desc in MODELS["whisper"][category]:
            cached = is_model_cached(model)
            status = " ✓ Downloaded" if cached else ""
            model_choices.append(
                Choice(model, name=f"{model.split('/')[-1]} - {size} - {desc}{status}")
            )

        model_id = inquirer.select(
            message="Select model to download:",
            choices=model_choices,
        ).execute()

    elif pipeline_choice == "musicgen":
        # MusicGen models
        model_choices = []
        for model, size, desc in MODELS["musicgen"]:
            cached = is_model_cached(model)
            status = " ✓ Downloaded" if cached else ""
            model_choices.append(
                Choice(model, name=f"{model.split('/')[-1]} - {size} - {desc}{status}")
            )

        model_id = inquirer.select(
            message="Select MusicGen model:",
            choices=model_choices,
        ).execute()

    elif pipeline_choice == "flux":
        # Flux models
        model_choices = []
        for model, size, desc in MODELS["flux"]:
            cached = is_model_cached(model)
            status = " ✓ Downloaded" if cached else ""
            model_choices.append(
                Choice(model, name=f"{model.split('/')[-1]} - {size} - {desc}{status}")
            )

        model_id = inquirer.select(
            message="Select Flux model:",
            choices=model_choices,
        ).execute()

    elif pipeline_choice == "rag":
        # RAG models
        model_choices = []
        for model, size, desc in MODELS["rag"]:
            cached = is_model_cached(model)
            status = " ✓ Downloaded" if cached else ""
            model_choices.append(
                Choice(model, name=f"{model.split('/')[-1]} - {size} - {desc}{status}")
            )

        model_id = inquirer.select(
            message="Select RAG model:",
            choices=model_choices,
        ).execute()

    if model_id is None:
        input("\n[dim]Press Enter to continue...[/dim]")
        return

    # Check if already cached
    if is_model_cached(model_id):
        console.print(f"\n[yellow]⚠️  Model already downloaded: {model_id}[/yellow]")
        redownload = inquirer.confirm(
            message="Re-download anyway?",
            default=False,
        ).execute()
        if not redownload:
            input("\n[dim]Press Enter to continue...[/dim]")
            return

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

    # Note: Quantized versions are available by adding -4bit or -8bit suffixes
    console.print("\n[dim]Note: Many models have quantized variants (add -4bit or -8bit to model name)[/dim]")

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
        filename = inquirer.text(
            message="Enter filename (without extension):", default="music"
        ).execute()
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


def get_indexed_files():
    """Scan all metadata files and return set of already-indexed PDF paths."""
    indexed_files = set()
    indexes_dir = Path("var/indexes")

    if not indexes_dir.exists():
        return indexed_files

    # Find all metadata files
    for meta_file in indexes_dir.rglob("*.meta.json"):
        try:
            with open(meta_file) as f:
                import json
                metadata = json.load(f)
                # Add all document_names to the set
                if "document_names" in metadata:
                    for doc in metadata["document_names"]:
                        indexed_files.add(Path(doc).resolve())
        except Exception:
            continue

    return indexed_files


def scan_new_files():
    """Scan for new PDF files that haven't been indexed yet."""
    source_dir = Path("var/source_docs")

    if not source_dir.exists():
        return {}, {}

    # Get all PDFs grouped by bank (subdirectory)
    all_files_by_bank = {}
    for pdf_file in source_dir.rglob("*.pdf"):
        # Get bank name (immediate parent directory)
        bank = pdf_file.parent.name
        if bank not in all_files_by_bank:
            all_files_by_bank[bank] = []
        all_files_by_bank[bank].append(pdf_file.resolve())

    # Get already indexed files
    indexed = get_indexed_files()

    # Find new files
    new_files_by_bank = {}
    for bank, files in all_files_by_bank.items():
        new_files = [f for f in files if f not in indexed]
        if new_files:
            new_files_by_bank[bank] = new_files

    return new_files_by_bank, all_files_by_bank


def configure_ingest():
    """Interactive configuration for ingestion pipeline with smart file detection."""
    console.print("\n[bold blue]📚 Ingestion Configuration[/bold blue]\n")

    # Scan for new files
    new_files_by_bank, all_files_by_bank = scan_new_files()

    if not all_files_by_bank:
        console.print("[yellow]No PDF files found in var/source_docs/[/yellow]\n")
        console.print("[dim]To ingest documents:[/dim]")
        console.print("[dim]  1. Create knowledge banks: var/source_docs/<bank-name>/[/dim]")
        console.print("[dim]  2. Place PDFs in each bank directory[/dim]")
        console.print("[dim]  3. Run ingestion to build indexes[/dim]")
        input("\n[dim]Press Enter to continue...[/dim]")
        return None

    # Show statistics
    total_files = sum(len(files) for files in all_files_by_bank.values())
    total_new = sum(len(files) for files in new_files_by_bank.values())
    total_indexed = total_files - total_new

    console.print(f"[cyan]Found {len(all_files_by_bank)} knowledge banks with {total_files} PDFs[/cyan]")
    console.print(f"[green]✓ Already indexed: {total_indexed} files[/green]")
    console.print(f"[yellow]⚡ New files to ingest: {total_new} files[/yellow]\n")

    if not new_files_by_bank:
        console.print("[green]✓ All files are already indexed![/green]")

        reindex = inquirer.confirm(
            message="Re-index everything anyway?", default=False
        ).execute()

        if not reindex:
            input("\n[dim]Press Enter to continue...[/dim]")
            return None
    else:
        # Show new files by bank
        console.print("[bold]New files to ingest:[/bold]")
        for bank, files in new_files_by_bank.items():
            console.print(f"  [cyan]{bank}:[/cyan] {len(files)} new files")

    console.print()

    # Choose ingestion mode
    mode = inquirer.select(
        message="What would you like to ingest?",
        choices=[
            Choice("new", name="⚡ Only new files (smart mode)"),
            Choice("all", name="🔄 Re-index everything"),
            Choice("select", name="📂 Select specific banks"),
            Choice("cancel", name="❌ Cancel"),
        ],
        default="new"
    ).execute()

    if mode == "cancel":
        return None

    if mode == "select":
        # Let user choose which banks to process
        bank_choices = [
            Choice(bank, name=f"{bank} ({len(files)} files)")
            for bank, files in all_files_by_bank.items()
        ]
        selected_banks = inquirer.checkbox(
            message="Select banks to ingest:",
            choices=bank_choices,
        ).execute()

        if not selected_banks:
            console.print("[yellow]No banks selected.[/yellow]")
            input("\n[dim]Press Enter to continue...[/dim]")
            return None

        # Build command for selected banks
        cmd = f"uv run ingest-cli --banks-root var/source_docs --output-dir var/indexes"
        console.print(f"\n[dim]Note: Will process selected banks: {', '.join(selected_banks)}[/dim]")

    elif mode == "new":
        # Ingest only new files (create temporary list)
        if not new_files_by_bank:
            console.print("[yellow]No new files to ingest.[/yellow]")
            input("\n[dim]Press Enter to continue...[/dim]")
            return None

        cmd = f"uv run ingest-cli --banks-root var/source_docs --output-dir var/indexes"
        console.print(f"\n[dim]Will process {total_new} new files across {len(new_files_by_bank)} banks[/dim]")

    else:  # mode == "all"
        cmd = f"uv run ingest-cli --banks-root var/source_docs --output-dir var/indexes"
        console.print(f"\n[dim]Will re-index all {total_files} files across {len(all_files_by_bank)} banks[/dim]")

    return cmd


def configure_rag():
    """Interactive configuration for RAG pipeline."""
    console.print("\n[bold cyan]🔍 RAG Configuration[/bold cyan]\n")

    # Scan for available vector databases
    indexes_dir = Path("var/indexes")
    if not indexes_dir.exists():
        console.print("[red]No indexes directory found at var/indexes/[/red]")
        console.print("[yellow]You need to ingest documents first.[/yellow]\n")
        console.print("[dim]To create a vector database:[/dim]")
        console.print("[dim]  1. Place your documents in var/source_docs/<bank-name>/[/dim]")
        console.print("[dim]  2. Run: 📚 Ingest - Build Vector Index from the main menu[/dim]")
        console.print("[dim]  3. This will create indexes at var/indexes/<bank-name>/vdb.npz[/dim]")
        input("\n[dim]Press Enter to continue...[/dim]")
        return None

    # Find all available banks
    available_banks = []

    # Check for bank-specific indexes
    for bank_dir in sorted(indexes_dir.iterdir()):
        if bank_dir.is_dir():
            vdb_file = bank_dir / "vdb.npz"
            if vdb_file.exists():
                available_banks.append((str(vdb_file), bank_dir.name))

    # Check for old combined index
    combined_vdb = indexes_dir / "vdb.npz"
    if combined_vdb.exists():
        available_banks.insert(0, (str(combined_vdb), "combined (all banks)"))

    if not available_banks:
        console.print("[red]No vector databases found in var/indexes/[/red]")
        console.print("[yellow]You need to ingest documents first.[/yellow]\n")
        input("\n[dim]Press Enter to continue...[/dim]")
        return None

    # Let user choose which bank to query
    bank_choices = [
        Choice(path, name=f"📁 {name}")
        for path, name in available_banks
    ]

    selected_vdb = inquirer.select(
        message="Select knowledge bank to query:",
        choices=bank_choices,
        default=bank_choices[0].value,
    ).execute()

    use_reranker = inquirer.confirm(
        message="Use reranker? (slower but more accurate)", default=False
    ).execute()

    top_k = inquirer.number(
        message="Number of documents to retrieve:", min_allowed=1, max_allowed=20, default=5
    ).execute()

    max_tokens = inquirer.number(
        message="Max tokens for answer:", min_allowed=128, max_allowed=2048, default=512
    ).execute()

    cmd_parts = [
        "uv run rag-cli",
        f"--vdb-path {selected_vdb}",
        f"--top-k {top_k}",
        f"--max-tokens {max_tokens}"
    ]

    if not use_reranker:
        cmd_parts.append("--no-reranker")

    cmd = " ".join(cmd_parts)

    console.print(f"\n[green]Starting RAG CLI (interactive mode)[/green]")
    console.print(f"[dim]Command: {cmd}[/dim]\n")

    return cmd


def configure_classify():
    """Interactive configuration for classification pipeline."""
    console.print("\n[bold cyan]🏷️  Text Classification Configuration[/bold cyan]\n")

    # Scan for available vector databases
    indexes_dir = Path("var/indexes")
    available_banks = []

    if indexes_dir.exists():
        # Check for bank-specific indexes
        for bank_dir in sorted(indexes_dir.iterdir()):
            if bank_dir.is_dir():
                vdb_file = bank_dir / "vdb.npz"
                if vdb_file.exists():
                    available_banks.append((str(vdb_file), bank_dir.name))

        # Check for old combined index
        combined_vdb = indexes_dir / "vdb.npz"
        if combined_vdb.exists():
            available_banks.insert(0, (str(combined_vdb), "combined (all banks)"))

    # Select classification mode
    mode = inquirer.select(
        message="Select classification mode:",
        choices=[
            Choice("sentiment", name="😊 Sentiment Analysis (positive/negative/neutral)"),
            Choice("emotion", name="❤️  Emotion Detection (joy/sadness/anger/fear/surprise)"),
            Choice("zero-shot", name="🎯 Zero-shot Classification (custom labels)"),
            Choice("interactive", name="💬 Interactive Mode (classify text in real-time)"),
        ],
        default="sentiment",
    ).execute()

    # Interactive mode doesn't need VDB
    if mode == "interactive":
        cmd = f"uv run classify-cli --mode interactive"
        console.print(f"\n[green]Starting Interactive Classification Mode[/green]")
        console.print(f"[dim]Type text to classify in real-time. Press Ctrl+C to exit.[/dim]\n")
        return cmd

    # Choose input source
    source = inquirer.select(
        message="Select input source:",
        choices=[
            Choice("vdb", name="📁 Vector Database Chunks"),
            Choice("text", name="📝 Single Text Input"),
            Choice("cancel", name="❌ Cancel"),
        ],
        default="vdb" if available_banks else "text",
    ).execute()

    if source == "cancel":
        return None

    cmd_parts = ["uv run classify-cli", f"--mode {mode}"]

    if source == "vdb":
        if not available_banks:
            console.print("[red]No vector databases found in var/indexes/[/red]")
            console.print("[yellow]You need to ingest documents first, or use text input.[/yellow]\n")
            input("\n[dim]Press Enter to continue...[/dim]")
            return None

        # Let user choose which bank to classify
        bank_choices = [
            Choice(path, name=f"📁 {name}")
            for path, name in available_banks
        ]

        selected_vdb = inquirer.select(
            message="Select knowledge bank to classify:",
            choices=bank_choices,
            default=bank_choices[0].value,
        ).execute()

        cmd_parts.append(f"--vdb-path {selected_vdb}")

    elif source == "text":
        text = inquirer.text(
            message="Enter text to classify:",
            default="This is a great product! I love it!"
        ).execute()

        if not text.strip():
            console.print("[yellow]No text provided.[/yellow]")
            input("\n[dim]Press Enter to continue...[/dim]")
            return None

        cmd_parts.append(f'--text "{text}"')

    # Zero-shot mode requires labels
    if mode == "zero-shot":
        labels_input = inquirer.text(
            message="Enter classification labels (space-separated):",
            default="technology science politics sports"
        ).execute()

        if labels_input.strip():
            cmd_parts.append(f"--labels {labels_input}")
        else:
            console.print("[yellow]Zero-shot mode requires labels. Using sentiment analysis instead.[/yellow]")
            cmd_parts[1] = "--mode sentiment"

    # Additional options
    top_k = int(inquirer.number(
        message="Number of top predictions to show:",
        min_allowed=1,
        max_allowed=10,
        default=3
    ).execute())
    cmd_parts.append(f"--top-k {top_k}")

    min_score = float(inquirer.number(
        message="Minimum confidence threshold (0.0-1.0):",
        min_allowed=0.0,
        max_allowed=1.0,
        default=0.0,
        float_allowed=True
    ).execute())

    if min_score > 0:
        cmd_parts.append(f"--min-score {min_score}")

    # Ask if user wants to save results
    save_output = inquirer.confirm(
        message="Save results to JSON file?",
        default=False
    ).execute()

    if save_output:
        output_path = inquirer.text(
            message="Output file path:",
            default="var/classifications/results.json"
        ).execute()
        cmd_parts.append(f"--output {output_path}")

    cmd = " ".join(cmd_parts)

    console.print(f"\n[green]Starting Classification Pipeline[/green]")
    console.print(f"[dim]Command: {cmd}[/dim]\n")

    return cmd


def configure_chat():
    """Interactive configuration for chat pipeline."""
    console.print("\n[bold green]💬 Chat Configuration[/bold green]\n")

    # Check if local GPT-OSS exists
    local_gpt_oss = Path("mlx-models/gpt-oss-20b-mxfp4")
    default_model = str(local_gpt_oss) if local_gpt_oss.exists() else "mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx"

    # Model selection
    model_choices = [
        Choice(str(local_gpt_oss), name=f"🚀 GPT-OSS 20B (local) - {local_gpt_oss}") if local_gpt_oss.exists() else None,
        Choice("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx", name="☁️  GPT-OSS 20B (HuggingFace)"),
        Choice("mlx-community/Phi-3-mini-4k-instruct-4bit", name="⚡ Phi-3 Mini 4k (faster, smaller)"),
        Choice("mlx-community/Llama-3.2-3B-Instruct-4bit", name="🦙 Llama 3.2 3B"),
    ]
    model_choices = [c for c in model_choices if c is not None]

    model_id = inquirer.select(
        message="Select chat model:",
        choices=model_choices,
        default=default_model if any(c.value == default_model for c in model_choices) else model_choices[0].value
    ).execute()

    # Generation settings
    max_tokens = int(inquirer.number(
        message="Max tokens per response:",
        min_allowed=128,
        max_allowed=2048,
        default=512
    ).execute())

    temperature = float(inquirer.number(
        message="Temperature (0.0-1.0, higher = more creative):",
        min_allowed=0.0,
        max_allowed=1.0,
        default=0.7,
        float_allowed=True
    ).execute())

    stream = inquirer.confirm(
        message="Enable streaming (show tokens as they generate)?",
        default=False
    ).execute()

    save_chat = inquirer.confirm(
        message="Save conversation history on exit?",
        default=True
    ).execute()

    classify_on_exit = inquirer.confirm(
        message="Classify conversation (sentiment/topics) on exit?",
        default=True
    ).execute()

    # Build command
    cmd_parts = [
        "uv run chat-cli",
        f"--model-id {model_id}",
        f"--max-tokens {max_tokens}",
        f"--temperature {temperature}"
    ]

    if stream:
        cmd_parts.append("--stream")

    if save_chat:
        cmd_parts.append("--save-chat")

    if classify_on_exit:
        cmd_parts.append("--classify-on-exit")

    cmd = " ".join(cmd_parts)

    console.print(f"\n[green]Starting Chat Interface[/green]")
    console.print(f"[dim]Command: {cmd}[/dim]\n")
    console.print("[dim]Special commands in chat:[/dim]")
    console.print("[dim]  /clear  - Clear conversation history[/dim]")
    console.print("[dim]  /history - Show conversation history[/dim]")
    console.print("[dim]  /exit   - Exit chat[/dim]\n")

    return cmd


def configure_voice_chat():
    """Interactive configuration for voice chat pipeline."""
    console.print("\n[bold green]🗣️  Voice Chat Configuration[/bold green]\n")

    # Check if local GPT-OSS exists
    local_gpt_oss = Path("mlx-models/gpt-oss-20b-mxfp4")
    default_model = str(local_gpt_oss) if local_gpt_oss.exists() else "mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx"

    # Model selection
    model_choices = [
        Choice(str(local_gpt_oss), name=f"🚀 GPT-OSS 20B (local)") if local_gpt_oss.exists() else None,
        Choice("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx", name="☁️  GPT-OSS 20B (HuggingFace)"),
        Choice("mlx-community/Phi-3-mini-4k-instruct-4bit", name="⚡ Phi-3 Mini (faster)"),
    ]
    model_choices = [c for c in model_choices if c is not None]

    model_id = inquirer.select(
        message="Select chat model:",
        choices=model_choices,
        default=default_model if any(c.value == default_model for c in model_choices) else model_choices[0].value
    ).execute()

    # TTS Engine
    tts_engine = inquirer.select(
        message="Select TTS engine:",
        choices=[
            Choice("kokoro", name="🎭 Kokoro TTS (54 voices, phoneme output)"),
            Choice("marvis", name="🎤 Marvis TTS (simple, fast)"),
        ],
        default="kokoro"
    ).execute()

    # Voice selection (Kokoro only)
    tts_voice = "af_bella"
    if tts_engine == "kokoro":
        tts_voice = inquirer.select(
            message="Select voice:",
            choices=[
                Choice("af_bella", name="👩 Bella (American female)"),
                Choice("af_sarah", name="👩 Sarah (American female)"),
                Choice("am_adam", name="👨 Adam (American male)"),
                Choice("am_fenrir", name="👨 Fenrir (American male)"),
                Choice("bf_emma", name="👩 Emma (British female)"),
                Choice("bm_george", name="👨 George (British male)"),
            ],
            default="af_bella"
        ).execute()

    # Generation settings
    max_tokens = int(inquirer.number(
        message="Max tokens per response:",
        min_allowed=128,
        max_allowed=512,
        default=256
    ).execute())

    stream = inquirer.confirm(
        message="Stream text before audio synthesis?",
        default=True
    ).execute()

    live_mode = inquirer.confirm(
        message="Enable push-to-talk mode (hold Space to talk)?",
        default=False,
    ).execute()

    whisper_model = "mlx-community/whisper-large-v3-mlx"
    if live_mode:
        whisper_model = inquirer.select(
            message="Select Whisper/STT model for push-to-talk:",
            choices=[
                Choice("mlx-community/whisper-large-v3-mlx", name="🎯 Large-v3 (best accuracy)"),
                Choice("mlx-community/whisper-medium-mlx", name="⚡ Medium (balanced)"),
                Choice("mlx-community/whisper-small-mlx", name="🚀 Small (fast)"),
            ],
            default="mlx-community/whisper-large-v3-mlx",
        ).execute()

    # Build command
    cmd_parts = [
        "uv run voice-chat-cli",
        f"--chat-model {model_id}",
        f"--tts-engine {tts_engine}",
        f"--max-tokens {max_tokens}",
        f"--whisper-model {whisper_model}",
    ]

    if tts_engine == "kokoro":
        cmd_parts.append(f"--tts-voice {tts_voice}")

    if stream:
        cmd_parts.append("--stream")
    if live_mode:
        cmd_parts.append("--live")

    cmd = " ".join(cmd_parts)

    console.print(f"\n[green]Starting Voice Chat[/green]")
    console.print(f"[dim]Command: {cmd}[/dim]\n")

    return cmd


def configure_sts_avatar():
    """Interactive configuration for STS avatar pipeline."""
    console.print("\n[bold cyan]🎭 STS Avatar Configuration[/bold cyan]\n")

    def prompt_optional_int(message: str) -> Optional[int]:
        """Helper for optional integer prompts."""
        while True:
            raw_value = (
                inquirer.text(message=message, default="").execute().strip()
            )
            if raw_value == "":
                return None
            try:
                return int(raw_value)
            except ValueError:
                console.print("[red]Enter a number or leave blank[/red]")

    # Check if local GPT-OSS exists
    local_gpt_oss = Path("mlx-models/gpt-oss-20b-mxfp4")
    default_model = str(local_gpt_oss) if local_gpt_oss.exists() else "mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx"

    # Model selection
    model_choices = [
        Choice(str(local_gpt_oss), name=f"🚀 GPT-OSS 20B (local)") if local_gpt_oss.exists() else None,
        Choice("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx", name="☁️  GPT-OSS 20B (HuggingFace)"),
        Choice("mlx-community/Phi-3-mini-4k-instruct-4bit", name="⚡ Phi-3 Mini (faster)"),
    ]
    model_choices = [c for c in model_choices if c is not None]

    model_id = inquirer.select(
        message="Select chat model:",
        choices=model_choices,
        default=default_model if any(c.value == default_model for c in model_choices) else model_choices[0].value
    ).execute()

    # Whisper model
    whisper_model = inquirer.select(
        message="Select Whisper model:",
        choices=[
            Choice("mlx-community/whisper-large-v3-mlx", name="🎯 Large-v3 (best accuracy)"),
            Choice("mlx-community/whisper-medium-mlx", name="⚡ Medium (balanced)"),
            Choice("mlx-community/whisper-small-mlx", name="🚀 Small (fast)"),
        ],
        default="mlx-community/whisper-large-v3-mlx"
    ).execute()

    stt_backend = inquirer.select(
        message="Select STT backend:",
        choices=[
            Choice("whisper", name="🎧 MLX Whisper (no diarization)"),
            Choice("whisperx", name="🌀 WhisperX + diarization"),
        ],
        default="whisper",
    ).execute()

    diarize = False
    min_speakers = None
    max_speakers = None
    hf_token = ""
    speaker_voice_pool_input = ""

    if stt_backend == "whisperx":
        diarize = inquirer.confirm(
            message="Enable speaker diarization?",
            default=True,
        ).execute()
        if diarize:
            min_speakers = prompt_optional_int(
                "Minimum speakers (leave blank for auto):"
            )
            max_speakers = prompt_optional_int(
                "Maximum speakers (leave blank for auto):"
            )
            hf_token = inquirer.text(
                message="Hugging Face token for diarization (leave blank if already set in env):",
                default="",
            ).execute().strip()

    # TTS Engine
    tts_engine = inquirer.select(
        message="Select TTS engine:",
        choices=[
            Choice("kokoro", name="🎭 Kokoro TTS (with viseme output for avatars)"),
            Choice("marvis", name="🎤 Marvis TTS (audio only)"),
        ],
        default="kokoro"
    ).execute()

    # Voice selection (Kokoro only)
    tts_voice = "af_bella"
    if tts_engine == "kokoro":
        tts_voice = inquirer.select(
            message="Select voice:",
            choices=[
                Choice("af_bella", name="👩 Bella (American female)"),
                Choice("af_sarah", name="👩 Sarah (American female)"),
                Choice("am_adam", name="👨 Adam (American male)"),
                Choice("am_fenrir", name="👨 Fenrir (American male)"),
                Choice("bf_emma", name="👩 Emma (British female)"),
                Choice("bm_george", name="👨 George (British male)"),
                Choice("em_alex", name="👨 Alex (Spanish male)"),
            ],
            default="af_bella"
        ).execute()

    if stt_backend == "whisperx" and diarize and tts_engine == "kokoro":
        speaker_voice_pool_input = inquirer.text(
            message="Additional Kokoro voices for new speakers (comma-separated, blank to reuse base voice):",
            default="",
        ).execute().strip()

    # Generation settings
    max_tokens = int(inquirer.number(
        message="Max tokens per response:",
        min_allowed=128,
        max_allowed=512,
        default=256
    ).execute())

    stream = inquirer.confirm(
        message="Stream text responses?",
        default=True
    ).execute()

    # Build command
    cmd_parts = [
        "uv run sts-avatar-cli",
        f"--chat-model {model_id}",
        f"--whisper-model {whisper_model}",
        f"--stt-backend {stt_backend}",
        f"--tts-engine {tts_engine}",
        f"--max-tokens {max_tokens}"
    ]

    if tts_engine == "kokoro":
        cmd_parts.append(f"--tts-voice {tts_voice}")

    if stream:
        cmd_parts.append("--stream")

    if stt_backend == "whisperx":
        if diarize:
            cmd_parts.append("--diarize")
            if min_speakers is not None:
                cmd_parts.append(f"--min-speakers {min_speakers}")
            if max_speakers is not None:
                cmd_parts.append(f"--max-speakers {max_speakers}")
            if speaker_voice_pool_input:
                cmd_parts.append(
                    f"--speaker-voice-pool {shlex.quote(speaker_voice_pool_input)}"
                )
        if hf_token:
            cmd_parts.append(f"--hf-token {shlex.quote(hf_token)}")

    cmd = " ".join(cmd_parts)

    console.print(f"\n[green]Starting STS Avatar Pipeline[/green]")
    console.print(f"[dim]Command: {cmd}[/dim]\n")
    console.print("[bold]Usage:[/bold]")
    console.print("  - Provide audio file paths when prompted")
    console.print("  - Each response saved in var/sts_avatar/response_TIMESTAMP/")
    console.print("  - Contains: audio.wav, visemes.json, response.txt, transcription.txt")
    console.print("  - With diarization: + transcription_speakers.txt + speakers.json\n")

    return cmd


def configure_generators():
    """Generators hub (e.g., MLX Q&A dataset)."""
    while True:
        action = inquirer.select(
            message="Generators menu:",
            choices=[
                Choice("qa_dataset", name="🧪 Q&A Dataset (MLX models)"),
                Choice("coming_soon", name="🤖 Auto generator planner (coming soon)"),
                Choice("back", name="⬅️  Back to main menu"),
            ],
        ).execute()

        if action == "back":
            break
        elif action == "qa_dataset":
            run_qa_dataset_generator()
        else:
            console.print("\n[yellow]Hang tight, this one is on the roadmap.[/yellow]\n")


def run_qa_dataset_generator():
    """Interactive wrapper for experiments/dataset_generation."""
    default_cfg = QAGenerationConfig()

    source_dir_input = inquirer.text(
        message="Directory with PDFs:",
        default=str(default_cfg.source_docs_dir),
    ).execute().strip()
    source_dir = Path(source_dir_input or default_cfg.source_docs_dir)

    if not source_dir.exists():
        console.print(f"[red]Directory not found:[/red] {source_dir}")
        return

    pdf_files = sorted(source_dir.glob("*.pdf"))
    if not pdf_files:
        console.print(f"[red]No PDF files in {source_dir}. Add documents first.[/red]")
        return

    pdf_choices = [Choice("ALL", name="📂 All PDFs in directory")]
    pdf_choices += [Choice(str(p), name=p.name) for p in pdf_files]

    selected = inquirer.checkbox(
        message="Select PDFs to include (Space to toggle, Enter to confirm):",
        choices=pdf_choices,
        default=["ALL"],
    ).execute()

    if not selected or "ALL" in selected:
        selected_paths = pdf_files
    else:
        selected_paths = [Path(path) for path in selected]

    output_path_input = inquirer.text(
        message="Output dataset path:",
        default=str(default_cfg.output_dataset_path),
    ).execute().strip()
    output_path = Path(output_path_input or default_cfg.output_dataset_path)

    max_qa = int(
        inquirer.number(
            message="Max Q&A pairs per document:",
            default=default_cfg.max_qa_per_doc,
            min_allowed=1,
            max_allowed=200,
        ).execute()
    )

    min_chars = int(
        inquirer.number(
            message="Min characters per chunk:",
            default=default_cfg.min_chars_per_chunk,
            min_allowed=20,
            max_allowed=5000,
        ).execute()
    )

    question_model = (
        inquirer.text(
            message="Question model (MLX ID):",
            default=default_cfg.question_model,
        )
        .execute()
        .strip()
        or default_cfg.question_model
    )

    answer_model = (
        inquirer.text(
            message="Answer model (MLX ID):",
            default=default_cfg.answer_model,
        )
        .execute()
        .strip()
        or default_cfg.answer_model
    )

    cfg = QAGenerationConfig(
        source_docs_dir=source_dir,
        output_dataset_path=output_path,
        question_model=question_model,
        answer_model=answer_model,
        question_max_tokens=default_cfg.question_max_tokens,
        answer_max_tokens=default_cfg.answer_max_tokens,
        max_qa_per_doc=max_qa,
        min_chars_per_chunk=min_chars,
    )

    console.print(
        f"\n[cyan]Generating dataset from {len(selected_paths)} PDF(s)...[/cyan]"
    )

    try:
        generate_qa_dataset(config=cfg, pdf_paths=selected_paths)
        console.print(
            f"[green]Done! Dataset saved to {cfg.output_dataset_path}[/green]\n"
        )
    except Exception as exc:
        console.print(f"[red]Generator failed: {exc}[/red]\n")


def run_pipeline(pipeline_id: str):
    """Configure and run a pipeline."""
    pipeline = PIPELINES[pipeline_id]
    header_info = PIPELINE_HEADERS.get(pipeline_id)

    # Display ASCII art header if available
    if header_info:
        console.print(f"[{header_info['color']}]{header_info['ascii']}[/{header_info['color']}]")
    else:
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
    elif pipeline_id == "ingest":
        cmd = configure_ingest()
    elif pipeline_id == "classify":
        cmd = configure_classify()
    elif pipeline_id == "chat":
        cmd = configure_chat()
    elif pipeline_id == "voice_chat":
        cmd = configure_voice_chat()
    elif pipeline_id == "sts_avatar":
        cmd = configure_sts_avatar()
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


def models_management_menu():
    """Unified models management: download, cache, delete."""
    while True:
        console.clear()
        show_header()

        console.print("[bold cyan]📦 Models Management[/bold cyan]\n")

        # Show quick stats
        cache_info = get_cache_info()
        if cache_info:
            total_size = cache_info.size_on_disk / 1e9
            total_repos = len(cache_info.repos)
            console.print(f"[dim]Cached models: {total_repos} ({total_size:.1f} GB)[/dim]\n")

        action = inquirer.select(
            message="Model Management:",
            choices=[
                Choice("download", name="📥 Download Models"),
                Choice("view", name="📋 View Available Models"),
                Choice("cache", name="💾 View Cache Details"),
                Choice("delete", name="🗑️  Delete Cached Models"),
                Separator(),
                Choice("back", name="⬅️  Back to Main Menu"),
            ],
            default="download",
        ).execute()

        if action == "back":
            break
        elif action == "download":
            download_model()
        elif action == "view":
            show_models_menu()
        elif action == "cache":
            show_cache_info()
        elif action == "delete":
            delete_cached_models()


def system_management_menu():
    """Unified system management: info, cleanup."""
    while True:
        console.clear()
        show_header()

        console.print("[bold cyan]💻 System Management[/bold cyan]\n")

        action = inquirer.select(
            message="System Management:",
            choices=[
                Choice("info", name="📊 System Information"),
                Choice("cleanup", name="🧹 Clean Memory (MLX)"),
                Separator(),
                Choice("back", name="⬅️  Back to Main Menu"),
            ],
            default="info",
        ).execute()

        if action == "back":
            break
        elif action == "info":
            show_system_info()
        elif action == "cleanup":
            console.print("\n[bold]🧹 Cleaning memory...[/bold]\n")
            gc.collect()
            console.print("[green]✓ Memory cleanup complete[/green]")
            input("\n[dim]Press Enter to continue...[/dim]")


def ui_settings_menu():
    """UI Settings and preferences."""
    console.clear()
    run_ui_playground(console)


def user_menu():
    """User profile and exit options."""
    import getpass
    username = getpass.getuser()

    action = inquirer.select(
        message=f"User: {username}",
        choices=[
            Choice("settings", name="⚙️  UI Settings"),
            Choice("exit", name="🚪 Exit MLX Lab"),
            Separator(),
            Choice("back", name="⬅️  Back"),
        ],
        default="back",
    ).execute()

    return action


def main_menu():
    """Display and handle the main menu with fixed header."""
    while True:
        console.clear()
        show_header()

        action = inquirer.select(
            message="What would you like to do?",
            choices=[
                Separator("═══ PIPELINES ═══"),
                Choice("chat", name="💬 Chat - Conversational AI"),
                Choice("voice_chat", name="🗣️  Voice Chat - Text to Speech"),
                Choice("sts_avatar", name="🎭 STS Avatar - Speech to Speech"),
                Choice("rag", name="🔍 RAG - Question Answering"),
                Choice("ingest", name="📚 Ingest - Build Vector Index"),
                Choice("classify", name="🏷️  Classify - Text Classification"),
                Choice("flux", name="🎨 Flux - Image Generation"),
                Choice("musicgen", name="🎵 MusicGen - Audio Generation"),
                Choice("whisper", name="🎙️  Whisper - Speech-to-Text"),
                Choice("bench", name="📊 Benchmark - Performance Testing"),
                Separator("═══ TOOLS ═══"),
                Choice("generators", name="🧪 Generators - Dataset Tools"),
                Choice("models", name="📦 Models Management"),
                Choice("system", name="💻 System Management"),
                Separator(),
                Choice("user", name="👤 User Menu"),
            ],
            default="chat",
        ).execute()

        if action == "user":
            user_action = user_menu()
            if user_action == "exit":
                console.print("\n[cyan]👋 Goodbye![/cyan]\n")
                break
            elif user_action == "settings":
                ui_settings_menu()
        elif action == "models":
            models_management_menu()
        elif action == "generators":
            console.clear()
            show_header()
            configure_generators()
        elif action == "system":
            system_management_menu()
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

"""
Local-first launcher that exposes the main MLX-RAG apps behind a simple CLI menu.

Usage:
    uv run python -m rag.cli.app_launcher            # interactive menu
    uv run python -m rag.cli.app_launcher --list     # show options
    uv run python -m rag.cli.app_launcher --app rag-tui
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

import typer

ROOT = Path(__file__).resolve().parents[3]
SRC_PATH = ROOT / "src"

app = typer.Typer(help="Unified launcher for RAG TUI, Flux, and MusicGen workflows.")


def _default_env() -> Dict[str, str]:
    env = os.environ.copy()
    py_path = env.get("PYTHONPATH", "")
    src_str = str(SRC_PATH)
    if py_path:
        if src_str not in py_path.split(os.pathsep):
            env["PYTHONPATH"] = src_str + os.pathsep + py_path
    else:
        env["PYTHONPATH"] = src_str
    return env


def _run_command(cmd: List[str]) -> int:
    typer.echo("\n→ Running:\n  " + " ".join(shlex.quote(part) for part in cmd))
    try:
        completed = subprocess.run(cmd, env=_default_env())
    except FileNotFoundError as exc:
        typer.echo(f"[launcher] Failed to start command: {exc}")
        return 1
    if completed.returncode != 0:
        typer.echo(f"[launcher] Command exited with code {completed.returncode}")
    return completed.returncode


def _prompt_float(prompt: str, default: float) -> float:
    return float(typer.prompt(prompt, default=str(default)))


def _prompt_int(prompt: str, default: int) -> int:
    return int(typer.prompt(prompt, default=str(default)))


@dataclass
class LauncherOption:
    key: str
    label: str
    description: str
    builder: Callable[[], List[str]]


def build_rag_tui_cmd() -> List[str]:
    vdb_path = typer.prompt("Vector DB path", default="models/indexes/vdb.npz")
    model_id = typer.prompt(
        "Model ID", default="mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit"
    )
    return [
        sys.executable,
        "-m",
        "rag.cli.rag_tui",
        "--vdb-path",
        vdb_path,
        "--model-id",
        model_id,
    ]


def build_flux_generate_cmd() -> List[str]:
    prompt = typer.prompt("Prompt", default="a cinematic photo of an astronaut on mars")
    model = typer.prompt("Model (schnell/dev)", default="schnell")
    steps = _prompt_int("Steps", 4)
    image_size = typer.prompt("Image size (e.g., 512 or 512x768)", default="512")
    output_dir = typer.prompt("Output directory", default="outputs/flux/launcher")
    return [
        sys.executable,
        "-m",
        "rag.cli.flux_txt2image",
        prompt,
        "--model",
        model,
        "--steps",
        str(steps),
        "--image-size",
        image_size,
        "--output",
        output_dir,
    ]


def build_flux_benchmark_cmd() -> List[str]:
    presets = {
        "1": {
            "label": "Benchmark (both models)",
            "args": [
                "--model",
                "both",
                "--prompt-key",
                "astronaut_horse",
                "--image-size",
                "512",
            ],
        },
        "2": {
            "label": "Schnell pic",
            "args": [
                "--model",
                "schnell",
                "--prompt-key",
                "schnell_pic",
                "--image-size",
                "512",
            ],
        },
        "3": {
            "label": "LoRA fuse (dragon)",
            "args": [
                "--model",
                "dev",
                "--adapter",
                "models-mlx/lora/dragon-v1.safetensors",
                "--fuse-adapter",
                "--no-t5-padding",
                "--prompt-key",
                "lora_subject",
                "--image-size",
                "512",
            ],
        },
        "4": {
            "label": "Pro portrait (dev @1024)",
            "args": [
                "--model",
                "dev",
                "--prompt-key",
                "pro_portrait",
                "--image-size",
                "1024",
            ],
        },
    }
    typer.echo("\nFlux benchmark presets:")
    for choice, info in presets.items():
        typer.echo(f"  {choice}. {info['label']}")
    selection = typer.prompt("Select preset", default="1")
    preset = presets.get(selection)
    if not preset:
        raise typer.BadParameter("Invalid preset selection.")
    steps = _prompt_int("Steps", 4)
    repeats = _prompt_int("Benchmark repeats", 3)
    warmup = _prompt_int("Warmup runs", 1)
    json_out = typer.prompt(
        "JSON output path (leave blank to skip)", default="benchmarks/results/latest.json"
    )
    script = str(ROOT / "benchmarks" / "flux" / "bench_flux.py")
    cmd = [
        sys.executable,
        script,
        "--steps",
        str(steps),
        "--repeats",
        str(repeats),
        "--warmup",
        str(warmup),
    ] + preset["args"]
    if json_out:
        cmd += ["--json-out", json_out]
    return cmd


def build_musicgen_cmd() -> List[str]:
    prompt = typer.prompt("Music prompt", default="a calming piano melody")
    duration = _prompt_float("Duration (seconds)", 15.0)
    model_size = typer.prompt("Model size (small/medium/large)", default="small")
    output_dir = typer.prompt("Output directory", default="var/music_output")
    seed = typer.prompt("Seed (-1 for random)", default="-1")
    return [
        sys.executable,
        "-m",
        "rag.cli.generate_music",
        "--prompt",
        prompt,
        "--duration",
        str(duration),
        "--model-size",
        model_size,
        "--seed",
        seed,
        "--output-dir",
        output_dir,
    ]


OPTIONS: List[LauncherOption] = [
    LauncherOption(
        key="rag-tui",
        label="RAG Textual UI",
        description="Textual interface for local retrieval + answer generation.",
        builder=build_rag_tui_cmd,
    ),
    LauncherOption(
        key="flux-generate",
        label="Flux quick generation",
        description="Run flux_txt2image with a custom prompt and model.",
        builder=build_flux_generate_cmd,
    ),
    LauncherOption(
        key="flux-bench",
        label="Flux benchmarks",
        description="Execute benchmark presets (benchmark, Schnell pic, LoRA fuse, pro portrait).",
        builder=build_flux_benchmark_cmd,
    ),
    LauncherOption(
        key="musicgen",
        label="MusicGen sample",
        description="Generate a short audio clip with rag.cli.generate_music.",
        builder=build_musicgen_cmd,
    ),
]

OPTION_MAP = {opt.key: opt for opt in OPTIONS}


def _choose_option() -> Optional[LauncherOption]:
    typer.echo("\nAvailable apps:\n")
    for idx, option in enumerate(OPTIONS, start=1):
        typer.echo(f"  {idx}. {option.label} [{option.key}]")
        typer.echo(f"     {option.description}")
    typer.echo("  q. Quit")
    choice = typer.prompt("\nSelect an option", default="q").strip().lower()
    if choice in {"q", "quit", "exit"}:
        return None
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(OPTIONS):
            return OPTIONS[idx]
    if choice in OPTION_MAP:
        return OPTION_MAP[choice]
    typer.echo("Unrecognized selection.")
    return _choose_option()


def _execute(option: LauncherOption) -> None:
    typer.echo(f"\nSelected: {option.label}")
    cmd = option.builder()
    if not typer.confirm("Run this command?", default=True):
        typer.echo("Command cancelled.")
        return
    _run_command(cmd)


@app.command()
def main(
    app_key: Optional[str] = typer.Option(
        None,
        "--app",
        "-a",
        help="Run a specific option directly (keys: rag-tui, flux-generate, flux-bench, musicgen).",
    ),
    list_apps: bool = typer.Option(
        False,
        "--list-apps",
        "--list",
        "-l",
        is_flag=True,
        help="List available options and exit.",
    ),
) -> None:
    """
    Launch the interactive menu or run a specific app directly.
    """
    if list_apps:
        typer.echo("Launcher options:")
        for option in OPTIONS:
            typer.echo(f"- {option.key}: {option.label}")
        raise typer.Exit()

    if app_key:
        option = OPTION_MAP.get(app_key)
        if not option:
            raise typer.BadParameter(f"Unknown app key '{app_key}'.")
        _execute(option)
        return

    option = _choose_option()
    if option:
        _execute(option)


if __name__ == "__main__":
    app()

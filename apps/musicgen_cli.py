import argparse
import gc
import json
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional

from libs.musicgen_core.musicgen_mlx import MusicGen
from libs.musicgen_core.utils import save_audio

DEFAULT_MODEL = "facebook/musicgen-small"
DEFAULT_MAX_STEPS = 500  # ~16 seconds at 30ms/step
DEFAULT_OUTPUT_DIR = Path("var/music_output")
PROMPT_SOURCE_PATH = Path("examples/musicgen/prompts-models.txt")
PROMPT_LIBRARY_PATH = Path("mlx-models/musicgen-prompts/prompts-models.json")

_model = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MusicGen CLI – generate audio from text descriptions (MLX)."
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="",
        help="Text description for the music. Optional when using --prompt-preset.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Model name (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=DEFAULT_MAX_STEPS,
        help=f"Generation steps (~30ms/step). Default: {DEFAULT_MAX_STEPS}.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Explicit output path (e.g., music.wav).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for auto-named outputs (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="musicgen",
        help="Filename prefix when using --output-dir.",
    )
    parser.add_argument(
        "--prompt-preset",
        type=str,
        default=None,
        help="Use a preset prompt for the selected model (see --list-prompts).",
    )
    parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="List available prompt presets and exit.",
    )
    parser.add_argument(
        "--download-prompts",
        action="store_true",
        help="Install curated prompts into mlx-models/musicgen-prompts/."
    )
    return parser


def cleanup_handler(signum, frame):
    global _model
    print("\n\n🧹 Cleaning up MusicGen resources...")
    if _model is not None:
        del _model
        _model = None
    gc.collect()
    print("✅ Cleanup complete. Bye.\n")
    sys.exit(0)


def ingest_prompt_library() -> Dict[str, List[str]]:
    if not PROMPT_SOURCE_PATH.exists():
        raise FileNotFoundError(f"Prompt source not found: {PROMPT_SOURCE_PATH}")

    library: Dict[str, List[str]] = {}
    current_model: Optional[str] = None
    for line in PROMPT_SOURCE_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("[MODEL:"):
            current_model = line.replace("[MODEL:", "").replace("]", "").strip()
            library[current_model] = []
            continue
        if line[0].isdigit() and current_model:
            _, prompt = line.split(".", 1)
            library[current_model].append(prompt.strip().strip('"'))
    return library


def download_prompt_library():
    library_dir = PROMPT_LIBRARY_PATH.parent
    library_dir.mkdir(parents=True, exist_ok=True)

    try:
        data = ingest_prompt_library()
    except Exception as exc:
        print(f"[red]Failed to parse prompt source: {exc}[/red]")
        sys.exit(1)

    PROMPT_LIBRARY_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[green]Prompt library saved to {PROMPT_LIBRARY_PATH}[/green]")


def load_prompt_library() -> Dict[str, List[str]]:
    if PROMPT_LIBRARY_PATH.exists():
        try:
            return json.loads(PROMPT_LIBRARY_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[yellow]Prompt library unreadable: {exc}[/yellow]")
    return {}


def list_prompts(library: Dict[str, List[str]]):
    if not library:
        print("[yellow]No prompt library found. Run with --download-prompts first.[/yellow]")
        return
    for model, prompts in library.items():
        print(f"\n[bold]{model}[/bold]")
        for idx, prompt in enumerate(prompts, 1):
            print(f"  {idx}. {prompt}")
    print()


def select_prompt(
    model_id: str,
    preset: str,
    library: Dict[str, List[str]],
) -> Optional[str]:
    prompts = library.get(model_id)
    if not prompts:
        print(f"[yellow]No presets for model '{model_id}'.[/yellow]")
        return None

    if preset.lower() == "random":
        return prompts[0]

    try:
        idx = int(preset) - 1
        if 0 <= idx < len(prompts):
            return prompts[idx]
    except ValueError:
        pass

    for prompt in prompts:
        if preset.lower() in prompt.lower():
            return prompt

    print(f"[yellow]Preset '{preset}' not found for model {model_id}.[/yellow]")
    return None


def resolve_output_path(args) -> Path:
    if args.output:
        return args.output
    args.output_dir.mkdir(parents=True, exist_ok=True)
    existing = list(args.output_dir.glob(f"{args.prefix}_*.wav"))
    next_num = len(existing) + 1
    return args.output_dir / f"{args.prefix}_{next_num:03d}.wav"


def main():
    global _model

    signal.signal(signal.SIGINT, cleanup_handler)
    args = build_parser().parse_args()

    if args.download_prompts:
        download_prompt_library()
        return

    prompt_library = load_prompt_library()
    if args.list_prompts:
        list_prompts(prompt_library)
        return

    prompt_text = args.prompt
    if args.prompt_preset:
        prompt_text = select_prompt(args.model, args.prompt_preset, prompt_library)

    if not prompt_text:
        print("[red]No prompt provided (text or preset).[/red]")
        sys.exit(1)

    output_path = resolve_output_path(args)

    print(f"🎵 Loading MusicGen model: {args.model}")
    _model = MusicGen.from_pretrained(args.model)

    print(f"🎹 Generating audio for prompt: \"{prompt_text}\"")
    print(f"⏱  Max steps: {args.max_steps} (~{args.max_steps * 0.03:.1f}s generation time)")

    try:
        audio = _model.generate(prompt_text, max_steps=args.max_steps)
        save_audio(str(output_path), audio, _model.sampling_rate)
        print(f"✅ Audio saved to: {output_path.resolve()}")
        print(f"📊 Sampling rate: {_model.sampling_rate} Hz")
        print(f"🔊 Duration: ~{args.max_steps / 30:.1f} seconds")
    except Exception as exc:
        print(f"❌ Error during generation: {exc}")
        sys.exit(1)
    finally:
        if _model is not None:
            del _model
            _model = None
        gc.collect()


if __name__ == "__main__":
    main()

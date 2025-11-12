import argparse
import gc
import signal
import sys
from pathlib import Path

# Use libs/musicgen_core for the actual implementation
from libs.musicgen_core.musicgen_mlx import MusicGen
from libs.musicgen_core.utils import save_audio

DEFAULT_MODEL = "facebook/musicgen-small"
DEFAULT_MAX_STEPS = 500  # ~16 seconds at 30ms/step
DEFAULT_OUTPUT_DIR = Path("var/music_output")

# Global reference for cleanup
_model = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MusicGen CLI – generate audio from text descriptions (MLX)."
    )
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="Text description of the music to generate.",
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
        help=f"Generation steps (~30ms/step). Default: {DEFAULT_MAX_STEPS} (~16s audio).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (e.g., music.wav). If not specified, uses --output-dir and --prefix.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="musicgen",
        help="Output filename prefix when --output is not specified.",
    )
    return parser


def cleanup_handler(signum, frame):
    """Handle Ctrl+C gracefully by cleaning up MLX resources."""
    global _model

    print("\n\n🧹 Cleaning up MusicGen resources...")

    # Delete model to free GPU/unified memory
    if _model is not None:
        del _model
        _model = None

    # Force garbage collection
    gc.collect()

    print("✅ Cleanup complete. Bye.\n")
    sys.exit(0)


def main() -> None:
    global _model

    # Register signal handler for graceful Ctrl+C cleanup
    signal.signal(signal.SIGINT, cleanup_handler)

    args = build_parser().parse_args()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        # Find next available numbered file
        existing = list(args.output_dir.glob(f"{args.prefix}_*.wav"))
        next_num = len(existing) + 1
        output_path = args.output_dir / f"{args.prefix}_{next_num:03d}.wav"

    print(f"🎵 Loading MusicGen model: {args.model}")
    _model = MusicGen.from_pretrained(args.model)

    print(f"🎹 Generating audio for prompt: \"{args.prompt}\"")
    print(f"⏱  Max steps: {args.max_steps} (~{args.max_steps * 0.03:.1f}s generation time)")

    try:
        audio = _model.generate(args.prompt, max_steps=args.max_steps)
        save_audio(str(output_path), audio, _model.sampling_rate)
        print(f"✅ Audio saved to: {output_path.resolve()}")
        print(f"📊 Sampling rate: {_model.sampling_rate} Hz")
        print(f"🔊 Duration: ~{args.max_steps / 30:.1f} seconds")
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        sys.exit(1)
    finally:
        # Cleanup even on success
        if _model is not None:
            del _model
            _model = None
        gc.collect()


if __name__ == "__main__":
    main()

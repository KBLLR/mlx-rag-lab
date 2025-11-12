import argparse
import gc
import signal
import sys
from pathlib import Path

# Import from existing MLX Whisper implementation
sys.path.insert(0, str(Path(__file__).parent.parent / "mlx-models" / "whisper"))
from mlx_whisper import transcribe

DEFAULT_MODEL = "mlx-community/whisper-large-v3"
DEFAULT_OUTPUT_DIR = Path("var/transcripts")
DEFAULT_OUTPUT_FORMAT = "txt"

# Global reference for cleanup
_active = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Whisper CLI – transcribe audio to text using MLX."
    )
    parser.add_argument(
        "audio",
        nargs="+",
        type=Path,
        help="Audio file(s) to transcribe (mp3, wav, m4a, etc.).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Whisper model to use (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for transcripts (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        default=DEFAULT_OUTPUT_FORMAT,
        choices=["txt", "json", "srt", "vtt", "tsv", "all"],
        help=f"Output format (default: {DEFAULT_OUTPUT_FORMAT}).",
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Language hint (e.g., 'English', 'Spanish'). Auto-detected if not specified.",
    )
    parser.add_argument(
        "--task",
        type=str,
        default="transcribe",
        choices=["transcribe", "translate"],
        help="Task: 'transcribe' (default) or 'translate' to English.",
    )
    parser.add_argument(
        "--word-timestamps",
        action="store_true",
        help="Include word-level timestamps in output.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Show progress during transcription (default: True).",
    )
    return parser


def cleanup_handler(signum, frame):
    """Handle Ctrl+C gracefully by cleaning up MLX resources."""
    global _active

    print("\n\n🧹 Cleaning up Whisper resources...")

    # Mark as inactive
    _active = False

    # Force garbage collection
    gc.collect()

    print("✅ Cleanup complete. Bye.\n")
    sys.exit(0)


def save_transcript(output_path: Path, result: dict, format: str) -> None:
    """Save transcript in specified format."""
    if format == "txt":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
    elif format == "json":
        import json

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    elif format in ["srt", "vtt", "tsv"]:
        # These formats require the writers from mlx_whisper
        from mlx_whisper.writers import get_writer

        writer = get_writer(format, str(output_path.parent))
        writer(result, str(output_path.stem))
    else:
        raise ValueError(f"Unsupported format: {format}")


def main() -> None:
    global _active

    # Register signal handler for graceful Ctrl+C cleanup
    signal.signal(signal.SIGINT, cleanup_handler)

    args = build_parser().parse_args()
    _active = True

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎙️  Whisper Model: {args.model}")
    print(f"📝 Output format: {args.output_format}")
    print(f"📂 Output directory: {args.output_dir.resolve()}\n")

    for audio_file in args.audio:
        if not audio_file.exists():
            print(f"❌ File not found: {audio_file}")
            continue

        try:
            print(f"🔊 Transcribing: {audio_file.name}")

            # Run transcription
            result = transcribe(
                str(audio_file),
                path_or_hf_repo=args.model,
                verbose=args.verbose,
                language=args.language,
                task=args.task,
                word_timestamps=args.word_timestamps,
            )

            # Determine output filename
            output_stem = audio_file.stem
            if args.output_format == "all":
                # Save in all formats
                for fmt in ["txt", "json", "srt", "vtt", "tsv"]:
                    ext = "txt" if fmt == "txt" else fmt
                    output_path = args.output_dir / f"{output_stem}.{ext}"
                    save_transcript(output_path, result, fmt)
                    print(f"  ✅ Saved {fmt.upper()}: {output_path.resolve()}")
            else:
                # Save in single format
                ext = "txt" if args.output_format == "txt" else args.output_format
                output_path = args.output_dir / f"{output_stem}.{ext}"
                save_transcript(output_path, result, args.output_format)
                print(f"  ✅ Saved: {output_path.resolve()}")

            # Display stats
            print(f"  🌐 Language: {result.get('language', 'unknown')}")
            print(f"  📊 Segments: {len(result.get('segments', []))}")
            print(f"  📝 Characters: {len(result['text'])}\n")

        except Exception as e:
            print(f"  ❌ Error during transcription: {e}\n")
            continue

    # Cleanup on success
    gc.collect()


if __name__ == "__main__":
    main()

import argparse
import os
from rag.cli.utils import print_section, print_variable
from libs.musicgen_core import MusicgenAdapter

def main():
    parser = argparse.ArgumentParser(description="Generate music from a text prompt using Musicgen.")
    parser.add_argument("--prompt", type=str, required=True, help="Text prompt for music generation.")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration of the generated music in seconds.")
    parser.add_argument("--model-size", type=str, default="small", help="Size of the Musicgen model to use (e.g., small, medium, large, melody).")
    parser.add_argument("--seed", type=int, default=-1, help="Seed for reproducible music generation. Use -1 for random.")
    parser.add_argument("--output-format", type=str, default="wav", help="Output format for the generated music (e.g., wav). MP3 is not yet supported.")
    parser.add_argument("--output-dir", type=str, default="./var/music_output", help="Directory to save the generated music.")

    args = parser.parse_args()

    if args.output_format.lower() != "wav":
        print_section("Error")
        print_variable("Unsupported Format", f"Output format '{args.output_format}' is not yet supported. Only WAV is available.")
        raise SystemExit(1)

    print_section("Music Generation")
    print_variable("Prompt", args.prompt)
    print_variable("Duration", f"{args.duration} seconds")
    print_variable("Model Size", args.model_size)
    print_variable("Seed", str(args.seed) if args.seed != -1 else "Random")
    print_variable("Output Format", args.output_format)
    print_variable("Output Directory", args.output_dir)

    adapter = MusicgenAdapter(model_id=args.model_size)
    output_filepath = adapter.generate_music(args.prompt, args.duration, args.output_dir, seed=args.seed)

    print_variable("Generated Music", output_filepath)
    print_section("Generation Complete")

if __name__ == "__main__":
    main()
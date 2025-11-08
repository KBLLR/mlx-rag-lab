import argparse
import os
from rag.cli.utils import print_section, print_variable
from libs.musicgen_core import MusicgenAdapter

def main():
    parser = argparse.ArgumentParser(description="Generate music from a text prompt using Musicgen.")
    parser.add_argument("--prompt", type=str, required=True, help="Text prompt for music generation.")
    parser.add_argument("--duration", type=int, default=10, help="Duration of the generated music in seconds.")
    parser.add_argument("--output_dir", type=str, default="./var/music_output", help="Directory to save the generated music.")

    args = parser.parse_args()

    print_section("Music Generation")
    print_variable("Prompt", args.prompt)
    print_variable("Duration", f"{args.duration} seconds")
    print_variable("Output Directory", args.output_dir)

    adapter = MusicgenAdapter()
    output_filepath = adapter.generate_music(args.prompt, args.duration, args.output_dir)

    print_variable("Generated Music", output_filepath)
    print_section("Generation Complete")

if __name__ == "__main__":
    main()

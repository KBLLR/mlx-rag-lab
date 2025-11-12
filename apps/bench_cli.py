import argparse

from benchmarks.flux_benchmark import main as flux_bench_main
from benchmarks.prompt_evaluation import main as prompt_bench_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dispatch bench scripts for the MLX lab.")
    sub = parser.add_subparsers(dest="target", required=True)
    sub.add_parser("flux", help="Run Flux benchmarks.")
    sub.add_parser("prompt", help="Run prompt evaluation benchmarks.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.target == "flux":
        flux_bench_main()
    elif args.target == "prompt":
        prompt_bench_main()
    else:
        raise SystemExit(f"Unknown target {args.target}")


if __name__ == "__main__":
    main()

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"


def _build_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    paths = [str(SRC_PATH)]
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Flux txt2img demo (MLX).")
    parser.add_argument("--prompt", required=True, help="Text prompt to render.")
    parser.add_argument(
        "--model",
        choices=["schnell", "dev", "schnell-4bit"],
        default="schnell",
        help="Flux model variant.",
    )
    parser.add_argument("--steps", type=int, default=20, help="Denoising steps.")
    parser.add_argument(
        "--image-size",
        default="512",
        help="Pixel size (single int) or WxH string (e.g., 512x768).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/flux"),
        help="Output directory for generated images.",
    )
    parser.add_argument("--output-prefix", default="flux_cli", help="Output filename prefix.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "rag.cli.flux_txt2image",
        args.prompt,
        "--model",
        args.model,
        "--steps",
        str(args.steps),
        "--image-size",
        args.image_size,
        "--output",
        str(args.output_dir),
        "--output-prefix",
        args.output_prefix,
    ]

    print("Running:", shlex.join(cmd))
    completed = subprocess.run(cmd, env=_build_env())
    if completed.returncode != 0:
        sys.exit(completed.returncode)


if __name__ == "__main__":
    main()

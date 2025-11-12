#!/usr/bin/env python
import argparse
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from functools import lru_cache

# ---------------------------------------------------------------------
# Evaluation Configuration
# ---------------------------------------------------------------------

SUBJECTS = [
    "a photorealistic portrait of a medieval knight in shining armor",
    "a futuristic cityscape at night, with flying vehicles and neon signs",
    "a tranquil landscape with a serene lake and distant mountains",
    "a red sports car driving on a winding coastal road at sunset",
    "a close-up of a delicious-looking gourmet burger with all the toppings",
    "an astronaut floating in the vast emptiness of space, with Earth in the background",
]

STYLES = [
    "in a cinematic 8k photorealistic style",
    "in the style of a Van Gogh painting",
    "as a watercolor painting",
    "as a detailed charcoal sketch",
    "in a vibrant, colorful anime style",
    "as a low-poly 3D render",
]

BASE_CMD = ["uv", "run", "python", "src/rag/cli/flux_txt2image.py"]
PEAK_MEM_RE = re.compile(
    r"(?:\[\s*)?MLX\s+GPU(?:\s*\])?\s*Peak memory:\s*([0-9.]+)\s*MB",
    re.IGNORECASE,
)
DEFAULT_MODELS_DIR = Path(os.environ.get("MLX_MODELS_DIR", "mlx-models"))

# ---------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------

@dataclass
class TestCase:
    model: str
    subject: str
    style: str
    steps: int
    guidance: float
    seed: int
    full_prompt: str = ""

    def __post_init__(self):
        self.full_prompt = f"{self.subject}, {self.style}"

@dataclass
class TestResult:
    config: TestCase
    latency_s: float
    peak_memory_mb: Optional[float]
    output_image_path: Path

# ---------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------

def _build_flux_env(models_dir: Path) -> dict:
    env = os.environ.copy()
    env["MLX_MODELS_DIR"] = str(models_dir.resolve())
    return env


@lru_cache(maxsize=None)
def _ensure_flux_weights(model: str) -> None:
    from rag.models.flux.utils import ensure_flux_assets, resolve_model_choice

    base_name, variant = resolve_model_choice(f"flux-{model}")
    ensure_flux_assets(base_name, variant)


def run_evaluation_case(case: TestCase, output_dir: Path, models_dir: Path, verbose: bool = False) -> TestResult:
    """Runs a single evaluation case and returns the result."""
    filename_base = f"{case.model}_{case.subject[:30]}_{case.style[:30]}".replace(" ", "_").replace(",", "")

    cmd = BASE_CMD + [
        case.full_prompt,
        "--model", case.model,
        "--steps", str(case.steps),
        "--guidance", str(case.guidance),
        "--seed", str(case.seed),
        "--output", str(output_dir),
        "--output-prefix", filename_base,
    ]

    if verbose:
        print(f"Running command: {' '.join(cmd)}")

    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=_build_flux_env(models_dir))
    t1 = time.perf_counter()

    if proc.returncode != 0:
        print(f"ERROR: Evaluation case failed for model={case.model}")
        print(proc.stderr)
        # Create a placeholder result on failure
        return TestResult(
            config=case,
            latency_s=-1.0,
            peak_memory_mb=None,
            output_image_path=Path("error.png"),
        )

    latency = t1 - t0

    # Parse peak memory from stdout/stderr
    text = proc.stdout + "\n" + proc.stderr
    match = PEAK_MEM_RE.search(text)
    peak_mem = float(match.group(1)) if match else None

    # The CLI saves the file with a suffix, find it
    saved_file = next(output_dir.glob(f"{filename_base}*.png"), None)
    if not saved_file:
        raise FileNotFoundError(f"Could not find output image for prefix {filename_base} in {output_dir}")

    return TestResult(
        config=case,
        latency_s=latency,
        peak_memory_mb=peak_mem,
        output_image_path=saved_file.relative_to(output_dir.parent),
    )

def generate_report(results: List[TestResult], output_dir: Path, args: argparse.Namespace):
    """Generates a Markdown report from the evaluation results."""
    report_path = output_dir / "report.md"

    with open(report_path, "w") as f:
        f.write(f"# Flux Prompt Evaluation Report\n\n")
        f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Parameters:**\n")
        f.write(f"- **Steps:** {args.steps}\n")
        f.write(f"- **Guidance:** {args.guidance}\n\n")

        for model in ["schnell", "dev"]:
            f.write(f"## Model: Flux.1 [{model.upper()}]\n\n")
            model_results = [r for r in results if r.config.model == model]

            if not model_results:
                continue

            f.write("| Prompt (Subject + Style) | Generated Image | Performance |\n")
            f.write("|--------------------------|-----------------|-------------|\n")

            for result in model_results:
                prompt_md = result.config.full_prompt.replace('"', "'")
                image_md = f"![{result.output_image_path.name}]({result.output_image_path})"
                perf_md = f"**Latency:** {result.latency_s:.2f}s<br>**Peak Memory:** {result.peak_memory_mb or 'N/A'} MB"
                f.write(f"| {prompt_md} | {image_md} | {perf_md} |\n")

                f.write("\n")

                print(f"Generated evaluation report at {report_path}")

# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a qualitative prompt evaluation for Flux models.")
    parser.add_argument("--steps", type=int, default=8, help="Number of inference steps.")
    parser.add_argument("--guidance", type=float, default=7.5, help="Guidance scale.")
    parser.add_argument("--seed", type=int, default=1337, help="Base seed for generation.")
    parser.add_argument("--output-dir", type=str, default="evaluations", help="Root directory to save evaluation results.")
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help="Directory containing flux-* weight folders (defaults to ./mlx-models or $MLX_MODELS_DIR).",
    )
    parser.add_argument("--verbose", action="store_true", help="Print detailed command information.")
    return parser.parse_args()

def main():
    args = parse_args()

    models_dir = Path(args.models_dir).resolve()
    os.environ.pop("MLX_PROFILE_FORCE_DOWNLOAD", None)
    os.environ["MLX_MODELS_DIR"] = str(models_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_output_dir = Path(args.output_dir) / timestamp
    run_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting prompt evaluation... Results will be saved to: {run_output_dir}")

    test_cases = [
        TestCase(model=model, subject=subject, style=style, steps=args.steps, guidance=args.guidance, seed=args.seed)
        for model in ["schnell", "dev"]
        for subject in SUBJECTS
        for style in STYLES
    ]
    
    all_results: List[TestResult] = []
    
    for i, case in enumerate(test_cases):
        print(f"--- Running case {i+1}/{len(test_cases)}: model={case.model} ---")
        model_output_dir = run_output_dir / case.model
        model_output_dir.mkdir(exist_ok=True)
        _ensure_flux_weights(case.model)
        result = run_evaluation_case(case, model_output_dir, models_dir, args.verbose)
        all_results.append(result)

    print("\n--- Evaluation complete. Generating report... ---")
    generate_report(all_results, run_output_dir, args)

if __name__ == "__main__":
    main()

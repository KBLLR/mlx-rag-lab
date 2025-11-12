#!/usr/bin/env python
import argparse
import json
import os
import re
import statistics as stats
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import prompts  # benchmarks/flux/prompts.py
from tqdm import tqdm

# ---------------------------------------------------------------------
# Core config / dataclasses
# ---------------------------------------------------------------------


@dataclass
class RunConfig:
    model: str  # e.g. "schnell", "dev", "schnell-4bit"
    prompt: str  # resolved text prompt
    prompt_key: Optional[str]
    steps: int
    n_images: int
    image_size: str  # "512", "512x768", etc.
    seed: int
    adapter: Optional[str] = None
    fuse_adapter: bool = False
    no_t5_padding: bool = False
    extra_args: List[str] = field(default_factory=list)


@dataclass
class RunResult:
    latency_s: float
    peak_memory_mb: Optional[float] = None


@dataclass
class BenchmarkSummary:
    model: str
    steps: int
    n_images: int
    image_size: str
    repeats: int
    warmup: int
    latencies_s: List[float]
    peak_memory_mb: Optional[Dict[str, float]]  # mean / max / min or None
    run_config: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        percentile = lambda p: _percentile(self.latencies_s, p)
        summary = {
            "model": self.model,
            "steps": self.steps,
            "n_images": self.n_images,
            "image_size": self.image_size,
            "repeats": self.repeats,
            "warmup": self.warmup,
            "latency": {
                "mean_s": stats.mean(self.latencies_s),
                "std_s": stats.pstdev(self.latencies_s) if len(self.latencies_s) > 1 else 0.0,
                "p50_s": percentile(50),
                "p90_s": percentile(90),
                "min_s": min(self.latencies_s),
                "max_s": max(self.latencies_s),
                "images_per_second": (self.n_images * self.repeats) / sum(self.latencies_s),
            },
            "run_config": self.run_config,
        }
        if self.peak_memory_mb is not None:
            summary["peak_memory_mb"] = self.peak_memory_mb
        return summary


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

# Adjust to your actual CLI path
BASE_CMD = ["uv", "run", "python", "src/rag/cli/flux_txt2image.py"]

DEFAULT_MODELS_DIR = Path(os.environ.get("MLX_MODELS_DIR", "mlx-models"))

PEAK_MEM_RE = re.compile(
    r"(?:\[\s*)?MLX\s+GPU(?:\s*\])?\s*Peak memory:\s*([0-9.]+)\s*MB",
    re.IGNORECASE,
)


def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = (len(ordered) - 1) * (p / 100.0)
    lower = int(idx)
    upper = min(lower + 1, len(ordered) - 1)
    weight = idx - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _parse_peak_memory(stdout: str, stderr: str) -> Optional[float]:
    """Extract MLX peak memory from CLI output if present."""
    text = stdout + "\n" + stderr
    match = PEAK_MEM_RE.search(text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _build_flux_env(models_dir: Path) -> Dict[str, str]:
    env = os.environ.copy()
    env["MLX_MODELS_DIR"] = str(models_dir.resolve())
    return env


@lru_cache(maxsize=None)
def _ensure_flux_weights(model: str, models_dir: Path) -> None:
    """
    Ensure that the FLUX weights for a given model string exist locally.

    model: "schnell", "dev", "schnell-4bit", etc.

    This mimics the mlx-examples behavior: resolve "flux-schnell" + variant,
    and only snapshot_download if something's missing under MLX_MODELS_DIR.
    """
    # Keep MLX_MODELS_DIR aligned
    os.environ["MLX_MODELS_DIR"] = str(models_dir.resolve())

    from rag.models.flux.utils import ensure_flux_assets, resolve_model_choice

    base_name, variant = resolve_model_choice(f"flux-{model}")
    ensure_flux_assets(base_name, variant)


def run_flux_once(
    cfg: RunConfig,
    tmp_dir: Path,
    models_dir: Path,
    verbose: bool = False,
) -> RunResult:
    """Run a single Flux generation via the existing CLI and measure wall-clock time."""
    output_dir = tmp_dir / f"{cfg.model}"
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = BASE_CMD + [
        cfg.prompt,
        "--model",
        cfg.model,
        "--steps",
        str(cfg.steps),
        "--n-images",
        str(cfg.n_images),
        "--image-size",
        cfg.image_size,
        "--seed",
        str(cfg.seed),
        "--output",
        str(output_dir),
    ]

    if cfg.adapter:
        cmd += ["--adapter", cfg.adapter]
    if cfg.fuse_adapter:
        cmd += ["--fuse-adapter"]
    if cfg.no_t5_padding:
        cmd += ["--no-t5-padding"]

    if cfg.extra_args:
        cmd += cfg.extra_args

    if verbose:
        print(" ".join(cmd))

    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=_build_flux_env(models_dir),
    )
    t1 = time.perf_counter()

    if proc.returncode != 0:
        raise RuntimeError(f"Flux run failed for model={cfg.model}:\n{proc.stderr}")

    latency = t1 - t0
    peak_mem = _parse_peak_memory(proc.stdout, proc.stderr)
    return RunResult(latency_s=latency, peak_memory_mb=peak_mem)


def benchmark_model(
    model: str,
    prompt: str,
    prompt_key: Optional[str],
    steps: int,
    n_images: int,
    image_size: str,
    repeats: int,
    warmup: int,
    base_seed: int,
    models_dir: Path,
    adapter: Optional[str] = None,
    fuse_adapter: bool = False,
    no_t5_padding: bool = False,
    extra_args: Optional[List[str]] = None,
    verbose: bool = False,
) -> BenchmarkSummary:
    """Run multiple warmup + benchmark iterations and aggregate stats."""

    if extra_args is None:
        extra_args = []

    cfg_base = RunConfig(
        model=model,
        prompt=prompt,
        prompt_key=prompt_key,
        steps=steps,
        n_images=n_images,
        image_size=image_size,
        seed=base_seed,
        adapter=adapter,
        fuse_adapter=fuse_adapter,
        no_t5_padding=no_t5_padding,
        extra_args=extra_args,
    )

    latencies: List[float] = []
    mem_values: List[float] = []

    _ensure_flux_weights(model, models_dir)

    with tempfile.TemporaryDirectory(prefix="flux_bench_") as tmp:
        tmp_dir = Path(tmp)

        # Warmup runs (not recorded)
        for _ in tqdm(range(warmup), desc=f"Warmup ({model})"):
            _ = run_flux_once(cfg_base, tmp_dir, models_dir=models_dir, verbose=verbose)

        # Measured runs
        for i in tqdm(range(repeats), desc=f"Benchmark ({model})"):
            cfg = cfg_base
            cfg.seed = base_seed + i  # vary seed so the model can't cache
            result = run_flux_once(cfg, tmp_dir, models_dir=models_dir, verbose=verbose)
            latencies.append(result.latency_s)
            if result.peak_memory_mb is not None:
                mem_values.append(result.peak_memory_mb)

    mem_summary: Optional[Dict[str, float]]
    if mem_values:
        mem_summary = {
            "mean": stats.mean(mem_values),
            "max": max(mem_values),
            "min": min(mem_values),
        }
    else:
        mem_summary = None

    run_cfg_dict = asdict(cfg_base)
    # This will include adapter, fuse_adapter, prompt_key, etc.

    return BenchmarkSummary(
        model=model,
        steps=steps,
        n_images=n_images,
        image_size=image_size,
        repeats=repeats,
        warmup=warmup,
        latencies_s=latencies,
        peak_memory_mb=mem_summary,
        run_config=run_cfg_dict,
    )


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark Flux.1 [schnell/dev/variants] via MLX.")

    parser.add_argument(
        "--model",
        type=str,
        default="both",
        help=(
            "Which model to benchmark. "
            "You can pass 'schnell', 'dev', 'schnell-4bit', etc., "
            "or 'both' to run on ['schnell', 'dev']."
        ),
    )

    # Prompt options
    parser.add_argument(
        "--prompt-key",
        type=str,
        default="astronaut_horse",
        help=(
            f"Named prompt key from prompts.py (available: {', '.join(prompts.list_prompt_keys())})"
        ),
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help=("Raw prompt text. If set, overrides --prompt-key."),
    )

    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--n-images", type=int, default=1)

    parser.add_argument(
        "--image-size",
        type=str,
        default="512",
        help=(
            "Image size passed to flux_txt2image.py. "
            "Can be '512' (for 512x512) or '512x768' etc., "
            "depending on what your CLI supports."
        ),
    )

    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)

    parser.add_argument(
        "--models-dir",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help=(
            "Base directory containing flux-* weight folders "
            "(defaults to ./mlx-models or $MLX_MODELS_DIR). "
            "Inside, you might have flux-schnell/, flux-dev/, "
            "flux-schnell-4bit/, etc."
        ),
    )

    # LoRA / adapter options
    parser.add_argument(
        "--adapter",
        type=str,
        default=None,
        help=(
            "Path to a LoRA adapter (e.g. models-mlx/lora/dragon-v1.safetensors) "
            "to pass via --adapter to the Flux CLI."
        ),
    )
    parser.add_argument(
        "--fuse-adapter",
        action="store_true",
        help="Pass --fuse-adapter to fuse the LoRA into the model for this run.",
    )
    parser.add_argument(
        "--no-t5-padding",
        action="store_true",
        help="Pass --no-t5-padding to the Flux CLI.",
    )

    # Extra passthrough args
    parser.add_argument(
        "--extra-arg",
        action="append",
        default=None,
        help=(
            "Extra argument(s) to pass through to flux_txt2image.py verbatim. "
            "Can be repeated, e.g. --extra-arg --save-raw --extra-arg --verbose"
        ),
    )

    parser.add_argument(
        "--json-out",
        type=str,
        default=None,
        help="Path to write JSON summary.",
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Optional tag for this run (e.g., 'm3-max-36gb-dev', 'schnell-lora-fused').",
    )
    parser.add_argument("--verbose", action="store_true")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    models_dir = args.models_dir.resolve()
    os.environ.pop("MLX_PROFILE_FORCE_DOWNLOAD", None)
    os.environ["MLX_MODELS_DIR"] = str(models_dir)

    # Prompt resolution
    if args.prompt is not None:
        prompt_text = args.prompt
        prompt_key = None
    else:
        prompt_text = prompts.resolve_prompt(args.prompt_key)
        prompt_key = args.prompt_key

    # Models to run
    if args.model == "both":
        models_to_run = ["schnell", "dev"]
    else:
        models_to_run = [args.model]

    extra_args = args.extra_arg or []

    all_summaries: List[BenchmarkSummary] = []

    for m in models_to_run:
        print(f"\n=== Benchmarking Flux.1 [{m}] ===")
        summary = benchmark_model(
            model=m,
            prompt=prompt_text,
            prompt_key=prompt_key,
            steps=args.steps,
            n_images=args.n_images,
            image_size=args.image_size,
            repeats=args.repeats,
            warmup=args.warmup,
            base_seed=args.seed,
            models_dir=models_dir,
            adapter=args.adapter,
            fuse_adapter=args.fuse_adapter,
            no_t5_padding=args.no_t5_padding,
            extra_args=extra_args,
            verbose=args.verbose,
        )
        all_summaries.append(summary)
        _print_summary(summary)

    # Optional: JSON log
    if args.json_out:
        payload = {
            "tag": args.tag,
            "timestamp": time.time(),
            "hardware_note": os.uname().machine,
            "models_dir": str(models_dir),
            "runs": [s.to_dict() for s in all_summaries],
        }
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w") as f:
            json.dump(payload, f, indent=2)
        print(f"\nSaved benchmark JSON to {out_path}")


def _print_summary(summary: BenchmarkSummary) -> None:
    d = summary.to_dict()
    lat = d["latency"]
    print(
        f"  model: {d['model']} | steps={d['steps']} | "
        f"n_images={d['n_images']} | repeats={d['repeats']} "
        f"(warmup={d['warmup']})"
    )
    print(
        "  latency: "
        f"mean={lat['mean_s']:.3f}s, "
        f"p50={lat['p50_s']:.3f}s, "
        f"p90={lat['p90_s']:.3f}s, "
        f"min={lat['min_s']:.3f}s, "
        f"max={lat['max_s']:.3f}s"
    )
    print(f"  throughput: {lat['images_per_second']:.3f} images/s")
    if d.get("peak_memory_mb"):
        pm = d["peak_memory_mb"]
        print(
            f"  peak GPU memory (MLX): mean={pm['mean']:.1f} MB, "
            f"max={pm['max']:.1f} MB, min={pm['min']:.1f} MB"
        )
    rc = d.get("run_config", {})
    if rc.get("adapter") or rc.get("fuse_adapter"):
        print(
            "  adapter config: "
            f"adapter={rc.get('adapter')}, "
            f"fuse_adapter={rc.get('fuse_adapter')}, "
            f"no_t5_padding={rc.get('no_t5_padding')}"
        )


if __name__ == "__main__":
    main()

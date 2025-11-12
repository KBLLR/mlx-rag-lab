#!/usr/bin/env python
import argparse
import json
import time
import statistics as stats
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import torch
from audiocraft.models import MusicGen


# ---------------------------------------------------------------------
# Model + prompt registry
# ---------------------------------------------------------------------

MODEL_ALIASES = {
    "small": "facebook/musicgen-small",
    "medium": "facebook/musicgen-medium",
    "large": "facebook/musicgen-large",
    "melody": "facebook/musicgen-melody",
}

PROMPT_LIBRARY = {
    "techno_groove": "dark, minimal techno groove with punchy kick and hypnotic bass",
    "lofi_chill": "jazzy lo-fi beat with warm Rhodes, vinyl crackle and tape hiss",
    "cinematic": "epic orchestral score with sweeping strings, brass and huge drums",
    "ambient": "slow evolving ambient pads, soft texture, no percussion, meditative",
    "funk": "upbeat funk with clavinet, slap bass and tight drum kit",
}


# ---------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------

@dataclass
class RunConfig:
    model_id: str
    prompt: str
    duration: int
    temperature: float
    top_k: int
    top_p: float
    cfg_coef: float
    use_sampling: bool
    device: str


@dataclass
class RunResult:
    latency_s: float
    peak_memory_mb: Optional[float] = None


@dataclass
class BenchmarkSummary:
    model_id: str
    model_alias: str
    duration: int
    repeats: int
    warmup: int
    prompt: str
    latencies_s: List[float]
    peak_memory_mb: Optional[Dict[str, float]]

    def to_dict(self) -> Dict[str, Any]:
        percentile = lambda p: _percentile(self.latencies_s, p)
        total_time = sum(self.latencies_s)
        summary: Dict[str, Any] = {
            "model": self.model_alias,
            "model_id": self.model_id,
            "duration_s": self.duration,
            "repeats": self.repeats,
            "warmup": self.warmup,
            "prompt": self.prompt,
            "latency": {
                "mean_s": stats.mean(self.latencies_s),
                "std_s": stats.pstdev(self.latencies_s)
                if len(self.latencies_s) > 1
                else 0.0,
                "p50_s": percentile(50),
                "p90_s": percentile(90),
                "min_s": min(self.latencies_s),
                "max_s": max(self.latencies_s),
                "clips_per_second": self.repeats / total_time
                if total_time > 0
                else 0.0,
            },
        }
        if self.peak_memory_mb is not None:
            summary["peak_memory_mb"] = self.peak_memory_mb
        return summary


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = (len(ordered) - 1) * (p / 100.0)
    lower = int(idx)
    upper = min(lower + 1, len(ordered) - 1)
    weight = idx - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _select_device(user_choice: Optional[str] = None) -> str:
    if user_choice:
        return user_choice

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _reset_peak_memory(device: str) -> None:
    if device.startswith("cuda"):
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
    # Torch MPS has less formal memory APIs; skip for now.


def _get_peak_memory_mb(device: str) -> Optional[float]:
    if device.startswith("cuda"):
        return torch.cuda.max_memory_allocated() / (1024 ** 2)
    return None


def _load_model(model_id: str, device: str) -> MusicGen:
    print(f"Loading MusicGen model: {model_id} on device={device}")
    model = MusicGen.get_pretrained(model_id)
    model.to(device)
    return model


def run_musicgen_once(
    model: MusicGen,
    cfg: RunConfig,
    seed: Optional[int] = None,
) -> RunResult:
    if seed is not None:
        torch.manual_seed(seed)

    # Generation parameters
    gen_params = dict(
        duration=cfg.duration,
        temperature=cfg.temperature,
        top_k=cfg.top_k,
        top_p=cfg.top_p,
        cfg_coef=cfg.cfg_coef,
        use_sampling=cfg.use_sampling,
    )
    model.set_generation_params(**gen_params)

    _reset_peak_memory(cfg.device)

    t0 = time.perf_counter()
    _ = model.generate(
        descriptions=[cfg.prompt],
        progress=False,
    )
    t1 = time.perf_counter()

    peak_mb = _get_peak_memory_mb(cfg.device)

    return RunResult(latency_s=t1 - t0, peak_memory_mb=peak_mb)


def benchmark_model(
    alias: str,
    prompt: str,
    duration: int,
    repeats: int,
    warmup: int,
    temperature: float,
    top_k: int,
    top_p: float,
    cfg_coef: float,
    use_sampling: bool,
    device: str,
    base_seed: int,
) -> BenchmarkSummary:
    model_id = MODEL_ALIASES[alias]
    device = _select_device(device)

    cfg = RunConfig(
        model_id=model_id,
        prompt=prompt,
        duration=duration,
        temperature=temperature,
        top_k=top_k,
        top_p=top_p,
        cfg_coef=cfg_coef,
        use_sampling=use_sampling,
        device=device,
    )

    model = _load_model(model_id, device)

    latencies: List[float] = []
    mem_values: List[float] = []

    # Warmup (not recorded)
    for i in range(warmup):
        print(f"[{alias}] warmup run {i+1}/{warmup}")
        _ = run_musicgen_once(model, cfg, seed=base_seed + i)

    # Measured runs
    for i in range(repeats):
        print(f"[{alias}] benchmark run {i+1}/{repeats}")
        result = run_musicgen_once(model, cfg, seed=base_seed + warmup + i)
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

    return BenchmarkSummary(
        model_id=model_id,
        model_alias=alias,
        duration=duration,
        repeats=repeats,
        warmup=warmup,
        prompt=prompt,
        latencies_s=latencies,
        peak_memory_mb=mem_summary,
    )


def _print_summary(summary: BenchmarkSummary) -> None:
    d = summary.to_dict()
    lat = d["latency"]
    print(
        f"\n  model: {d['model']} ({d['model_id']}) | "
        f"duration={d['duration_s']}s | repeats={d['repeats']} (warmup={d['warmup']})"
    )
    print(
        "  latency: "
        f"mean={lat['mean_s']:.3f}s, "
        f"p50={lat['p50_s']:.3f}s, "
        f"p90={lat['p90_s']:.3f}s, "
        f"min={lat['min_s']:.3f}s, "
        f"max={lat['max_s']:.3f}s"
    )
    print(f"  throughput: {lat['clips_per_second']:.3f} clips/s")
    if d.get("peak_memory_mb"):
        pm = d["peak_memory_mb"]
        print(
            f"  peak GPU memory: mean={pm['mean']:.1f} MB, "
            f"max={pm['max']:.1f} MB, min={pm['min']:.1f} MB"
        )


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark MusicGen (audiocraft) on Apple Silicon / GPU."
    )

    parser.add_argument(
        "--models",
        type=str,
        default="medium",
        help=(
            "Comma-separated list of models to test from: "
            f"{','.join(MODEL_ALIASES.keys())} or 'all'"
        ),
    )

    # Prompt configuration
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Custom text prompt for generation.",
    )
    parser.add_argument(
        "--prompt-preset",
        type=str,
        choices=list(PROMPT_LIBRARY.keys()),
        default="techno_groove",
        help="Use one of the built-in music prompts.",
    )

    # Generation / sampling
    parser.add_argument("--duration", type=int, default=12, help="Seconds per clip.")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=250)
    parser.add_argument("--top-p", type=float, default=0.0)
    parser.add_argument("--cfg-coef", type=float, default=3.0)
    parser.add_argument(
        "--greedy",
        action="store_true",
        help="Disable sampling (use_sampling=False) if set.",
    )

    # Benchmarking
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1234)

    # Device / output
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Override device: 'mps', 'cuda', or 'cpu' (default: auto).",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default=None,
        help="Optional path to write JSON summary.",
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Optional tag for this run (e.g. 'm3-max-36gb-musicgen').",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Resolve prompt
    if args.prompt is not None:
        prompt = args.prompt
    else:
        prompt = PROMPT_LIBRARY[args.prompt_preset]

    # Resolve models
    if args.models.strip().lower() == "all":
        model_aliases = list(MODEL_ALIASES.keys())
    else:
        model_aliases = [
            m.strip() for m in args.models.split(",") if m.strip()
        ]
        for m in model_aliases:
            if m not in MODEL_ALIASES:
                raise SystemExit(
                    f"Unknown model alias '{m}'. "
                    f"Valid options: {', '.join(MODEL_ALIASES.keys())}, or 'all'."
                )

    use_sampling = not args.greedy

    all_summaries: List[BenchmarkSummary] = []

    for alias in model_aliases:
        print(f"\n=== Benchmarking MusicGen [{alias}] ===")
        summary = benchmark_model(
            alias=alias,
            prompt=prompt,
            duration=args.duration,
            repeats=args.repeats,
            warmup=args.warmup,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
            cfg_coef=args.cfg_coef,
            use_sampling=use_sampling,
            device=args.device,
            base_seed=args.seed,
        )
        _print_summary(summary)
        all_summaries.append(summary)

    if args.json_out:
        payload = {
            "tag": args.tag,
            "timestamp": time.time(),
            "hardware_note": f"{torch.get_num_threads()}-threads",
            "device": _select_device(args.device),
            "runs": [s.to_dict() for s in all_summaries],
        }
        with open(args.json_out, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"\nSaved benchmark JSON to {args.json_out}")


if __name__ == "__main__":
    main()

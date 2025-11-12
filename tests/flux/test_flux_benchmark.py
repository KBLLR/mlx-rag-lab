import subprocess
from pathlib import Path

import pytest

BASE_CMD = ["uv", "run", "python", "src/rag/cli/flux_txt2image.py"]
PROMPT = "benchmark astronaut on mars"
OUT_DIR = Path("tests/outputs/flux_benchmark")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _make_cmd(model: str) -> list[str]:
    return BASE_CMD + [
        PROMPT,
        "--model",
        model,
        "--steps",
        "4",
        "--n-images",
        "1",
        "--output",
        str(OUT_DIR),
        "--output-prefix",
        f"benchmark_{model}",
    ]


@pytest.mark.slow
def test_flux_schnell_benchmark(benchmark):
    cmd = _make_cmd("schnell")

    def run_once():
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)

    benchmark(run_once)


@pytest.mark.slow
def test_flux_dev_vs_schnell_relative_perf():
    """Very rough relative perf check using the benchmark module itself."""
    from benchmarks.flux_benchmark import benchmark_model

    prompt = PROMPT
    steps = 4
    n_images = 1
    image_size = 512

    schnell = benchmark_model(
        model="schnell",
        prompt=prompt,
        steps=steps,
        n_images=n_images,
        image_size=image_size,
        repeats=3,
        warmup=1,
        base_seed=123,
    )
    dev = benchmark_model(
        model="dev",
        prompt=prompt,
        steps=steps,
        n_images=n_images,
        image_size=image_size,
        repeats=3,
        warmup=1,
        base_seed=123,
    )

    s_mean = schnell.to_dict()["latency"]["mean_s"]
    d_mean = dev.to_dict()["latency"]["mean_s"]

    # This is intentionally loose; we just want to catch regressions.
    assert s_mean <= d_mean * 1.5, f"schnell is suspiciously slow vs dev: {s_mean:.2f}s vs {d_mean:.2f}s"

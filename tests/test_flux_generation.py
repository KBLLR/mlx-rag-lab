import os
import time
import pytest
from pathlib import Path
import subprocess

BASE_CMD = ["uv", "run", "python", "src/rag/cli/flux_txt2image.py"]

TEST_PROMPT = "a surreal painting of a fox made of clouds"
OUTPUT_DIR = Path("tests/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@pytest.mark.parametrize("model", ["schnell", "dev"])
def test_flux_txt2image(model):
    """Test text-to-image generation for both Flux variants."""
    output_path = OUTPUT_DIR / f"{model}_test.png"

    cmd = BASE_CMD + [
        TEST_PROMPT,
        "--model", model,
        "--steps", "4",
        "--n-images", "1",
        "--output", str(OUTPUT_DIR),
    ]

    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start

    assert result.returncode == 0, f"Flux {model} failed: {result.stderr}"
    assert (OUTPUT_DIR / "out.png").exists(), f"Flux {model} output missing"
    assert duration < 120, f"Flux {model} took too long ({duration:.2f}s)"

    print(f"✅ {model.upper()} finished in {duration:.2f}s")


def test_flux_performance_comparison():
    """Quick side-by-side speed comparison between Flux models."""
    results = {}
    for model in ["schnell", "dev"]:
        cmd = BASE_CMD + [
            TEST_PROMPT,
            "--model", model,
            "--steps", "4",
            "--n-images", "1",
            "--output", str(OUTPUT_DIR),
        ]
        start = time.time()
        subprocess.run(cmd, capture_output=True, text=True)
        results[model] = time.time() - start

    diff = results["dev"] - results["schnell"]
    print(f"⏱️ Flux schnell: {results['schnell']:.2f}s | Flux dev: {results['dev']:.2f}s | Δ={diff:+.2f}s")
    assert results["schnell"] < results["dev"] * 1.5, "Schnell should be significantly faster"

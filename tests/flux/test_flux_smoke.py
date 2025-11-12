import subprocess
from pathlib import Path

BASE_CMD = ["uv", "run", "python", "src/rag/cli/flux_txt2image.py"]
PROMPT = "a quick smoke test astronaut on mars"
OUT_DIR = Path("tests/outputs/flux_smoke")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _run(model: str) -> None:
    cmd = BASE_CMD + [
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
        f"smoke_{model}",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_flux_schnell_smoke():
    _run("schnell")


def test_flux_dev_smoke():
    _run("dev")

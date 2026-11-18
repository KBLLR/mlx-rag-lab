"""Console scripts must import and answer --help.

Regression: apps.rag_cli imported rag.models.qwen_reranker at module load.
rag.cli.entrypoints imported every app up front, so that missing module
crashed all twelve [project.scripts] targets before argparse could print help.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"


def _project_scripts() -> dict[str, str]:
    with PYPROJECT.open("rb") as handle:
        scripts = tomllib.load(handle)["project"]["scripts"]
    if not isinstance(scripts, dict) or not scripts:
        raise AssertionError("[project.scripts] is missing from pyproject.toml")
    return {str(name): str(target) for name, target in scripts.items()}


SCRIPTS = _project_scripts()


def _app_module_name(script: str) -> str:
    name = script.replace("-", "_")
    if not name.endswith("_cli"):
        name = f"{name}_cli"
    return f"apps.{name}"


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(ROOT / "src")
    root = str(ROOT)
    prior = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(part for part in (src, root, prior) if part)
    return env


def _metal_kernel_available() -> bool:
    """MusicGen builds an MLX Metal kernel at import. CPU MLX cannot."""
    try:
        import mlx.core as mx
    except Exception:
        return False
    try:
        mx.fast.metal_kernel(
            name="entrypoint_probe",
            input_names=[],
            output_names=["out"],
            source="out[thread_position_in_grid.x] = 1;",
        )
    except Exception:
        return False
    return True


METAL_KERNEL_AVAILABLE = _metal_kernel_available()


def _run_help(module_name: str, func_name: str, script: str) -> subprocess.CompletedProcess[str]:
    code = (
        "import sys\n"
        f"sys.argv = [{script!r}, '--help']\n"
        f"from {module_name} import {func_name} as main\n"
        "main()\n"
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=_subprocess_env(),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


@pytest.mark.parametrize("script", sorted(SCRIPTS))
def test_entry_point_module_imports_and_help(script: str) -> None:
    """Import the app module behind each script and run --help."""
    app_module = _app_module_name(script)
    if app_module == "apps.musicgen_cli" and not METAL_KERNEL_AVAILABLE:
        pytest.skip("musicgen_cli builds an MLX Metal kernel at import; no Metal backend")

    completed = _run_help(app_module, "main", script)
    output = f"{completed.stdout}\n{completed.stderr}"
    assert completed.returncode == 0, output
    assert "usage:" in output.lower(), output


@pytest.mark.parametrize("script", sorted(SCRIPTS))
def test_console_script_help(script: str) -> None:
    """Run the actual [project.scripts] callable."""
    if _app_module_name(script) == "apps.musicgen_cli" and not METAL_KERNEL_AVAILABLE:
        pytest.skip("musicgen_cli builds an MLX Metal kernel at import; no Metal backend")

    _module_name, func_name = SCRIPTS[script].split(":")
    completed = _run_help("rag.cli.entrypoints", func_name, script)
    output = f"{completed.stdout}\n{completed.stderr}"
    assert completed.returncode == 0, output
    assert "usage:" in output.lower(), output


def _import_app(module_name: str):
    """Import an apps.* module from the repo, not the editable namespace mapping."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    existing = sys.modules.get("apps")
    app_dir = str(ROOT / "apps")
    if existing is not None and app_dir not in list(getattr(existing, "__path__", [])):
        for name in list(sys.modules):
            if name == "apps" or name.startswith("apps."):
                del sys.modules[name]
    return importlib.import_module(module_name)


def test_qwen_reranker_import_is_lazy() -> None:
    """Missing qwen_reranker must not break import, and must fail only on use."""
    sys.modules.pop("rag.models.qwen_reranker", None)
    rag_cli = _import_app("apps.rag_cli")
    assert "rag.models.qwen_reranker" not in sys.modules

    with pytest.raises(SystemExit, match="--no-reranker"):
        rag_cli.load_qwen_reranker("mlx-community/mxbai-rerank-large-v2")

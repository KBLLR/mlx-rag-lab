import importlib
import sys
import types
from pathlib import Path

import pytest


def _import_with_stubbed_mlx(monkeypatch):
    """
    Ensure `src.rag.cli.flux_txt2image` can be imported in environments that lack MLX.
    """
    for name in ("src.rag.cli.flux_txt2image",):
        sys.modules.pop(name, None)

    fake_mlx = types.ModuleType("mlx")
    fake_core = types.ModuleType("mlx.core")
    fake_nn = types.ModuleType("mlx.nn")

    fake_core.load = lambda *args, **kwargs: ({}, {"lora_rank": "0", "lora_blocks": "0"})
    fake_core.eval = lambda *_args, **_kwargs: None
    fake_core.get_peak_memory = lambda: 0
    fake_core.reset_peak_memory = lambda: None
    fake_core.concatenate = lambda *args, **kwargs: args[0]
    fake_core.pad = lambda value, *_, **__kwargs: value
    fake_core.uint8 = int

    fake_nn.quantize = lambda *_args, **_kwargs: None

    fake_mlx.core = fake_core
    fake_mlx.nn = fake_nn

    fake_utils = types.ModuleType("mlx.utils")
    fake_utils.tree_unflatten = lambda *args, **kwargs: args[-1] if args else None

    class DummyFluxPipeline:
        def __init__(self, *args, **kwargs):
            pass

    dummy_flux_module = types.ModuleType("rag.models.flux.flux")
    dummy_flux_module.FluxPipeline = DummyFluxPipeline
    dummy_flux_module.__package__ = "rag.models.flux"

    dummy_flux_package = types.ModuleType("rag.models.flux")
    dummy_flux_package.__path__ = []
    dummy_flux_package.flux = dummy_flux_module
    dummy_flux_package.FluxPipeline = DummyFluxPipeline
    dummy_flux_package.__package__ = "rag.models.flux"

    monkeypatch.setitem(sys.modules, "mlx", fake_mlx)
    monkeypatch.setitem(sys.modules, "mlx.core", fake_core)
    monkeypatch.setitem(sys.modules, "mlx.nn", fake_nn)
    monkeypatch.setitem(sys.modules, "mlx.utils", fake_utils)
    monkeypatch.setitem(sys.modules, "rag.models.flux", dummy_flux_package)
    monkeypatch.setitem(sys.modules, "rag.models.flux.flux", dummy_flux_module)

    monkeypatch.syspath_prepend(str(Path.cwd() / "src"))

    return importlib.import_module("rag.cli.flux_txt2image")


@pytest.fixture()
def flux_txt2image(monkeypatch):
    return _import_with_stubbed_mlx(monkeypatch)


def test_parse_image_size_accepts_int_literals(flux_txt2image):
    assert flux_txt2image.parse_image_size_arg(256) == (256, 256)


def test_parse_image_size_accepts_tuple_inputs(flux_txt2image):
    assert flux_txt2image.parse_image_size_arg((480, 640)) == (480, 640)


def test_parse_image_size_handles_wxh_strings(flux_txt2image):
    assert flux_txt2image.parse_image_size_arg("512x768") == (512, 768)


def test_parse_image_size_rejects_invalid_strings(flux_txt2image):
    with pytest.raises(ValueError):
        flux_txt2image.parse_image_size_arg("512x768x32")

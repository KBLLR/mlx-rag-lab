import importlib


def _capture_main(module_name: str):
    module = importlib.import_module(module_name)
    assert hasattr(module, "main")
    return module.main


def test_rag_cli_entrypoint_imports():
    entrypoints = importlib.import_module("rag.cli.entrypoints")
    assert callable(entrypoints.rag_cli_main)
    _capture_main("apps.rag_cli")


def test_flux_cli_entrypoint_imports():
    entrypoints = importlib.import_module("rag.cli.entrypoints")
    assert callable(entrypoints.flux_cli_main)
    _capture_main("apps.flux_cli")


def test_bench_cli_entrypoint_imports():
    entrypoints = importlib.import_module("rag.cli.entrypoints")
    assert callable(entrypoints.bench_cli_main)
    _capture_main("apps.bench_cli")

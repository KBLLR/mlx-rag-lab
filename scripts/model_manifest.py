#!/usr/bin/env python3
"""
Utility helpers for maintaining per-model metadata manifests under `mlx-models/`.

Usage examples:

    # Refresh manifests for flux models without scanning the full directory tree
    python scripts/model_manifest.py sync --models flux-schnell flux-dev --fast

    # Show a quick summary table
    python scripts/model_manifest.py show
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_MODELS_DIR = Path(os.environ.get("MLX_MODELS_DIR", "mlx-models"))
DEFAULT_REGISTRY = Path("docs/models/model_registry.json")
MANIFEST_DIR_NAME = "manifests"
MANIFEST_SUFFIX = ".manifest.json"


def load_registry(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if "models" in data:
        models = data["models"]
    else:
        models = data
    if not isinstance(models, dict):
        raise ValueError("Model registry must be a mapping of model_name → metadata")
    return models


def resolve_targets(
    requested: Optional[List[str]],
    models_dir: Path,
    registry: Dict[str, Any],
    include_unregistered: bool,
) -> List[str]:
    if requested:
        return sorted({name.strip() for name in requested if name.strip()})

    targets = set(registry.keys())
    if include_unregistered or not targets:
        for entry in models_dir.iterdir():
            if entry.name == MANIFEST_DIR_NAME:
                continue
            if entry.is_dir():
                targets.add(entry.name)
    return sorted(targets)


def collect_storage_stats(model_dir: Path, fast: bool) -> Dict[str, Any]:
    stats: Dict[str, Any] = {"present": model_dir.exists(), "file_count": 0, "size_bytes": 0, "last_modified": None}
    if not model_dir.exists():
        return stats
    if fast:
        stats["file_count"] = None
        stats["size_bytes"] = None
        return stats

    file_count = 0
    size_bytes = 0
    last_modified: Optional[float] = None

    for path in model_dir.rglob("*"):
        if not path.is_file():
            continue
        stat = path.stat()
        file_count += 1
        size_bytes += stat.st_size
        if last_modified is None or stat.st_mtime > last_modified:
            last_modified = stat.st_mtime

    stats["file_count"] = file_count
    stats["size_bytes"] = size_bytes
    if last_modified is not None:
        stats["last_modified"] = (
            datetime.fromtimestamp(last_modified, tz=timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
    return stats


def coerce_value(raw: str) -> Any:
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def apply_overrides(manifest: Dict[str, Any], overrides: Iterable[str]) -> None:
    for override in overrides:
        if "=" not in override:
            raise ValueError(f"Override '{override}' must use key=value syntax")
        key, raw_value = override.split("=", 1)
        path_parts = [part for part in key.strip().split(".") if part]
        if not path_parts:
            raise ValueError(f"Invalid override path in '{override}'")
        value = coerce_value(raw_value.strip())
        cursor: Any = manifest
        for part in path_parts[:-1]:
            if not isinstance(cursor, dict):
                raise ValueError(f"Cannot set nested key '{key}' on non-dict segment '{part}'")
            cursor = cursor.setdefault(part, {})
        if not isinstance(cursor, dict):
            raise ValueError(f"Cannot assign '{key}' because parent is not a dict")
        cursor[path_parts[-1]] = value


def manifest_path_for(models_dir: Path, model_name: str) -> Path:
    manifest_dir = models_dir / MANIFEST_DIR_NAME
    manifest_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{model_name}{MANIFEST_SUFFIX}"
    return manifest_dir / file_name


def sync_manifests(args: argparse.Namespace) -> int:
    models_dir = args.models_dir.resolve()
    registry = load_registry(args.registry.resolve()) if args.registry else {}
    targets = resolve_targets(args.models, models_dir, registry, args.include_unregistered)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    if not targets:
        print("No models to sync. Provide --models or add entries to the registry.")
        return 0

    for model_name in targets:
        manifest_file = manifest_path_for(models_dir, model_name)
        existing: Dict[str, Any] = {}
        if manifest_file.exists():
            with manifest_file.open("r", encoding="utf-8") as fh:
                existing = json.load(fh)

        registry_entry = registry.get(model_name, {})
        model_dir = models_dir / model_name
        storage_stats = collect_storage_stats(model_dir, fast=args.fast)

        manifest: Dict[str, Any] = existing if isinstance(existing, dict) else {}
        manifest["model"] = model_name
        manifest["model_path"] = str(model_dir.relative_to(models_dir))

        for key in ("source_id", "variant", "precision", "quantization"):
            value = registry_entry.get(key)
            if value and key not in manifest:
                manifest[key] = value

        reg_tags = registry_entry.get("tags") or []
        manifest_tags = set(manifest.get("tags", []))
        manifest_tags.update(reg_tags)
        if manifest_tags:
            manifest["tags"] = sorted(manifest_tags)

        if not manifest.get("notes") and registry_entry.get("notes"):
            manifest["notes"] = registry_entry["notes"]
        if args.notes:
            manifest["notes"] = args.notes

        adapter_block = manifest.get("adapter", {})
        adapter_block.setdefault("allows_lora", registry_entry.get("allows_lora", True))
        adapter_block.setdefault("currently_fused", registry_entry.get("currently_fused", False))
        if "fused_from" not in adapter_block and registry_entry.get("default_adapter_source"):
            adapter_block["fused_from"] = registry_entry["default_adapter_source"]
        manifest["adapter"] = adapter_block

        manifest["storage"] = storage_stats
        manifest["generated_at"] = timestamp

        apply_overrides(manifest, args.overrides or [])

        if args.dry_run:
            print(json.dumps(manifest, indent=2))
            continue

        with manifest_file.open("w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
        rel_path = manifest_file.relative_to(Path.cwd())
        print(f"[manifest] wrote {rel_path}")

    return 0


def model_name_from_manifest(path: Path) -> str:
    name = path.name
    if name.endswith(MANIFEST_SUFFIX):
        return name[: -len(MANIFEST_SUFFIX)]
    return path.stem


def show_manifests(args: argparse.Namespace) -> int:
    models_dir = args.models_dir.resolve()
    manifest_dir = models_dir / MANIFEST_DIR_NAME
    if not manifest_dir.exists():
        print("No manifest directory found. Run the 'sync' command first.")
        return 1

    filter_set = {name.strip() for name in args.models} if args.models else None
    manifest_files = sorted(
        p
        for p in manifest_dir.glob(f"*{MANIFEST_SUFFIX}")
        if not filter_set or model_name_from_manifest(p) in filter_set
    )
    if not manifest_files:
        print("No manifests match the provided filters.")
        return 0

    rows = []
    for file in manifest_files:
        with file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        rows.append(
            {
                "model": data.get("model", model_name_from_manifest(file)),
                "quant": data.get("quantization", "unknown"),
                "fused": data.get("adapter", {}).get("currently_fused", False),
                "allows_lora": data.get("adapter", {}).get("allows_lora", True),
                "present": data.get("storage", {}).get("present", False),
                "size": data.get("storage", {}).get("size_bytes"),
            }
        )

    if args.as_json:
        print(json.dumps(rows, indent=2))
        return 0

    headers = ["model", "quant", "present", "size(MB)", "fused", "allows_lora"]
    print(" | ".join(headers))
    print("-" * 64)
    for row in rows:
        size_mb = "n/a"
        if isinstance(row["size"], (int, float)) and row["size"] is not None:
            size_mb = f"{row['size'] / (1024**2):.1f}"
        print(
            f"{row['model']} | {row['quant']} | {row['present']} | "
            f"{size_mb} | {row['fused']} | {row['allows_lora']}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage mlx-model metadata manifests.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--models-dir", type=Path, default=DEFAULT_MODELS_DIR, help="Base directory for MLX models.")

    sync_parser = subparsers.add_parser("sync", parents=[common], help="Create or update manifests.")
    sync_parser.add_argument("--models", nargs="+", help="Specific model names to sync.")
    sync_parser.add_argument(
        "--include-unregistered",
        action="store_true",
        help="Also create manifests for directories not present in the registry.",
    )
    sync_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Path to the model registry json.")
    sync_parser.add_argument("--fast", action="store_true", help="Skip deep directory scans for size stats.")
    sync_parser.add_argument(
        "--override",
        dest="overrides",
        action="append",
        default=[],
        help="Override manifest fields (dot.notation) via key=value.",
    )
    sync_parser.add_argument("--notes", type=str, help="Override the manifest notes field for this run.")
    sync_parser.add_argument("--dry-run", action="store_true", help="Print manifests instead of writing files.")
    sync_parser.set_defaults(func=sync_manifests)

    show_parser = subparsers.add_parser("show", parents=[common], help="Display manifest summaries.")
    show_parser.add_argument("--models", nargs="+", help="Filter to specific model names.")
    show_parser.add_argument("--as-json", action="store_true", help="Emit the summary as JSON.")
    show_parser.set_defaults(func=show_manifests)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

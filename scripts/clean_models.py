#!/usr/bin/env python3
"""
Curate local MLX model caches + Hugging Face caches using manifest metadata.

Examples:

    # Preview which fused Flux models could be deleted (no files touched)
    python scripts/clean_models.py preview --fused-only

    # Actually delete a specific model directory after previewing
    python scripts/clean_models.py preview --models flux-schnell --apply --yes

    # Forward to huggingface-cli scan-cache for HF cache hygiene
    python scripts/clean_models.py hf --scan
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

DEFAULT_MODELS_DIR = Path(os.environ.get("MLX_MODELS_DIR", "mlx-models"))
MANIFEST_SUFFIX = ".manifest.json"


@dataclass
class ManifestRecord:
    name: str
    path: Path
    metadata: Dict[str, Any]

    @property
    def tags(self) -> List[str]:
        return list(self.metadata.get("tags", []))

    @property
    def quantization(self) -> Optional[str]:
        return self.metadata.get("quantization")

    @property
    def adapter_state(self) -> Dict[str, Any]:
        return self.metadata.get("adapter", {})

    @property
    def storage(self) -> Dict[str, Any]:
        return self.metadata.get("storage", {})


def load_manifests(models_dir: Path) -> List[ManifestRecord]:
    manifest_dir = models_dir / "manifests"
    if not manifest_dir.exists():
        raise SystemExit("Manifest directory missing. Run scripts/model_manifest.py sync first.")

    records: List[ManifestRecord] = []
    for manifest_file in sorted(manifest_dir.glob(f"*{MANIFEST_SUFFIX}")):
        with manifest_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        model_name = data.get("model")
        if not model_name:
            continue
        model_path = models_dir / data.get("model_path", model_name)
        records.append(ManifestRecord(name=model_name, path=model_path, metadata=data))
    return records


def filter_records(
    records: Sequence[ManifestRecord],
    models: Optional[Sequence[str]],
    tags: Optional[Sequence[str]],
    quantization: Optional[Sequence[str]],
    fused_only: bool,
    missing_only: bool,
) -> List[ManifestRecord]:
    model_filter = {m.strip() for m in models} if models else None
    tag_filter = {t.strip() for t in tags} if tags else None
    quant_filter = {q.strip() for q in quantization} if quantization else None

    selected: List[ManifestRecord] = []
    for record in records:
        if model_filter and record.name not in model_filter:
            continue
        if fused_only and not record.adapter_state.get("currently_fused", False):
            continue
        storage = record.storage
        if missing_only and storage.get("present", True):
            continue
        if tag_filter:
            record_tags = set(record.tags)
            if not tag_filter.intersection(record_tags):
                continue
        if quant_filter and (record.quantization not in quant_filter):
            continue
        selected.append(record)
    return selected


def ensure_size_stats(record: ManifestRecord) -> Optional[int]:
    storage = record.storage
    if storage.get("size_bytes") is not None:
        return storage["size_bytes"]
    if not record.path.exists():
        return None
    total = 0
    for path in record.path.rglob("*"):
        if path.is_file():
            total += path.stat().st_size
    storage["size_bytes"] = total
    storage["file_count"] = storage.get("file_count") or 0
    storage["present"] = True
    return total


def human_size(size_bytes: Optional[int]) -> str:
    if size_bytes is None:
        return "n/a"
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size_bytes)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"


def preview_cleanup(args: argparse.Namespace) -> int:
    models_dir = args.models_dir.resolve()
    records = filter_records(
        load_manifests(models_dir),
        models=args.models,
        tags=args.tags,
        quantization=args.quantization,
        fused_only=args.fused_only,
        missing_only=args.missing_only,
    )

    if not records:
        print("No model directories match the provided filters.")
        return 0

    total_bytes = 0
    print("Candidate directories:")
    print("-" * 72)
    for record in records:
        size_bytes = record.storage.get("size_bytes")
        if size_bytes is None and args.compute_size:
            size_bytes = ensure_size_stats(record)
        present = record.storage.get("present", False)
        size_label = human_size(size_bytes)
        fused_flag = "fused" if record.adapter_state.get("currently_fused") else "base"
        print(f"{record.name:20} | {fused_flag:5} | {size_label:>10} | present={present} | {record.path}")
        if present and size_bytes:
            total_bytes += size_bytes

    print("-" * 72)
    print(f"Total reclaimable (if all deleted): {human_size(total_bytes)}")

    if not args.apply:
        print("\nDry-run only. Pass --apply --yes to delete the listed directories.")
        return 0

    if not args.yes:
        response = input("Delete the directories above? [y/N]: ").strip().lower()
        if response not in {"y", "yes"}:
            print("Aborted.")
            return 0

    for record in records:
        if not record.path.exists():
            print(f"[skip] {record.path} does not exist.")
            continue
        shutil.rmtree(record.path)
        print(f"[deleted] {record.path}")

    print("Done. Re-run scripts/model_manifest.py sync to refresh manifests.")
    return 0


def run_hf_cache(args: argparse.Namespace) -> int:
    cli = shutil.which("huggingface-cli")
    if not cli:
        print("huggingface-cli not found in PATH. Install via `pip install huggingface_hub`.")
        return 1

    env = os.environ.copy()
    if args.hf_home:
        env["HF_HOME"] = args.hf_home

    if args.scan:
        cmd = [cli, "scan-cache"]
    elif args.pattern:
        cmd = [cli, "delete-cache", "--pattern", args.pattern]
        if not args.yes:
            response = input(f"Run `{' '.join(cmd)}` ? [y/N]: ").strip().lower()
            if response not in {"y", "yes"}:
                print("Aborted.")
                return 0
    else:
        print("Specify --scan or --pattern to take action.")
        return 1

    print(" ".join(cmd))
    if args.dry_run:
        return 0

    subprocess.run(cmd, check=True, env=env)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clean up local MLX models + HF caches using manifest metadata.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preview_parser = subparsers.add_parser("preview", help="Preview / delete model directories under mlx-models.")
    preview_parser.add_argument("--models-dir", type=Path, default=DEFAULT_MODELS_DIR, help="Base MLX models directory.")
    preview_parser.add_argument("--models", nargs="+", help="Filter to exact model names (e.g., flux-schnell).")
    preview_parser.add_argument("--tags", nargs="+", help="Filter by manifest tags.")
    preview_parser.add_argument("--quantization", nargs="+", help="Filter by quantization labels (fp16, 4bit, etc.).")
    preview_parser.add_argument("--fused-only", action="store_true", help="Only include manifests marked as fused.")
    preview_parser.add_argument("--missing-only", action="store_true", help="Only show manifests whose folders are missing.")
    preview_parser.add_argument("--compute-size", action="store_true", help="Walk folders to compute current disk usage.")
    preview_parser.add_argument("--apply", action="store_true", help="Delete the selected directories.")
    preview_parser.add_argument("--yes", action="store_true", help="Skip confirmation prompts.")
    preview_parser.set_defaults(func=preview_cleanup)

    hf_parser = subparsers.add_parser("hf", help="Forward helper for huggingface-cli cache hygiene.")
    hf_parser.add_argument("--hf-home", type=str, help="Override HF_HOME for the command.")
    hf_parser.add_argument("--scan", action="store_true", help="Run `huggingface-cli scan-cache`.")
    hf_parser.add_argument(
        "--pattern",
        type=str,
        help="Pass a pattern to `huggingface-cli delete-cache --pattern ...` to prune matching repos.",
    )
    hf_parser.add_argument("--dry-run", action="store_true", help="Print the huggingface-cli command without executing.")
    hf_parser.add_argument("--yes", action="store_true", help="Skip confirmation before delete-cache.")
    hf_parser.set_defaults(func=run_hf_cache)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

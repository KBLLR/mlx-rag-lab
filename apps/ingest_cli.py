"""
Ingestion CLI wrapper - builds vector databases from PDF documents.
"""

import sys
from pathlib import Path

# Ensure src is in path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    """Entry point for ingest CLI."""
    # Import and run the actual ingestion module
    from rag.ingestion.create_vdb import (
        console,
        gather_pdf_paths,
        ingest_bank,
        ingest_multiple_banks,
    )
    import argparse

    parser = argparse.ArgumentParser(description="Create Vector DBs from PDF files.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--pdfs",
        nargs="+",
        help="Explicit list of PDF files or directories containing PDFs.",
    )
    group.add_argument(
        "--banks-root",
        type=str,
        help="Path whose immediate subfolders are treated as knowledge banks (one VDB per subfolder).",
    )

    parser.add_argument(
        "--vdb",
        type=str,
        default="var/indexes/combined_vdb.npz",
        help="Output path when using --pdfs (ignored for --banks-root).",
    )
    parser.add_argument(
        "--bank-name",
        type=str,
        help="Optional bank name when using --pdfs. Defaults to the VDB filename stem.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="var/indexes",
        help="Directory where per-bank indexes are written when using --banks-root.",
    )
    parser.add_argument(
        "--mlx-batch-size",
        type=int,
        default=4,
        help="Batch size for the mlx.data pipeline.",
    )
    parser.add_argument(
        "--mlx-prefetch",
        type=int,
        default=8,
        help="Number of batches to prefetch in the mlx.data pipeline.",
    )

    args = parser.parse_args()

    if args.banks_root:
        banks_root = Path(args.banks_root).expanduser().resolve()
        output_dir = Path(args.output_dir).expanduser().resolve()
        summary = ingest_multiple_banks(
            banks_root,
            output_dir,
            mlx_batch_size=args.mlx_batch_size,
            mlx_prefetch=args.mlx_prefetch,
        )
        if not summary:
            console.print(
                "[yellow]No banks were processed. Ensure the root contains subfolders with PDFs.[/yellow]"
            )
        else:
            console.print(f"[green]Completed ingestion for banks: {summary}[/green]")
    else:
        pdf_paths = gather_pdf_paths(args.pdfs)
        if not pdf_paths:
            raise SystemExit("No PDFs found for ingestion.")
        vdb_path = Path(args.vdb).expanduser().resolve()
        vdb_path.parent.mkdir(parents=True, exist_ok=True)
        bank_name = args.bank_name or vdb_path.stem
        processed = ingest_bank(
            bank_name,
            pdf_paths,
            vdb_path,
            mlx_batch_size=args.mlx_batch_size,
            mlx_prefetch=args.mlx_prefetch,
        )
        if processed == 0:
            console.print("[yellow]No PDFs produced embeddings. No VDB written.[/yellow]")


if __name__ == "__main__":
    main()

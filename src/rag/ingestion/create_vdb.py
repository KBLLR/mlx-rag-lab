import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from unstructured.partition.pdf import partition_pdf

try:
    import mlx.data as dx
except ImportError as exc:
    raise SystemExit(
        "The ingestion pipeline now requires `mlx-data`. Install it with `uv add mlx-data`."
    ) from exc

from rag.retrieval.vdb import CHUNK_OVERLAP, CHUNK_SIZE, VectorDB

console = Console()


def extract_text(pdf_path: Path) -> str:
    elements = partition_pdf(filename=str(pdf_path))
    return "\n\n".join([e.text for e in elements if getattr(e, "text", "")])


def write_metadata(vdb_path: Path, bank_name: str, document_paths: List[str], source_root: Path | None) -> None:
    meta = {
        "bank": bank_name,
        "index_path": str(vdb_path),
        "document_names": document_paths,
        "source_root": str(source_root) if source_root else None,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "embedding_model": "vegaluisjose/mlx-rag",
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    meta_path = vdb_path.with_suffix(vdb_path.suffix + ".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2))


def gather_pdf_paths(paths: List[str]) -> List[Path]:
    collected: List[Path] = []
    for path_str in paths:
        path = Path(path_str).expanduser().resolve()
        if path.is_dir():
            collected.extend(sorted(path.rglob("*.pdf")))
        elif path.suffix.lower() == ".pdf":
            collected.append(path)
        else:
            console.print(f"[yellow]Skipping non-PDF input: {path}[/yellow]")
    return collected


def iter_documents_mlx(
    pdf_paths: List[Path], *, batch_size: int = 4, prefetch: int = 8
) -> Iterator[Tuple[str, str]]:
    if not pdf_paths:
        return iter(())

    samples = [{"pdf_path": str(path)} for path in pdf_paths]
    buffer = dx.buffer_from_vector(samples)

    def _load_text(sample):
        path = Path(str(sample["pdf_path"]))
        sample["text"] = extract_text(path)
        sample["pdf_path"] = str(path)
        return sample

    batch_size = max(1, batch_size)
    prefetch = max(1, prefetch)
    num_threads = max(1, prefetch // 2)

    stream = (
        buffer.shuffle()
        .to_stream()
        .sample_transform(_load_text)
        .batch(batch_size)
        .prefetch(prefetch, num_threads)
    )

    def generator():
        for batch in stream:
            paths = batch["pdf_path"]
            texts = batch["text"]
            for path, text in zip(paths, texts):
                yield str(path), str(text)

    return generator()


def ingest_bank(
    bank_name: str,
    pdf_paths: List[Path],
    vdb_path: Path,
    source_root: Path | None = None,
    *,
    mlx_batch_size: int = 4,
    mlx_prefetch: int = 8,
) -> int:
    if not pdf_paths:
        console.print(f"[yellow]No PDFs found for bank '{bank_name}'. Skipping.[/yellow]")
        return 0

    vdb = VectorDB()
    processed_docs: List[str] = []

    progress_columns = [
        SpinnerColumn(),
        TextColumn(f"[progress.description]{bank_name}:{{task.completed}}/{{task.total}} PDFs[/progress.description]"),
        BarColumn(),
        TimeElapsedColumn(),
    ]

    doc_iter = iter_documents_mlx(
        pdf_paths, batch_size=mlx_batch_size, prefetch=mlx_prefetch
    )

    with Progress(*progress_columns, console=console) as progress:
        task_id = progress.add_task(f"Ingesting {bank_name}", total=len(pdf_paths))
        seen = 0
        for doc_path, text in doc_iter:
            seen += 1
            if not text.strip():
                console.print(f"[yellow]No text extracted from {doc_path}. Skipping.[/yellow]")
            else:
                vdb.ingest(content=text, document_name=doc_path)
                processed_docs.append(doc_path)
            progress.update(task_id, completed=min(seen, len(pdf_paths)))

    if not processed_docs:
        console.print(f"[yellow]Bank '{bank_name}' produced no embeddings. Nothing saved.[/yellow]")
        return 0

    vdb.savez(vdb_path)
    write_metadata(vdb_path, bank_name, processed_docs, source_root)
    console.print(f"[green]Saved bank '{bank_name}' → {vdb_path} ({len(processed_docs)} PDFs).[/green]")
    return len(processed_docs)


def ingest_multiple_banks(
    banks_root: Path,
    output_dir: Path,
    *,
    mlx_batch_size: int = 4,
    mlx_prefetch: int = 8,
) -> Dict[str, int]:
    output: Dict[str, int] = {}
    for child in sorted(p for p in banks_root.iterdir() if p.is_dir()):
        pdfs = sorted(child.rglob("*.pdf"))
        bank_name = child.name
        bank_output_dir = output_dir / bank_name
        bank_output_dir.mkdir(parents=True, exist_ok=True)
        vdb_path = bank_output_dir / "vdb.npz"
        count = ingest_bank(
            bank_name,
            pdfs,
            vdb_path,
            source_root=child,
            mlx_batch_size=mlx_batch_size,
            mlx_prefetch=mlx_prefetch,
        )
        if count:
            output[bank_name] = count
    return output


if __name__ == "__main__":
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
        default="models/indexes/combined_vdb.npz",
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
        default="models/indexes",
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
            console.print("[yellow]No banks were processed. Ensure the root contains subfolders with PDFs.[/yellow]")
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

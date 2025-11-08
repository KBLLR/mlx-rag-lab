import argparse
import os
from pathlib import Path
from typing import List
from rag.retrieval.vdb import VectorDB
from unstructured.partition.pdf import partition_pdf
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.console import Console

console = Console()

def process_pdfs(pdf_paths: List[str]):
    all_elements = []
    successfully_processed_paths = []

    progress_columns = [
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ]
    with Progress(*progress_columns, console=console) as progress:
        task = progress.add_task("Processing PDFs...", total=len(pdf_paths))
        for pdf_path_str in pdf_paths:
            pdf_path = Path(pdf_path_str).expanduser().resolve()
            if not pdf_path.exists():
                console.print(f"[yellow]Skipping missing PDF: {pdf_path}[/yellow]")
                progress.update(task, advance=1)
                continue

            console.print(f"[INFO] Processing {pdf_path}...")
            elements = partition_pdf(
                filename=str(pdf_path),
                # strategy="hi_res", # You can uncomment and set a strategy if needed
            )
            all_elements.extend(elements)
            successfully_processed_paths.append(str(pdf_path))
            progress.update(task, advance=1)

    return all_elements, successfully_processed_paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Vector DB from PDF files")
    # Input
    parser.add_argument(
        "--pdfs",
        nargs="+",
        help="The paths to the input PDF files (can be multiple)",
        required=True,
    )
    # Output
    parser.add_argument(
        "--vdb",
        type=str,
        default="models/indexes/combined_vdb.npz",
        help="The path to store the vector DB",
    )
    args = parser.parse_args()

    vdb_instance = VectorDB()
    
    elements, processed_pdf_paths = process_pdfs(args.pdfs)
    combined_content = "\n\n".join([e.text for e in elements])

    if not combined_content.strip():
        print("[WARN] No content extracted from provided PDFs. Vector database will be empty.")
    else:
        vdb_instance.ingest(content=combined_content, document_names=processed_pdf_paths)
        vdb_instance.savez(args.vdb)
        print(f"Vector database created at {args.vdb} from {len(processed_pdf_paths)} PDF(s).")
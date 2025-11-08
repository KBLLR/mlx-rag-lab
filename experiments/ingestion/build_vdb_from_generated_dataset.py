import json
from pathlib import Path
from typing import List, Dict, Any

import ollama # Import ollama for embedding model

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from rag.retrieval.vdb import VectorDB
from libs.ollama_core.embedding_engine import OllamaEmbeddingEngine # Use OllamaEmbeddingEngine

console = Console()

# --- Configuration ---
GENERATED_DATASET_PATH = "var/benchmarking/generated_qa_dataset.json"
OUTPUT_VDB_PATH = "models/indexes/combined_vdb.npz"
EMBEDDING_MODEL_ID = "nomic-embed-text:latest" # Using Ollama embedding model

def build_vdb_from_dataset():
    console.print(f"[bold cyan]Starting VDB build from generated dataset...[/bold cyan]")
    console.print(f"  Generated Dataset: {GENERATED_DATASET_PATH}")
    console.print(f"  Output VDB Path: {OUTPUT_VDB_PATH}")
    console.print(f"  Embedding Model: {EMBEDDING_MODEL_ID}\n")

    # --- Load dataset ---
    dataset_path = Path(GENERATED_DATASET_PATH)
    if not dataset_path.exists():
        console.print(f"[red]Error: Dataset not found at {dataset_path}. "
                      f"Please run `generate_qa_dataset.py` first.[/red]")
        exit(1)

    with open(dataset_path, "r", encoding="utf-8") as f:
        generated_dataset = json.load(f)

    if not generated_dataset:
        console.print("[yellow]Warning: Generated dataset is empty.[/yellow]")
        exit(0)

    console.print(f"[bold cyan]Loaded {len(generated_dataset)} Q&A pairs.[/bold cyan]")

    # --- Collect texts & sources ---
    all_texts: List[str] = []
    all_sources: List[str] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Collecting chunks for ingestion...", total=len(generated_dataset))
        for entry in generated_dataset:
            text = entry["relevant_document_text"]
            source = entry["relevant_document_source"]
            all_texts.append(text)
            all_sources.append(source)
            progress.update(task, advance=1)

    console.print("[bold cyan]Embedding and ingesting all texts...[/bold cyan]")

    # --- Initialize VectorDB with embedding model ---
    try:
        embedding_model = OllamaEmbeddingEngine(model_id=EMBEDDING_MODEL_ID)
        console.print(f"[bold cyan]Initialized OllamaEmbeddingEngine with model: {EMBEDDING_MODEL_ID}[/bold cyan]")
    except Exception as e:
        console.print(f"[red]Error initializing OllamaEmbeddingEngine: {e}[/red]")
        exit(1)

    vdb = VectorDB(embedding_model=embedding_model) # Initialize VectorDB with the embedding model

    try:
        # Ingest each chunk with its source name
        # VectorDB.ingest expects content as a list of dicts, each with 'text' and 'source'
        content_for_vdb = [{'text': t, 'source': s} for t, s in zip(all_texts, all_sources)]
        vdb.ingest(content=content_for_vdb)

        console.print("[bold cyan]Ingestion complete.[/bold cyan]")

    except Exception as e:
        console.print(f"[red]Error during VDB ingestion: {e}[/red]")
        raise SystemExit(1)

    # --- Save combined VDB ---
    Path(OUTPUT_VDB_PATH).parent.mkdir(parents=True, exist_ok=True)
    vdb.savez(OUTPUT_VDB_PATH)

    console.print(
        f"[bold green]VDB built successfully from {len(all_texts)} chunks "
        f"and saved to {OUTPUT_VDB_PATH}[/bold green]"
    )


if __name__ == "__main__":
    build_vdb_from_dataset()
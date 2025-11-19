import argparse
import gc
import json
import signal
import sys
from pathlib import Path
from textwrap import shorten

from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from libs.mlx_core.model_engine import MLXModelEngine
from rag.chat.templates import strip_channel_controls
from rag.models.qwen_reranker import QwenReranker
from rag.retrieval.vdb import VectorDB
from rag.ingestion.create_vdb import gather_pdf_paths, extract_text, write_metadata
from ui import FramedApp, get_console, label, build_rag_dashboard

console = get_console()

DEFAULT_INDEX_ROOT = Path("var/indexes")
DEFAULT_SOURCE_ROOT = Path("var/source_docs")
DEFAULT_COLLECTION = "default"
DEFAULT_MODEL_ID = "mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit"
DEFAULT_RERANKER_ID = "mlx-community/mxbai-rerank-large-v2"

# Global references for cleanup
_model_engine = None
_reranker = None
_vdb = None
_current_collection = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MLX RAG CLI – ask questions over collection-based vector indexes (Phase 4)."
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=DEFAULT_COLLECTION,
        help="Collection name to query/manage (Phase 4 architecture).",
    )
    parser.add_argument(
        "--index-root",
        type=Path,
        default=DEFAULT_INDEX_ROOT,
        help="Root directory for all collection indexes.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=DEFAULT_SOURCE_ROOT,
        help="Root directory for source documents (organized by collection subdirs).",
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default=DEFAULT_MODEL_ID,
        help="MLX model ID used for answer generation.",
    )
    parser.add_argument(
        "--reranker-id",
        type=str,
        default=DEFAULT_RERANKER_ID,
        help="Optional cross-encoder for re-ranking retrieved chunks.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of reranked documents to keep for the context prompt.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Max tokens for the MLX text model.",
    )
    parser.add_argument(
        "--no-reranker",
        action="store_true",
        help="Skip reranking step (use raw VectorDB scores).",
    )
    return parser


def format_context(chunks: list[dict], max_len: int = 180) -> tuple[str, str]:
    if not chunks:
        return "", ""
    context_lines = []
    summary_lines = []
    for chunk in chunks:
        text = chunk.get("text", "")
        source = chunk.get("source", "unknown")
        snippet = shorten(text, width=max_len, placeholder="...")
        context_lines.append(f"Source: {source}\n{snippet}")
        summary_lines.append(f"[{source}] {snippet}")
    return "\n\n".join(context_lines), "\n".join(summary_lines)


def build_prompt(context: str, question: str) -> str:
    return (
        "You are a precise assistant. Answer concisely and cite the sources.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )


def get_collection_path(index_root: Path, collection: str) -> Path:
    """Get the VDB path for a collection (Phase 4 structure)."""
    return index_root / collection / "vdb.npz"


def get_collection_source_dir(source_root: Path, collection: str) -> Path:
    """Get the source directory for a collection."""
    return source_root / collection


def list_collections(index_root: Path) -> list[str]:
    """List all available collections."""
    if not index_root.exists():
        return []
    return sorted([d.name for d in index_root.iterdir() if d.is_dir() and (d / "vdb.npz").exists()])


def list_source_collections(source_root: Path) -> list[str]:
    """List all collections with source documents."""
    if not source_root.exists():
        return []
    return sorted([d.name for d in source_root.iterdir() if d.is_dir()])


def rebuild_collection(collection: str, index_root: Path, source_root: Path) -> VectorDB:
    """Rebuild VectorDB for a specific collection (Phase 4 compliant)."""
    source_dir = get_collection_source_dir(source_root, collection)
    vdb_path = get_collection_path(index_root, collection)

    console.print(f"\n[bold cyan]Rebuilding collection '{collection}'...[/bold cyan]")
    console.print(f"Source: {source_dir}")
    console.print(f"Index: {vdb_path}\n")

    # Ensure source directory exists
    source_dir.mkdir(parents=True, exist_ok=True)

    # Gather PDF files
    pdf_files = gather_pdf_paths([str(source_dir)])

    if not pdf_files:
        console.print(f"[yellow]No PDF files found in {source_dir}[/yellow]")
        console.print("[yellow]VectorDB will remain unchanged.[/yellow]")
        return None

    console.print(f"[green]Found {len(pdf_files)} PDF(s)[/green]\n")

    # Create new VDB
    new_vdb = VectorDB()
    processed_docs = []

    # Process PDFs with progress bar
    progress_columns = [
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ]

    with Progress(*progress_columns, console=console) as progress:
        task = progress.add_task(f"Processing {collection}...", total=len(pdf_files))

        for pdf_path in pdf_files:
            try:
                text = extract_text(pdf_path)
                if text.strip():
                    new_vdb.ingest(content=text, document_name=str(pdf_path))
                    processed_docs.append(str(pdf_path))
                else:
                    console.print(f"[yellow]No text extracted from {pdf_path.name}[/yellow]")
            except Exception as e:
                console.print(f"[red]Error processing {pdf_path.name}: {e}[/red]")

            progress.update(task, advance=1)

    if not processed_docs:
        console.print("[yellow]No content extracted from any PDFs.[/yellow]")
        return None

    # Save VDB (Phase 4 structure)
    vdb_path.parent.mkdir(parents=True, exist_ok=True)
    new_vdb.savez(vdb_path)
    write_metadata(vdb_path, collection, processed_docs, source_dir)

    console.print(f"\n[bold green]✓ Collection '{collection}' rebuilt successfully![/bold green]")
    console.print(f"  • Processed: {len(processed_docs)} PDF(s)")
    console.print(f"  • Chunks: {len(new_vdb.content)}")
    console.print(f"  • Index: {vdb_path}\n")

    return new_vdb


def list_documents(vdb: VectorDB) -> None:
    """List all documents in the VectorDB."""
    if not vdb or not vdb.content:
        console.print("\n[yellow]No documents found in vector database.[/yellow]\n")
        return

    # Get unique document names
    doc_names = sorted(set(item['source'] for item in vdb.content))

    # Count chunks per document
    doc_chunks = {}
    for item in vdb.content:
        source = item['source']
        doc_chunks[source] = doc_chunks.get(source, 0) + 1

    # Build table
    table = Table(title=f"Indexed Documents ({len(doc_names)} total)")
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Document", style="cyan")
    table.add_column("Chunks", style="green", justify="right")

    for i, doc_name in enumerate(doc_names, 1):
        table.add_row(str(i), Path(doc_name).name, str(doc_chunks[doc_name]))

    console.print()
    console.print(table)
    console.print()


def show_collections(index_root: Path, source_root: Path, current_collection: str) -> None:
    """Show all available collections (Phase 4)."""
    indexed = list_collections(index_root)
    sources = list_source_collections(source_root)

    table = Table(title="Collections (Phase 4 Architecture)")
    table.add_column("Collection", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Active", style="yellow", justify="center")

    all_collections = sorted(set(indexed + sources))

    if not all_collections:
        console.print("\n[yellow]No collections found.[/yellow]")
        console.print(f"[dim]Create sources in: {source_root}/<collection>/[/dim]\n")
        return

    for coll in all_collections:
        has_index = coll in indexed
        has_source = coll in sources

        if has_index and has_source:
            status = "✓ Indexed"
        elif has_index:
            status = "⚠ Indexed (no source)"
        else:
            status = "○ Source only"

        is_active = "●" if coll == current_collection else ""
        table.add_row(coll, status, is_active)

    console.print()
    console.print(table)
    console.print()


def show_help(collection: str, source_root: Path) -> None:
    """Show available commands."""
    help_text = Text()
    help_text.append("\n Available Commands (Phase 4):\n", style="bold cyan")
    help_text.append("  • ", style="dim")
    help_text.append("rebuild", style="yellow")
    help_text.append(" - Scan and rebuild current collection from ", style="dim")
    help_text.append(f"{source_root}/{collection}/\n", style="cyan")
    help_text.append("  • ", style="dim")
    help_text.append("list", style="yellow")
    help_text.append(" - Show all indexed documents in current collection\n", style="dim")
    help_text.append("  • ", style="dim")
    help_text.append("collections", style="yellow")
    help_text.append(" - Show all available collections\n", style="dim")
    help_text.append("  • ", style="dim")
    help_text.append("help", style="yellow")
    help_text.append(" - Show this help message\n", style="dim")
    help_text.append("  • ", style="dim")
    help_text.append("exit", style="yellow")
    help_text.append(" or ", style="dim")
    help_text.append("quit", style="yellow")
    help_text.append(" - Exit the application\n", style="dim")
    help_text.append("\n  Type any question to query the RAG system\n", style="dim italic")
    help_text.append(f"\n  Current collection: ", style="dim")
    help_text.append(f"{collection}\n", style="cyan bold")

    console.print(help_text)


def cleanup_handler(signum, frame):
    """Handle Ctrl+C gracefully by cleaning up MLX resources and multiprocessing."""
    global _model_engine, _reranker, _vdb

    console.print("\n\n[yellow]Cleaning up resources...[/yellow]")

    # Delete MLX models to free GPU/unified memory
    if _model_engine is not None:
        del _model_engine
        _model_engine = None

    if _reranker is not None:
        del _reranker
        _reranker = None

    if _vdb is not None:
        del _vdb
        _vdb = None

    # Force garbage collection to release memory
    gc.collect()

    console.print("[success]Cleanup complete. Bye.[/success]\n")
    sys.exit(0)


def main() -> None:
    global _model_engine, _reranker, _vdb, _current_collection

    # Register signal handler for graceful Ctrl+C cleanup
    signal.signal(signal.SIGINT, cleanup_handler)

    args = build_parser().parse_args()
    _current_collection = args.collection

    # Get collection-specific path (Phase 4)
    vdb_path = get_collection_path(args.index_root, args.collection)

    console.print("\n[bold cyan]Loading RAG system (Phase 4)...[/bold cyan]")
    console.print(f"Collection: [yellow]{args.collection}[/yellow]")
    console.print(f"Index: {vdb_path}")

    # Load VDB if it exists
    if vdb_path.exists():
        _vdb = VectorDB(str(vdb_path))
        console.print(f"[green]Loaded {len(_vdb.content)} chunks[/green]")
    else:
        console.print(f"[yellow]Collection not indexed yet. Use 'rebuild' command.[/yellow]")
        _vdb = VectorDB()  # Empty VDB

    # Make reranker optional to avoid timeouts/semaphore leaks
    if args.no_reranker:
        _reranker = None
    else:
        _reranker = QwenReranker(args.reranker_id)

    _model_engine = MLXModelEngine(args.model_id, model_type="text")
    console.print("[green]RAG system loaded successfully![/green]\n")

    # Use local references for the loop
    vdb = _vdb
    reranker = _reranker
    model_engine = _model_engine

    # Create framed app
    app = FramedApp("rag", viewport_height=20)

    # Set footer
    footer_text = Text()
    footer_text.append("Ask a question | ", style="dim")
    footer_text.append("Commands: ", style="dim")
    footer_text.append("rebuild", style="yellow")
    footer_text.append(", ", style="dim")
    footer_text.append("list", style="yellow")
    footer_text.append(", ", style="dim")
    footer_text.append("collections", style="yellow")
    footer_text.append(", ", style="dim")
    footer_text.append("help", style="yellow")
    footer_text.append(" | ", style="dim")
    footer_text.append("Ctrl+C to exit", style="cyan")
    app.set_footer(footer_text)

    # Add dashboard to body
    model_name = Path(args.model_id).name if "/" in args.model_id else args.model_id
    dashboard = build_rag_dashboard(
        vdb_path=str(vdb_path),
        num_chunks=len(vdb.content),
        model_name=model_name,
    )
    app.add_content(dashboard)
    app.add_content(Text(""))
    app.add_content(label(f"Phase 4 Architecture | Collection: {args.collection}", "muted"))
    app.add_content(label(f"Reranker: {'Enabled' if not args.no_reranker else 'Disabled'} | Top-K: {args.top_k}", "muted"))
    app.add_content(label(f"Source: {get_collection_source_dir(args.source_root, args.collection)}", "muted"))
    app.add_content(Text(""))

    # Show help hint
    help_hint = Text()
    help_hint.append("💡 Type ", style="dim")
    help_hint.append("help", style="yellow")
    help_hint.append(" to see commands or ", style="dim")
    help_hint.append("collections", style="yellow")
    help_hint.append(" to see all collections", style="dim")
    app.add_content(help_hint)
    app.add_content(Text(""))

    last_query = None

    with app.run():
        while True:
            try:
                # Exit the Live context temporarily for input
                if app._live:
                    app._live.__exit__(None, None, None)

                user_input = console.input("[bold cyan]Question:[/bold cyan] ").strip()

                # Re-enter Live context
                if app._running and app._live:
                    app._live.__enter__()

            except (EOFError, KeyboardInterrupt):
                console.print("\n[cyan]Bye.[/cyan]")
                break

            if not user_input:
                continue

            # Handle commands
            command = user_input.lower()

            if command in ["exit", "quit"]:
                console.print("\n[cyan]Bye.[/cyan]")
                break

            elif command == "help":
                if app._live:
                    app._live.__exit__(None, None, None)
                show_help(args.collection, args.source_root)
                if app._running and app._live:
                    app._live.__enter__()
                continue

            elif command == "collections":
                if app._live:
                    app._live.__exit__(None, None, None)
                show_collections(args.index_root, args.source_root, args.collection)
                if app._running and app._live:
                    app._live.__enter__()
                continue

            elif command == "list":
                if app._live:
                    app._live.__exit__(None, None, None)
                list_documents(vdb)
                if app._running and app._live:
                    app._live.__enter__()
                continue

            elif command == "rebuild":
                if app._live:
                    app._live.__exit__(None, None, None)

                # Rebuild collection (Phase 4)
                new_vdb = rebuild_collection(args.collection, args.index_root, args.source_root)

                if new_vdb is not None:
                    # Update global reference
                    _vdb = new_vdb
                    vdb = new_vdb

                    # Update dashboard
                    app.clear_content()
                    dashboard = build_rag_dashboard(
                        vdb_path=str(vdb_path),
                        num_chunks=len(vdb.content),
                        model_name=model_name,
                    )
                    app.add_content(dashboard)
                    app.add_content(Text(""))
                    app.add_content(label(f"Phase 4 Architecture | Collection: {args.collection}", "muted"))
                    app.add_content(label(f"Reranker: {'Enabled' if not args.no_reranker else 'Disabled'} | Top-K: {args.top_k}", "muted"))
                    app.add_content(label(f"Source: {get_collection_source_dir(args.source_root, args.collection)}", "muted"))
                    app.add_content(Text(""))

                if app._running and app._live:
                    app._live.__enter__()
                continue

            # Treat as a question
            question = user_input
            last_query = question

            # Add question to display
            q_text = Text()
            q_text.append("Q: ", style="bold cyan")
            q_text.append(question)
            app.add_content(q_text)
            app.refresh()

            retrieved = vdb.query(question, k=20)
            if not retrieved:
                app.add_content(label("No documents retrieved for that question.", "warning"))
                app.add_content(Text(""))
                app.refresh()
                continue

            # Rerank if enabled, otherwise use raw VectorDB scores
            if reranker is not None:
                candidate_texts = [chunk["text"] for chunk in retrieved]
                ranks = reranker.rank(question, candidate_texts)
                selected = [retrieved[idx] for idx in ranks[: args.top_k]]
            else:
                selected = retrieved[: args.top_k]

            context, summary = format_context(selected)
            prompt = build_prompt(context, question)

            answer = model_engine.generate(prompt, max_tokens=args.max_tokens)

            # Display retrieved context
            app.add_content(label(f"Retrieved {len(selected)} chunks:", "secondary"))
            for i, chunk in enumerate(selected, 1):
                source = chunk.get("source", "unknown")
                snippet = shorten(chunk.get("text", ""), width=120, placeholder="...")
                chunk_text = Text()
                chunk_text.append(f"  [{i}] ", style="dim")
                chunk_text.append(f"{Path(source).name}: ", style="cyan")
                chunk_text.append(snippet, style="dim")
                app.add_content(chunk_text)

            # Display answer
            app.add_content(Text(""))
            if isinstance(answer, (dict, list)):
                answer_text = json.dumps(answer, indent=2, ensure_ascii=False)
            else:
                answer_text = strip_channel_controls(answer)

            answer_msg = Text()
            answer_msg.append("A: ", style="bold green")
            answer_msg.append(answer_text)
            app.add_content(answer_msg)
            app.add_content(Text(""))
            app.refresh()


if __name__ == "__main__":
    main()

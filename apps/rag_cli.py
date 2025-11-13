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

from libs.mlx_core.model_engine import MLXModelEngine
from rag.chat.templates import strip_channel_controls
from rag.models.qwen_reranker import QwenReranker
from rag.retrieval.vdb import VectorDB
from apps.ui import get_console, render_header, render_footer, render_chat_message, truncate_source_path

console = get_console()

DEFAULT_VDB_PATH = Path("var/indexes/vdb.npz")
DEFAULT_MODEL_ID = "mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit"
DEFAULT_RERANKER_ID = "mlx-community/mxbai-rerank-large-v2"

# Global references for cleanup
_model_engine = None
_reranker = None
_vdb = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MLX RAG CLI – ask questions over a local vector index."
    )
    parser.add_argument(
        "--vdb-path",
        type=Path,
        default=DEFAULT_VDB_PATH,
        help="Path to the vector database (.npz).",
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
    global _model_engine, _reranker, _vdb

    # Register signal handler for graceful Ctrl+C cleanup
    signal.signal(signal.SIGINT, cleanup_handler)

    args = build_parser().parse_args()

    console.print("\n[bold cyan]Loading RAG system...[/bold cyan]")
    _vdb = VectorDB(str(args.vdb_path))

    # Make reranker optional to avoid timeouts/semaphore leaks
    if args.no_reranker:
        _reranker = None
    else:
        _reranker = QwenReranker(args.reranker_id)

    _model_engine = MLXModelEngine(args.model_id, model_type="text")

    # Render header with metadata
    console.print()
    meta = {
        "Model": Path(args.model_id).name if "/" in args.model_id else args.model_id,
        "VDB": args.vdb_path.name,
        "Chunks": len(_vdb.content),
        "Reranker": "Enabled" if not args.no_reranker else "Disabled",
        "Top-K": args.top_k,
    }
    render_header("MLX RAG CLI", meta)

    # Render footer with commands
    render_footer(["Type a question", "Ctrl+C to exit"])
    console.print()

    # Use local references for the loop
    vdb = _vdb
    reranker = _reranker
    model_engine = _model_engine

    while True:
        try:
            question = console.input("[bold cyan]Question:[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[cyan]Bye.[/cyan]")
            break

        if not question:
            continue

        retrieved = vdb.query(question, k=20)
        if not retrieved:
            console.print("[warning]No documents retrieved for that question.[/warning]\n")
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

        # Display results in a two-panel layout
        console.print()

        # Context panel (left side or top)
        context_table = Table(title="Retrieved Context", show_header=True, header_style="bold cyan")
        context_table.add_column("Source", style="dim", max_width=30)
        context_table.add_column("Snippet", style="white", no_wrap=False)

        for chunk in selected:
            source = truncate_source_path(chunk.get("source", "unknown"), max_len=28)
            snippet = shorten(chunk.get("text", ""), width=100, placeholder="...")
            context_table.add_row(source, snippet)

        console.print(context_table)

        # Answer panel
        console.print()
        if isinstance(answer, (dict, list)):
            answer_text = json.dumps(answer, indent=2, ensure_ascii=False)
        else:
            answer_text = strip_channel_controls(answer)

        console.print(
            Panel(
                answer_text,
                title="Answer",
                border_style="green",
                padding=(1, 2),
            )
        )
        console.print()


if __name__ == "__main__":
    main()

import argparse
import gc
import json
import signal
import sys
from pathlib import Path
from textwrap import shorten

from libs.mlx_core.model_engine import MLXModelEngine
from rag.chat.templates import strip_channel_controls
from rag.models.qwen_reranker import QwenReranker
from rag.retrieval.vdb import VectorDB

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

    print("\n\n🧹 Cleaning up resources...")

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

    print("✅ Cleanup complete. Bye.\n")
    sys.exit(0)


def main() -> None:
    global _model_engine, _reranker, _vdb

    # Register signal handler for graceful Ctrl+C cleanup
    signal.signal(signal.SIGINT, cleanup_handler)

    args = build_parser().parse_args()
    _vdb = VectorDB(str(args.vdb_path))

    # Make reranker optional to avoid timeouts/semaphore leaks
    if args.no_reranker:
        _reranker = None
        print(f"Loaded VDB from {args.vdb_path.resolve()} ({len(_vdb.content)} chunks)")
        print(f"Using model {args.model_id} (reranker disabled)")
    else:
        _reranker = QwenReranker(args.reranker_id)
        print(f"Loaded VDB from {args.vdb_path.resolve()} ({len(_vdb.content)} chunks)")
        print(f"Using model {args.model_id} and reranker {args.reranker_id}")

    _model_engine = MLXModelEngine(args.model_id, model_type="text")
    print("\nType a question (Ctrl+C to exit):\n")

    # Use local references for the loop
    vdb = _vdb
    reranker = _reranker
    model_engine = _model_engine

    while True:
        try:
            question = input("❓> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not question:
            continue

        retrieved = vdb.query(question, k=20)
        if not retrieved:
            print("[!] No documents retrieved for that question.")
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

        print("\n🔎 Retrieved context:")
        print(summary or "(empty)")
        print("\n💬 Answer:")
        if isinstance(answer, (dict, list)):
            print(json.dumps(answer, indent=2, ensure_ascii=False))
        else:
            print(strip_channel_controls(answer))
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()

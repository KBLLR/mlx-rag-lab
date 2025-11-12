import argparse
import json
from pathlib import Path
from textwrap import shorten

from libs.mlx_core.model_engine import MLXModelEngine
from rag.models.qwen_reranker import QwenReranker
from rag.retrieval.vdb import VectorDB


DEFAULT_VDB_PATH = Path("models/indexes/vdb.npz")
DEFAULT_MODEL_ID = "mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit"
DEFAULT_RERANKER_ID = "mlx-community/mxbai-rerank-large-v2"


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


def main() -> None:
    args = build_parser().parse_args()
    vdb = VectorDB(str(args.vdb_path))
    reranker = QwenReranker(args.reranker_id)
    model_engine = MLXModelEngine(args.model_id, model_type="text")

    print(f"Loaded VDB from {args.vdb_path.resolve()} ({len(vdb.content)} chunks)")
    print(f"Using model {args.model_id} and reranker {args.reranker_id}")
    print("\nType a question (Ctrl+C to exit):\n")

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

        candidate_texts = [chunk["text"] for chunk in retrieved]
        ranks = reranker.rank(question, candidate_texts)
        selected = [retrieved[idx] for idx in ranks[: args.top_k]]
        context, summary = format_context(selected)
        prompt = build_prompt(context, question)

        answer = model_engine.generate(prompt, max_tokens=args.max_tokens)

        print("\n🔎 Retrieved context:")
        print(summary or "(empty)")
        print("\n💬 Answer:")
        print(json.dumps(answer, indent=2) if isinstance(answer, (dict, list)) else answer)
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()

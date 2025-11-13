import argparse
from pathlib import Path
from typing import Iterator

from rag.retrieval.vdb import VectorDB
from libs.mlx_core.model_engine import MLXModelEngine

TEMPLATE = """You are an expert assistant. Your goal is to provide short, direct, and factually grounded answers based ONLY on the provided context. Your total response, including context, must not exceed 4096 tokens. Cite your sources clearly. The retrieval strategy used is hybrid search.

Provide your answer in JSON format, as a list of dictionaries, where each dictionary has an 'answer' key for the concise response and a 'source' key for the citation.

Context:
{context}

Question: {question}

Concise Answer (JSON):"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query a vector DB")
    # Input
    parser.add_argument(
        "--question",
        help="The question that needs to be answered",
        default="what is flash attention?",
    )
    # Input
    parser.add_argument(
        "--vdb",
        type=str,
        default="var/indexes/vdb.npz", # Updated default VDB
        help="The path to read the vector DB",
    )
    parser.add_argument(
        "--bank",
        type=str,
        help="Optional knowledge bank name (loads var/indexes/<bank>/vdb.npz). Overrides --vdb.",
    )
    parser.add_argument(
        "--indexes-dir",
        type=str,
        default="var/indexes",
        help="Root directory for per-bank indexes.",
    )
    # Model
    parser.add_argument(
        "--model-id",
        type=str,
        default="mlx-community/NeuralBeagle14-7B-4bit-mlx", # Updated default LLM
        help="The Hugging Face model ID or path to the MLX model",
    )
    args = parser.parse_args()

    if args.bank:
        vdb_path = Path(args.indexes_dir).expanduser().resolve() / args.bank / "vdb.npz"
    else:
        vdb_path = Path(args.vdb).expanduser().resolve()

    if not vdb_path.exists():
        raise SystemExit(f"Vector DB not found at {vdb_path}.")

    # Initialize VectorDB
    m = VectorDB(str(vdb_path))
    
    # Get raw contexts from VDB
    raw_contexts = m.query(args.question, k=5)
    if not raw_contexts:
        raise SystemExit("No results returned from the vector database.")

    def format_context(item):
        if isinstance(item, dict):
            source = item.get("source", "unknown")
            text = item.get("text", "")
            return f"Source: {source}\n{text}"
        return str(item)

    context = "\n---\n".join(format_context(item) for item in raw_contexts)
    
    # Format prompt
    prompt = TEMPLATE.format(context=context, question=args.question)
    
    # Initialize MLXModelEngine
    model_engine = MLXModelEngine(args.model_id, model_type="text")

    # Generate and print answer
    final_answer = model_engine.generate(prompt)
    print(final_answer)

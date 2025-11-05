import argparse
from rag.retrieval.vdb import VectorDB
from libs.mlx_core.model_engine import MLXModelEngine
from typing import Iterator

TEMPLATE = """You are a helpful assistant. Answer the following question truthfully and concisely, using ONLY the provided context. If the answer is not in the context, state that you don't know.

Context:
{context}

Question: {question}

Concise Answer:"""


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
        default="models/indexes/combined_vdb.npz",
        help="The path to read the vector DB",
    )
    # Model
    parser.add_argument(
        "--model-id",
        type=str,
        default="mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit",
        help="The Hugging Face model ID or path to the MLX model",
    )
    args = parser.parse_args()

    # Initialize VectorDB
    m = VectorDB(args.vdb)
    
    # Get raw contexts from VDB
    raw_contexts = m.query(args.question, k=5)
    context = "\n---\n".join(raw_contexts)
    
    # Format prompt
    prompt = TEMPLATE.format(context=context, question=args.question)
    
    # Initialize MLXModelEngine
    model_engine = MLXModelEngine(args.model_id, model_type="text")

    # Generate and print answer
    final_answer = model_engine.generate(prompt)
    print(final_answer)
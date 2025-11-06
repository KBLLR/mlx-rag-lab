import argparse
from rag.retrieval.vdb import VectorDB
from libs.mlx_core.model_engine import MLXModelEngine
from typing import Iterator

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
        default="models/indexes/vdb.npz", # Updated default VDB
        help="The path to read the vector DB",
    )
    # Model
    parser.add_argument(
        "--model-id",
        type=str,
        default="mlx-community/NeuralBeagle14-7B-4bit-mlx", # Updated default LLM
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
import os
from pathlib import Path
from typing import List, Dict, Any
import json # Import json

from rag.retrieval.vdb import VectorDB
from rag.models.qwen_reranker import QwenReranker, QwenRerankerConfig
from rich.console import Console

console = Console()

# --- Configuration ---
DEFAULT_VDB_PATH = "models/indexes/combined_vdb.npz"
RERANKER_MODEL_ID = "mlx-community/mxbai-rerank-large-v2"
GENERATED_DATASET_PATH = "var/benchmarking/generated_qa_dataset.json" # Path to generated dataset

# --- Matching Function ---
def is_match(retrieved: str, relevant: str) -> bool:
    """Checks if retrieved text is a substring of relevant text or vice-versa."""
    # Normalize whitespace and case for more robust matching
    retrieved_norm = ' '.join(retrieved.lower().split())
    relevant_norm = ' '.join(relevant.lower().split())
    return (retrieved_norm in relevant_norm) or (relevant_norm in retrieved_norm)

# --- Metrics Calculation ---
def calculate_recall_at_k(retrieved_docs: List[str], relevant_docs: List[str], k: int) -> float:
    """Calculates Recall@k using a tolerant matching function."""
    if not relevant_docs:
        return 1.0 # If no relevant documents, recall is 1 if nothing is missed
    
    retrieved_at_k = retrieved_docs[:k]
    for relevant_doc in relevant_docs:
        if any(is_match(retrieved_doc, relevant_doc) for retrieved_doc in retrieved_at_k):
            return 1.0 # Found at least one match
    return 0.0

def calculate_mrr(retrieved_docs: List[str], relevant_docs: List[str]) -> float:
    """Calculates Mean Reciprocal Rank (MRR) using a tolerant matching function."""
    for i, retrieved_doc in enumerate(retrieved_docs):
        if any(is_match(retrieved_doc, relevant_doc) for relevant_doc in relevant_docs):
            return 1.0 / (i + 1)
    return 0.0

# --- Main Benchmarking Function ---
def run_retrieval_benchmark(
    queries_with_ground_truth: List[Dict[str, Any]],
    vdb_path: str = DEFAULT_VDB_PATH,
    reranker_model_id: str = RERANKER_MODEL_ID,
    k_recall: int = 5, # k for Recall@k
    initial_retrieval_k: int = 20, # Number of candidates for initial VDB query
    final_rerank_k: int = 5, # Number of candidates after re-ranking
):
    console.print(f"[bold cyan]Starting Retrieval Benchmark...[/bold cyan]")
    console.print(f"  VectorDB Path: {vdb_path}")
    console.print(f"  Reranker Model: {reranker_model_id}")
    console.print(f"  Recall@k: {k_recall}")
    console.print(f"  Initial Retrieval K: {initial_retrieval_k}")
    console.print(f"  Final Rerank K: {final_rerank_k}\n")

    # Load RAG Components
    vdb = VectorDB(vdb_path)
    reranker = QwenReranker(model_id=reranker_model_id)

    all_recall_scores = []
    all_mrr_scores = []

    for i, entry in enumerate(queries_with_ground_truth):
        query = entry["query"]
        # Use 'relevant_document_text' from the generated dataset as ground truth
        ground_truth_docs = [entry["relevant_document_text"]]

        console.print(f"[bold yellow]Query {i+1}:[/bold yellow] {query}")

        # 1. Initial Retrieval from VDB
        initial_candidates = vdb.query(query, k=initial_retrieval_k)
        candidate_texts = [c["text"] for c in initial_candidates]

        # 2. Re-ranking
        if candidate_texts:
            reranked_indices = reranker.rank(query, candidate_texts)
            final_ranked_candidates = [candidate_texts[idx] for idx in reranked_indices[:final_rerank_k]]
        else:
            final_ranked_candidates = []

        # 3. Calculate Metrics
        recall_score = calculate_recall_at_k(final_ranked_candidates, ground_truth_docs, k_recall)
        mrr_score = calculate_mrr(final_ranked_candidates, ground_truth_docs)

        all_recall_scores.append(recall_score)
        all_mrr_scores.append(mrr_score)

        console.print(f"  Recall@{k_recall}: {recall_score:.4f}")
        console.print(f"  MRR: {mrr_score:.4f}\n")

    # Aggregate and Report Final Results
    avg_recall = sum(all_recall_scores) / len(all_recall_scores) if all_recall_scores else 0.0
    avg_mrr = sum(all_mrr_scores) / len(all_mrr_scores) if all_mrr_scores else 0.0

    console.print(f"[bold green]--- Benchmark Results ---[/bold green]")
    console.print(f"  Average Recall@{k_recall}: [bold]{avg_recall:.4f}[/bold]")
    console.print(f"  Average MRR: [bold]{avg_mrr:.4f}[/bold]")

    # Optionally save results
    # with open(Path("var/benchmarking/results.txt"), "w") as f:
    #     f.write(f"Average Recall@{k_recall}: {avg_recall:.4f}\n")
    #     f.write(f"Average MRR: {avg_mrr:.4f}\n")

# --- Main execution ---
if __name__ == "__main__":
    # Load the generated Q&A dataset
    dataset_path = Path(GENERATED_DATASET_PATH)
    if not dataset_path.exists():
        console.print(f"[red]Error: Generated dataset not found at {dataset_path}. "
                      f"Please run `generate_qa_dataset.py` first.[/red]")
        exit(1)

    with open(dataset_path, "r", encoding="utf-8") as f:
        generated_dataset = json.load(f)
    
    if not generated_dataset:
        console.print("[yellow]Warning: Generated dataset is empty. No benchmarks to run.[/yellow]")
        exit(0)

    run_retrieval_benchmark(generated_dataset)


import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Any

from rag.retrieval.vdb import VectorDB

def run_latency_test(vdb: VectorDB, questions: List[str], num_queries: int) -> None:
    """Runs a latency test on the VDB."""
    print(f"\n--- Running Latency Test ({num_queries} queries) ---")
    
    start_time = time.time()
    for i in range(num_queries):
        question = questions[i % len(questions)]
        vdb.query(question, k=3)
    end_time = time.time()

    total_time = end_time - start_time
    avg_latency = total_time / num_queries
    
    print(f"Total time for {num_queries} queries: {total_time:.4f} seconds")
    print(f"Average latency per query: {avg_latency:.4f} seconds")

def run_accuracy_test(vdb: VectorDB, qa_dataset: List[Dict[str, Any]]) -> None:
    """Runs an accuracy test on the VDB."""
    print("\n--- Running Accuracy Test ---")
    
    correct_retrievals = 0
    for item in qa_dataset:
        question = item["question"]
        expected_answer = item["expected_answer"]
        
        retrieved_chunks = vdb.query(question, k=3)
        
        found = any(expected_answer in chunk for chunk in retrieved_chunks)
        if found:
            correct_retrievals += 1
            print(f"[PASS] Question: '{question}' -> Correctly retrieved chunk containing '{expected_answer}'")
        else:
            print(f"[FAIL] Question: '{question}' -> Did not retrieve chunk containing '{expected_answer}'")
            print(f"  Retrieved: {retrieved_chunks}")

    accuracy = (correct_retrievals / len(qa_dataset)) * 100
    print(f"\nRetrieval Accuracy: {accuracy:.2f}% ({correct_retrievals}/{len(qa_dataset)})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark the RAG pipeline")
    parser.add_argument(
        "--source-doc",
        type=str,
        default="var/benchmarking/mlx_faq.txt",
        help="Path to the source document for the VDB.",
    )
    parser.add_argument(
        "--qa-dataset",
        type=str,
        default="var/benchmarking/qa_dataset.json",
        help="Path to the QA dataset for accuracy testing.",
    )
    parser.add_argument(
        "--num-queries",
        type=int,
        default=100,
        help="Number of queries to run for the latency test.",
    )
    args = parser.parse_args()

    # 1. Create VDB from the source document
    print("--- Setting up VDB for benchmarking ---")
    source_path = Path(args.source_doc)
    if not source_path.exists():
        print(f"[ERROR] Source document not found at: {source_path}")
        exit(1)
    
    with open(source_path, "r") as f:
        content = f.read()

    vdb = VectorDB()
    vdb.ingest(content, document_names=[str(source_path)])
    print("VDB created successfully.")

    # 2. Load QA dataset
    qa_path = Path(args.qa_dataset)
    if not qa_path.exists():
        print(f"[ERROR] QA dataset not found at: {qa_path}")
        exit(1)
        
    with open(qa_path, "r") as f:
        qa_dataset = json.load(f)
    
    questions = [item["question"] for item in qa_dataset]

    # 3. Run tests
    run_latency_test(vdb, questions, args.num_queries)
    run_accuracy_test(vdb, qa_dataset)

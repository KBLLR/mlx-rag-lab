import argparse
import os
from pathlib import Path
from rag.retrieval.vdb import VectorDB
from libs.mlx_core.model_engine import MLXModelEngine
from rag.ingestion.create_vdb import process_pdfs # Reusing the PDF processing logic

# Define the TEMPLATE for the LLM
TEMPLATE = """You are an expert assistant. Your goal is to provide short, direct, and factually grounded answers based ONLY on the provided context. Your total response, including context, must not exceed 4096 tokens. Cite your sources clearly. The retrieval strategy used is hybrid search.

Provide your answer in JSON format, as a list of dictionaries, where each dictionary has an 'answer' key for the concise response and a 'source' key for the citation.

Context:
{context}

Question: {question}

Concise Answer (JSON):"""

DEFAULT_VDB_PATH = "models/indexes/combined_vdb.npz"
DEFAULT_MODEL_ID = "mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit"
SOURCE_DOCS_DIR = "var/source_docs"

class InteractiveRAG:
    def __init__(self, vdb_path: str, model_id: str):
        self.vdb_path = vdb_path
        self.model_id = model_id
        self.vdb = None
        self.model_engine = None
        self._load_components()

    def _load_components(self):
        print(f"[INFO] Loading VectorDB from {self.vdb_path}...")
        try:
            self.vdb = VectorDB(self.vdb_path)
            print(f"[INFO] Loaded VDB with {len(self.vdb.content)} chunks from {len(self.vdb.document_names)} documents.")
        except Exception as e:
            print(f"[ERROR] Failed to load VectorDB: {e}. Please rebuild it.")
            self.vdb = VectorDB() # Initialize an empty VDB

        print(f"[INFO] Loading LLM: {self.model_id}...")
        self.model_engine = MLXModelEngine(self.model_id, model_type="text")
        print("[INFO] LLM loaded.")

    def _rebuild_vdb(self):
        print(f"[INFO] Rebuilding VectorDB from PDFs in {SOURCE_DOCS_DIR}...")
        pdf_files = list(Path(SOURCE_DOCS_DIR).glob("*.pdf"))
        if not pdf_files:
            print(f"[WARN] No PDF files found in {SOURCE_DOCS_DIR}. VDB will be empty.")
            self.vdb = VectorDB() # Reset to empty VDB
            return

        # Convert Path objects to strings for process_pdfs
        pdf_file_paths_str = [str(p) for p in pdf_files]
        elements, processed_pdf_paths = process_pdfs(pdf_file_paths_str)
        combined_content = "\n\n".join([e.text for e in elements])

        if not combined_content.strip():
            print("[WARN] No content extracted from provided PDFs. Vector database will be empty.")
            self.vdb = VectorDB() # Reset to empty VDB
        else:
            new_vdb = VectorDB() # Create a new VDB instance
            new_vdb.ingest(content=combined_content, document_names=processed_pdf_paths)
            new_vdb.savez(self.vdb_path)
            self.vdb = new_vdb # Update the current VDB instance
            print(f"[INFO] Vector database rebuilt at {self.vdb_path} from {len(processed_pdf_paths)} PDF(s).")

    def ask_question(self, question: str):
        if not self.vdb or not self.vdb.content:
            print("[WARN] Vector database is empty. Please rebuild it first.")
            return

        print(f"[INFO] Querying VDB for: '{question}'")
        raw_contexts = self.vdb.query(question, k=5)
        context = "\n---".join(raw_contexts)
        prompt = TEMPLATE.format(context=context, question=question)

        print("[INFO] Generating answer with LLM...")
        final_answer = self.model_engine.generate(prompt)
        print("\n--- Answer ---")
        print(final_answer)
        print("--------------")

    def list_documents(self):
        if not self.vdb or not self.vdb.document_names:
            print("[INFO] No documents found in the vector database.")
            return

        print("\n--- Indexed Documents ---")
        for i, doc_name in enumerate(self.vdb.document_names):
            print(f"{i+1}. {doc_name}")
        print("-------------------------")

    def run(self):
        print("\n--- Interactive RAG CLI ---")
        print(f"Type 'ask <your question>' to query the documents.")
        print(f"Type 'list_docs' to see indexed documents.")
        print(f"Type 'rebuild_vdb' to re-ingest PDFs from {SOURCE_DOCS_DIR}.")
        print(f"Type 'exit' or 'quit' to leave.")
        print("-------------------------")

        while True:
            user_input = input("\nRAG> ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting Interactive RAG CLI. Goodbye!")
                break
            elif user_input.lower() == "list_docs":
                self.list_documents()
            elif user_input.lower() == "rebuild_vdb":
                self._rebuild_vdb()
            elif user_input.lower().startswith("ask "):
                question = user_input[4:].strip()
                if question:
                    self.ask_question(question)
                else:
                    print("[WARN] Please provide a question after 'ask'.")
            else:
                print("[WARN] Unknown command. Available commands: ask, list_docs, rebuild_vdb, exit/quit.")

if __name__ == "__main__":
    # Ensure the source documents directory exists
    os.makedirs(SOURCE_DOCS_DIR, exist_ok=True)

    # Initial VDB creation if it doesn't exist or is empty
    if not Path(DEFAULT_VDB_PATH).exists() or Path(DEFAULT_VDB_PATH).stat().st_size == 0:
        print(f"[INFO] No existing VDB found at {DEFAULT_VDB_PATH} or it is empty. Attempting initial build...")
        # Temporarily create an instance to call rebuild_vdb
        temp_rag = InteractiveRAG(DEFAULT_VDB_PATH, DEFAULT_MODEL_ID)
        temp_rag._rebuild_vdb()

    rag_cli = InteractiveRAG(DEFAULT_VDB_PATH, DEFAULT_MODEL_ID)
    rag_cli.run()

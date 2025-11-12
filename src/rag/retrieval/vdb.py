import mlx.core as mx
import numpy as np
import json  # Added json import
from pathlib import Path  # Added Path import
from rag.models.model import Model
from typing import List, Optional, Dict
from unstructured.partition.pdf import partition_pdf

CHUNK_SIZE = 256
CHUNK_OVERLAP = 50


def split_text_into_chunks(text, chunk_size, overlap):
    """
    Split text into chunks with a specified size and overlap.

    Parameters:
    - text (str): The input text to be split into chunks.
    - chunk_size (int): The size of each chunk.
    - overlap (int): The number of characters to overlap between consecutive chunks.

    Returns:s
    - List of chunks (str).
    """
    if chunk_size <= 0 or overlap < 0:
        raise ValueError("Invalid chunk size or overlap value.")

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# takes as an input a list of strings
# the first output element is the data as a flatten array
# the second output element is the length of each string in the list
def chunks_to_mx_array(chunks: List[str]) -> (mx.array, mx.array):
    data = [ord(char) for string in chunks for char in string]
    lengths = [len(string) for string in chunks]
    return (mx.array(data), mx.array(lengths))


# This is doing the reverse operation of chunks_to_mx_array
def mx_array_to_chunks(data: mx.array, lengths: mx.array) -> List[str]:
    i = 0
    output = []
    for l in lengths:
        j = l.item() + i
        x = [chr(d.item()) for d in data[i:j]]
        output.append("".join(x))
        i = l.item()
    return output


class VectorDB:
    def __init__(self, vdb_file: Optional[str] = None) -> None:
        self.model = Model()
        self.embeddings = None
        self.content = []  # Now a list of dicts: [{"text": chunk, "source": doc_name}, ...]

        if vdb_file:
            try:
                vdb_path = Path(vdb_file)
                if vdb_path.exists():
                    vdb = mx.load(vdb_file)
                    self.embeddings = vdb["embeddings"]
                    # Reconstruct content from separate text and source arrays
                    texts = mx_array_to_chunks(vdb["chunk_data"], vdb["chunk_lengths"])
                    sources = mx_array_to_chunks(vdb["source_data"], vdb["source_lengths"])
                    self.content = [{"text": t, "source": s} for t, s in zip(texts, sources)]

            except Exception as e:
                print(f"[WARN] Could not load VDB from {vdb_file}: {e}")
                self.embeddings = None
                self.content = []

    def ingest(self, content: str, document_name: str) -> None:
        chunks = split_text_into_chunks(text=content, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        if not chunks:
            return

        new_embeddings = self.model.run(chunks)

        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = mx.concatenate([self.embeddings, new_embeddings])

        for chunk in chunks:
            self.content.append({"text": chunk, "source": document_name})

    def query(self, text: str, k: int = 3) -> List[Dict[str, str]]:
        if self.embeddings is None:
            return []
        query_emb = self.model.run(text)
        scores = mx.matmul(query_emb, self.embeddings.T) * 100
        sorted_indices = mx.argsort(scores, axis=1)
        top_k_indices = sorted_indices[:, ::-1][:, :k].flatten().tolist()
        
        # Return the list of content dictionaries
        responses = [self.content[i] for i in top_k_indices]
        return responses

    def savez(self, vdb_file) -> None:
        target = Path(vdb_file)
        target.parent.mkdir(parents=True, exist_ok=True)

        if self.embeddings is None or not self.content:
            raise ValueError("VectorDB.savez called before embeddings/content were initialized.")

        # Separate texts and sources for saving
        texts = [item["text"] for item in self.content]
        sources = [item["source"] for item in self.content]

        chunk_data, chunk_lengths = chunks_to_mx_array(texts)
        source_data, source_lengths = chunks_to_mx_array(sources)

        mx.savez(
            str(target),
            embeddings=self.embeddings,
            chunk_data=chunk_data,
            chunk_lengths=chunk_lengths,
            source_data=source_data,
            source_lengths=source_lengths,
        )


def vdb_from_pdf(pdf_file: str) -> VectorDB:
    model = VectorDB()
    elements = partition_pdf(pdf_file)
    content = "\n\n".join([e.text for e in elements])
    model.ingest(content=content)
    return model

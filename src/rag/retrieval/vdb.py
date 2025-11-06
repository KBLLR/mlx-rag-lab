import mlx.core as mx
import numpy as np
import json # Added json import
from pathlib import Path # Added Path import
from rag.models.model import Model
from typing import List, Optional
from unstructured.partition.pdf import partition_pdf


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
        self.content = None
        self.document_names = []
        if vdb_file:
            try:
                vdb_path = Path(vdb_file)
                meta_path = vdb_path.with_suffix(vdb_path.suffix + ".meta.json")

                vdb = mx.load(vdb_file)
                self.embeddings = vdb["embeddings"]
                chunk_data = vdb["chunk_data"]
                chunk_lengths = vdb["chunk_lengths"]
                self.content = mx_array_to_chunks(chunk_data, chunk_lengths)
                
                if meta_path.exists():
                    with meta_path.open("r", encoding="utf-8") as f:
                        meta = json.load(f)
                    self.document_names = list(meta.get("document_names", []))

            except Exception as e:
                raise Exception(f"failed with {e}")

    def ingest(self, content: str, document_names: List[str] = None) -> None:
        chunks = split_text_into_chunks(text=content, chunk_size=256, overlap=50)
        self.embeddings = self.model.run(chunks)
        self.content = chunks
        if document_names:
            self.document_names.extend(document_names)

    def query(self, text: str, k: int = 3) -> List[str]:
        query_emb = self.model.run(text)
        scores = mx.matmul(query_emb, self.embeddings.T) * 100
        sorted_indices = mx.argsort(scores, axis=1)
        top_k_indices = sorted_indices[:, ::-1][:, :k].flatten().tolist()
        responses = [self.content[i] for i in top_k_indices]
        return responses

    def savez(self, vdb_file) -> None:
        target = Path(vdb_file)
        target.parent.mkdir(parents=True, exist_ok=True)

        if self.embeddings is None or self.content is None:
            raise ValueError("VectorDB.savez called before embeddings/content were initialized.")

        chunk_data, chunk_lengths = chunks_to_mx_array(self.content)

        # 1) Save numeric tensors
        mx.savez(
            str(target),
            embeddings=self.embeddings,
            chunk_data=chunk_data,
            chunk_lengths=chunk_lengths,
        )

        # 2) Save metadata in sidecar JSON
        meta = {
            "document_names": self.document_names,
        }
        meta_path = target.with_suffix(target.suffix + ".meta.json")
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)


def vdb_from_pdf(pdf_file: str) -> VectorDB:
    model = VectorDB()
    elements = partition_pdf(pdf_file)
    content = "\n\n".join([e.text for e in elements])
    model.ingest(content=content)
    return model
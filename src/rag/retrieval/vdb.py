import json
from pathlib import Path
from typing import List, Optional, Dict, Tuple

try:
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    import numpy as np

import numpy as np  # Always import numpy for fallback

from rag.models.model import Model

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
def chunks_to_mx_array(chunks: List[str]) -> Tuple:
    data = [ord(char) for string in chunks for char in string]
    lengths = [len(string) for string in chunks]
    if MLX_AVAILABLE:
        return (mx.array(data), mx.array(lengths))
    else:
        return (np.array(data), np.array(lengths))


# This is doing the reverse operation of chunks_to_mx_array
def mx_array_to_chunks(data, lengths) -> List[str]:
    i = 0
    output = []
    for l in lengths:
        if hasattr(l, 'item'):
            l_val = l.item()
        else:
            l_val = int(l)
        j = l_val + i
        x = []
        for d in data[i:j]:
            if hasattr(d, 'item'):
                x.append(chr(d.item()))
            else:
                x.append(chr(int(d)))
        output.append("".join(x))
        i = l_val
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
                    if MLX_AVAILABLE:
                        vdb = mx.load(vdb_file)
                    else:
                        vdb = np.load(vdb_file)
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
            if MLX_AVAILABLE:
                self.embeddings = mx.concatenate([self.embeddings, new_embeddings])
            else:
                self.embeddings = np.concatenate([self.embeddings, new_embeddings])

        for chunk in chunks:
            self.content.append({"text": chunk, "source": document_name})

    def score(self, query_vec, doc_vec) -> float:
        """
        Compute cosine similarity between query and document vectors.

        Parameters:
        - query_vec: Query embedding vector (mx.array or np.array, float32)
        - doc_vec: Document embedding vector (mx.array or np.array, float32)

        Returns:
        - float: Cosine similarity score in range [-1, 1]
        """
        if MLX_AVAILABLE:
            # Ensure vectors are float32
            query_vec = query_vec.astype(mx.float32)
            doc_vec = doc_vec.astype(mx.float32)

            # Compute cosine similarity: dot(a,b) / (||a|| * ||b|| + epsilon)
            dot_product = mx.dot(query_vec, doc_vec)
            query_norm = mx.linalg.norm(query_vec)
            doc_norm = mx.linalg.norm(doc_vec)

            # Add epsilon to avoid division by zero
            epsilon = 1e-8
            similarity = dot_product / (query_norm * doc_norm + epsilon)

            # Return as Python float
            return float(similarity.item())
        else:
            # Numpy fallback
            query_vec = query_vec.astype(np.float32)
            doc_vec = doc_vec.astype(np.float32)

            dot_product = np.dot(query_vec, doc_vec)
            query_norm = np.linalg.norm(query_vec)
            doc_norm = np.linalg.norm(doc_vec)

            epsilon = 1e-8
            similarity = dot_product / (query_norm * doc_norm + epsilon)

            return float(similarity)

    def query(self, text: str, k: int = 3) -> List[Dict[str, str]]:
        if self.embeddings is None:
            return []
        query_emb = self.model.run(text)

        # Compute cosine similarity scores for all documents
        scores = []
        if MLX_AVAILABLE:
            query_vec = query_emb[0]  # Extract first row (single query)
            for i in range(self.embeddings.shape[0]):
                doc_vec = self.embeddings[i]
                score = self.score(query_vec, doc_vec)
                scores.append(score)
        else:
            # Fallback for non-MLX (using numpy)
            query_vec = query_emb[0]
            for i in range(self.embeddings.shape[0]):
                doc_vec = self.embeddings[i]
                # Compute cosine similarity using numpy
                dot_product = np.dot(query_vec, doc_vec)
                query_norm = np.linalg.norm(query_vec)
                doc_norm = np.linalg.norm(doc_vec)
                score = dot_product / (query_norm * doc_norm + 1e-8)
                scores.append(float(score))

        # Sort indices by score in descending order (most similar first)
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        # Get top k results
        top_k_indices = sorted_indices[:k]

        # Return the list of content dictionaries
        responses = [self.content[i] for i in top_k_indices]
        return responses

    def delete(self, filter_criteria: Dict[str, str]) -> int:
        """
        Delete chunks that match ALL filter criteria.

        Parameters:
        - filter_criteria (Dict[str, str]): Dictionary of field:value pairs to match.
          All criteria must match for a chunk to be deleted.

        Returns:
        - int: Number of chunks deleted.
        """
        if not filter_criteria:
            return 0

        if self.embeddings is None or not self.content:
            return 0

        # Find indices to keep (inverse of indices to delete)
        indices_to_keep = []
        for i, chunk_dict in enumerate(self.content):
            # Check if this chunk matches ALL filter criteria
            matches = all(
                chunk_dict.get(key) == value for key, value in filter_criteria.items()
            )
            if not matches:
                indices_to_keep.append(i)

        deleted_count = len(self.content) - len(indices_to_keep)

        if deleted_count == 0:
            return 0

        # Update content list
        self.content = [self.content[i] for i in indices_to_keep]

        # Update embeddings array
        if MLX_AVAILABLE:
            if indices_to_keep:
                self.embeddings = self.embeddings[mx.array(indices_to_keep)]
            else:
                # All chunks deleted
                self.embeddings = None
        else:
            if indices_to_keep:
                self.embeddings = self.embeddings[indices_to_keep]
            else:
                # All chunks deleted
                self.embeddings = None

        return deleted_count

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

        if MLX_AVAILABLE:
            mx.savez(
                str(target),
                embeddings=self.embeddings,
                chunk_data=chunk_data,
                chunk_lengths=chunk_lengths,
                source_data=source_data,
                source_lengths=source_lengths,
            )
        else:
            np.savez(
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

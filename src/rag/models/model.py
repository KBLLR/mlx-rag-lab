"""Embedding model for RAG retrieval.

This module provides a simple embedding model interface that can be
used with or without MLX depending on the environment.
"""

from typing import List, Sequence, Union

try:
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    # Fallback to numpy for non-Apple platforms
    import numpy as np


def _text_to_vector(text: str) -> List[float]:
    """Generate deterministic embedding from text.

    This is a simple hash-based embedding for testing and development.
    In production, this should be replaced with a real embedding model.

    Args:
        text: Input text to embed

    Returns:
        4-dimensional embedding vector
    """
    if not text:
        return [0.0, 0.0, 0.0, 0.0]

    encoded = text.encode("utf-8")
    length = len(text)
    byte_sum = sum(encoded) % 997
    vowels = sum(1 for c in text.lower() if c in "aeiou")
    unique_tokens = len({token.strip(".,!?").lower() for token in text.split() if token})

    return [float(length), float(byte_sum), float(vowels), float(unique_tokens or 1)]


class Model:
    """Simple embedding model for RAG retrieval.

    This is a deterministic stub implementation that generates embeddings
    based on text features. In production, this should be replaced with
    a real embedding model (e.g., sentence-transformers via MLX).

    The interface matches what VectorDB expects:
    - run(input_text) -> mx.array or np.array
    """

    def __init__(self, model_id: str = "deterministic-stub"):
        """Initialize the embedding model.

        Args:
            model_id: Model identifier (currently unused in stub)
        """
        self.model_id = model_id
        self.embedding_dim = 4  # Dimension of stub embeddings

    def run(self, input_text: Union[str, Sequence[str]]):
        """Generate embeddings for input text(s).

        Args:
            input_text: Single string or sequence of strings

        Returns:
            MLX array (if available) or numpy array of shape (n, embedding_dim)
        """
        # Normalize input to list
        if isinstance(input_text, str):
            texts = [input_text]
        else:
            texts = list(input_text)

        # Generate embeddings
        vectors = [_text_to_vector(t) for t in texts]

        # Return as MLX array if available, otherwise numpy
        if MLX_AVAILABLE:
            return mx.array(vectors, dtype=mx.float32)
        else:
            return np.array(vectors, dtype=np.float32)

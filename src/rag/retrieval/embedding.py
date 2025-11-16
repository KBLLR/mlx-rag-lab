"""Embedding model loader with support for real MLX models and stub fallback.

This module provides a factory function to load embedding models based on
environment configuration. It supports:
- Real MLX-based embedding models (when RAG_EMBEDDINGS_MODEL_PATH is set)
- Deterministic stub model (for testing and when no model path is provided)
"""

import os
from pathlib import Path
from typing import List, Sequence, Union

try:
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    import numpy as np

from rag.models.model import Model as StubModel


class MLXEmbeddingModel:
    """Real MLX-based embedding model loaded from local path.

    This model loads a sentence-transformers compatible model from disk
    and runs inference using MLX for Apple Silicon acceleration.
    """

    def __init__(self, model_path: str):
        """Initialize the MLX embedding model.

        Args:
            model_path: Path to the local model directory
        """
        if not MLX_AVAILABLE:
            raise RuntimeError(
                "MLX is not available. Real embedding models require MLX "
                "and Apple Silicon hardware."
            )

        model_path = Path(model_path)
        if not model_path.exists():
            raise ValueError(f"Model path does not exist: {model_path}")

        self.model_path = model_path
        self.model_id = f"mlx-local:{model_path.name}"

        # Import here to avoid dependency when using stub
        try:
            from transformers import AutoTokenizer, AutoModel
        except ImportError:
            raise RuntimeError(
                "transformers is required for real embedding models. "
                "Install with: pip install transformers"
            )

        # Load tokenizer and model
        # Note: We're loading HF transformers model, but will convert to MLX arrays
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)

        # For now, use basic HF model - will optimize with MLX-specific models later
        # This is a minimal implementation for TASK 2
        import torch
        self.model = AutoModel.from_pretrained(str(model_path), local_files_only=True)
        self.model.eval()  # Set to evaluation mode

        # Get embedding dimension from model config
        self.embedding_dim = self.model.config.hidden_size

    def run(self, input_text: Union[str, Sequence[str]]):
        """Generate embeddings for input text(s).

        Args:
            input_text: Single string or sequence of strings

        Returns:
            MLX array of shape (n, embedding_dim) with dtype float32
        """
        # Normalize input to list
        if isinstance(input_text, str):
            texts = [input_text]
        else:
            texts = list(input_text)

        # Tokenize
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )

        # Run inference (no gradient computation needed)
        import torch
        with torch.no_grad():
            outputs = self.model(**encoded)
            # Use mean pooling over token embeddings
            # Shape: (batch_size, seq_len, hidden_size) -> (batch_size, hidden_size)
            embeddings = outputs.last_hidden_state.mean(dim=1)

        # Convert to numpy, then to MLX array
        embeddings_np = embeddings.cpu().numpy().astype('float32')

        # Convert to MLX array
        return mx.array(embeddings_np, dtype=mx.float32)


def load_embedding_model():
    """Load embedding model based on environment configuration.

    Checks RAG_EMBEDDINGS_MODEL_PATH environment variable:
    - If set: Load real MLX embedding model from the specified path
    - If not set: Return deterministic stub model for testing

    Returns:
        Embedding model instance with .run() method
    """
    model_path = os.getenv("RAG_EMBEDDINGS_MODEL_PATH")

    if model_path:
        # Load real MLX model
        return MLXEmbeddingModel(model_path)
    else:
        # Fallback to deterministic stub
        return StubModel()

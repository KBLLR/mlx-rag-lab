"""Embedding model for RAG retrieval.

This module provides a sentence-transformer-based embedding model
using the transformers library with MLX array outputs.
"""

import logging
from pathlib import Path
from typing import List, Sequence, Union

try:
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    # Fallback to numpy for non-Apple platforms
    import numpy as np

import torch
from transformers import AutoModel, AutoTokenizer, PreTrainedTokenizerBase

logger = logging.getLogger(__name__)


def mean_pooling(token_embeddings: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    """Apply mean pooling to token embeddings.

    Args:
        token_embeddings: Token-level embeddings from the model
        attention_mask: Attention mask to exclude padding tokens

    Returns:
        Sentence-level embeddings
    """
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return sum_embeddings / sum_mask


class Model:
    """Sentence-transformer-based embedding model for RAG retrieval.

    This implementation uses transformers library with a sentence-transformers
    compatible model to generate semantic embeddings. The outputs are returned
    as MLX arrays for compatibility with the MLX-based vector database.

    The interface matches what VectorDB expects:
    - run(input_text) -> mx.array or np.array
    """

    def __init__(self, model_id: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize the embedding model.

        Args:
            model_id: HuggingFace model identifier or local path
        """
        self.model_id = model_id

        logger.info(f"Loading embedding model: {model_id}")

        # Load model and tokenizer from HuggingFace
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModel.from_pretrained(model_id)

        # Set model to evaluation mode
        self.model.eval()

        # Determine embedding dimension from model config
        self.embedding_dim = self.model.config.hidden_size

        logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")

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

        # Tokenize input texts
        encoded_input = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )

        # Generate embeddings
        with torch.no_grad():
            model_output = self.model(**encoded_input)

            # Apply mean pooling to get sentence embeddings
            sentence_embeddings = mean_pooling(
                model_output.last_hidden_state,
                encoded_input["attention_mask"]
            )

            # Normalize embeddings (L2 normalization for cosine similarity)
            sentence_embeddings = torch.nn.functional.normalize(
                sentence_embeddings,
                p=2,
                dim=1
            )

        # Convert to numpy
        embeddings_np = sentence_embeddings.cpu().numpy()

        # Return as MLX array if available, otherwise numpy
        if MLX_AVAILABLE:
            return mx.array(embeddings_np, dtype=mx.float32)
        else:
            return embeddings_np.astype("float32")

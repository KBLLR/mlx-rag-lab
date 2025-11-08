import ollama
from typing import List, Union, Any
import mlx.core as mx

class OllamaEmbeddingEngine:
    def __init__(self, model_id: str, **kwargs: Any) -> None:
        self.model_id = model_id
        self.ollama_client = ollama.Client(timeout=60.0) # Initialize Ollama client with a timeout

    def embed(self, texts: Union[str, List[str]]) -> mx.array:
        if isinstance(texts, str):
            texts = [texts]

        try:
            response = self.ollama_client.embeddings(model=self.model_id, prompt=texts)
            # Ollama returns a list of embeddings, each with an 'embedding' key
            embeddings = [item['embedding'] for item in response['embeddings']]
            return mx.array(embeddings)
        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings with Ollama model {self.model_id}: {e}") from e

    def run(self, texts: Union[str, List[str]]) -> mx.array:
        """Mimics the interface expected by VectorDB (e.g., mlx_lm.generate).
           Takes a list of strings and returns their embeddings as an mx.array.
        """
        return self.embed(texts)
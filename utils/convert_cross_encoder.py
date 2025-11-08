
import argparse
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import mlx.core as mx
from mlx.utils import tree_flatten
import numpy as np
from pathlib import Path

def convert_model(hf_path: str, mlx_path: str):
    """Converts a Hugging Face cross-encoder model to MLX format."""
    mlx_path = Path(mlx_path)
    mlx_path.mkdir(parents=True, exist_ok=True)

    print(f"Loading Hugging Face model from {hf_path}...")
    model = AutoModelForSequenceClassification.from_pretrained(hf_path)
    tokenizer = AutoTokenizer.from_pretrained(hf_path)

    # Save the tokenizer
    tokenizer.save_pretrained(mlx_path)

    # Save the model weights as npz
    weights = model.state_dict()
    weights = {k: v.to("cpu").numpy() for k, v in weights.items()}
    
    # The MLX BERT implementation might have slightly different key names.
    # This is a placeholder for potential key mapping.
    # For example, PyTorch's 'bert.encoder.layer.0.attention.self.query.weight' might be
    # 'encoder.layers.0.attention.query_proj.weight' in MLX.
    # For now, we save them as is and will adjust in the model loading code if needed.
    np.savez(str(mlx_path / "weights.npz"), **weights)

    print(f"Model converted and saved to {mlx_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a cross-encoder model to MLX.")
    parser.add_argument(
        "--hf-path",
        type=str,
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        help="The Hugging Face model path.",
    )
    parser.add_argument(
        "--mlx-path",
        type=str,
        default="models/mlx-models/cross-encoder-ms-marco-MiniLM-L-6-v2",
        help="The path to save the MLX model.",
    )
    args = parser.parse_args()
    convert_model(args.hf_path, args.mlx_path)

# -*- coding: utf-8 -*-
import argparse
from rag.models.hub import hub_api

def main():
    """
    A CLI utility to pre-download and cache models from the Hugging Face Hub
    using the project's central HubAPI.
    """
    parser = argparse.ArgumentParser(
        description="Download and cache required models for the MLX-RAG project.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=["schnell", "dev", "all"],
        default="all",
        help="Which base model to download ('schnell', 'dev', or 'all').",
    )
    parser.add_argument(
        "--quantization",
        type=str,
        default="default",
        help="Which variant to download (e.g., 'default', '4bit').",
    )
    
    args = parser.parse_args()

    available_models = hub_api.list_available_models()
    models_to_download = available_models.keys() if args.model == "all" else [f"flux-{args.model}"]

    for model_name in models_to_download:
        if model_name in available_models:
            if args.quantization in available_models[model_name]:
                try:
                    hub_api.get_model(model_name, args.quantization)
                except (IOError, ValueError) as e:
                    print(f"Failed to download {model_name} [{args.quantization}]: {e}")
            else:
                print(f"Warning: Quantization '{args.quantization}' not available for model '{model_name}'. Skipping.")
        else:
            print(f"Warning: Model '{model_name}' not found in registry. Skipping.")

    print("\nPre-caching process complete.")

if __name__ == "__main__":
    main()
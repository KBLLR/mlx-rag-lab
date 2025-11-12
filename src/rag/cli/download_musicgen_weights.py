import typer
from typing_extensions import Annotated
import json
from pathlib import Path
from huggingface_hub import snapshot_download

# Define the base directory for MLX models within our repo
MLX_MODELS_DIR = Path("./mlx-models/")

def download_model_weights(repo_id: str, local_subfolder: str = None, allow_patterns: list = None):
    print(f"Downloading model weights for {repo_id}...")
    
    local_dir = MLX_MODELS_DIR / (local_subfolder if local_subfolder else repo_id.split('/')[-1])
    local_dir.mkdir(parents=True, exist_ok=True)

    # Use snapshot_download to get the files
    downloaded_path = snapshot_download(
        repo_id=repo_id,
        allow_patterns=allow_patterns if allow_patterns else ["*.json", "*.safetensors", "*.bin", "*.model"],
        local_dir=local_dir,
        local_dir_use_symlinks=False, # Copy files directly
    )
    print(f"Downloaded {repo_id} to {downloaded_path}")
    return downloaded_path

app = typer.Typer()

@app.command()
def main(
    musicgen_model_size: Annotated[str, typer.Option("--musicgen-model-size", "-m", help="Size of the Musicgen model to download (e.g., small, medium, large, melody).")] = "small",
    encodec_model_repo_id: Annotated[str, typer.Option("--encodec-model-repo-id", help="Hugging Face repository ID for the Encodec model. If None, it will be inferred from Musicgen config.")] = None,
):
    """
    Download Musicgen and Encodec model weights.
    """
    # Construct Musicgen repo_id based on model_size
    if musicgen_model_size.lower() == "melody":
        musicgen_repo_id = "facebook/musicgen-melody"
    else:
        musicgen_repo_id = f"facebook/musicgen-{musicgen_model_size}"

    # Download Musicgen model weights
    musicgen_local_path = download_model_weights(musicgen_repo_id, local_subfolder=f"musicgen-{musicgen_model_size}")

    # Infer and download Encodec model weights if not provided
    if encodec_model_repo_id is None:
        config_path = Path(musicgen_local_path) / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Musicgen config.json not found at {config_path}. Cannot infer Encodec model.")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        encodec_name = config["audio_encoder"]["_name_or_path"].split('/')[-1]
        encodec_name = encodec_name.replace("_", "-")
        inferred_encodec_repo_id = f"mlx-community/{encodec_name}-float32"
        print(f"Inferred Encodec model: {inferred_encodec_repo_id}")
        download_model_weights(inferred_encodec_repo_id, local_subfolder=f"{encodec_name}-float32")
    else:
        download_model_weights(encodec_model_repo_id, local_subfolder=encodec_model_repo_id.split('/')[-1])

    print("All required model weights downloaded successfully!")

if __name__ == "__main__":
    app()

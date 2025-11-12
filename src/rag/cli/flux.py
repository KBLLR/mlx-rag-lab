import typer
from . import flux_txt2image, flux_dreambooth

app = typer.Typer()

@app.command("txt2image")
def txt2image():
    """
    Generate images from a textual prompt using stable diffusion
    """
    flux_txt2image.main()

@app.command("dreambooth")
def dreambooth():
    """
    Finetune Flux to generate images with a specific subject
    """
    flux_dreambooth.main()

if __name__ == "__main__":
    app()

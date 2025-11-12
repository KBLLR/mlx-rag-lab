# Copyright © 2024 Apple Inc.

import argparse
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import numpy as np
from PIL import Image
from tqdm import tqdm

from rag.models.flux.flux import FluxPipeline


def to_latent_size(image_size):
    h, w = image_size
    h = ((h + 15) // 16) * 16
    w = ((w + 15) // 16) * 16

    if (h, w) != image_size:
        print(
            "Warning: The image dimensions need to be divisible by 16px. "
            f"Changing size to {h}x{w}."
        )

    return (h // 8, w // 8)


def quantization_predicate(name, m):
    return hasattr(m, "to_quantized") and m.weight.shape[1] % 512 == 0


def load_adapter(flux, adapter_file, fuse=False):
    weights, lora_config = mx.load(adapter_file, return_metadata=True)
    rank = int(lora_config["lora_rank"])
    num_blocks = int(lora_config["lora_blocks"])
    flux.linear_to_lora_layers(rank, num_blocks)
    flux.flow.load_weights(list(weights.items()), strict=False)
    if fuse:
        flux.fuse_lora_layers()


def parse_image_size_arg(value):
    """
    Accept either a single integer (e.g., 512) or a WxH string (e.g., 512x768)
    and return (height, width) as ints.
    """
    if isinstance(value, tuple) and len(value) == 2:
        return value
    if isinstance(value, int):
        return (value, value)

    text = str(value).lower().strip()
    if "x" in text:
        parts = text.split("x")
        if len(parts) != 2:
            raise ValueError(f"Invalid image size format: {value}")
        height, width = (int(parts[0]), int(parts[1]))
        return (height, width)

    size = int(text)
    return (size, size)

def parse_args():
    parser = argparse.ArgumentParser(description="Flux text-to-image generator")

    parser.add_argument("prompt", type=str, help="Text prompt for image generation")
    parser.add_argument("--model", choices=["schnell", "dev", "schnell-4bit"], default="schnell")
    parser.add_argument("--n-images", type=int, default=1)
    parser.add_argument(
        "--image-size",
        type=str,
        default="512",
        help="Either a single integer (512) or WxH string (512x768) for rectangular renders.",
    )
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--guidance", type=float, default=7.5)
    parser.add_argument("--n-rows", type=int, default=1)
    parser.add_argument("--decoding-batch-size", type=int, default=1)
    parser.add_argument("--quantize", action="store_true")
    parser.add_argument("--preload-models", action="store_true")
    parser.add_argument("--output", type=str, default="outputs/", help="Directory to save output images.")
    parser.add_argument("--output-prefix", type=str, default="flux_output", help="Prefix for output filenames (e.g., 'test_schnell').")
    parser.add_argument("--save-raw", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--adapter", type=str, default=None)
    parser.add_argument("--fuse-adapter", action="store_true")
    parser.add_argument("--no-t5-padding", action="store_true")

    return parser.parse_args()

def main():
    args = parse_args()

    # Load the models
    flux = FluxPipeline("flux-" + args.model)
    args.steps = args.steps or (50 if args.model == "dev" else 2)

    if args.adapter:
        load_adapter(flux, args.adapter, fuse=args.fuse_adapter)

    if args.quantize:
        nn.quantize(flux.flow, class_predicate=quantization_predicate)
        nn.quantize(flux.t5, class_predicate=quantization_predicate)
        nn.quantize(flux.clip, class_predicate=quantization_predicate)

    if args.preload_models:
        flux.ensure_models_are_loaded()

    # Make the generator
    try:
        image_dims = parse_image_size_arg(args.image_size)
    except ValueError as exc:
        raise SystemExit(str(exc))
    latent_size = to_latent_size(image_dims)
    latents = flux.generate_latents(
        args.prompt,
        n_images=args.n_images,
        num_steps=args.steps,
        latent_size=latent_size,
        guidance=args.guidance,
        seed=args.seed,
    )

    # First we get and eval the conditioning
    conditioning = next(latents)
    mx.eval(conditioning)
    peak_mem_conditioning = mx.get_peak_memory() / 1024**3
    mx.reset_peak_memory()

    # The following is not necessary but it may help in memory constrained
    # systems by reusing the memory kept by the text encoders.
    del flux.t5
    del flux.clip

    # Actual denoising loop
    for x_t in tqdm(latents, total=args.steps):
        mx.eval(x_t)

    # The following is not necessary but it may help in memory constrained
    # systems by reusing the memory kept by the flow transformer.
    del flux.flow
    peak_mem_generation = mx.get_peak_memory() / 1024**3
    mx.reset_peak_memory()

    # Decode them into images
    decoded = []
    for i in tqdm(range(0, args.n_images, args.decoding_batch_size)):
        decoded.append(flux.decode(x_t[i : i + args.decoding_batch_size], latent_size))
        mx.eval(decoded[-1])
    peak_mem_decoding = mx.get_peak_memory() / 1024**3
    peak_mem_overall = max(
        peak_mem_conditioning, peak_mem_generation, peak_mem_decoding
    )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.save_raw:
        for i in range(len(x_t)):
            im = Image.fromarray(np.array(mx.concatenate(decoded, axis=0)[i]))
            im.save(output_dir / f"{args.output_prefix}_raw_{i}.png")
    else:
        # Arrange them on a grid
        x = mx.concatenate(decoded, axis=0)
        x = mx.pad(x, [(0, 0), (4, 4), (4, 4), (0, 0)])
        B, H, W, C = x.shape
        x = x.reshape(args.n_rows, B // args.n_rows, H, W, C).transpose(0, 2, 1, 3, 4)
        x = x.reshape(args.n_rows * H, B // args.n_rows * W, C)
        x = (x * 255).astype(mx.uint8)

        # Save them to disc
        im = Image.fromarray(np.array(x))
        im.save(output_dir / f"{args.output_prefix}_grid_0.png")

    # Report the peak memory used during generation
    if args.verbose:
        print(f"Peak memory used for the text:       {peak_mem_conditioning:.3f}GB")
        print(f"Peak memory used for the generation: {peak_mem_generation:.3f}GB")
        print(f"Peak memory used for the decoding:   {peak_mem_decoding:.3f}GB")
        print(f"Peak memory used overall:            {peak_mem_overall:.3f}GB")

    print_mlx_peak_memory()

def print_mlx_peak_memory():
    try:
        peak = mx.get_peak_memory() / 1024**2
    except Exception:
        return
    print(f"[MLX GPU] Peak memory: {peak:.2f} MB")
    mx.reset_peak_memory()


if __name__ == "__main__":
    main()

import mlx.core as mx
import mlx.nn as nn
import numpy as np
import pytest
from pathlib import Path
import soundfile as sf

from libs.musicgen_core.encodec_model import EncodecModel, preprocess_audio

# Helper functions for MSE and SNR
def calculate_mse(original_audio, reconstructed_audio):
    """
    Calculates Mean Squared Error between two MLX arrays.
    """
    original_audio = mx.array(original_audio)
    reconstructed_audio = mx.array(reconstructed_audio)
    if original_audio.shape != reconstructed_audio.shape:
        raise ValueError("Original and reconstructed audio must have the same shape.")

    mse = mx.mean(mx.square(original_audio - reconstructed_audio))
    return mse

def calculate_snr(original_audio, reconstructed_audio):
    """
    Calculates Signal-to-Noise Ratio in dB between two MLX arrays.
    """
    original_audio = mx.array(original_audio)
    reconstructed_audio = mx.array(reconstructed_audio)
    if original_audio.shape != reconstructed_audio.shape:
        raise ValueError("Original and reconstructed audio must have the same shape.")

    signal_power = mx.mean(mx.square(original_audio))
    noise_power = mx.mean(mx.square(original_audio - reconstructed_audio))

    if noise_power == 0:
        return mx.array(float('inf'))
    if signal_power == 0:
        return mx.array(float('-inf'))

    snr_db = 10 * mx.log10(signal_power / noise_power)
    return snr_db

@pytest.fixture(scope="module")
def encodec_model_and_processor():
    # Use a small model for faster testing
    model_id = "mlx-community/encodec-32khz-float32"
    model, processor = EncodecModel.from_pretrained(model_id)
    return model, processor

def test_encodec_model_properties(encodec_model_and_processor):

    model, _ = encodec_model_and_processor



    print(f"\nTesting EncodecModel properties...")

    assert model.sampling_rate == 32000

    assert model.channels == 1 # Encodec 32kHz float32 is mono

    assert model.chunk_length is None

    assert model.chunk_stride is None


    print(f"Model sampling_rate: {model.sampling_rate}")
    print(f"Model channels: {model.channels}")
    print(f"Model chunk_length: {model.chunk_length}")
    print(f"Model chunk_stride: {model.chunk_stride}")

    # Test eval/train modes
    assert model.training is True # Default after loading
    model.eval()
    assert model.training is False
    model.train()
    assert model.training is True

    # Test parameters
    assert len(model.parameters()) > 0
    assert len(model.trainable_parameters()) > 0

    # Test freeze/unfreeze (example: freeze encoder)
    initial_trainable_params = len(model.trainable_parameters())
    model.freeze(keys=["encoder"])
    assert len(model.trainable_parameters()) < initial_trainable_params
    model.unfreeze()
    assert len(model.trainable_parameters()) == initial_trainable_params
    print("EncodecModel properties and modes tested successfully.")

def test_encodec_model_round_trip(encodec_model_and_processor):
    model, processor = encodec_model_and_processor

    print(f"\nTesting EncodecModel encode/decode round-trip...")

    # Generate dummy audio data (e.g., 5 seconds of mono audio at 32kHz)
    duration_s = 1
    sampling_rate = model.sampling_rate
    num_samples = int(duration_s * sampling_rate)

    # Create a simple sine wave for a more structured signal than random noise
    t = mx.arange(num_samples) / sampling_rate
    frequency = 440 # Hz
    original_audio = mx.sin(2 * mx.pi * frequency * t)[..., None] # (num_samples, 1)

    print(f"Original audio shape: {original_audio.shape}")

    # Preprocess audio
    # preprocess_audio expects (T,) or (T, C) and returns (B, T, C)
    processed_audio, padding_mask = processor(original_audio, sampling_rate=sampling_rate)
    print(f"Processed audio shape: {processed_audio.shape}")
    print(f"Padding mask shape: {padding_mask.shape}")

    # Encode
    # EncodecModel.encode expects (batch_size, sequence_length, channels) for input_values
    codes, scales = model.encode(processed_audio, padding_mask=padding_mask)
    print(f"Encoded codes shape: {codes.shape}")
    # Expected codes shape: (num_chunks, batch_size, num_codebooks, frames_per_chunk)
    # For a single chunk, it would be (1, B, 4, F)

    # Decode
    # EncodecModel.decode expects (num_chunks, batch_size, num_codebooks, frames_per_chunk) for audio_codes
    # and a list of scales (one per chunk)
    reconstructed_audio = model.decode(codes, scales, padding_mask=padding_mask)
    print(f"Reconstructed audio shape: {reconstructed_audio.shape}")

    # Ensure shapes are consistent after round-trip
    # The reconstructed audio might have a slightly different length due to padding/chunking
    # We need to compare the relevant part of the original audio with the reconstructed
    min_len = min(original_audio.shape[0], reconstructed_audio.shape[1])
    original_trimmed = original_audio[:min_len, :]
    reconstructed_trimmed = reconstructed_audio[0, :min_len, :]

    # Check that the shapes are now compatible for comparison
    assert original_trimmed.shape == reconstructed_trimmed.shape, \
        f"Shape mismatch after trimming: {original_trimmed.shape} vs {reconstructed_trimmed.shape}"

    # Verify that the reconstructed audio is reasonably close to the original
    # Using Mean Squared Error (MSE) as a metric for similarity
    mse = mx.mean((original_trimmed - reconstructed_trimmed) ** 2)
    print(f"MSE between original and reconstructed audio: {mse.item()}")

    # Set a reasonable threshold for the MSE
    # This value might need adjustment depending on the model's performance
    mse_threshold = 0.1
    assert mse.item() < mse_threshold, f"MSE {mse.item()} exceeds threshold {mse_threshold}"

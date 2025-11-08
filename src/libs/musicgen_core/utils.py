import mlx.core as mx
import soundfile as sf
import numpy as np

def save_audio(path: str, audio: mx.array, sampling_rate: int):
    """
    Save an MLX array as a WAV audio file.

    Args:
        path (str): The output file path.
        audio (mlx.core.array): The audio data as an MLX array.
        sampling_rate (int): The sampling rate of the audio.
    """
    # Ensure audio is 1D or 2D (samples, channels)
    if audio.ndim > 2:
        raise ValueError("Audio array must be 1D (mono) or 2D (samples, channels).")
    if audio.ndim == 1:
        audio = audio.reshape(-1, 1) # Ensure 2D for soundfile

    # Convert MLX array to numpy array for soundfile
    audio_np = np.array(audio.tolist())

    sf.write(path, audio_np, sampling_rate)

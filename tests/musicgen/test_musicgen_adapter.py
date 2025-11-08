import os
import pytest
import mlx.core as mx
import soundfile as sf
from pathlib import Path

from libs.musicgen_core.adapter import MusicgenAdapter

# This test requires the actual Musicgen model weights to be downloaded.
# If the test fails due to model loading, please ensure the model
# 'facebook/musicgen-small' (and its Encodec dependency)
# is available locally in the expected path (e.g., mlx-models/).
# You can use the `uv run python -m rag.cli.download_musicgen_weights` command to download them.

def test_musicgen_adapter_generation():
    # Define a temporary output directory for the test
    test_output_dir = Path("./var/test_music_output")
    if not test_output_dir.exists():
        test_output_dir.mkdir(parents=True)

    adapter = MusicgenAdapter()
    prompt = "a short test melody"
    duration = 3  # Short duration for quick testing

    output_filepath = adapter.generate_music(prompt, duration, str(test_output_dir))

    assert os.path.exists(output_filepath)
    assert output_filepath.endswith(".wav")

    # Optionally, load the audio file to check its properties (requires soundfile)
    try:
        audio_data, samplerate = sf.read(output_filepath)
        assert samplerate == adapter.model.sampling_rate
        # Check if the audio data has some content (not just silence or empty)
        assert audio_data.size > 0
        # Basic check for duration (allow for slight variations)
        expected_frames = duration * samplerate
        assert abs(audio_data.shape[0] - expected_frames) < samplerate # within 1 second

    except Exception as e:
        pytest.fail(f"Failed to read or validate generated audio file: {e}")

    # Clean up the generated file
    os.remove(output_filepath)
    # Clean up the test output directory if empty
    if not any(test_output_dir.iterdir()):
        os.rmdir(test_output_dir)

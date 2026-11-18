"""WhisperX client stays callable against PyPI whisperx 3.8.x."""

from rag.stt.whisperx_client import (
    _accepted_kwargs,
    _mlx_checkpoint_to_whisper_arch,
)


def test_mlx_checkpoint_maps_onto_faster_whisper_arch():
    assert _mlx_checkpoint_to_whisper_arch("mlx-community/whisper-large-v3-mlx") == "large-v3"
    assert _mlx_checkpoint_to_whisper_arch("large-v3") == "large-v3"


def test_accepted_kwargs_drops_fork_only_load_model_arguments():
    def load_model(whisper_arch, device, compute_type="default", language=None, threads=4):
        return (whisper_arch, device, compute_type, language, threads)

    accepted = _accepted_kwargs(
        load_model,
        {
            "device": "cpu",
            "compute_type": "float16",
            "language": "en",
            "threads": 0,
            "backend": "mlx",
            "batch_size": 4,
        },
    )
    assert "backend" not in accepted
    assert "batch_size" not in accepted
    assert load_model("large-v3", **accepted) == ("large-v3", "cpu", "float16", "en", 0)


def test_accepted_kwargs_keeps_token_name_the_installed_pipeline_uses():
    def __init__(self, model_name=None, token=None, device="cpu"):
        return None

    accepted = _accepted_kwargs(
        __init__,
        {
            "model_name": "pyannote/speaker-diarization-3.1",
            "use_auth_token": "hf_example",
            "token": "hf_example",
            "device": "cpu",
        },
    )
    assert accepted == {
        "model_name": "pyannote/speaker-diarization-3.1",
        "token": "hf_example",
        "device": "cpu",
    }

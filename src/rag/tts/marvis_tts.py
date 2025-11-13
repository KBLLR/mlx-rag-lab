#!/usr/bin/env python3
"""
TTS wrapper for Marvis-AI/marvis-tts-100m-v0.2

Clean abstraction for text-to-speech on Apple Silicon with:
- Easy model loading
- Configurable voice/speaker
- WAV output to disk or bytes
- Batch processing support
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import numpy as np


@dataclass
class TTSConfig:
    """Configuration for TTS generation."""
    speaker: Optional[str] = None  # Speaker ID (model-specific)
    language: Optional[str] = "en"  # Language code
    sample_rate: int = 22050  # Output sample rate
    speed: float = 1.0  # Speech speed multiplier


class MarvisTTSClient:
    """
    Client for Marvis TTS model.

    Usage:
        client = MarvisTTSClient("Marvis-AI/marvis-tts-100m-v0.2")
        audio_bytes = client.synthesize("Hello world!")
        client.save_wav(audio_bytes, "output.wav")
    """

    def __init__(
        self,
        model_id: str = "Marvis-AI/marvis-tts-100m-v0.2",
        device: str = "mps"  # Metal Performance Shaders for Apple Silicon
    ):
        """
        Initialize TTS client.

        Args:
            model_id: HuggingFace model ID or local path
            device: Device to run on ("mps" for Metal, "cpu" for CPU)
        """
        self.model_id = model_id
        self.device = device
        self.model = None
        self.processor = None

        self._load_model()

    def _load_model(self):
        """Load TTS model and processor."""
        try:
            from transformers import AutoProcessor, AutoModelForTextToWaveform
            import torch

            print(f"Loading TTS model: {self.model_id}...")

            # Load processor (tokenizer + feature extractor)
            self.processor = AutoProcessor.from_pretrained(self.model_id)

            # Load model
            self.model = AutoModelForTextToWaveform.from_pretrained(self.model_id)

            # Move to Metal if available
            if self.device == "mps" and torch.backends.mps.is_available():
                self.model = self.model.to("mps")
                print("✓ TTS model loaded on Metal (MPS)")
            else:
                print("✓ TTS model loaded on CPU")

        except ImportError as e:
            raise ImportError(
                f"Missing dependencies for TTS: {e}\n"
                "Install with: pip install transformers torch torchaudio"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load TTS model: {e}")

    def synthesize(
        self,
        text: str,
        config: Optional[TTSConfig] = None
    ) -> np.ndarray:
        """
        Synthesize speech from text.

        Args:
            text: Input text to speak
            config: Optional TTS configuration

        Returns:
            Audio as numpy array (float32, shape: [samples])
        """
        if config is None:
            config = TTSConfig()

        try:
            import torch

            # Prepare inputs
            inputs = self.processor(
                text=text,
                return_tensors="pt",
                sampling_rate=config.sample_rate
            )

            # Move to device
            if self.device == "mps":
                inputs = {k: v.to("mps") if hasattr(v, "to") else v for k, v in inputs.items()}

            # Generate audio
            with torch.no_grad():
                outputs = self.model.generate(**inputs)

            # Convert to numpy
            audio = outputs.cpu().numpy().squeeze()

            # Apply speed adjustment if needed
            if config.speed != 1.0:
                audio = self._adjust_speed(audio, config.speed)

            return audio

        except Exception as e:
            raise RuntimeError(f"TTS synthesis failed: {e}")

    def synthesize_batch(
        self,
        texts: List[str],
        config: Optional[TTSConfig] = None
    ) -> List[np.ndarray]:
        """
        Synthesize multiple texts in batch.

        Args:
            texts: List of texts to synthesize
            config: Optional TTS configuration

        Returns:
            List of audio arrays
        """
        if config is None:
            config = TTSConfig()

        results = []
        for text in texts:
            audio = self.synthesize(text, config)
            results.append(audio)

        return results

    def _adjust_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """
        Adjust playback speed via resampling.

        Args:
            audio: Input audio array
            speed: Speed multiplier (>1.0 = faster, <1.0 = slower)

        Returns:
            Speed-adjusted audio
        """
        try:
            from scipy import signal

            # Resample to adjust speed
            new_length = int(len(audio) / speed)
            audio_adjusted = signal.resample(audio, new_length)

            return audio_adjusted

        except ImportError:
            print("Warning: scipy not available, skipping speed adjustment")
            return audio

    def save_wav(
        self,
        audio: np.ndarray,
        output_path: str | Path,
        sample_rate: Optional[int] = None
    ):
        """
        Save audio to WAV file.

        Args:
            audio: Audio array from synthesize()
            output_path: Output file path
            sample_rate: Sample rate (default: 22050)
        """
        if sample_rate is None:
            sample_rate = 22050

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import soundfile as sf

            # Ensure float32 and normalize if needed
            audio = audio.astype(np.float32)
            if np.abs(audio).max() > 1.0:
                audio = audio / np.abs(audio).max()

            sf.write(str(output_path), audio, sample_rate)
            print(f"✓ Audio saved to {output_path}")

        except ImportError:
            # Fallback to scipy.io.wavfile
            try:
                from scipy.io import wavfile

                # Convert to int16
                audio_int = (audio * 32767).astype(np.int16)
                wavfile.write(str(output_path), sample_rate, audio_int)
                print(f"✓ Audio saved to {output_path}")

            except ImportError:
                raise ImportError(
                    "No WAV writing library available. "
                    "Install soundfile: pip install soundfile"
                )

    def stream_to_file(
        self,
        text: str,
        output_path: str | Path,
        config: Optional[TTSConfig] = None
    ):
        """
        Synthesize and save in one call (convenience method).

        Args:
            text: Text to synthesize
            output_path: Where to save WAV
            config: Optional TTS configuration
        """
        if config is None:
            config = TTSConfig()

        audio = self.synthesize(text, config)
        self.save_wav(audio, output_path, config.sample_rate)


# ===== Utility Functions =====

def quick_speak(
    text: str,
    output_path: Optional[str] = None,
    model_id: str = "Marvis-AI/marvis-tts-100m-v0.2"
) -> Optional[np.ndarray]:
    """
    Quick TTS synthesis (convenience function).

    Args:
        text: Text to speak
        output_path: Optional output file (if None, returns audio array)
        model_id: TTS model to use

    Returns:
        Audio array if output_path is None, otherwise None
    """
    client = MarvisTTSClient(model_id)

    if output_path:
        client.stream_to_file(text, output_path)
        return None
    else:
        return client.synthesize(text)


def batch_synthesize(
    texts: List[str],
    output_dir: str | Path,
    model_id: str = "Marvis-AI/marvis-tts-100m-v0.2",
    prefix: str = "audio"
):
    """
    Batch synthesize multiple texts to files.

    Args:
        texts: List of texts to synthesize
        output_dir: Directory to save WAV files
        model_id: TTS model to use
        prefix: Filename prefix
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = MarvisTTSClient(model_id)

    for i, text in enumerate(texts):
        output_path = output_dir / f"{prefix}_{i:03d}.wav"
        client.stream_to_file(text, output_path)
        print(f"[{i+1}/{len(texts)}] Saved {output_path.name}")

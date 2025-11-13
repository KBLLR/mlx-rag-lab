"""
Kokoro TTS wrapper with phoneme output for lip-sync.

Features:
- 54 voices across 8 languages
- Phoneme-level output for viseme mapping
- 24kHz audio generation
- Lightweight (82M parameters)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

import numpy as np


@dataclass
class KokoroConfig:
    """Configuration for Kokoro TTS synthesis."""

    voice: str = "af_bella"  # Default: Bella (American female)
    lang_code: str = "a"  # 'a' for American English
    sample_rate: int = 24000
    speed: float = 1.0


@dataclass
class PhonemeData:
    """Phoneme timing data for lip-sync."""

    graphemes: str  # Text segment
    phonemes: str  # IPA phonemes
    audio: np.ndarray  # Audio chunk


class KokoroTTSClient:
    """
    Kokoro TTS client with phoneme output.

    Supports 54 voices across 8 languages with phoneme-level output
    for avatar lip-sync applications.
    """

    def __init__(self, lang_code: str = "a"):
        """
        Initialize Kokoro TTS client.

        Args:
            lang_code: Language code
                - 'a': American English
                - 'b': British English
                - 'j': Japanese
                - 'z': Mandarin Chinese
                - 'e': Spanish
                - 'f': French
                - 'h': Hindi
                - 'i': Italian
                - 'p': Brazilian Portuguese
        """
        try:
            from kokoro import KPipeline
        except ImportError:
            raise ImportError(
                "kokoro not installed. Install with: pip install kokoro soundfile"
            )

        self.lang_code = lang_code
        self.pipeline = KPipeline(lang_code=lang_code)

    def synthesize(
        self,
        text: str,
        config: Optional[KokoroConfig] = None,
    ) -> tuple[np.ndarray, list[PhonemeData]]:
        """
        Synthesize speech from text with phoneme output.

        Args:
            text: Input text to synthesize
            config: TTS configuration

        Returns:
            (audio_array, phoneme_data_list)
        """
        if config is None:
            config = KokoroConfig()

        # Generate audio + phonemes
        generator = self.pipeline(text, voice=config.voice)

        audio_chunks = []
        phoneme_data = []

        for gs, ps, audio in generator:
            audio_chunks.append(audio)
            phoneme_data.append(PhonemeData(graphemes=gs, phonemes=ps, audio=audio))

        # Concatenate all audio chunks
        full_audio = np.concatenate(audio_chunks)

        # Apply speed adjustment if needed
        if config.speed != 1.0:
            full_audio = self._adjust_speed(full_audio, config.speed)

        return full_audio, phoneme_data

    def synthesize_stream(
        self,
        text: str,
        config: Optional[KokoroConfig] = None,
    ) -> Iterator[PhonemeData]:
        """
        Stream audio generation with phoneme data.

        Args:
            text: Input text
            config: TTS configuration

        Yields:
            PhonemeData chunks
        """
        if config is None:
            config = KokoroConfig()

        generator = self.pipeline(text, voice=config.voice)

        for gs, ps, audio in generator:
            yield PhonemeData(graphemes=gs, phonemes=ps, audio=audio)

    def save_wav(
        self,
        audio: np.ndarray,
        output_path: Path,
        sample_rate: int = 24000,
    ) -> None:
        """
        Save audio to WAV file.

        Args:
            audio: Audio array
            output_path: Output file path
            sample_rate: Sample rate (default: 24kHz)
        """
        try:
            import soundfile as sf
        except ImportError:
            raise ImportError("soundfile not installed. Install with: pip install soundfile")

        sf.write(str(output_path), audio, sample_rate)

    def _adjust_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """Adjust playback speed using resampling."""
        try:
            from scipy import signal
        except ImportError:
            # Skip speed adjustment if scipy not available
            return audio

        target_length = int(len(audio) / speed)
        return signal.resample(audio, target_length)

    @staticmethod
    def list_voices(lang_code: str = "a") -> list[str]:
        """
        List available voices for a language.

        Args:
            lang_code: Language code

        Returns:
            List of voice identifiers
        """
        voices_map = {
            "a": [  # American English
                "af_heart",
                "af_alloy",
                "af_aoede",
                "af_bella",
                "af_jessica",
                "af_kore",
                "af_nicole",
                "af_nova",
                "af_river",
                "af_sarah",
                "af_sky",
                "am_adam",
                "am_echo",
                "am_eric",
                "am_fenrir",
                "am_liam",
                "am_michael",
                "am_onyx",
                "am_puck",
                "am_santa",
            ],
            "b": [  # British English
                "bf_alice",
                "bf_emma",
                "bf_isabella",
                "bf_lily",
                "bm_daniel",
                "bm_fable",
                "bm_george",
                "bm_lewis",
            ],
            "j": [  # Japanese
                "jf_alpha",
                "jf_gongitsune",
                "jf_nezumi",
                "jf_tebukuro",
                "jm_kumo",
            ],
            "z": [  # Mandarin Chinese
                "zf_xiaobei",
                "zf_xiaoni",
                "zf_xiaoxiao",
                "zf_xiaoyi",
                "zm_yunjian",
                "zm_yunxi",
                "zm_yunxia",
                "zm_yunyang",
            ],
            "e": ["ef_dora", "em_alex", "em_santa"],  # Spanish
            "f": ["ff_siwis"],  # French
            "h": ["hf_alpha", "hf_beta", "hm_omega", "hm_psi"],  # Hindi
            "i": ["if_sara", "im_nicola"],  # Italian
            "p": ["pf_dora", "pm_alex", "pm_santa"],  # Brazilian Portuguese
        }

        return voices_map.get(lang_code, [])

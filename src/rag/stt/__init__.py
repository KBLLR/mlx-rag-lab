"""
Speech-to-Text (STT) abstractions for Whisper and WhisperX.
"""

from .whisperx_client import (
    SpeakerSegment,
    WhisperXClient,
    WhisperXConfig,
    WhisperXResult,
)

__all__ = ["WhisperXClient", "WhisperXConfig", "WhisperXResult", "SpeakerSegment"]

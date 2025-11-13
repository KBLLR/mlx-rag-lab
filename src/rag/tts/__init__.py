"""
Text-to-Speech abstractions for Marvis TTS, Kokoro TTS, and viseme mapping.
"""

from .kokoro_tts import KokoroConfig, KokoroTTSClient, PhonemeData
from .marvis_tts import MarvisTTSClient, TTSConfig
from .viseme_mapper import VisemeData, VisemeMapper

__all__ = [
    "MarvisTTSClient",
    "TTSConfig",
    "KokoroTTSClient",
    "KokoroConfig",
    "PhonemeData",
    "VisemeMapper",
    "VisemeData",
]

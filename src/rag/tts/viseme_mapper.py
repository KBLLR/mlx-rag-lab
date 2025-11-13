"""
Phoneme to Viseme mapper for Ready Player Me / Oculus lip-sync.

Maps IPA phonemes to Oculus viseme IDs used by Ready Player Me avatars.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class VisemeData:
    """Viseme timing data for lip-sync."""

    viseme: str  # Oculus viseme ID
    time: float  # Start time in seconds
    duration: float  # Duration in seconds


class VisemeMapper:
    """
    Maps IPA phonemes to Oculus viseme IDs.

    Ready Player Me avatars support 14 Oculus visemes:
    - sil: Silence
    - PP: Bilabials (p, b, m)
    - FF: Labiodentals (f, v)
    - TH: Dental fricatives (th)
    - DD: Alveolar stops (t, d)
    - kk: Velar stops (k, g)
    - CH: Postalveolar affricates (ch, j)
    - SS: Sibilants (s, z)
    - nn: Nasal (n)
    - RR: Rhotic (r)
    - aa: Open vowels (a, æ)
    - E: Mid front vowels (e, ɛ)
    - I: Close front vowels (i)
    - O: Back rounded vowels (o, ɔ)
    - U: Close back vowels (u)
    """

    # IPA phoneme → Oculus viseme mapping
    PHONEME_TO_VISEME = {
        # Silence
        "": "sil",
        " ": "sil",
        "_": "sil",
        # Bilabials
        "p": "PP",
        "b": "PP",
        "m": "PP",
        "pʰ": "PP",
        # Labiodentals
        "f": "FF",
        "v": "FF",
        # Dental fricatives
        "θ": "TH",
        "ð": "TH",
        # Alveolar stops
        "t": "DD",
        "d": "DD",
        "tʰ": "DD",
        # Velar stops
        "k": "kk",
        "g": "kk",
        "ɡ": "kk",
        "kʰ": "kk",
        # Postalveolar affricates
        "tʃ": "CH",
        "dʒ": "CH",
        "ʃ": "CH",
        "ʒ": "CH",
        # Sibilants
        "s": "SS",
        "z": "SS",
        # Nasals
        "n": "nn",
        "ŋ": "nn",
        "ɲ": "nn",
        # Rhotics
        "r": "RR",
        "ɹ": "RR",
        "ɾ": "RR",
        # Approximants
        "l": "DD",
        "j": "I",
        "w": "U",
        "ʍ": "U",
        "h": "kk",
        "ɦ": "kk",
        # Open vowels
        "a": "aa",
        "ɑ": "aa",
        "æ": "aa",
        "ɐ": "aa",
        # Mid front vowels
        "e": "E",
        "ɛ": "E",
        "ə": "E",  # Schwa
        "ɜ": "E",
        "ɚ": "E",
        # Close front vowels
        "i": "I",
        "ɪ": "I",
        "iː": "I",
        "ɨ": "I",
        # Mid back vowels
        "o": "O",
        "ɔ": "O",
        "ɒ": "O",
        # Close back vowels
        "u": "U",
        "ʊ": "U",
        "uː": "U",
        # Diphthongs (use primary vowel)
        "aɪ": "aa",
        "aʊ": "aa",
        "eɪ": "E",
        "oʊ": "O",
        "ɔɪ": "O",
        "ɪə": "I",
        "eə": "E",
        "ʊə": "U",
    }

    @classmethod
    def map_phoneme(cls, phoneme: str) -> str:
        """
        Map a single IPA phoneme to Oculus viseme ID.

        Args:
            phoneme: IPA phoneme string

        Returns:
            Oculus viseme ID (defaults to "sil" if unmapped)
        """
        # Clean phoneme
        phoneme = phoneme.strip()

        # Direct mapping
        if phoneme in cls.PHONEME_TO_VISEME:
            return cls.PHONEME_TO_VISEME[phoneme]

        # Try removing length/stress markers
        clean = phoneme.rstrip("ːˈˌ")
        if clean in cls.PHONEME_TO_VISEME:
            return cls.PHONEME_TO_VISEME[clean]

        # Default to silence for unknown
        return "sil"

    @classmethod
    def map_phoneme_sequence(
        cls,
        phonemes: str,
        duration_ms: Optional[float] = None,
    ) -> list[VisemeData]:
        """
        Map phoneme sequence to viseme sequence with estimated timing.

        Args:
            phonemes: Space-separated IPA phonemes
            duration_ms: Total duration in milliseconds (for timing estimation)

        Returns:
            List of VisemeData with timing info
        """
        phoneme_list = phonemes.split()

        if not phoneme_list:
            return [VisemeData(viseme="sil", time=0.0, duration=0.1)]

        visemes = []
        num_phonemes = len(phoneme_list)

        # Estimate duration per phoneme if total duration provided
        if duration_ms:
            duration_per_phoneme = (duration_ms / 1000.0) / num_phonemes
        else:
            # Default: ~100ms per phoneme
            duration_per_phoneme = 0.1

        current_time = 0.0

        for phoneme in phoneme_list:
            viseme_id = cls.map_phoneme(phoneme)
            visemes.append(
                VisemeData(
                    viseme=viseme_id,
                    time=current_time,
                    duration=duration_per_phoneme,
                )
            )
            current_time += duration_per_phoneme

        return visemes

    @classmethod
    def to_headtts_format(cls, viseme_data: list[VisemeData]) -> dict:
        """
        Convert viseme data to HeadTTS-compatible JSON format.

        Args:
            viseme_data: List of VisemeData

        Returns:
            Dict matching HeadTTS output format
        """
        visemes = []
        vtimes = []
        vdurations = []

        for vd in viseme_data:
            visemes.append(vd.viseme)
            vtimes.append(int(vd.time * 1000))  # Convert to milliseconds
            vdurations.append(int(vd.duration * 1000))

        return {
            "visemes": visemes,
            "vtimes": vtimes,
            "vdurations": vdurations,
        }

    @classmethod
    def from_kokoro_phonemes(
        cls,
        phoneme_data_list: list,
        sample_rate: int = 24000,
    ) -> dict:
        """
        Convert Kokoro phoneme output to HeadTTS-compatible viseme format.

        Args:
            phoneme_data_list: List of PhonemeData from KokoroTTSClient
            sample_rate: Audio sample rate (default: 24kHz)

        Returns:
            HeadTTS-compatible dict with words, visemes, and timing
        """
        words = []
        wtimes = []
        wdurations = []
        all_viseme_data = []

        current_time_ms = 0

        for phoneme_data in phoneme_data_list:
            # Extract word/grapheme
            words.append(phoneme_data.graphemes)

            # Calculate duration from audio length
            audio_samples = len(phoneme_data.audio)
            duration_ms = (audio_samples / sample_rate) * 1000

            wtimes.append(current_time_ms)
            wdurations.append(int(duration_ms))

            # Map phonemes to visemes
            viseme_sequence = cls.map_phoneme_sequence(
                phoneme_data.phonemes,
                duration_ms=duration_ms,
            )

            # Adjust viseme timing to absolute time
            for vd in viseme_sequence:
                adjusted_vd = VisemeData(
                    viseme=vd.viseme,
                    time=(current_time_ms / 1000.0) + vd.time,
                    duration=vd.duration,
                )
                all_viseme_data.append(adjusted_vd)

            current_time_ms += int(duration_ms)

        # Convert to HeadTTS format
        viseme_dict = cls.to_headtts_format(all_viseme_data)

        return {
            "words": words,
            "wtimes": wtimes,
            "wdurations": wdurations,
            **viseme_dict,
        }

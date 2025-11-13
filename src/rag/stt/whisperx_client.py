"""
WhisperX client with optional diarization for Speech-to-Text flows.

This wrapper hides the WhisperX configuration surface so CLI apps can
toggle diarization without pulling pyannote/torch specifics into the app layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# torchaudio>=2.5 exposes AudioMetaData; reintroduce for newer releases where it's removed.
try:  # pragma: no cover - platform dep
    import torchaudio  # type: ignore

    if torchaudio is not None and not hasattr(torchaudio, "AudioMetaData"):
        from collections import namedtuple

        AudioMetaData = namedtuple(
            "AudioMetaData",
            ["sample_rate", "num_frames", "num_channels", "bits_per_sample"],
        )
        torchaudio.AudioMetaData = AudioMetaData  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    torchaudio = None  # noqa: F401


@dataclass
class SpeakerSegment:
    """Contiguous text spans grouped by speaker label."""

    speaker: str
    start: float
    end: float
    text: str
    words: Optional[List[Dict[str, Any]]] = None


@dataclass
class WhisperXConfig:
    """Configuration for WhisperX STT + diarization."""

    model_name: str = "mlx-community/whisper-large-v3-mlx"
    backend: str = "mlx"
    device: str = "cpu"
    compute_type: str = "float16"
    batch_size: int = 4
    chunk_size: int = 30
    language: Optional[str] = None
    task: str = "transcribe"
    vad_method: str = "silero"
    vad_options: Dict[str, Any] = field(
        default_factory=lambda: {
            "vad_onset": 0.5,
            "vad_offset": 0.363,
        }
    )
    asr_options: Dict[str, Any] = field(default_factory=dict)
    model_dir: Optional[str] = None
    model_cache_only: bool = False
    threads: int = 0
    print_progress: bool = False
    verbose: bool = False

    # Alignment
    enable_alignment: bool = True
    align_model: Optional[str] = None
    interpolate_method: str = "nearest"
    return_char_alignments: bool = False

    # Diarization
    enable_diarization: bool = True
    diarize_model: str = "pyannote/speaker-diarization-3.1"
    hf_token: Optional[str] = None
    diarize_device: str = "cpu"
    num_speakers: Optional[int] = None
    min_speakers: Optional[int] = None
    max_speakers: Optional[int] = None
    fill_nearest: bool = False
    merge_gap_s: float = 0.5


@dataclass
class WhisperXResult:
    """Structured transcription output."""

    text: str
    language: str
    segments: List[Dict[str, Any]]
    speaker_segments: List[SpeakerSegment]
    diarization_segments: Optional[List[Dict[str, Any]]] = None
    raw_result: Optional[Dict[str, Any]] = None


class WhisperXClient:
    """Thin wrapper around whisperx to keep app code clean."""

    def __init__(self, config: Optional[WhisperXConfig] = None):
        self.config = config or WhisperXConfig()

        try:
            import whisperx  # type: ignore
        except ImportError as exc:  # pragma: no cover - import guard
            raise ImportError(
                "whisperx is not installed. Install with:\n"
                "  pip install 'whisperx @ git+https://github.com/sooth/whisperx-mlx.git'"
            ) from exc

        self._whisperx = whisperx
        self._asr_model = self._load_asr_model()
        self._align_models: dict[str, tuple[Any, dict]] = {}
        self._diarize_pipeline = None

    def _load_asr_model(self):
        """Load WhisperX ASR backend once per client."""
        return self._whisperx.load_model(
            self.config.model_name,
            device=self.config.device,
            compute_type=self.config.compute_type,
            batch_size=self.config.batch_size,
            asr_options=self.config.asr_options,
            language=self.config.language,
            vad_method=self.config.vad_method,
            vad_options=self.config.vad_options,
            task=self.config.task,
            download_root=self.config.model_dir,
            local_files_only=self.config.model_cache_only,
            threads=self.config.threads,
            backend=self.config.backend,
        )

    def _get_align_model(self, language: str):
        """Lazy-load align models per language."""
        if not self.config.enable_alignment:
            return None, None

        cache_key = language or "default"
        if cache_key in self._align_models:
            return self._align_models[cache_key]

        align_model = self.config.align_model
        model, metadata = self._whisperx.load_align_model(
            language,
            device=self.config.device,
            model_name=align_model,
        )
        self._align_models[cache_key] = (model, metadata)
        return model, metadata

    def _get_diarize_pipeline(self):
        """Lazy-load diarization pipeline."""
        if not self.config.enable_diarization:
            return None

        if self._diarize_pipeline is None:
            self._diarize_pipeline = self._whisperx.diarize.DiarizationPipeline(  # type: ignore[attr-defined]
                model_name=self.config.diarize_model,
                use_auth_token=self.config.hf_token,
                device=self.config.diarize_device,
            )

        return self._diarize_pipeline

    def transcribe(self, audio_path: Path) -> WhisperXResult:
        """Transcribe + (optionally) diarize a single audio file."""
        audio_path = Path(audio_path)
        audio = self._whisperx.load_audio(str(audio_path))

        result = self._asr_model.transcribe(
            audio,
            batch_size=self.config.batch_size,
            chunk_size=self.config.chunk_size,
            print_progress=self.config.print_progress,
            verbose=self.config.verbose,
        )

        language = result.get("language") or self.config.language or "en"

        if self.config.enable_alignment and result.get("segments"):
            align_model, align_metadata = self._get_align_model(language)
            if align_model is not None:
                aligned = self._whisperx.align(
                    result["segments"],
                    align_model,
                    align_metadata,
                    audio,
                    self.config.device,
                    interpolate_method=self.config.interpolate_method,
                    return_char_alignments=self.config.return_char_alignments,
                    print_progress=self.config.print_progress,
                )
                aligned["language"] = language
                result = aligned

        diarization_segments = None
        if self.config.enable_diarization and result.get("segments"):
            diarize_pipeline = self._get_diarize_pipeline()
            if diarize_pipeline is not None:
                diarize_df = diarize_pipeline(
                    str(audio_path),
                    num_speakers=self.config.num_speakers,
                    min_speakers=self.config.min_speakers,
                    max_speakers=self.config.max_speakers,
                )
                result = self._whisperx.assign_word_speakers(
                    diarize_df,
                    result,
                    speaker_embeddings=None,
                    fill_nearest=self.config.fill_nearest,
                )
                diarization_segments = self._dataframe_to_segments(diarize_df)

        text = self._segments_to_text(result.get("segments", []))
        speaker_segments = self._merge_speaker_segments(result.get("segments", []))

        return WhisperXResult(
            text=text,
            language=language,
            segments=result.get("segments", []),
            speaker_segments=speaker_segments,
            diarization_segments=diarization_segments,
            raw_result=result,
        )

    @staticmethod
    def _segments_to_text(segments: List[Dict[str, Any]]) -> str:
        """Collapse Whisper segments into a single transcript."""
        texts = [seg.get("text", "").strip() for seg in segments if seg.get("text")]
        return " ".join(texts).strip()

    def _merge_speaker_segments(
        self,
        segments: List[Dict[str, Any]],
    ) -> List[SpeakerSegment]:
        """Group consecutive segments by speaker label."""
        merged: List[SpeakerSegment] = []
        gap = self.config.merge_gap_s

        for seg in segments:
            speaker = seg.get("speaker")
            text = seg.get("text", "").strip()

            if not speaker or not text:
                continue

            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start))
            words = seg.get("words")

            if (
                merged
                and merged[-1].speaker == speaker
                and start - merged[-1].end <= gap
            ):
                merged[-1].text = f"{merged[-1].text} {text}".strip()
                merged[-1].end = end
                if words:
                    merged[-1].words = (merged[-1].words or []) + words
            else:
                merged.append(
                    SpeakerSegment(
                        speaker=speaker,
                        start=start,
                        end=end,
                        text=text,
                        words=words,
                    )
                )

        return merged

    @staticmethod
    def _dataframe_to_segments(diarize_df) -> List[Dict[str, Any]]:
        """Convert diarization dataframe into serializable dicts."""
        segments: List[Dict[str, Any]] = []
        if diarize_df is None:
            return segments

        # The dataframe yields tuples ((Segment, track), label, speaker)
        for _, row in diarize_df.iterrows():
            segments.append(
                {
                    "speaker": row.get("speaker") or row.get("label"),
                    "start": float(row.get("start", 0.0)),
                    "end": float(row.get("end", 0.0)),
                }
            )
        return segments

#!/usr/bin/env python3
"""
Speech-to-Speech Avatar CLI - Full pipeline with viseme output for Ready Player Me.

Flow: Audio → Whisper → ChatSession → TTS (Marvis/Kokoro) → Audio + Visemes

Features:
- Whisper STT (speech-to-text)
- GPT-OSS conversational AI
- Marvis TTS (simple audio) or Kokoro TTS (audio + visemes)
- Viseme JSON output for Ready Player Me lip-sync
"""

import os

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import argparse
import json
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

console = Console()

# Import Whisper from examples
sys.path.insert(0, str(Path(__file__).parent.parent / "examples" / "whisper"))

try:
    from mlx_whisper import transcribe

    from rag.chat import ChatSession
    from rag.stt import (
        SpeakerSegment,
        WhisperXClient,
        WhisperXConfig,
        WhisperXResult,
    )
    from rag.tts import KokoroConfig, KokoroTTSClient, MarvisTTSClient, TTSConfig, VisemeMapper
except ImportError as e:
    console.print(f"[red]Import error: {e}[/red]")
    console.print("[yellow]Make sure project is installed: uv sync[/yellow]")
    sys.exit(1)


def parse_speaker_voice_map(value: Optional[str]) -> dict[str, str]:
    """Parse CLI mapping like 'SPEAKER_00=af_bella,SPEAKER_01=am_adam'."""
    mapping: dict[str, str] = {}
    if not value:
        return mapping

    pairs = [item.strip() for item in value.split(",") if item.strip()]
    for pair in pairs:
        if "=" not in pair:
            continue
        speaker, voice = pair.split("=", 1)
        speaker = speaker.strip()
        voice = voice.strip()
        if speaker and voice:
            mapping[speaker] = voice
    return mapping


def parse_voice_pool(value: Optional[str]) -> list[str]:
    """Parse comma separated voice list."""
    if not value:
        return []
    voices = [voice.strip() for voice in value.split(",") if voice.strip()]
    return [voice for voice in voices if voice]


class STSAvatarPipeline:
    """
    Speech-to-Speech pipeline with avatar lip-sync support.

    Supports two TTS modes:
    1. Marvis: Simple audio output (no visemes)
    2. Kokoro: Audio + phoneme + viseme data for avatar lip-sync
    """

    def __init__(
        self,
        chat_model: str,
        tts_engine: str = "kokoro",  # "marvis" or "kokoro"
        tts_voice: str = "af_bella",
        whisper_model: str = "mlx-community/whisper-large-v3-mlx",
        stt_backend: str = "whisper",
        diarize: bool = False,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
        hf_token: Optional[str] = None,
        speaker_voice_map: Optional[dict[str, str]] = None,
        speaker_voice_pool: Optional[list[str]] = None,
        system_prompt: str = "You are a helpful AI assistant. Keep responses concise for speech.",
        audio_output_dir: str = "var/sts_avatar",
        max_tokens: int = 256,
        save_visemes: bool = True,
    ):
        """
        Initialize STS avatar pipeline.

        Args:
            chat_model: GPT-OSS or other MLX chat model
            tts_engine: "marvis" or "kokoro"
            tts_voice: Voice ID (Kokoro: af_bella, am_adam, etc.)
            whisper_model: Whisper model ID
            stt_backend: "whisper" (default) or "whisperx"
            diarize: Enable speaker diarization (WhisperX backend only)
            min_speakers: Minimum speakers for diarization
            max_speakers: Maximum speakers for diarization
            hf_token: HF token for gated diarization models
            speaker_voice_map: Explicit mapping of speaker labels to Kokoro voices
            speaker_voice_pool: Voice list to auto-assign when new speakers appear
            system_prompt: System message for chat
            audio_output_dir: Where to save audio/viseme files
            max_tokens: Max tokens per response
            save_visemes: Whether to save viseme JSON (Kokoro only)
        """
        self.tts_engine = tts_engine
        self.save_visemes = save_visemes
        self.whisper_model = whisper_model
        self.stt_backend = stt_backend
        self.diarize = diarize if stt_backend == "whisperx" else False

        # Use absolute path for output directory
        if not Path(audio_output_dir).is_absolute():
            project_root = Path(__file__).resolve().parent.parent
            self.audio_output_dir = project_root / audio_output_dir
        else:
            self.audio_output_dir = Path(audio_output_dir)

        self.audio_output_dir.mkdir(parents=True, exist_ok=True)

        self.whisperx_client: Optional[WhisperXClient] = None
        if self.stt_backend == "whisperx":
            whisperx_cfg = WhisperXConfig(
                model_name=self.whisper_model,
                backend="mlx",
                enable_diarization=self.diarize,
                min_speakers=min_speakers,
                max_speakers=max_speakers,
                hf_token=hf_token,
            )
            try:
                self.whisperx_client = WhisperXClient(whisperx_cfg)
            except ImportError as exc:
                console.print(f"[red]WhisperX backend unavailable: {exc}[/red]")
                console.print("[yellow]Falling back to mlx_whisper without diarization.[/yellow]")
                self.stt_backend = "whisper"
                self.diarize = False

        # Initialize chat
        console.print("[cyan]Loading chat model...[/cyan]")
        self.chat = ChatSession(
            chat_model,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )

        # Initialize TTS
        console.print(f"[cyan]Loading {tts_engine.upper()} TTS...[/cyan]")
        if tts_engine == "kokoro":
            self.tts = KokoroTTSClient(lang_code="a")
            self.tts_config = KokoroConfig(voice=tts_voice)
        elif tts_engine == "marvis":
            self.tts = MarvisTTSClient("Marvis-AI/marvis-tts-100m-v0.2")
            self.tts_config = TTSConfig(language="en", sample_rate=22050)
        else:
            raise ValueError(f"Unknown TTS engine: {tts_engine}")

        self.speaker_voice_overrides = speaker_voice_map or {}
        self.speaker_voice_pool = speaker_voice_pool or [tts_voice]
        if not self.speaker_voice_pool:
            self.speaker_voice_pool = [tts_voice]
        self._speaker_voice_cache: dict[str, str] = dict(self.speaker_voice_overrides)
        self._speaker_voice_pool_index = 0

    def transcribe_audio(self, audio_path: Path) -> WhisperXResult:
        """
        Transcribe audio to text using selected STT backend.

        Args:
            audio_path: Path to audio file

        Returns:
            WhisperXResult with text + optional speaker data
        """
        console.print(f"[cyan]🎤 Transcribing: {audio_path.name}[/cyan]")

        if self.stt_backend == "whisperx" and self.whisperx_client:
            transcription = self.whisperx_client.transcribe(audio_path)
            self._display_speaker_preview(transcription.speaker_segments)
            console.print(f"[green]📝 Transcribed:[/green] {transcription.text}\n")
            return transcription

        # Fallback to baseline mlx_whisper
        result = transcribe(
            str(audio_path),
            path_or_hf_repo=self.whisper_model,
            verbose=False,
            task="transcribe",
        )

        transcribed_text = result["text"].strip()
        console.print(f"[green]📝 Transcribed:[/green] {transcribed_text}\n")

        return WhisperXResult(
            text=transcribed_text,
            language=result.get("language", "en"),
            segments=result.get("segments", []),
            speaker_segments=[],
            diarization_segments=None,
            raw_result=result,
        )

    def _display_speaker_preview(self, segments: Optional[list[SpeakerSegment]]):
        """Show short preview of detected speakers."""
        if not segments:
            return

        console.print("[dim]👥 Detected speakers:[/dim]")
        for seg in segments[:3]:
            preview = seg.text[:80] + ("..." if len(seg.text) > 80 else "")
            console.print(f"  [cyan]{seg.speaker}[/cyan]: {preview}")
        if len(segments) > 3:
            console.print(f"  [dim]... +{len(segments) - 3} more segments[/dim]")
        console.print()

    def _assign_voice_map(self, speakers: list[str]) -> dict[str, str]:
        """Return deterministic speaker→voice mapping."""
        mapping: dict[str, str] = {}
        for speaker in speakers:
            if speaker in self._speaker_voice_cache:
                mapping[speaker] = self._speaker_voice_cache[speaker]
                continue

            if speaker in self.speaker_voice_overrides:
                voice = self.speaker_voice_overrides[speaker]
            else:
                voice = self._next_voice_from_pool()

            self._speaker_voice_cache[speaker] = voice
            mapping[speaker] = voice
        return mapping

    def _next_voice_from_pool(self) -> str:
        """Round-robin through configured voice pool."""
        pool = self.speaker_voice_pool or [self.tts_config.voice]
        voice = pool[self._speaker_voice_pool_index % len(pool)]
        self._speaker_voice_pool_index += 1
        return voice

    def _save_speaker_metadata(
        self,
        response_dir: Path,
        transcription: WhisperXResult,
    ):
        """Persist diarization metadata alongside transcription."""
        if not transcription.speaker_segments:
            return

        speakers = [seg.speaker for seg in transcription.speaker_segments]
        voice_map = self._assign_voice_map(speakers)

        speaker_payload = []
        speaker_text_lines = []

        for seg in transcription.speaker_segments:
            voice = voice_map.get(seg.speaker, self.tts_config.voice)
            speaker_payload.append(
                {
                    "speaker": seg.speaker,
                    "voice": voice,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "words": seg.words,
                }
            )
            speaker_text_lines.append(f"{seg.speaker} ({voice}): {seg.text}")

        with open(response_dir / "speakers.json", "w") as f:
            json.dump(speaker_payload, f, indent=2)

        with open(response_dir / "transcription_speakers.txt", "w") as f:
            f.write("\n".join(speaker_text_lines))

    def generate_response(self, user_text: str, stream: bool = False) -> str:
        """
        Generate chat response.

        Args:
            user_text: User input text
            stream: Whether to stream response

        Returns:
            Response text
        """
        if stream:
            console.print("[bold cyan]Assistant:[/bold cyan] ", end="")
            response_text = ""
            for token in self.chat.chat_stream(user_text):
                console.print(token, end="")
                response_text += token
            console.print()
        else:
            response_text = self.chat.chat(user_text)
            console.print(f"[bold cyan]Assistant:[/bold cyan] {response_text}")

        return response_text

    def synthesize_speech(
        self,
        text: str,
        transcription: str = None,
    ) -> tuple[Path, Path | None]:
        """
        Synthesize speech from text.

        Args:
            text: Input text
            transcription: Optional transcription to save alongside

        Returns:
            (audio_path, viseme_json_path or None)
        """
        console.print("[dim]🎤 Synthesizing speech...[/dim]")

        # Create subfolder for this response
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response_dir = self.audio_output_dir / f"response_{timestamp}"
        response_dir.mkdir(parents=True, exist_ok=True)

        audio_path = response_dir / "audio.wav"
        viseme_path = None

        if self.tts_engine == "kokoro":
            # Kokoro: audio + phonemes + visemes
            audio, phoneme_data = self.tts.synthesize(text, self.tts_config)
            self.tts.save_wav(audio, audio_path, self.tts_config.sample_rate)

            if self.save_visemes:
                # Generate viseme data
                viseme_dict = VisemeMapper.from_kokoro_phonemes(
                    phoneme_data,
                    sample_rate=self.tts_config.sample_rate,
                )

                viseme_path = response_dir / "visemes.json"
                with open(viseme_path, "w") as f:
                    json.dump(viseme_dict, f, indent=2)

        elif self.tts_engine == "marvis":
            # Marvis: audio only
            audio = self.tts.synthesize(text, self.tts_config)
            self.tts.save_wav(audio, audio_path, self.tts_config.sample_rate)

        # Save response text
        response_text_path = response_dir / "response.txt"
        with open(response_text_path, "w") as f:
            f.write(text)

        # Save transcription if provided
        if transcription:
            transcription_path = response_dir / "transcription.txt"
            with open(transcription_path, "w") as f:
                f.write(transcription)

        return audio_path, viseme_path

    def process_audio_file(
        self,
        audio_path: Path,
        stream_text: bool = False,
    ) -> tuple[str, Path, Path | None, WhisperXResult]:
        """
        Process audio file through full STS pipeline.

        Args:
            audio_path: Input audio file
            stream_text: Whether to stream chat response

        Returns:
            (response_text, audio_path, viseme_json_path or None, transcription_result)
        """
        # 1. STT: Audio → Text
        transcription = self.transcribe_audio(audio_path)
        user_text = transcription.text

        # 2. Chat: Text → Response
        response_text = self.generate_response(user_text, stream=stream_text)

        # 3. TTS: Response → Audio + Visemes
        audio_out, viseme_out = self.synthesize_speech(response_text, transcription=user_text)

        if transcription.speaker_segments:
            self._save_speaker_metadata(audio_out.parent, transcription)

        return response_text, audio_out, viseme_out, transcription

    def _list_available_audio(self, source_dir: Path = None) -> list[Path]:
        """List available audio files from source directory."""
        if source_dir is None:
            # Use absolute path relative to project root
            from pathlib import Path
            project_root = Path(__file__).resolve().parent.parent
            source_dir = project_root / "var" / "source_audios"

        if not source_dir.exists():
            return []

        audio_extensions = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".mp4"}
        audio_files = []

        for ext in audio_extensions:
            audio_files.extend(source_dir.glob(f"*{ext}"))

        return sorted(audio_files, key=lambda p: p.stat().st_mtime, reverse=True)

    def _display_audio_list(self, audio_files: list[Path]):
        """Display numbered list of audio files."""
        console.print("\n[bold cyan]📁 Available Audio Files:[/bold cyan]")

        if not audio_files:
            console.print("[dim]No audio files found in var/source_audios/[/dim]\n")
            return

        for idx, file in enumerate(audio_files[:20], 1):  # Show max 20
            size_mb = file.stat().st_size / (1024 * 1024)
            console.print(f"  {idx:2d}. {file.name[:60]:<60} [{size_mb:.1f}MB]")

        if len(audio_files) > 20:
            console.print(f"  [dim]... and {len(audio_files) - 20} more[/dim]")

        console.print()

    def run_interactive(self, stream_text: bool = False):
        """
        Interactive mode: provide audio file paths for conversation.

        Args:
            stream_text: Whether to stream text responses
        """
        console.print("\n[bold green]🎙️  STS Avatar Pipeline Started[/bold green]")

        # List available audio files at startup
        # Use absolute path relative to project root
        project_root = Path(__file__).resolve().parent.parent
        source_dir = project_root / "var" / "source_audios"
        audio_files = self._list_available_audio(source_dir)
        self._display_audio_list(audio_files)

        console.print("[dim]Enter audio file path or number from list above[/dim]")
        console.print("[dim]Commands: /list, /exit, /clear, /history[/dim]\n")

        while True:
            try:
                user_input = console.input("[bold green]Audio file:[/bold green] ").strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[cyan]Bye![/cyan]")
                break

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ["/exit", "/quit", "/q"]:
                break
            elif user_input.lower() == "/list":
                audio_files = self._list_available_audio(source_dir)
                self._display_audio_list(audio_files)
                continue
            elif user_input.lower() == "/clear":
                self.chat.clear_history(keep_system=True)
                console.print("[yellow]History cleared[/yellow]\n")
                continue
            elif user_input.lower() == "/history":
                history = self.chat.get_history()
                if not history:
                    console.print("[dim]History is empty[/dim]\n")
                else:
                    for msg in history:
                        console.print(f"{msg['role']}: {msg['content'][:80]}...")
                console.print()
                continue

            # Handle numbered selection
            if user_input.isdigit():
                idx = int(user_input) - 1
                if 0 <= idx < len(audio_files):
                    audio_path = audio_files[idx]
                    console.print(f"[dim]Selected: {audio_path.name}[/dim]\n")
                else:
                    console.print(f"[red]Invalid number. Choose 1-{len(audio_files)}[/red]\n")
                    continue
            else:
                # Handle file path (absolute or relative)
                audio_path = Path(user_input)

                # If just filename provided, try source_audios directory
                if not audio_path.exists() and not audio_path.is_absolute():
                    audio_path = source_dir / user_input

            if not audio_path.exists():
                console.print(f"[red]File not found: {audio_path}[/red]\n")
                console.print("[dim]Tip: Use /list to see available files[/dim]\n")
                continue

            try:
                response_text, audio_out, viseme_out, transcription = self.process_audio_file(
                    audio_path, stream_text=stream_text
                )

                # Show folder containing all files
                response_folder = audio_out.parent
                console.print(f"\n[green]📁 Saved to: {response_folder.name}/[/green]")
                console.print(f"   [dim]• audio.wav[/dim]")
                console.print(f"   [dim]• response.txt[/dim]")
                console.print(f"   [dim]• transcription.txt[/dim]")
                if viseme_out:
                    console.print(f"   [dim]• visemes.json[/dim]")
                if transcription.speaker_segments:
                    console.print(f"   [dim]• transcription_speakers.txt[/dim]")
                    console.print(f"   [dim]• speakers.json[/dim]")
                    self._display_speaker_preview(transcription.speaker_segments)
                console.print(f"[green]🎧 Audio file:[/green] {audio_out}")
                console.print()

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]\n")
                continue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="STS Avatar CLI - Speech-to-Speech with viseme output"
    )

    parser.add_argument(
        "--chat-model",
        type=str,
        default="mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx",
        help="Chat model ID or path",
    )

    parser.add_argument(
        "--tts-engine",
        type=str,
        default="kokoro",
        choices=["marvis", "kokoro"],
        help="TTS engine: marvis (audio only) or kokoro (audio + visemes)",
    )

    parser.add_argument(
        "--tts-voice",
        type=str,
        default="af_bella",
        help="Voice ID (Kokoro: af_bella, am_adam, etc.; Marvis: ignored)",
    )

    parser.add_argument(
        "--whisper-model",
        type=str,
        default="mlx-community/whisper-large-v3-mlx",
        help="Whisper model ID",
    )
    parser.add_argument(
        "--stt-backend",
        type=str,
        default="whisper",
        choices=["whisper", "whisperx"],
        help="Speech-to-text backend: 'whisper' (default) or 'whisperx' for diarization",
    )
    parser.add_argument(
        "--diarize",
        action="store_true",
        help="Enable speaker diarization (WhisperX backend only)",
    )
    parser.add_argument(
        "--min-speakers",
        type=int,
        default=None,
        help="Minimum number of speakers to detect (WhisperX)",
    )
    parser.add_argument(
        "--max-speakers",
        type=int,
        default=None,
        help="Maximum number of speakers to detect (WhisperX)",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="HF token for diarization models that require authentication",
    )
    parser.add_argument(
        "--speaker-voices",
        type=str,
        help="Comma list mapping speaker labels to Kokoro voices (e.g. 'SPEAKER_00=af_bella,SPEAKER_01=am_adam')",
    )
    parser.add_argument(
        "--speaker-voice-pool",
        type=str,
        default=None,
        help="Comma-separated list of fallback voices used when new speakers appear",
    )

    parser.add_argument(
        "--system-prompt",
        type=str,
        default="You are a helpful, concise AI assistant. Keep responses brief for speech.",
        help="System prompt for chat",
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=256,
        help="Max tokens per response",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("var/sts_avatar"),
        help="Directory to save audio and viseme files",
    )

    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream text responses",
    )

    parser.add_argument(
        "--single",
        type=Path,
        help="Single audio file mode (vs interactive)",
    )

    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available Kokoro voices and exit",
    )
    return parser


def cleanup_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    console.print("\n\n[yellow]🧹 Cleaning up...[/yellow]")
    console.print("[green]✅ Bye![/green]\n")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, cleanup_handler)

    args = build_parser().parse_args()

    # List voices and exit
    if args.list_voices:
        console.print("\n[bold cyan]Kokoro TTS Voices (American English)[/bold cyan]\n")
        voices = KokoroTTSClient.list_voices("a")
        for voice in voices:
            prefix = voice[:2]
            gender = "Female" if prefix[1] == "f" else "Male"
            console.print(f"  {voice:20} [{gender}]")
        console.print()
        return

    # Initialize pipeline
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]STS Avatar Pipeline[/bold cyan]\n"
            f"Chat: {args.chat_model}\n"
            f"TTS: {args.tts_engine.upper()} ({args.tts_voice})\n"
            f"STT: {args.stt_backend} ({'diarize' if args.diarize else 'no diarize'})\n"
            f"Whisper: {args.whisper_model}\n"
            f"Max tokens: {args.max_tokens}\n"
            f"Output: {args.output_dir}\n"
            "Visemes: Yes (visemes.json saved per response)",
            border_style="cyan",
        )
    )
    console.print()

    speaker_voice_map = parse_speaker_voice_map(args.speaker_voices)
    speaker_voice_pool = parse_voice_pool(args.speaker_voice_pool)
    if not speaker_voice_pool:
        speaker_voice_pool = [args.tts_voice]

    pipeline = STSAvatarPipeline(
        chat_model=args.chat_model,
        tts_engine=args.tts_engine,
        tts_voice=args.tts_voice,
        whisper_model=args.whisper_model,
        stt_backend=args.stt_backend,
        diarize=args.diarize,
        min_speakers=args.min_speakers,
        max_speakers=args.max_speakers,
        hf_token=args.hf_token,
        speaker_voice_map=speaker_voice_map,
        speaker_voice_pool=speaker_voice_pool,
        system_prompt=args.system_prompt,
        audio_output_dir=str(args.output_dir),
        max_tokens=args.max_tokens,
    )

    # Single query or interactive
    if args.single:
        if not args.single.exists():
            console.print(f"[red]File not found: {args.single}[/red]")
            sys.exit(1)

        response_text, audio_path, viseme_path, transcription = pipeline.process_audio_file(
            args.single, stream_text=args.stream
        )

        response_folder = audio_path.parent
        console.print(f"\n[bold]Response:[/bold] {response_text[:200]}...")
        console.print(f"\n[green]📁 Saved to: {response_folder}/[/green]")
        console.print(f"   [dim]• audio.wav[/dim]")
        console.print(f"   [dim]• response.txt[/dim]")
        console.print(f"   [dim]• transcription.txt[/dim]")
        if viseme_path:
            console.print(f"   [dim]• visemes.json[/dim]")
        if transcription.speaker_segments:
            console.print(f"   [dim]• transcription_speakers.txt[/dim]")
            console.print(f"   [dim]• speakers.json[/dim]")
            pipeline._display_speaker_preview(transcription.speaker_segments)
        console.print(f"[green]🎧 Audio file:[/green] {audio_path}")
    else:
        pipeline.run_interactive(stream_text=args.stream)


if __name__ == "__main__":
    main()

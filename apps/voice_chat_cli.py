#!/usr/bin/env python3
"""
Voice Chat CLI - Full pipeline: User → GPT-OSS → TTS → Audio

Combines ChatSession (GPT-OSS 20B) with MarvisTTS for spoken responses.
"""

import argparse
import queue
import signal
import sys
import tempfile
import threading
from pathlib import Path
from datetime import datetime

import os

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np
import time
from rich.console import Console
from rich.panel import Panel
import sounddevice as sd
import soundfile as sf
from pynput import keyboard

console = Console()

sys.path.insert(0, str(Path(__file__).parent.parent / "examples" / "whisper"))

# Import our wrappers
try:
    from mlx_whisper import transcribe
    from rag.chat import ChatSession
    from rag.tts import KokoroConfig, KokoroTTSClient, MarvisTTSClient, TTSConfig
except ImportError as e:
    console.print(f"[red]Import error: {e}[/red]")
    console.print("[yellow]Make sure project is installed: uv sync[/yellow]")
    sys.exit(1)


class PushToTalkRecorder:
    """Capture microphone audio while spacebar is pressed."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = "float32"
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self._last_level = 0.0

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    @property
    def level(self) -> float:
        return self._last_level

    def _callback(self, indata, frames, time, status):  # pragma: no cover - realtime callback
        if status:
            console.print(f"[yellow]Audio warning: {status}[/yellow]")
        level = float(np.max(np.abs(indata))) if indata.size else 0.0
        # simple peak hold with quick decay
        self._last_level = max(level, self._last_level * 0.8)
        with self._lock:
            self._frames.append(indata.copy())

    def start(self) -> None:
        if self._stream is not None:
            return
        self._frames = []
        self._last_level = 0.0
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        if self._stream is None:
            return np.empty((0, self.channels), dtype=self.dtype)
        self._stream.stop()
        self._stream.close()
        self._stream = None
        with self._lock:
            if not self._frames:
                return np.empty((0, self.channels), dtype=self.dtype)
            return np.concatenate(self._frames, axis=0)


class VoiceChatPipeline:
    """
    Full pipeline: text input → GPT-OSS → TTS → audio output.
    """

    def __init__(
        self,
        chat_model: str,
        tts_engine: str = "marvis",  # "marvis" or "kokoro"
        tts_voice: str = "af_bella",
        tts_model: str = "Marvis-AI/marvis-tts-100m-v0.2",  # Deprecated, for backwards compat
        whisper_model: str = "mlx-community/whisper-large-v3-mlx",
        system_prompt: str = "You are a helpful AI assistant.",
        audio_output_dir: str = "var/voice_chat",
        max_tokens: int = 512,
        save_audio: bool = True
    ):
        """
        Initialize voice chat pipeline.

        Args:
            chat_model: GPT-OSS or other MLX model ID
            tts_engine: "marvis" or "kokoro"
            tts_voice: Voice ID for Kokoro (ignored for Marvis)
            tts_model: Deprecated, kept for backwards compatibility
            whisper_model: Whisper/STT model ID (used for live push-to-talk)
            system_prompt: System message for chat
            audio_output_dir: Where to save audio files
            max_tokens: Max tokens per chat response
            save_audio: Whether to save audio files (vs just play)
        """
        self.tts_engine = tts_engine
        self.audio_output_dir = Path(audio_output_dir)
        self.audio_output_dir.mkdir(parents=True, exist_ok=True)
        self.save_audio = save_audio
        self.whisper_model = whisper_model

        # Initialize chat
        console.print("[cyan]Loading chat model...[/cyan]")
        self.chat = ChatSession(
            chat_model,
            system_prompt=system_prompt,
            max_tokens=max_tokens
        )

        # Initialize TTS
        console.print(f"[cyan]Loading {tts_engine.upper()} TTS...[/cyan]")
        if tts_engine == "kokoro":
            self.tts = KokoroTTSClient(lang_code="a")
            self.tts_config = KokoroConfig(voice=tts_voice)
        elif tts_engine == "marvis":
            self.tts = MarvisTTSClient(tts_model)
            self.tts_config = TTSConfig(language="en", sample_rate=22050)
        else:
            raise ValueError(f"Unknown TTS engine: {tts_engine}")

    def _write_temp_wav(self, audio: np.ndarray, sample_rate: int) -> Path:
        """Persist recorded audio to a temporary WAV file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", prefix="voice_chat_", delete=False) as tmp:
            sf.write(tmp.name, audio, sample_rate)
            return Path(tmp.name)

    def _play_audio_array(self, audio: np.ndarray, sample_rate: int) -> None:
        """Play synthesized audio through default output."""
        try:
            sd.play(audio, sample_rate)
            sd.wait()
        except Exception as exc:  # pragma: no cover
            console.print(f"[yellow]Audio playback failed: {exc}[/yellow]")

    def transcribe_audio(self, audio_path: Path) -> str:
        """Transcribe recorded speech to text."""
        console.print("[cyan]🎤 Transcribing input...[/cyan]")
        result = transcribe(
            str(audio_path),
            path_or_hf_repo=self.whisper_model,
            verbose=False,
            task="transcribe",
        )
        text = result["text"].strip()
        console.print(f"[green]🗣️ You said:[/green] {text}\n")
        return text

    def _chat_and_tts(self, user_input: str, stream_text: bool = False) -> tuple[str, np.ndarray, int]:
        # 1. Generate text response
        if stream_text:
            console.print("\n[bold cyan]Assistant:[/bold cyan] ", end="")
            response_text = ""
            for token in self.chat.chat_stream(user_input):
                console.print(token, end="")
                response_text += token
            console.print()
        else:
            response_text = self.chat.chat(user_input)
            console.print(f"\n[bold cyan]Assistant:[/bold cyan] {response_text}")

        # 2. Synthesize to audio
        console.print("[dim]🎤 Synthesizing speech...[/dim]")

        if self.tts_engine == "kokoro":
            audio, _ = self.tts.synthesize(response_text, self.tts_config)
            sample_rate = self.tts_config.sample_rate
        else:  # marvis
            audio = self.tts.synthesize(response_text, self.tts_config)
            sample_rate = self.tts_config.sample_rate

        return response_text, audio, sample_rate

    def _save_audio_file(self, audio: np.ndarray, sample_rate: int) -> Path | None:
        """Save synthesized audio if enabled."""
        if not self.save_audio:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = self.audio_output_dir / f"response_{timestamp}.wav"

        self.tts.save_wav(audio, audio_path, sample_rate)
        return audio_path

    def process_message(self, user_input: str, stream_text: bool = False) -> tuple[str, Path | None]:
        """
        Process user message through full pipeline.

        Args:
            user_input: User's text input
            stream_text: Whether to stream text response

        Returns:
            (response_text, audio_file_path or None)
        """
        response_text, audio, sample_rate = self._chat_and_tts(user_input, stream_text)
        audio_path = self._save_audio_file(audio, sample_rate)
        return response_text, audio_path

    def run_interactive(self, stream_text: bool = False):
        """
        Interactive voice chat loop.

        Args:
            stream_text: Whether to stream text responses
        """
        console.print("\n[bold green]🎙️  Voice Chat Started[/bold green]")
        console.print("[dim]Type your message, get text + audio response[/dim]")
        console.print("[dim]Commands: /exit, /clear, /history[/dim]\n")

        while True:
            try:
                user_input = console.input("[bold green]You:[/bold green] ").strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[cyan]Bye![/cyan]")
                break

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ["/exit", "/quit", "/q"]:
                break
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

            # Process through pipeline
            try:
                response_text, audio_path = self.process_message(user_input, stream_text=stream_text)

                if audio_path:
                    console.print(f"[green]💾 Audio saved: {audio_path.name}[/green]\n")
                else:
                    console.print()

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]\n")
                continue

    def run_live(self, stream_text: bool = False):
        """Push-to-talk interaction: hold space to record, release to send."""
        recorder = PushToTalkRecorder()
        audio_queue: queue.Queue[np.ndarray | None] = queue.Queue()
        exit_event = threading.Event()
        meter_state = {"stop_event": None, "thread": None, "start": 0.0}

        console.print(
            "\n[bold green]🎙️  Live Voice Chat[/bold green]\n"
            "[dim]- Hold SPACE to speak\n"
            "- Release SPACE to send\n"
            "- Press ESC to exit\n"
            "- macOS: Add your terminal to System Settings → Privacy & Security → Accessibility[/dim]\n"
        )

        def start_meter():
            stop_event = threading.Event()
            meter_state["stop_event"] = stop_event
            meter_state["start"] = time.time()

            def meter_loop():
                while not stop_event.is_set():
                    duration = time.time() - meter_state["start"]
                    level = max(0.0, min(1.0, recorder.level * 4))
                    filled = int(level * 12)
                    bar = "█" * filled + "░" * (12 - filled)
                    sys.stdout.write(f"\r[REC {duration:4.1f}s] {bar}")
                    sys.stdout.flush()
                    time.sleep(0.15)
                sys.stdout.write("\r" + " " * 40 + "\r")
                sys.stdout.flush()

            thread = threading.Thread(target=meter_loop, daemon=True)
            meter_state["thread"] = thread
            thread.start()

        def stop_meter():
            stop_event = meter_state["stop_event"]
            thread = meter_state["thread"]
            if stop_event:
                stop_event.set()
            if thread:
                thread.join(timeout=0.3)
            meter_state["stop_event"] = None
            meter_state["thread"] = None

        def on_press(key):
            if key == keyboard.Key.esc:
                exit_event.set()
                audio_queue.put(None)
                stop_meter()
                return False
            if key == keyboard.Key.space and not recorder.is_recording:
                recorder.start()
                console.print("[bold red]⏺ Recording...[/bold red]")
                start_meter()
            return True

        def on_release(key):
            if key == keyboard.Key.space and recorder.is_recording:
                audio = recorder.stop()
                stop_meter()
                duration = audio.shape[0] / recorder.sample_rate if audio.size else 0.0
                peak = float(np.max(np.abs(audio))) if audio.size else 0.0
                if audio.size == 0 or duration < 0.35 or peak < 1e-4:
                    console.print("[yellow]Clip too short or silent. Hold SPACE a bit longer.[/yellow]")
                else:
                    console.print(f"[dim]Processing clip ({duration:.1f}s)...[/dim]")
                    audio_queue.put(audio)
            return not exit_event.is_set()

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()

        try:
            while not exit_event.is_set():
                audio_data = audio_queue.get()
                if audio_data is None:
                    break

                temp_path: Path | None = None
                try:
                    temp_path = self._write_temp_wav(audio_data, recorder.sample_rate)
                    user_text = self.transcribe_audio(temp_path)
                finally:
                    if temp_path:
                        try:
                            temp_path.unlink(missing_ok=True)
                        except Exception:
                            pass

                if not user_text:
                    console.print("[yellow]Detected silence; skipping.[/yellow]\n")
                    continue

                try:
                    response_text, audio, sample_rate = self._chat_and_tts(
                        user_text, stream_text=stream_text
                    )
                    audio_path = self._save_audio_file(audio, sample_rate)
                    self._play_audio_array(audio, sample_rate)
                    console.print(f"[bold cyan]Assistant:[/bold cyan] {response_text}\n")
                    if audio_path:
                        console.print(f"[green]💾 Audio saved: {audio_path.name}[/green]\n")
                    else:
                        console.print()
                except Exception as exc:
                    console.print(f"[red]Error: {exc}[/red]")
                    continue
        finally:
            listener.stop()
            console.print("[cyan]Live voice chat ended.[/cyan]")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Voice Chat CLI - GPT-OSS + TTS full pipeline"
    )

    parser.add_argument(
        "--chat-model",
        type=str,
        default="mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx",
        help="Chat model ID or path"
    )

    parser.add_argument(
        "--tts-engine",
        type=str,
        default="marvis",
        choices=["marvis", "kokoro"],
        help="TTS engine: marvis (simple) or kokoro (54 voices)"
    )

    parser.add_argument(
        "--tts-voice",
        type=str,
        default="af_bella",
        help="Voice ID for Kokoro (e.g., af_bella, am_adam)"
    )

    parser.add_argument(
        "--tts-model",
        type=str,
        default="Marvis-AI/marvis-tts-100m-v0.2",
        help="[Deprecated] TTS model ID for Marvis (use --tts-engine instead)"
    )
    parser.add_argument(
        "--whisper-model",
        type=str,
        default="mlx-community/whisper-large-v3-mlx",
        help="Whisper/STT model ID (used in push-to-talk mode)",
    )

    parser.add_argument(
        "--system-prompt",
        type=str,
        default="You are a helpful, concise AI assistant. Keep responses brief for speech.",
        help="System prompt for chat"
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=256,
        help="Max tokens per response (shorter is better for TTS)"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("var/voice_chat"),
        help="Directory to save audio files"
    )

    parser.add_argument(
        "--no-save-audio",
        action="store_true",
        help="Don't save audio files to disk"
    )

    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream text responses (audio still generated after)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Push-to-talk mode: hold Space to speak, release to send",
    )

    parser.add_argument(
        "--single",
        type=str,
        help="Single query mode (vs interactive)"
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

    if args.live and args.single:
        console.print("[red]--live cannot be combined with --single[/red]")
        sys.exit(1)

    # Initialize pipeline
    console.print()
    tts_display = f"{args.tts_engine.upper()}"
    if args.tts_engine == "kokoro":
        tts_display += f" ({args.tts_voice})"
    stt_display = args.whisper_model if args.live else "N/A (text input)"

    console.print(Panel.fit(
        f"[bold cyan]Voice Chat Pipeline[/bold cyan]\n"
        f"Chat: {args.chat_model}\n"
        f"TTS: {tts_display}\n"
        f"STT: {stt_display}\n"
        f"Max tokens: {args.max_tokens}\n"
        f"Audio output: {args.output_dir}",
        border_style="cyan"
    ))
    console.print()

    pipeline = VoiceChatPipeline(
        chat_model=args.chat_model,
        tts_engine=args.tts_engine,
        tts_voice=args.tts_voice,
        tts_model=args.tts_model,
        whisper_model=args.whisper_model,
        system_prompt=args.system_prompt,
        audio_output_dir=str(args.output_dir),
        max_tokens=args.max_tokens,
        save_audio=not args.no_save_audio
    )

    if args.live:
        pipeline.run_live(stream_text=args.stream)
        return

    # Single query or interactive
    if args.single:
        response_text, audio_path = pipeline.process_message(args.single, stream_text=args.stream)
        console.print(f"\n[bold]Response:[/bold] {response_text}")
        if audio_path:
            console.print(f"[green]Audio: {audio_path}[/green]")
    else:
        pipeline.run_interactive(stream_text=args.stream)


if __name__ == "__main__":
    main()

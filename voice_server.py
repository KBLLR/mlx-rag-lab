#!/usr/bin/env python3
"""
Voice Chat Server - HTTP endpoint for Smart Campus voice integration
Accepts audio → Whisper transcription → GPT-OSS chat → Kokoro TTS → audio response
"""

import argparse
import base64
import io
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np
import soundfile as sf
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add examples/whisper to path for mlx_whisper
sys.path.insert(0, str(Path(__file__).parent / "examples" / "whisper"))

try:
    from mlx_whisper import transcribe
    from rag.chat import ChatSession
    from rag.tts import KokoroConfig, KokoroTTSClient
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    print("Run: cd tier3b-mlx-rag && uv sync")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# Global pipeline components (initialized on startup)
chat_session = None
tts_client = None


class VoiceServer:
    """Voice chat pipeline server."""

    def __init__(
        self,
        chat_model: str = "mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx",
        whisper_model: str = "mlx-community/whisper-large-v3-mlx",
        default_voice: str = "af_bella",
        system_prompt: str = "You are a helpful AI assistant for Smart Campus. Provide concise, informative responses."
    ):
        self.whisper_model = whisper_model
        self.default_voice = default_voice

        print(f"🔧 Loading chat model: {chat_model}...")
        self.chat = ChatSession(
            chat_model,
            system_prompt=system_prompt,
            max_tokens=512
        )

        print(f"🔧 Loading Kokoro TTS...")
        self.tts = KokoroTTSClient(lang_code="a")

        print("✅ Voice server initialized")

    def process_voice_request(
        self,
        audio_file,
        room_id: str,
        agent_id: str,
        voice_id: str
    ) -> dict:
        """
        Process voice chat request.

        Args:
            audio_file: Audio file from request
            room_id: Room identifier
            agent_id: Agent identifier
            voice_id: Voice ID for TTS

        Returns:
            Response dict with transcript, response_text, audio_base64, voice
        """
        # 1. Save uploaded audio to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_file.save(tmp.name)
            audio_path = Path(tmp.name)

        try:
            # 2. Transcribe audio
            print(f"🎤 Transcribing audio from room {room_id}...")
            result = transcribe(
                str(audio_path),
                path_or_hf_repo=self.whisper_model,
                verbose=False,
                task="transcribe",
            )
            transcript = result["text"].strip()
            print(f"📝 Transcript: {transcript}")

            # 3. Generate chat response
            print(f"💬 Generating response...")
            response_text = self.chat.chat(transcript)
            print(f"💬 Response: {response_text}")

            # 4. Synthesize to audio
            print(f"🔊 Synthesizing speech with voice {voice_id}...")
            tts_config = KokoroConfig(voice=voice_id)
            audio_array, _ = self.tts.synthesize(response_text, tts_config)

            # 5. Convert audio to base64
            audio_bytes = io.BytesIO()
            sf.write(audio_bytes, audio_array, tts_config.sample_rate, format='WAV')
            audio_bytes.seek(0)
            audio_base64 = base64.b64encode(audio_bytes.read()).decode('utf-8')

            return {
                "transcript": transcript,
                "response_text": response_text,
                "audio_base64": audio_base64,
                "voice": voice_id,
                "room_id": room_id,
                "agent_id": agent_id
            }

        finally:
            # Cleanup temp file
            audio_path.unlink(missing_ok=True)


# Initialize server on startup
voice_server = None


@app.route('/voice-chat', methods=['POST'])
def voice_chat():
    """Voice chat endpoint accepting multipart/form-data."""
    try:
        # Validate request
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio']
        room_id = request.form.get('room_id', 'unknown')
        agent_id = request.form.get('agent_id', room_id)
        voice_id = request.form.get('voice_id', voice_server.default_voice)

        # Process voice request
        result = voice_server.process_voice_request(
            audio_file,
            room_id,
            agent_id,
            voice_id
        )

        return jsonify(result), 200

    except Exception as e:
        print(f"❌ Error processing voice request: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "voice_processing_error",
            "message": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "voice-chat",
        "components": {
            "chat": "ready" if voice_server and voice_server.chat else "not_initialized",
            "tts": "ready" if voice_server and voice_server.tts else "not_initialized"
        }
    }), 200


@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    return jsonify({
        "service": "Smart Campus Voice Chat Server",
        "endpoints": {
            "POST /voice-chat": "Process voice chat request",
            "GET /health": "Health check"
        }
    }), 200


def main():
    parser = argparse.ArgumentParser(description="Voice Chat Server")
    parser.add_argument('--port', type=int, default=7001, help='Port to listen on')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to')
    parser.add_argument(
        '--chat-model',
        type=str,
        default='mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx',
        help='Chat model ID'
    )
    parser.add_argument(
        '--whisper-model',
        type=str,
        default='mlx-community/whisper-large-v3-mlx',
        help='Whisper model ID'
    )
    parser.add_argument(
        '--voice',
        type=str,
        default='af_bella',
        help='Default Kokoro voice ID'
    )

    args = parser.parse_args()

    # Initialize global voice server
    global voice_server
    voice_server = VoiceServer(
        chat_model=args.chat_model,
        whisper_model=args.whisper_model,
        default_voice=args.voice
    )

    print(f"🚀 Starting voice server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()

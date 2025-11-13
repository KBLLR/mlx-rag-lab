# STS Avatar Pipeline: Speech-to-Speech with Viseme Output

## Architecture Overview

```
Audio Input (user recording)
    ↓
Whisper MLX (STT)
    - Transcribes speech to text
    - Multi-language support
    ↓
User Text
    ↓
ChatSession (GPT-OSS 20B)
    - Generates conversational response
    - Maintains conversation history
    ↓
Response Text
    ↓
TTS Engine (Marvis OR Kokoro)
    ├─ Marvis TTS: Audio only
    └─ Kokoro TTS: Audio + Phonemes + Visemes
    ↓
Audio Output + Optional Viseme JSON
    ↓
Ready Player Me Avatar (Three.js frontend)
    - Lip-sync via Oculus visemes
    - 14 viseme blend shapes
```

## Components

### 1. Whisper STT (`examples/whisper/mlx_whisper`)

**Purpose**: Convert speech to text using MLX Whisper

**Key Features**:
- ✅ Metal-accelerated transcription
- ✅ Multi-language support
- ✅ Large-v3 model by default
- ✅ Fast on Apple Silicon

**Models**:
- `mlx-community/whisper-large-v3` (default, ~3GB)
- `mlx-community/whisper-medium`
- `mlx-community/whisper-small`

### 2. Chat Session (`src/rag/chat/gpt_oss_wrapper.py`)

**Purpose**: Conversational AI with proper chat template

**Key Features**:
- ✅ GPT-OSS 20B support
- ✅ Conversation history
- ✅ System prompts
- ✅ Streaming support

**See**: `docs/CHAT_WRAPPER_USAGE.md`

### 3. TTS Engines

#### Marvis TTS (`src/rag/tts/marvis_tts.py`)

**Purpose**: Simple, fast TTS without viseme data

**Features**:
- ✅ 100M parameters (~400MB)
- ✅ MPS acceleration
- ✅ 22kHz audio
- ✅ Fast inference

**Use Case**: Simple voice responses without avatar lip-sync

#### Kokoro TTS (`src/rag/tts/kokoro_tts.py`)

**Purpose**: TTS with phoneme output for avatar lip-sync

**Features**:
- ✅ 82M parameters (~350MB)
- ✅ **54 voices** across 8 languages
- ✅ **Phoneme-level output**
- ✅ 24kHz audio
- ✅ Apache 2.0 license

**Use Case**: Avatar applications requiring lip-sync

**Available Voices**:

**American English (20 voices)**:
- Female: `af_bella`, `af_sarah`, `af_nova`, `af_sky`, etc.
- Male: `am_adam`, `am_fenrir`, `am_eric`, `am_michael`, etc.

**Other Languages**:
- British English (8 voices)
- Spanish (3 voices: `ef_dora`, `em_alex`, `em_santa`)
- Japanese (5 voices)
- Mandarin Chinese (8 voices)
- French, Hindi, Italian, Portuguese

### 4. Viseme Mapper (`src/rag/tts/viseme_mapper.py`)

**Purpose**: Convert IPA phonemes to Oculus viseme IDs

**Key Features**:
- ✅ IPA → Oculus viseme mapping
- ✅ Timing estimation
- ✅ HeadTTS-compatible JSON output
- ✅ Ready Player Me support (14 visemes)

**Oculus Viseme IDs**:
- `sil`: Silence
- `PP`: Bilabials (p, b, m)
- `FF`: Labiodentals (f, v)
- `TH`: Dental fricatives (th)
- `DD`: Alveolar stops (t, d)
- `kk`: Velar stops (k, g)
- `CH`: Postalveolar affricates (ch, j)
- `SS`: Sibilants (s, z)
- `nn`: Nasal (n)
- `RR`: Rhotic (r)
- `aa`: Open vowels (a)
- `E`: Mid front vowels (e)
- `I`: Close front vowels (i)
- `O`: Back rounded vowels (o)
- `U`: Close back vowels (u)

**Output Format** (HeadTTS-compatible):
```json
{
  "words": ["Hello ", "world"],
  "wtimes": [0, 500],
  "wdurations": [400, 600],
  "visemes": ["sil", "kk", "E", "DD", "O"],
  "vtimes": [0, 100, 200, 300, 400],
  "vdurations": [100, 100, 100, 100, 200]
}
```

### 5. STS Avatar CLI (`apps/sts_avatar_cli.py`)

**Purpose**: Full speech-to-speech pipeline orchestration

**Features**:
- ✅ Interactive audio file mode
- ✅ Single query mode
- ✅ TTS engine selection (Marvis/Kokoro)
- ✅ Voice selection
- ✅ Viseme JSON export
- ✅ Conversation history

## Usage

### Installation

```bash
# Install dependencies
uv sync

# Verify Kokoro
python3 -c "import kokoro; print(kokoro.__version__)"
```

### Quick Start

#### Interactive Mode (Audio Files)

```bash
# Kokoro TTS with visemes
uv run sts-avatar-cli

# Then provide audio file paths:
Audio file: var/recordings/question.wav
```

#### Single Query

```bash
# Process one audio file
uv run sts-avatar-cli --single var/recordings/hello.wav
```

#### List Available Voices

```bash
uv run sts-avatar-cli --list-voices
```

### Advanced Options

#### Use Marvis TTS (No Visemes)

```bash
uv run sts-avatar-cli --tts-engine marvis
```

#### Select Kokoro Voice

```bash
# American male (Adam)
uv run sts-avatar-cli --tts-voice am_adam

# British female (Emma)
uv run sts-avatar-cli --tts-voice bf_emma

# Spanish male (Alex)
uv run sts-avatar-cli --tts-voice em_alex
```

#### Custom Models

```bash
uv run sts-avatar-cli \
  --chat-model mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx \
  --whisper-model mlx-community/whisper-large-v3 \
  --tts-engine kokoro \
  --tts-voice af_bella \
  --max-tokens 256 \
  --stream
```

#### Disable Viseme Output

```bash
uv run sts-avatar-cli --no-save-visemes
```

### Interactive Commands

While in interactive mode:
- `/exit`, `/quit`, `/q` - Exit
- `/clear` - Clear conversation history
- `/history` - Show conversation history

## Output Files

All files saved to `var/sts_avatar/` (configurable):

1. **Audio Files**: `response_YYYYMMDD_HHMMSS.wav`
   - Marvis: 22kHz WAV
   - Kokoro: 24kHz WAV

2. **Viseme JSON**: `visemes_YYYYMMDD_HHMMSS.json` (Kokoro only)
   ```json
   {
     "words": ["Hello"],
     "wtimes": [0],
     "wdurations": [600],
     "visemes": ["sil", "kk", "E", "DD", "O"],
     "vtimes": [0, 100, 200, 300, 400],
     "vdurations": [100, 100, 100, 100, 200]
   }
   ```

## Performance Notes

### Latency Breakdown (M3 Max)

**Typical STS Flow**:
1. **Whisper STT**: 1-3s for 5-10s audio
2. **Chat Generation**: 2-5s for 128 tokens
3. **TTS Synthesis**:
   - Marvis: 1-2s
   - Kokoro: 1-2s
4. **Viseme Mapping**: <100ms
5. **Total**: 4-10s per turn

### Optimization Tips

- Use `--max-tokens 256` for faster responses
- Shorter audio clips = faster transcription
- Consider Whisper medium/small for speed
- Kokoro is faster than Marvis despite phoneme output

### Memory Usage

- **GPT-OSS 20B MXFP4**: ~12GB
- **Whisper Large-v3**: ~3GB
- **Kokoro TTS**: ~400MB
- **Total**: ~15.5GB (fits M3 Max)

## Integration with Ready Player Me

### Frontend Setup (Three.js)

```javascript
import { TalkingHead } from './modules/talkinghead.mjs';

// Load avatar
const head = new TalkingHead();
await head.showAvatar({
  url: './avatars/avatar.glb',
  lipsyncLang: 'en'
});

// Fetch viseme data from backend
const response = await fetch('/api/sts-avatar', {
  method: 'POST',
  body: audioBlob
});

const data = await response.json();

// Play audio with lip-sync
head.speakAudio({
  audio: data.audioUrl,
  visemes: data.visemes,
  vtimes: data.vtimes,
  vdurations: data.vdurations
});
```

### Backend API Endpoint

```python
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from apps.sts_avatar_cli import STSAvatarPipeline

app = FastAPI()
pipeline = STSAvatarPipeline(
    chat_model="mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx",
    tts_engine="kokoro",
    tts_voice="af_bella"
)

@app.post("/api/sts-avatar")
async def sts_avatar(audio: UploadFile):
    # Save uploaded audio
    audio_path = Path(f"tmp/{audio.filename}")
    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    # Process through pipeline
    response_text, audio_out, viseme_out = pipeline.process_audio_file(audio_path)

    # Load viseme data
    import json
    with open(viseme_out) as f:
        viseme_data = json.load(f)

    return {
        "text": response_text,
        "audioUrl": f"/static/{audio_out.name}",
        **viseme_data
    }
```

## Python API Usage

### Basic STS Pipeline

```python
from pathlib import Path
from apps.sts_avatar_cli import STSAvatarPipeline

# Initialize
pipeline = STSAvatarPipeline(
    chat_model="mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx",
    tts_engine="kokoro",
    tts_voice="af_bella",
    audio_output_dir="var/sts_avatar"
)

# Process audio
audio_input = Path("var/recordings/question.wav")
response_text, audio_out, viseme_out = pipeline.process_audio_file(audio_input)

print(f"Response: {response_text}")
print(f"Audio: {audio_out}")
print(f"Visemes: {viseme_out}")
```

### Kokoro TTS Only

```python
from rag.tts import KokoroTTSClient, KokoroConfig, VisemeMapper

# Initialize
tts = KokoroTTSClient(lang_code="a")
config = KokoroConfig(voice="af_bella")

# Synthesize
text = "Hello, I am your AI assistant."
audio, phoneme_data = tts.synthesize(text, config)

# Generate visemes
viseme_dict = VisemeMapper.from_kokoro_phonemes(phoneme_data)

# Save
tts.save_wav(audio, "output.wav", config.sample_rate)
import json
with open("visemes.json", "w") as f:
    json.dump(viseme_dict, f)
```

### Marvis TTS (No Visemes)

```python
from rag.tts import MarvisTTSClient, TTSConfig

tts = MarvisTTSClient()
config = TTSConfig(language="en", sample_rate=22050)

audio = tts.synthesize("Hello world!", config)
tts.save_wav(audio, "output.wav", config.sample_rate)
```

## Comparison: TTS Engines

| Feature | Marvis TTS | Kokoro TTS |
|---------|------------|------------|
| **Size** | 100M params | 82M params |
| **Voices** | 1 (default) | 54 voices (8 languages) |
| **Sample Rate** | 22kHz | 24kHz |
| **Phoneme Output** | ❌ No | ✅ Yes |
| **Viseme Support** | ❌ No | ✅ Yes |
| **Speed** | Fast (~1-2s) | Fast (~1-2s) |
| **License** | Check model | Apache 2.0 |
| **Use Case** | Simple TTS | Avatar lip-sync |

## Troubleshooting

### Kokoro Installation Issues

```bash
# Install with pip
pip install kokoro>=0.9.2 soundfile

# Verify
python3 -c "from kokoro import KPipeline; print('OK')"
```

### Viseme Timing Inaccurate

The current viseme mapper uses **estimated timing** based on audio duration. For production accuracy, consider:

1. **Use HeadTTS microservice** (Node.js):
   - Provides phoneme-level timestamps
   - More accurate viseme timing
   - See: `https://github.com/met4citizen/HeadTTS`

2. **Forced alignment** (future):
   - Use Montreal Forced Aligner
   - Align phonemes to audio precisely

### Audio Quality Issues

**Kokoro**:
```python
config = KokoroConfig(
    voice="af_bella",
    sample_rate=24000,
    speed=1.0  # Adjust playback speed
)
```

**Marvis**:
```python
config = TTSConfig(
    sample_rate=22050,  # Try 16000 or 44100
    speed=1.0
)
```

### Metal/MPS Not Available

```bash
# Check PyTorch MPS
python3 -c "import torch; print(torch.backends.mps.is_available())"

# Reinstall PyTorch with MPS
pip install --upgrade torch torchaudio
```

## Future Enhancements

### Real-Time Streaming

Instead of processing full audio files:

```python
# Stream audio from microphone → Whisper → Chat → TTS → Avatar
# Requires:
# - Streaming Whisper (chunk-based)
# - Streaming TTS
# - WebSocket audio transport
```

### Multi-Language Support

Kokoro supports 8 languages:

```python
# Spanish
pipeline = STSAvatarPipeline(
    tts_engine="kokoro",
    tts_voice="em_alex",  # Spanish male
    whisper_model="mlx-community/whisper-large-v3"
)
```

### HeadTTS Microservice Integration

For production-grade viseme timing:

```bash
# Start HeadTTS server
cd services/headtts
npm install
npm start

# Configure pipeline to use HeadTTS API
pipeline = STSAvatarPipeline(
    viseme_service="http://localhost:8882"
)
```

## File Layout

```
src/rag/
├── chat/
│   └── gpt_oss_wrapper.py       # ChatSession
├── tts/
│   ├── __init__.py
│   ├── marvis_tts.py            # Marvis TTS
│   ├── kokoro_tts.py            # Kokoro TTS + phonemes
│   └── viseme_mapper.py         # Phoneme → Viseme

apps/
├── voice_chat_cli.py            # Text → TTS
├── whisper_cli.py               # Audio → Text
└── sts_avatar_cli.py            # Audio → Audio + Visemes

docs/
├── CHAT_WRAPPER_USAGE.md
├── VOICE_CHAT_PIPELINE.md
└── STS_AVATAR_PIPELINE.md       # This file
```

## Dependencies

**Core** (already in project):
- `mlx` - MLX framework
- `mlx_lm` - Language models
- `transformers` - Model loading
- `rich` - Console output

**TTS-specific**:
- `torch` - PyTorch (MPS support)
- `torchaudio` - Audio processing
- `kokoro>=0.9.2` - Kokoro TTS
- `soundfile` - WAV I/O
- `scipy` - Audio manipulation

**Whisper** (already integrated):
- MLX Whisper in `examples/whisper/`

## Quick Reference

```bash
# Interactive mode (Kokoro + visemes)
uv run sts-avatar-cli

# Single query
uv run sts-avatar-cli --single var/recordings/hello.wav

# Marvis TTS (no visemes)
uv run sts-avatar-cli --tts-engine marvis

# List voices
uv run sts-avatar-cli --list-voices

# Custom voice
uv run sts-avatar-cli --tts-voice am_fenrir

# Spanish voice
uv run sts-avatar-cli --tts-voice em_alex

# No viseme JSON
uv run sts-avatar-cli --no-save-visemes
```

## See Also

- **Chat Wrapper**: `docs/CHAT_WRAPPER_USAGE.md`
- **Voice Chat Pipeline**: `docs/VOICE_CHAT_PIPELINE.md`
- **Ready Player Me**: https://readyplayer.me/
- **TalkingHead**: https://github.com/met4citizen/TalkingHead
- **HeadTTS**: https://github.com/met4citizen/HeadTTS
- **Kokoro TTS**: https://huggingface.co/hexgrad/Kokoro-82M

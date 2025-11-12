# Whisper Pipeline

**Status**: In Development
**Model**: `mlx-community/whisper-large-v3` (Automatically downloaded)
**CLI**: `apps/whisper_cli.py`
**Created**: 2025-11-12

---

## Goal

Build a production-ready MLX pipeline for speech-to-text transcription using OpenAI's Whisper model. Transform audio files into accurate text transcripts for content processing workflows.

---

## Model Details

### Whisper Large V3
- **Source**: `mlx-community/whisper-large-v3` (OpenAI/MLX Community)
- **Size**: ~1.5GB (downloaded on first use)
- **Location**: Auto-cached in `~/.cache/huggingface/hub/`
- **Capabilities**:
  - Multi-language speech recognition (99+ languages)
  - Speech translation to English
  - Automatic language detection
  - Word-level timestamps
  - Multiple output formats (txt, json, srt, vtt, tsv)

### Model Variants
- **whisper-tiny**: ~39MB, fastest but least accurate
- **whisper-base**: ~74MB, good speed/accuracy balance
- **whisper-small**: ~244MB, better accuracy
- **whisper-medium**: ~769MB, high accuracy
- **whisper-large-v3**: ~1.5GB, best accuracy (recommended)

---

## Pipeline Architecture

```
Audio File → Log-Mel Spectrogram → Whisper Encoder → Decoder → Transcript
```

### Components

1. **Audio Processor** (`mlx_whisper.audio`)
   - Loads audio at 16kHz sample rate
   - Converts to log-mel spectrogram (80 bands)
   - Pads/trims to 30-second chunks

2. **Whisper Model** (`mlx_whisper.transcribe`)
   - Encoder processes mel spectrogram
   - Decoder generates text tokens
   - Auto-regressive with beam search
   - Cached model loading for repeated calls

3. **Output Formatters** (`mlx_whisper.writers`)
   - Plain text (.txt)
   - JSON with segments and timestamps
   - SubRip subtitles (.srt)
   - WebVTT subtitles (.vtt)
   - TSV with timestamps

---

## CLI Usage

### Basic Transcription

```bash
# Transcribe audio file
uv run whisper-cli audio.mp3

# Specify model size
uv run whisper-cli audio.mp3 --model mlx-community/whisper-large-v3

# Save to specific output directory
uv run whisper-cli audio.mp3 --output-dir transcripts/

# Choose output format
uv run whisper-cli audio.mp3 --output-format json
uv run whisper-cli audio.mp3 --output-format srt  # subtitles
```

### Advanced Options

```bash
# Transcribe with language hint (faster)
uv run whisper-cli audio.mp3 --language English

# Translate to English (from any language)
uv run whisper-cli audio.mp3 --task translate

# Generate word-level timestamps
uv run whisper-cli audio.mp3 --word-timestamps

# Batch processing
uv run whisper-cli audio1.mp3 audio2.mp3 audio3.mp3

# Quiet mode (no progress output)
uv run whisper-cli audio.mp3 --verbose False
```

---

## Python API

### Direct Usage

```python
import sys
sys.path.insert(0, "mlx-models/whisper")
from mlx_whisper import transcribe

# Transcribe audio file
result = transcribe(
    "audio.mp3",
    path_or_hf_repo="mlx-community/whisper-large-v3",
    verbose=True
)

print(result["text"])  # Full transcript
print(result["language"])  # Detected language
print(result["segments"])  # Segment-level details with timestamps
```

### Integrated Workflow

```python
# Example: Transcribe generated music from MusicGen
from apps.musicgen_cli import generate_audio
from libs.whisper_core import transcribe

# Generate audio
audio = generate_audio("happy rock", max_steps=300)
audio.save("music.wav")

# Transcribe lyrics/sounds (if any)
result = transcribe("music.wav")
print(f"Detected sounds: {result['text']}")
```

---

## Data Transformation Use Cases

### 1. **RAG Integration**
Index transcripts for semantic search:
```bash
# Transcribe video/audio content
uv run whisper-cli lecture.mp3 --output-format json

# Ingest transcript into VectorDB
uv run rag-cli ingest transcripts/lecture.json
```

### 2. **Content Processing Pipeline**
Process large audio datasets:
```python
import glob
from mlx_whisper import transcribe

for audio_file in glob.glob("podcasts/*.mp3"):
    result = transcribe(audio_file, path_or_hf_repo="mlx-community/whisper-large-v3")
    with open(f"{audio_file}.txt", "w") as f:
        f.write(result["text"])
```

### 3. **Subtitle Generation**
Create subtitles for videos:
```bash
# Generate SRT subtitles
uv run whisper-cli video_audio.mp3 --output-format srt --word-timestamps

# Output: video_audio.srt (ready for video editing software)
```

### 4. **Multi-language Translation**
Translate speech to English:
```bash
# Transcribe German audio and translate to English
uv run whisper-cli german_audio.mp3 --task translate

# Auto-detects German, outputs English translation
```

---

## Performance

### Transcription Speed (Apple Silicon)
- **whisper-tiny**: ~10x real-time (10min audio → 1min processing)
- **whisper-base**: ~5x real-time
- **whisper-small**: ~3x real-time
- **whisper-medium**: ~2x real-time
- **whisper-large-v3**: ~1-1.5x real-time

### Memory Usage (M3 Max)
- **Model loading**: ~2GB unified memory (large-v3)
- **Transcription**: +500MB during inference
- **Peak**: ~2.5GB total

---

## Integration with MusicGen

### Workflow Example

```
Text Prompt → MusicGen → Audio File
                           ↓
                  Whisper Transcription
                           ↓
                    Metadata + Lyrics
                           ↓
                     VectorDB Index
                           ↓
                Searchable Music Library
```

**Use case**: Generate music, transcribe any vocal/lyrical content, index for semantic search.

---

## Known Limitations

1. **Language support**: Works best with English; accuracy varies for other languages
2. **Background noise**: Performance degrades with heavy background noise
3. **Speaker diarization**: Does not distinguish between multiple speakers
4. **Real-time streaming**: Batch processing only (no streaming mode yet)

---

## Next Steps

### Phase 1: Core CLI ✅
- [x] Create `apps/whisper_cli.py`
- [x] Add to `pyproject.toml` scripts
- [x] Add Whisper dependencies (tiktoken, numba, scipy, more-itertools)
- [x] Generate missing mel_filters.npz asset
- [x] Add signal handling (Ctrl+C cleanup)
- [x] Test basic transcription (`uv run whisper-cli audio.wav`)

**Test Results** (2025-11-12):
- Successfully transcribed audio files with whisper-tiny model
- Auto-downloaded model from HuggingFace (~39MB)
- Generated mel_filters.npz (missing from distribution)
- Output formats working: txt, json, srt, vtt, tsv
- Language detection working correctly

### Phase 2: Polish
- [ ] Add progress bar for long files
- [ ] Implement batch mode from file list
- [ ] Add audio format validation
- [ ] Support for multiple output formats simultaneously

### Phase 3: Integration
- [ ] Create Whisper → VectorDB pipeline
- [ ] Add to benchmarking suite
- [ ] Integrate with MusicGen pipeline (audio generation → transcription)
- [ ] Document best practices for audio quality

### Phase 4: Advanced Features
- [ ] Fine-tuning support for domain-specific vocabulary
- [ ] Speaker diarization integration
- [ ] Real-time streaming transcription
- [ ] Multi-model ensemble (speed vs accuracy trade-off)

---

## References

- **Paper**: [Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356) (OpenAI, 2022)
- **Original Code**: https://github.com/openai/whisper
- **MLX Implementation**: https://github.com/ml-explore/mlx-examples/tree/main/whisper
- **Model Card**: https://huggingface.co/mlx-community/whisper-large-v3

---

## Project Structure

```
mlx-RAG/
├── apps/
│   └── whisper_cli.py          # Main CLI (production)
├── libs/
│   └── whisper_core/           # Core transcription logic
│       ├── __init__.py
│       ├── transcribe.py
│       ├── audio.py
│       └── ...
├── mlx-models/
│   └── whisper/                # Reference implementation (1.9MB)
│       ├── mlx_whisper/
│       └── ...
└── docs/projects/whisper-pipeline/
    ├── README.md               # This file
    ├── EXAMPLES.md             # Usage examples
    └── sessions/
        └── 2025-11-12_setup.md
```

---

## Credits

- **OpenAI**: Original Whisper model
- **Apple MLX**: MLX implementation and optimization
- **David Caballero**: Pipeline development and integration

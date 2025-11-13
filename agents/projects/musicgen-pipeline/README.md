# MusicGen Pipeline

**Status**: In Development
**Model**: `facebook/musicgen-small` (5.4GB)
**CLI**: `apps/musicgen_cli.py`
**Created**: 2025-11-12

---

## Goal

Build a production-ready MLX pipeline for text-to-audio generation using Meta's MusicGen model. Transform text descriptions into high-quality audio files for creative workflows.

---

## Model Details

### MusicGen Small
- **Source**: `facebook/musicgen-small` (Meta)
- **Size**: 5.4GB
- **Location**: `mlx-models/musicgen-small/`
- **Capabilities**:
  - Text-to-audio generation
  - 32kHz sampling rate
  - Configurable generation length (steps)
  - Multiple audio styles supported

### Dependencies
- **Encodec** (`mlx-models/encodec-32khz-float32/`, 221MB) — Audio codec
- **T5** (`mlx-models/t5/`, 36KB) — Text encoder

---

## Pipeline Architecture

```
Text Prompt → T5 Encoder → MusicGen Model → Encodec Decoder → WAV File
```

### Components

1. **Text Conditioner** (`TextConditioner`)
   - Uses T5 model to encode text prompts
   - Projects embeddings to MusicGen's latent space

2. **MusicGen Model** (`MusicGen.from_pretrained()`)
   - Transformer-based audio generation
   - Auto-regressive generation with KV caching
   - Controlled by max_steps parameter

3. **Audio Codec** (`EncodecModel`)
   - Decodes latent codes to waveform
   - 32kHz sampling rate
   - Efficient compression/decompression

---

## CLI Usage

### Basic Generation

```bash
# Generate 10-second clip (default ~300 steps)
uv run musicgen-cli --prompt "happy rock" --output music/happy_rock.wav

# Longer generation (30 seconds)
uv run musicgen-cli --prompt "calming piano melody" --max-steps 900 --output music/piano.wav

# Specify model (if multiple available)
uv run musicgen-cli --model facebook/musicgen-small --prompt "upbeat electronic" --output edm.wav
```

### Advanced Options

```bash
# Batch generation with different prompts
uv run musicgen-cli --prompt "jazzy saxophone" --output music/jazz_01.wav
uv run musicgen-cli --prompt "ambient synth pads" --output music/ambient_01.wav

# Custom output directory
uv run musicgen-cli --prompt "lofi hip hop" --output-dir ./var/music_output --prefix lofi
# Saves as: ./var/music_output/lofi_001.wav
```

---

## Python API

### Direct Usage

```python
import sys
sys.path.insert(0, "musicgen")
from musicgen import MusicGen
from utils import save_audio

# Load model
model = MusicGen.from_pretrained("facebook/musicgen-small")

# Generate audio
audio = model.generate("happy rock", max_steps=500)

# Save to file
save_audio("output.wav", audio, model.sampling_rate)
```

### Integrated Workflow

```python
# Example: Generate background music for video project
from apps.musicgen_cli import generate_audio

prompts = [
    "uplifting orchestral intro",
    "tense action sequence",
    "emotional piano outro"
]

for i, prompt in enumerate(prompts):
    audio = generate_audio(prompt, max_steps=600)
    audio.save(f"soundtrack_{i:02d}.wav")
```

---

## Data Transformation Use Cases

### 1. **Audio Dataset Generation**
Generate synthetic audio for training other models:
```bash
# Create labeled audio dataset
for style in rock jazz classical; do
    uv run musicgen-cli --prompt "$style music" --output datasets/audio/$style.wav
done
```

### 2. **Procedural Content**
Generate audio for games, apps, installations:
```python
# Dynamic music based on user input
user_mood = "calm"  # from user interaction
prompt = f"{user_mood} ambient soundscape"
generate_and_play(prompt)
```

### 3. **Audio Augmentation**
Create variations for data augmentation:
```bash
# Generate 10 variations of "upbeat pop"
for i in {1..10}; do
    uv run musicgen-cli --prompt "upbeat pop song" --output aug/pop_var_$i.wav
done
```

---

## Performance

### Generation Speed (Apple Silicon)
- **~30ms/step** on M3 Max
- **300 steps** (10s audio) → ~9 seconds generation time
- **900 steps** (30s audio) → ~27 seconds generation time

### Memory Usage
- **Model loading**: ~6GB unified memory
- **Generation**: +1-2GB during inference
- **Peak**: ~8GB total

---

## Integration with RAG

### Potential Workflow

```
Text description → MusicGen → Audio file
                              ↓
                    Transcription metadata
                              ↓
                         VectorDB
                              ↓
                    Searchable audio library
```

**Future enhancement**: Combine with Whisper to make generated audio searchable.

---

## Known Limitations

1. **Generation length**: Limited by max_steps (longer = slower)
2. **Style control**: Text prompts are somewhat unpredictable
3. **Quality**: "Small" model may lack detail vs "medium/large"
4. **No streaming**: Must wait for full generation to complete

---

## Next Steps

### Phase 1: Core CLI ✅
- [x] Create `apps/musicgen_cli.py`
- [x] Add to `pyproject.toml` scripts
- [x] Test basic generation (`uv run musicgen-cli --prompt "happy rock" --max-steps 300`)
- [x] Add signal handling (Ctrl+C cleanup)

**Test Results** (2025-11-12):
- Generated 10s audio (300 steps) in ~7 seconds
- Performance: ~44 it/s (~23ms/step on M3 Max)
- Output: 371KB WAV, 16-bit mono PCM, 32kHz
- Model loading and cleanup work correctly

### Phase 2: Polish
- [ ] Add progress bar for long generations
- [ ] Implement batch mode (multiple prompts from file)
- [ ] Add audio preview/playback option
- [ ] Support for different sampling rates

### Phase 3: Integration
- [ ] Create MusicGen → VectorDB pipeline (with metadata)
- [ ] Add to benchmarking suite
- [ ] Document best practices for prompt engineering

### Phase 4: Advanced Features
- [ ] Fine-tuning support (LoRA adapters)
- [ ] Style transfer (existing audio + prompt)
- [ ] Multi-model ensemble (small + medium)

---

## References

- **Paper**: [Simple and Controllable Music Generation](https://arxiv.org/abs/2306.05284) (Meta AI, 2023)
- **Original Code**: https://github.com/facebookresearch/audiocraft
- **MLX Implementation**: Based on Apple MLX examples
- **Model Card**: https://huggingface.co/facebook/musicgen-small

---

## Project Structure

```
mlx-RAG/
├── apps/
│   └── musicgen_cli.py          # Main CLI (production)
├── musicgen/
│   ├── musicgen.py              # Core model class
│   ├── generate.py              # Legacy script (reference)
│   ├── utils.py                 # Audio save helpers
│   ├── encodec.py → ../encodec/ # Symlink to codec
│   └── t5.py → ../t5/           # Symlink to text encoder
├── mlx-models/
│   ├── musicgen-small/          # Model weights (5.4GB)
│   ├── encodec-32khz-float32/   # Codec (221MB)
│   └── t5/                      # Text encoder (36KB)
└── docs/projects/musicgen-pipeline/
    ├── README.md                # This file
    ├── EXAMPLES.md              # Prompt library
    └── sessions/
        └── 2025-11-12_setup.md
```

---

## Credits

- **Meta AI Research**: Original MusicGen model
- **Apple MLX**: Framework and reference implementation
- **David Caballero**: Pipeline development and integration

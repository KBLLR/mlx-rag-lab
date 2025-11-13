# Llasa Pipeline Project

**Status**: Planning
**Owner**: David Caballero
**Created**: 2025-11-13
**Model**: llasa-3b-Q4-mlx (HKUST-Audio/Llasa-3B, 4-bit quantized)

## Goal

Establish a production-ready pipeline using the Llasa-3B language model for audio-aware text generation, transcription post-processing, and potentially audio-enhanced RAG workflows.

## Context

Llasa-3B is a 3-billion parameter language model optimized for audio-related tasks. The model is available locally at `mlx-models/llasa-3b-Q4-mlx/` in 4-bit quantized MLX format, providing:

- **Efficient inference**: 4-bit quantization for reduced memory footprint (~2GB)
- **Audio-aware generation**: Specialized for audio transcription, captioning, analysis
- **Chat interface**: Supports chat template for conversational interactions
- **MLX optimized**: Native Apple Silicon acceleration

### Potential Use Cases
- Post-process Whisper transcriptions (formatting, correction, summarization)
- Generate audio descriptions and captions
- Audio content analysis and metadata generation
- Conversational interface for audio workflows
- Integration with Whisper pipeline for enhanced transcription

## Key Features to Implement

### Phase 1: Core Llasa Pipeline
- [ ] Create `apps/llasa_cli.py` following existing CLI patterns
- [ ] Implement basic text generation with chat template
- [ ] Support for audio transcription post-processing
- [ ] Interactive chat mode
- [ ] Model loading with mlx-lm

### Phase 2: Integration with Audio Pipelines
- [ ] Connect with Whisper pipeline for transcription enhancement
- [ ] Automatic transcription formatting and cleanup
- [ ] Speaker identification and diarization support
- [ ] Audio content summarization

### Phase 3: Advanced Features
- [ ] Fine-tuning interface for domain-specific audio tasks
- [ ] Batch processing for multiple transcripts
- [ ] Audio metadata generation
- [ ] Integration with RAG for audio document retrieval

## Reference Architecture

### Model Details
- **Model**: HKUST-Audio/Llasa-3B (via srinivasbilla/llasa-3b)
- **Size**: 3B parameters (4-bit quantized → ~1.9GB)
- **Framework**: MLX (Apple Silicon optimized)
- **Quantization**: Q4 (4-bit) for efficiency
- **Context**: Supports chat template with role-based messages

### Integration Points
- `apps/llasa_cli.py` - New CLI entrypoint
- `src/rag/models/llasa_engine.py` - Llasa model wrapper
- `apps/whisper_cli.py` - Integration for transcription enhancement
- `[project.scripts]` - Add `llasa-cli` command

## Success Criteria

- [ ] `llasa-cli` command works with `--help` and basic generation
- [ ] Can generate text: `uv run llasa-cli --prompt "Explain MLX framework"`
- [ ] Chat mode: `uv run llasa-cli --chat` for interactive conversations
- [ ] Whisper integration: `uv run llasa-cli --enhance-transcript transcript.txt`
- [ ] Model loads efficiently with 4-bit quantization
- [ ] Documentation in `docs/COMMANDS_MANIFEST.md`

## Common Use Cases

### 1. Basic Text Generation
```bash
uv run llasa-cli --prompt "Explain machine learning on Apple Silicon"
```

### 2. Chat Mode (Interactive)
```bash
uv run llasa-cli --chat
# User: What is MLX?
# Llasa: MLX is Apple's machine learning framework...
```

### 3. Transcription Enhancement
```bash
# Clean up and format Whisper output
uv run llasa-cli --enhance-transcript var/transcripts/audio.json \
  --output var/transcripts/audio_enhanced.txt
```

### 4. Audio Description Generation
```bash
# Generate metadata from transcription
uv run llasa-cli --task describe-audio \
  --transcript var/transcripts/podcast.txt \
  --output var/metadata/podcast_description.txt
```

### 5. Batch Transcription Processing
```bash
# Process multiple transcripts
uv run llasa-cli --batch-enhance var/transcripts/*.json \
  --output-dir var/transcripts/enhanced/
```

## Architecture Decisions

### 1. Integration Strategy
**Decision**: Separate CLI with optional integration into Whisper/audio pipelines.

**Rationale**:
- Llasa is specialized for audio tasks but still a general LLM
- Can be used standalone for text generation
- Natural integration point with existing Whisper pipeline
- Can enhance audio RAG workflows

**Structure**:
```
apps/
  llasa_cli.py         # Standalone Llasa CLI
  whisper_cli.py       # (enhanced with llasa integration)

src/rag/
  models/
    llasa_engine.py    # Llasa model wrapper
  audio/               # Audio-specific utilities (new)
    transcription.py   # Whisper + Llasa integration
    enhancement.py     # Transcription post-processing
```

### 2. Model Loading
**Decision**: Use mlx-lm directly with 4-bit quantization.

**Benefits**:
- Efficient memory usage (~2GB vs ~6GB for full precision)
- Fast inference on Apple Silicon
- Standard mlx-lm patterns (load, generate)

**Implementation**:
```python
from mlx_lm import load, generate

model, tokenizer = load("srinivasbilla/llasa-3b-Q4-mlx")
response = generate(model, tokenizer, prompt=prompt, verbose=True)
```

### 3. Chat Template Support
**Decision**: Use built-in chat template when available.

**Format**:
```python
if hasattr(tokenizer, "apply_chat_template"):
    messages = [{"role": "user", "content": prompt}]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
```

### 4. Whisper Integration
**Decision**: Optional post-processing mode in whisper-cli, plus standalone llasa-cli.

**Whisper CLI Enhancement**:
```bash
# Original Whisper output
uv run whisper-cli audio.mp3 --output-format json

# With Llasa post-processing
uv run whisper-cli audio.mp3 --output-format json --enhance

# Or standalone enhancement
uv run llasa-cli --enhance-transcript var/transcripts/audio.json
```

## Dependencies

### Existing
- MLX framework (~0.29.3)
- mlx-lm (already available)
- transformers (for tokenizer)

### New (to add)
- llasa-3b-Q4-mlx weights (already downloaded locally)
- No additional Python packages needed

## Resources

- **Local Model**: `/Users/davidcaballero/mlx-RAG/mlx-models/llasa-3b-Q4-mlx/`
- **Base Model**: https://huggingface.co/HKUST-Audio/Llasa-3B
- **MLX Conversion**: https://huggingface.co/srinivasbilla/llasa-3b-Q4-mlx
- **MLX-LM Docs**: https://github.com/ml-explore/mlx-lm

## Next Steps for Agents

1. **Test model loading**: Verify llasa-3b-Q4-mlx loads correctly with mlx-lm
2. **Create llasa_engine.py**: Wrapper for model loading and generation
3. **Create llasa_cli.py**: CLI with basic generation and chat mode
4. **Wire entrypoint**: Add `llasa-cli` to `pyproject.toml`
5. **Test basic generation**: Simple prompts and chat interactions
6. **Whisper integration**: Add `--enhance` flag to whisper-cli (optional Phase 2)

## Alignment with MLX Ecosystem

This project follows the MLX ecosystem patterns:
- ✅ Uses MLX framework natively
- ✅ 4-bit quantization for efficiency (following mlx-lm best practices)
- ✅ Standard mlx-lm load/generate patterns
- ✅ Chat template support for conversational AI
- ✅ Integration with existing audio pipeline (Whisper)

## Integration with Existing Pipelines

### With Whisper
- **Transcription Enhancement**: Clean up, format, and improve Whisper outputs
- **Speaker Diarization**: Identify and label speakers in transcripts
- **Content Summarization**: Generate summaries of audio content
- **Metadata Generation**: Create titles, descriptions, tags from audio

### With RAG
- **Audio Document RAG**: Index and retrieve audio transcripts
- **Multimodal Search**: Search across text and audio content
- **Context-aware Answers**: Use audio context for better RAG responses

### With Vision
- **Video Processing**: Combine audio transcription + visual analysis
- **Multimodal Captioning**: Generate captions from audio + image inputs

## Open Questions

1. **Audio-specific capabilities**: What makes Llasa-3B specialized for audio? Need to test and document.
2. **Whisper integration depth**: Should enhancement be automatic or opt-in?
3. **Chat template**: Is the built-in chat template suitable for audio tasks, or do we need custom prompts?
4. **Fine-tuning**: Would fine-tuning on specific audio domains (podcasts, meetings, music) improve results?

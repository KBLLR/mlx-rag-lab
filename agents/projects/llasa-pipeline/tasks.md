# Llasa Pipeline Task Ledger

Track every task for the Llasa pipeline project. Keep the table sorted by priority (top = highest). Move items between sections as they progress.

## Backlog

| ID | Title | Description | Priority | Owner | Notes |
|----|-------|-------------|----------|-------|-------|
| LL-001 | Test llasa-3b-Q4 loading | Verify model loads correctly with mlx-lm | High | | Prerequisite for all dev |
| LL-002 | Research llasa capabilities | Understand what makes it audio-specialized | High | | Informs implementation |
| LL-003 | Create llasa_engine.py | Model wrapper with load, generate, chat support | High | | Backend layer |
| LL-004 | Create llasa_cli.py | Standalone CLI following existing patterns | High | | Main interface |
| LL-005 | Wire llasa-cli entrypoint | Add to `pyproject.toml` and entrypoints | High | | CLI availability |
| LL-006 | Implement basic generation | Simple prompt-based text generation | High | | Core feature |
| LL-007 | Implement chat mode | Interactive chat with conversation history | High | | User experience |
| LL-008 | Chat template support | Use built-in chat template when available | Medium | | Better conversation |
| LL-009 | Transcript enhancement | Tool to post-process Whisper JSON outputs | Medium | | Whisper integration |
| LL-010 | Formatting and cleanup | Clean up transcription artifacts, punctuation | Medium | | Quality improvement |
| LL-011 | Audio metadata generation | Generate titles, descriptions from transcripts | Medium | | Content analysis |
| LL-012 | Batch transcript processing | Process multiple files in one command | Medium | | Efficiency |
| LL-013 | Whisper CLI integration | Add `--enhance` flag to whisper-cli | Low | | Seamless workflow |
| LL-014 | Speaker diarization support | Identify and label speakers in transcripts | Low | | Phase 2 feature |
| LL-015 | Content summarization | Summarize audio content from transcripts | Low | | Phase 2 feature |
| LL-016 | Audio RAG integration | Index and retrieve audio transcripts | Low | | Phase 3 feature |
| LL-017 | Fine-tuning interface | CLI for domain-specific audio fine-tuning | Low | | Phase 3 feature |
| LL-018 | Add to mlxlab CLI | Add Llasa option to main menu | Medium | | UX consistency |
| LL-019 | Documentation | Usage examples and command reference | Medium | | User docs |
| LL-020 | ASCII art header | Colorful header for Llasa in mlxlab | Low | | Visual consistency |

## In Progress
| ID | Title | Started | Owner | Notes |
|----|-------|---------|-------|-------|

## Review / QA
| ID | Title | PR / Branch | Reviewer | Notes |
|----|-------|-------------|----------|-------|

## Done
| ID | Title | Completed | Outcome |
|----|-------|-----------|---------|

## Notes

### Architecture (from decisions)
- **Integration**: Separate CLI (`llasa-cli`) with optional Whisper integration
- **Model**: 4-bit quantized (Q4) for efficiency (~2GB memory)
- **Specialization**: Audio-aware LLM for transcription enhancement

### Module Structure
```
apps/
  llasa_cli.py           # Standalone Llasa CLI
  whisper_cli.py         # (enhanced with --enhance flag)

src/rag/
  models/
    llasa_engine.py      # Llasa model wrapper
  audio/                 # New audio utilities module
    transcription.py     # Whisper + Llasa integration
    enhancement.py       # Post-processing logic
```

### CLI Interface Examples
```bash
# Basic generation
uv run llasa-cli --prompt "Explain MLX framework"

# Chat mode
uv run llasa-cli --chat
# (interactive conversation)

# Enhance Whisper transcript
uv run llasa-cli --enhance-transcript var/transcripts/audio.json \
  --output var/transcripts/audio_enhanced.txt

# Generate audio metadata
uv run llasa-cli --task describe-audio \
  --transcript var/transcripts/podcast.txt

# Batch processing
uv run llasa-cli --batch-enhance var/transcripts/*.json \
  --output-dir var/transcripts/enhanced/

# Whisper integration (future)
uv run whisper-cli audio.mp3 --output-format json --enhance
```

### Model Details
- **Size**: 3B params, 4-bit quantized → ~1.9GB
- **Quantization**: Q4 (4-bit) via MLX
- **Base**: HKUST-Audio/Llasa-3B
- **MLX Version**: srinivasbilla/llasa-3b-Q4-mlx
- **Context**: Chat template supported

### Use Cases (Priority Order)
1. **Post-process transcriptions**: Clean up Whisper outputs
2. **Audio metadata**: Generate titles, descriptions, summaries
3. **Interactive chat**: Conversational interface for audio workflows
4. **Batch processing**: Handle multiple transcript files
5. **Speaker diarization**: Identify speakers (Phase 2)
6. **Audio RAG**: Index and search transcripts (Phase 3)

### Integration Points

#### With Whisper
- Optional `--enhance` flag in whisper-cli
- Standalone transcript enhancement via llasa-cli
- Automatic formatting and cleanup
- Content summarization

#### With RAG
- Audio document indexing
- Transcript-based retrieval
- Multimodal search (text + audio)
- Context-aware answers from audio content

#### With Vision
- Video processing: audio + visual analysis
- Multimodal captioning for video content

### Testing Checklist
- [ ] Model loads with mlx-lm
- [ ] Basic text generation works
- [ ] Chat template applies correctly
- [ ] Can process JSON transcript from Whisper
- [ ] Batch processing handles multiple files
- [ ] Memory usage stays under 4GB
- [ ] Performance benchmarks (tokens/sec)

### Open Questions to Research
1. **Audio specialization**: What audio-specific training/fine-tuning does Llasa have?
2. **Optimal prompts**: What prompt patterns work best for audio tasks?
3. **Whisper integration depth**: Should enhancement be automatic or opt-in?
4. **Fine-tuning needs**: Would domain-specific fine-tuning improve results?

### Dependencies
- MLX framework (already available)
- mlx-lm (already available)
- transformers (already available)
- llasa-3b-Q4-mlx weights (already downloaded)
- No new packages needed

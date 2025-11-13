# T5 Pipeline Project

**Status**: Planning
**Owner**: David Caballero
**Created**: 2025-11-13
**Model**: T5 / FLAN-T5 (google/t5-small through t5-11b)

## Goal

Establish a production-ready T5 text-to-text pipeline for various NLP tasks including translation, summarization, question answering, and text transformation using the T5/FLAN-T5 encoder-decoder models optimized for MLX.

## Context

T5 (Text-To-Text Transfer Transformer) is a versatile encoder-decoder model that frames all NLP tasks as text-to-text problems. The model is already available locally at `mlx-models/t5/` and provides:

- **Translation**: Multi-language translation with task prefix (e.g., "translate English to German:")
- **Summarization**: Document and text summarization
- **Question Answering**: Extract answers from context
- **Text Classification**: Sentiment, intent, topic classification
- **Paraphrasing**: Text rewriting and style transfer
- **Custom Tasks**: Any task that can be framed as text-to-text

### T5 vs FLAN-T5
- **T5**: Original pre-trained models (60M - 11B params)
- **FLAN-T5**: Instruction-finetuned variants with better zero-shot performance
- Both use the same architecture and API

## Key Features to Implement

### Phase 1: Core T5 Pipeline
- [ ] Create `apps/t5_cli.py` following existing CLI patterns
- [ ] Support task-prefixed prompts (translate, summarize, etc.)
- [ ] Batch text processing
- [ ] Model selection (small, base, large, 3b, 11b)
- [ ] FLAN-T5 variant support

### Phase 2: Integration with RAG
- [ ] Use T5 for query transformation/expansion
- [ ] Document summarization before ingestion
- [ ] Answer refinement/post-processing
- [ ] Multi-document summarization from retrieved chunks

### Phase 3: Advanced Features
- [ ] Custom task fine-tuning interface
- [ ] Streaming generation for long outputs
- [ ] Constrained decoding for structured outputs
- [ ] Multi-task pipeline chaining

## Reference Architecture

### Model Details
- **Model Family**: T5 / FLAN-T5 (Google)
- **Architecture**: Encoder-Decoder Transformer
- **Framework**: MLX (Apple Silicon optimized)
- **Size Range**: 60M (t5-small) to 11B (t5-11b)
- **Task Format**: Prefix-based (e.g., "translate English to German: text")

### Supported Models
| Model | Parameters | Size | Use Case |
|-------|-----------|------|----------|
| t5-small | 60M | ~240MB | Fast, testing |
| t5-base | 220M | ~900MB | Balanced |
| t5-large | 770M | ~3GB | Higher quality |
| t5-3b | 3B | ~12GB | Production |
| t5-11b | 11B | ~44GB | Maximum quality |

Plus FLAN-T5 variants: `google/flan-t5-small`, `google/flan-t5-base`, etc.

### Integration Points
- `apps/t5_cli.py` - New CLI entrypoint
- `src/rag/models/t5_engine.py` - T5 model wrapper
- `src/rag/text/` - Integration with text RAG pipeline
- `[project.scripts]` - Add `t5-cli` command

## Success Criteria

- [ ] `t5-cli` command works with `--help` and basic translation
- [ ] Can translate text: `uv run t5-cli --task translate --source en --target de --text "Hello world"`
- [ ] Can summarize: `uv run t5-cli --task summarize --text "long document..."`
- [ ] Batch processing: process multiple texts in one command
- [ ] Model selection: choose between different T5 sizes
- [ ] FLAN-T5 support: use instruction-tuned variants
- [ ] Integration with RAG for query expansion
- [ ] Documentation in `docs/COMMANDS_MANIFEST.md`

## Common Use Cases

### 1. Translation
```bash
uv run t5-cli --task translate --source en --target de \
  --text "The quick brown fox jumps over the lazy dog"
# Output: "Der schnelle braune Fuchs springt über den faulen Hund"
```

### 2. Summarization
```bash
uv run t5-cli --task summarize \
  --text "$(cat long_document.txt)" \
  --max-length 100
```

### 3. Question Answering
```bash
uv run t5-cli --task qa \
  --context "MLX is Apple's machine learning framework" \
  --question "What is MLX?"
```

### 4. Custom Task
```bash
uv run t5-cli --prompt "paraphrase: The weather is nice today" \
  --model google/flan-t5-base
```

### 5. RAG Integration (Query Expansion)
```bash
# Expand user query before RAG retrieval
uv run t5-cli --task expand \
  --text "apple silicon performance" \
  --variants 3
# Output variations for better retrieval
```

## Architecture Decisions

### 1. Integration Strategy
**Decision**: Separate CLI for T5 tasks, with optional integration into RAG pipeline.

**Rationale**:
- T5 is a general-purpose text transformation tool
- Not specific to RAG (unlike vision which is multimodal RAG)
- Can be used standalone for translation, summarization, etc.
- RAG can import T5 utilities for query expansion, answer refinement

**Structure**:
```
apps/
  t5_cli.py          # Standalone T5 CLI

src/rag/
  models/
    t5_engine.py     # T5 model wrapper
  text/
    t5_utils.py      # T5 utilities for RAG (query expansion, etc.)
```

### 2. Task Interface
**Decision**: Support both task prefixes and explicit task flags.

**Examples**:
```bash
# Explicit task flag (recommended)
uv run t5-cli --task translate --source en --target de --text "..."

# Raw prompt with prefix (advanced)
uv run t5-cli --prompt "translate English to German: ..."
```

### 3. Model Selection
**Decision**: Default to `t5-base`, allow override with `--model` flag.

**Options**:
- `--model t5-small` → fast, lightweight
- `--model t5-base` → default, balanced
- `--model google/flan-t5-large` → instruction-tuned variant

## Dependencies

### Existing
- MLX framework (~0.29.3)
- mlx-lm for model loading
- transformers (for tokenizer)

### New (to add)
- T5 model files (download on first use from HF Hub)
- SentencePiece (T5 tokenizer dependency)

## Resources

- **Local Model**: `/Users/davidcaballero/mlx-RAG/mlx-models/t5/`
- **T5 Paper**: https://arxiv.org/abs/1910.10683
- **FLAN-T5 Paper**: https://arxiv.org/abs/2210.11416
- **HF Model Hub**: https://huggingface.co/docs/transformers/model_doc/t5
- **FLAN-T5 Models**: https://huggingface.co/docs/transformers/model_doc/flan-t5

## Next Steps for Agents

1. **Audit T5 code**: Review `mlx-models/t5/` to understand the existing implementation
2. **Create t5_cli.py**: Build CLI with task-based interface
3. **Implement t5_engine.py**: Wrapper for T5 model loading and generation
4. **Wire entrypoint**: Add `t5-cli` to `pyproject.toml`
5. **Test common tasks**: Translation, summarization, QA
6. **RAG integration**: Add query expansion utilities to `src/rag/text/`

## Alignment with MLX Ecosystem

This project follows the MLX ecosystem patterns:
- ✅ Uses MLX framework natively
- ✅ Encoder-decoder architecture (different from LLM-only)
- ✅ Supports multiple model sizes
- ✅ Task-oriented interface (follows T5 design)
- ✅ Can integrate with existing RAG pipeline

## Integration with Existing Pipelines

### With RAG
- **Query Expansion**: Generate query variations for better retrieval
- **Summarization**: Condense long documents before ingestion
- **Answer Refinement**: Post-process generated answers

### With Vision
- **Image Caption Translation**: Translate captions from vision pipeline
- **Multimodal Summarization**: Summarize text + image descriptions

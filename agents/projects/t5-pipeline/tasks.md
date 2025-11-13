# T5 Pipeline Task Ledger

Track every task for the T5 pipeline project. Keep the table sorted by priority (top = highest). Move items between sections as they progress.

## Backlog

| ID | Title | Description | Priority | Owner | Notes |
|----|-------|-------------|----------|-------|-------|
| T5-001 | Audit T5 code | Review existing code in `mlx-models/t5/` to understand implementation | High | | Prerequisite for wrapper |
| T5-002 | Create t5_engine.py | T5 model wrapper with loading and generation | High | | Backend layer |
| T5-003 | Create t5_cli.py | Standalone CLI for T5 tasks following existing patterns | High | | Main interface |
| T5-004 | Wire t5-cli entrypoint | Add `t5-cli` command to `pyproject.toml` and entrypoints | High | | CLI availability |
| T5-005 | Implement translation task | Support `--task translate --source XX --target YY` | High | | Core feature |
| T5-006 | Implement summarization task | Support `--task summarize --text "..."` | High | | Core feature |
| T5-007 | Implement QA task | Support `--task qa --context "..." --question "..."` | Medium | | Common use case |
| T5-008 | Model selection | Support `--model t5-small/base/large/3b/11b` and FLAN variants | High | | Flexibility |
| T5-009 | Batch text processing | Process multiple inputs in single command | Medium | | Efficiency |
| T5-010 | Raw prompt mode | Support `--prompt "prefix: text"` for custom tasks | Medium | | Advanced usage |
| T5-011 | RAG query expansion | Create `t5_utils.py` with query expansion for RAG | Medium | | RAG integration |
| T5-012 | Document summarization | Integrate with ingestion pipeline for pre-summarization | Low | | RAG integration |
| T5-013 | Answer refinement | Post-process RAG answers with T5 | Low | | RAG integration |
| T5-014 | Add to mlxlab CLI | Add T5 option to main `mlxlab` menu | Medium | | UX consistency |
| T5-015 | Streaming generation | Support streaming for long outputs | Low | | Phase 3 feature |
| T5-016 | Constrained decoding | Implement structured output generation | Low | | Phase 3 feature |
| T5-017 | Custom task fine-tuning | CLI for fine-tuning T5 on custom datasets | Low | | Phase 3 feature |
| T5-018 | Multi-task chaining | Pipeline multiple T5 tasks together | Low | | Phase 3 feature |
| T5-019 | Documentation | Add usage examples and command reference | Medium | | User docs |
| T5-020 | ASCII art header | Create colorful header for T5 pipeline in mlxlab | Low | | Visual consistency |

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
- **Integration**: Separate CLI (`t5-cli`), not integrated into rag-cli
- **Rationale**: T5 is general-purpose text transformation, not RAG-specific
- **RAG Utils**: Optional integration via `src/rag/text/t5_utils.py`

### Module Structure
```
apps/
  t5_cli.py          # Standalone T5 CLI

src/rag/
  models/
    t5_engine.py     # T5 model wrapper (load, generate)
  text/
    t5_utils.py      # T5 utilities for RAG (query expansion, etc.)
```

### CLI Interface Examples
```bash
# Translation
uv run t5-cli --task translate --source en --target de \
  --text "Hello world"

# Summarization
uv run t5-cli --task summarize \
  --text "$(cat document.txt)" \
  --max-length 100

# Question Answering
uv run t5-cli --task qa \
  --context "MLX is Apple's ML framework" \
  --question "What is MLX?"

# Raw prompt (advanced)
uv run t5-cli --prompt "paraphrase: The weather is nice today" \
  --model google/flan-t5-base

# Batch processing
uv run t5-cli --task translate --source en --target es \
  --batch texts.txt \
  --output translations.txt
```

### Supported Tasks (Phase 1)
1. **translate**: Multi-language translation
2. **summarize**: Text summarization
3. **qa**: Question answering
4. **paraphrase**: Text rewriting (via raw prompt)
5. **classify**: Text classification (via raw prompt)

### Model Sizes
- `t5-small` (60M) → ~240MB, fast testing
- `t5-base` (220M) → ~900MB, default balanced
- `t5-large` (770M) → ~3GB, higher quality
- `t5-3b` (3B) → ~12GB, production
- `t5-11b` (11B) → ~44GB, maximum quality

### FLAN-T5 Variants
- Better zero-shot performance (instruction-tuned)
- Same API: `--model google/flan-t5-small|base|large|xl|xxl`

### RAG Integration Points
1. **Query Expansion**: Generate query variations before retrieval
2. **Summarization**: Condense documents before ingestion
3. **Answer Refinement**: Polish generated answers
4. **Multi-doc Summary**: Summarize retrieved chunks

### Dependencies
- MLX framework (already available)
- mlx-lm (already available)
- transformers (already available)
- SentencePiece (T5 tokenizer, may need to add)
- T5 model weights (download from HF Hub on first use)

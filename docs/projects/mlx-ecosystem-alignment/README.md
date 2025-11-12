# MLX Ecosystem Alignment Project

**Status**: Planning
**Owner**: TBD
**Created**: 2025-11-12

## Goal

Align mlx-RAG with the official MLX ecosystem projects (`mlx-lm`, `mlx-data`, `mlx-examples`) and establish a training pipeline for fine-tuning and LoRA workflows.

## Context

From David (2025-11-12):
> "please use mlx-lm, mlx-explore and mlx-data as examples and mlx-examples to inspire the functionality. we need to stablish a training pipeline as well and clean the project from unnecessary code"

This signals a shift from "experimental lab" to "production-ready MLX toolkit" aligned with Apple's official MLX ecosystem.

## Reference Projects

### mlx-lm
- **Repo**: https://github.com/ml-explore/mlx-lm
- **Purpose**: LLM inference and fine-tuning with MLX
- **Key features**:
  - LoRA training/inference
  - Quantization (4-bit, 8-bit)
  - Model conversion from HF
  - CLI for `mlx_lm.generate`, `mlx_lm.convert`, `mlx_lm.fuse`

### mlx-data
- **Repo**: https://github.com/ml-explore/mlx-data
- **Purpose**: Efficient data loading for MLX training
- **Key features**:
  - Stream-based data pipelines
  - Lazy loading and prefetching
  - Integration with MLX array format

### mlx-examples
- **Repo**: https://github.com/ml-explore/mlx-examples
- **Purpose**: Reference implementations for MLX workflows
- **Relevant examples**:
  - `llms/` — LLM inference and fine-tuning patterns
  - `lora/` — LoRA adapter training
  - `stable_diffusion/` — Image generation (Flux inspiration)

## Current State Analysis

### What Aligns Already ✅
- Using `mlx-lm.load()` for model loading (see `qwen_reranker.py`, `model_engine.py`)
- Using `mlx-data` for VectorDB ingestion (see `create_vdb.py`)
- Quantized models supported (Phi-3 4-bit, llasa-3b-Q4)
- LoRA adapters partially supported in Flux (`--adapter`, `--fuse-adapter` flags)

### What Needs Work ⚠️
- **Training pipeline missing**: No `mlx_lm.lora` or fine-tuning workflows
- **Code bloat**: Many experimental scripts/apps that don't follow MLX patterns
- **Ingestion inconsistency**: Some paths use raw NumPy, others use mlx-data
- **Model management**: No unified `convert` / `fuse` CLI (Flux has ad-hoc version)

### What to Remove 🗑️
- **Archived TUI**: Already moved to `archive/tui/rag_tui.py`, but keep cleaning up deps
- **Non-MLX experiments**: Any scripts using PyTorch, TensorFlow, or other frameworks
- **Duplicate utilities**: Consolidate under `libs/mlx_core/` following mlx-lm patterns
- **Unused benchmarks**: If not actively measuring MLX performance, archive them

## Proposed Actions

### Phase 1: Training Pipeline (Priority: High)

**Goal**: Establish LoRA fine-tuning for LLMs (Phi-3, llasa) following `mlx-lm` patterns.

**Tasks**:
1. Create `apps/train_cli.py` inspired by `mlx_lm.lora` CLI
2. Add training data prep scripts (mlx-data integration)
3. Document LoRA training workflow in `docs/TRAINING.md`
4. Test with small dataset (e.g., fine-tune Phi-3 on domain docs)

**Reference**:
- `mlx-examples/llms/mlx_lm/tuner/` — LoRA training loop
- `mlx-examples/llms/mlx_lm/lora.py` — Adapter management

### Phase 2: Code Cleanup (Priority: High)

**Goal**: Remove experimental code that doesn't align with production MLX use.

**Audit targets**:
- `experiments/` — Keep only mlx-data ingestion demos
- `benchmarks/` — Archive unless actively used for MLX performance tuning
- `third_party/` — Remove if unused, or document explicitly
- `utils/`, `scripts/` — Consolidate into `libs/mlx_core/` or `apps/`
- `musicgen/`, `segment_anything/`, `speechcommands/` — Archive if not core to RAG

**Decision criteria**:
- Does it use MLX natively?
- Is it used by a `[project.scripts]` entrypoint?
- Does it have tests?
- Is it documented in `COMMANDS_MANIFEST.md`?

If "no" to most → archive or delete.

### Phase 3: Ingestion Standardization (Priority: Medium)

**Goal**: All data pipelines use mlx-data consistently (no raw NumPy/Pandas except for final output).

**Changes**:
- Audit `src/rag/ingestion/` for non-mlx-data paths
- Migrate PDF chunking to mlx-data streams (see `create_vdb.py` for partial impl)
- Document mlx-data usage in `docs/DEVELOPMENT_GUIDELINES.md`

### Phase 4: Model Management CLI (Priority: Medium)

**Goal**: Provide `mlx-rag model convert|fuse|quantize` commands mirroring `mlx-lm`.

**Example**:
```bash
# Convert HF model to MLX format
uv run mlx-rag model convert --hf-id mistralai/Mistral-7B-v0.1 --output mlx-models/mistral-7b

# Fuse LoRA adapter
uv run mlx-rag model fuse --base mlx-models/phi-3 --adapter lora/domain-adapter --output mlx-models/phi-3-fused

# Quantize model
uv run mlx-rag model quantize --model mlx-models/phi-3 --bits 4 --output mlx-models/phi-3-4bit
```

## Success Criteria

- [ ] Training CLI can fine-tune Phi-3 with LoRA on sample dataset
- [ ] Code audit complete: all non-MLX code archived or removed
- [ ] Ingestion pipeline 100% mlx-data (no NumPy except output)
- [ ] Model management CLI covers convert/fuse/quantize
- [ ] All CLIs (`rag-cli`, `flux-cli`, `train-cli`, `model-cli`) follow mlx-lm patterns
- [ ] Documentation references mlx-lm, mlx-data, mlx-examples explicitly

## Next Steps for Agents

1. **Audit codebase**: Run `Explore` agent to identify non-MLX code
2. **Archive dead code**: Move experiments/benchmarks not in active use
3. **Prototype train-cli**: Start with minimal LoRA training script
4. **Document patterns**: Create `docs/MLX_PATTERNS.md` showing canonical workflows

## Resources

- MLX main repo: https://github.com/ml-explore/mlx
- mlx-lm: https://github.com/ml-explore/mlx-lm
- mlx-data: https://github.com/ml-explore/mlx-data
- mlx-examples: https://github.com/ml-explore/mlx-examples
- MLX Community Hub: https://huggingface.co/mlx-community

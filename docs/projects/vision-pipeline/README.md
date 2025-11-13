# Vision Pipeline Project

**Status**: Planning
**Owner**: David Caballero
**Created**: 2025-11-13
**Model**: Phi-3-Vision-MLX (microsoft/Phi-3.5-vision-instruct)

## Goal

Establish a production-ready vision pipeline using Phi-3-Vision-MLX for multimodal AI tasks including visual question answering, image captioning, and vision-augmented RAG workflows.

## Context

The Phi-3-Vision-MLX model is already available locally at `mlx-models/Phi-3-Vision-MLX/` and provides:
- Visual question answering (VQA)
- Image captioning and analysis
- Multi-turn conversations with visual context
- Code generation with visual feedback loop
- LoRA fine-tuning for domain-specific vision tasks
- Agent interactions with tool use (APIs, code execution)

This project aims to integrate these capabilities into the MLX-RAG ecosystem as a first-class pipeline, following the patterns established in `mlx-lm` and the existing CLI structure (`rag-cli`, `flux-cli`, etc.).

## Key Features to Implement

### Phase 1: Core Vision Pipeline
- [ ] Create `apps/vision_cli.py` following existing CLI patterns
- [ ] Implement visual question answering (VQA) interface
- [ ] Support batch image analysis
- [ ] Image captioning and description generation
- [ ] Multi-turn conversation with image context

### Phase 2: Vision-Augmented RAG
- [ ] Integrate vision pipeline with existing VectorDB
- [ ] Implement multimodal RAG (text + images)
- [ ] Image-based document retrieval
- [ ] Visual context injection for LLM responses

### Phase 3: Advanced Features
- [ ] LoRA fine-tuning interface for domain-specific vision tasks
- [ ] Constrained beam decoding for structured outputs
- [ ] External API integration (image gen, TTS)
- [ ] Custom agent toolchains

## Reference Architecture

### Model Details
- **Model**: microsoft/Phi-3.5-vision-instruct
- **Framework**: MLX (Apple Silicon optimized)
- **Size**: ~4-7GB (with quantization options)
- **Capabilities**: Vision + Language multimodal

### Integration Points
- `libs/mlx_core/` - Model engine integration
- `apps/vision_cli.py` - New CLI entrypoint
- `src/rag/models/` - Vision model wrapper
- `[project.scripts]` - Add `vision-cli` command

## Success Criteria

- [ ] `vision-cli` command works with `--help` and basic VQA
- [ ] Can analyze images from CLI: `uv run vision-cli --image path/to/image.jpg --prompt "What's in this image?"`
- [ ] Batch processing: analyze multiple images in one command
- [ ] Multi-turn conversation mode for iterative image analysis
- [ ] Integration with RAG: retrieve images based on text queries
- [ ] Documentation in `docs/COMMANDS_MANIFEST.md`
- [ ] Working examples in `docs/examples/vision-pipeline/`

## Dependencies

### Existing
- `phi_3_vision_mlx` library (already in `mlx-models/Phi-3-Vision-MLX/`)
- MLX framework (~0.29.3)
- mlx-lm for model loading

### New (to add)
- May need to add `phi-3-vision-mlx` to `pyproject.toml` dependencies
- Image processing libs (PIL/Pillow already available)

## Resources

- **Local Model**: `/Users/davidcaballero/mlx-RAG/mlx-models/Phi-3-Vision-MLX/`
- **Original Repo**: https://github.com/JosefAlbers/Phi-3-Vision-MLX
- **Model Card**: https://huggingface.co/microsoft/Phi-3.5-vision-instruct
- **Documentation**: https://josefalbers.github.io/Phi-3-Vision-MLX/
- **Tutorial Series**: https://medium.com/@albersj66

## Next Steps for Agents

1. **Audit existing code**: Review `mlx-models/Phi-3-Vision-MLX/` to understand available APIs
2. **Create vision_cli.py**: Start with minimal VQA interface following `rag-cli` patterns
3. **Wire entrypoint**: Add `vision-cli = "rag.cli.entrypoints:vision_cli_main"` to `pyproject.toml`
4. **Test basic VQA**: `uv run vision-cli --image test.jpg --prompt "Describe this image"`
5. **Document usage**: Add examples and command reference to docs

## Alignment with MLX Ecosystem

This project follows the MLX ecosystem patterns:
- ✅ Uses MLX framework natively
- ✅ Model already optimized for Apple Silicon
- ✅ Supports quantization for memory efficiency
- ✅ LoRA fine-tuning capabilities (Phase 3)
- ✅ Agent-based architecture (can integrate with existing patterns)

## Architecture Decisions

### 1. Integration Strategy: Unified RAG CLI with Modes
**Decision**: Integrate into existing `rag-cli` with subcommands/modes, NOT a separate binary.

**Rationale**: Users think in "RAG", not "RAG-but-vision-edition". Avoids cluttering UX with multiple entry points.

**Interface**:
```bash
# text-only (current behavior)
uv run rag-cli text ...

# image-aware RAG (text + image embeddings)
uv run rag-cli vision ...

# hybrid mode – both indexes
uv run rag-cli multimodal ...
```

**Structure**:
```
src/rag/
  text/           # existing text RAG
  vision/         # new vision RAG module
  shared/         # configs, VectorDB helpers, session/state
```

### 2. Multimodal Storage Architecture
**Decision**: Split indexes by modality with unified metadata.

**Structure**:
```
models/indexes/
  text_vdb.npz          # text embeddings (MiniLM / Phi text head)
  image_vdb.npz         # image embeddings (Phi-3-Vision-MLX)
  multimodal_meta.json  # unified metadata
```

**Embedding Entry Format**:
```python
{
    "id": "chunk-uuid",
    "doc_id": "doc-uuid",
    "modality": "text" | "image",
    "embedding": np.ndarray[dim],
    "metadata": {
        "page": 3,
        "bbox": [x1, y1, x2, y2],
        "source": "file.pdf#page=3",
        ...
    }
}
```

**Retrieval Flow** (multimodal mode):
1. Encode query text → search `text_vdb.npz`
2. If query image present → encode image → search `image_vdb.npz`
3. Merge candidate sets → rerank (optionally) → generate answer

### 3. Model Integration Strategy
**Decision**: Use existing Phi-3-Vision-MLX as backend + thin local wrapper.

**Structure**:
```
src/rag/models/
  phi3_vision_backend.py   # raw MLX model loading / forward pass
  phi3_vision_embedder.py  # high-level embedding API for RAG
```

**Benefits**:
- Standardizes input types (path, PIL image, array)
- Normalizes output format (np.ndarray + metadata)
- Centralizes device/dtype/precision knobs
- Makes model swappable (could test CLIP, other MLX ports later)

### 4. Supported Formats & Sources

**Phase 1 (MVP)**:
- **Formats**: `.png`, `.jpg`, `.jpeg`, `.webp`
- **Sources**:
  - Local file paths
  - HTTP/HTTPS URLs (download to temp, treat as local)

**Phase 2 (Future)**:
- PDF ingestion: "PDF → pages → images" → embed page images
- Base64 support (API/programmatic only, not primary CLI)

**CLI Interface**:
```bash
# local images
uv run rag-cli vision --add-image path/to/img1.png path/to/img2.jpg

# URLs (download into var/images/cache/)
uv run rag-cli vision --add-image \
  "https://example.com/figure1.png" \
  "https://example.com/chart2.jpg"

# query with reference images
uv run rag-cli vision \
  --query "Explain the trend in these charts" \
  --query-image local_chart.png
```

**Normalization**: All sources become normalized local file paths before hitting the encoder.

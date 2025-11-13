# MLX-RAG Usability Status

Last updated: 2025-11-12 | Agent: **Rhyme** (LabCustodian)

## Quick Health Check

Run these commands to verify your lab is operational:

```bash
# 1. Check CLI entrypoints
uv run rag-cli --help
uv run flux-cli --help
uv run bench-cli --help

# 2. Verify VectorDB loads
uv run python -c "from rag.retrieval.vdb import VectorDB; vdb = VectorDB('models/indexes/combined_vdb.npz'); print(f'✓ VDB has {len(vdb.content)} chunks')"

# 3. Test MLX model engine (downloads Phi-3 if needed)
uv run python -c "from libs.mlx_core.model_engine import MLXModelEngine; engine = MLXModelEngine('mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit', model_type='text'); print('✓ Model engine works')"
```

Expected: All three checks pass within 30 seconds (model download may take longer on first run).

---

## What's Ready for Production Use

### ✅ **VectorDB Operations**
- **Load existing indexes**: `VectorDB('models/indexes/combined_vdb.npz')` works instantly
- **Query embeddings**: Semantic search over 352 chunks confirmed working
- **Build new indexes**: Ingestion pipeline functional (see `create_vdb.py`)

**Use case**: Local-first document search without LLM overhead.

```bash
# Quick query example (without reranker)
uv run python -c "
from rag.retrieval.vdb import VectorDB
vdb = VectorDB('models/indexes/combined_vdb.npz')
results = vdb.query('What is MLX?', k=5)
for i, chunk in enumerate(results, 1):
    print(f'{i}. {chunk[\"text\"][:100]}...')
"
```

### ✅ **MLX Model Loading**
- **Phi-3-mini (4-bit)**: Loads successfully, generates text
- **Auto-download**: HF Hub integration works (respects `HF_HOME` env var)
- **Metal acceleration**: No NSRangeException encountered during basic model init

**Use case**: Standalone text generation with MLX models.

```bash
# Test generation (without full RAG pipeline)
uv run python -c "
from libs.mlx_core.model_engine import MLXModelEngine
engine = MLXModelEngine('mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit', model_type='text')
result = engine.generate('Explain MLX in one sentence.', max_tokens=50)
print(result)
"
```

### ✅ **CLI Structure**
- All apps properly wired through `[project.scripts]`
- Entrypoints use `rag.cli.entrypoints` shim to set `PYTHONPATH`
- Help text renders correctly for all commands

**Use case**: Foundation for building custom workflows.

---

## Known Blockers

### 🚫 **RAG CLI Query Loop (Blocked)**

**Issue**: The full `rag-cli` interactive loop hangs during reranker initialization.

**Root cause**: `QwenReranker` tries to load `mlx-community/mxbai-rerank-large-v2`, which either:
- Downloads a large model (timeouts after 30s)
- Hits a multiprocessing semaphore leak (Python 3.12 + macOS issue)
- Fails silently without error messages

**Evidence**:
```bash
$ echo "test" | timeout 30 uv run rag-cli --vdb-path models/indexes/combined_vdb.npz
# Hangs, then:
# resource_tracker: There appear to be 1 leaked semaphore objects to clean up at shutdown
```

**Workaround**: Make reranker optional in `apps/rag_cli.py` (see fix below).

**Files involved**:
- `apps/rag_cli.py:77` — hardcodes `QwenReranker` initialization
- `src/rag/models/qwen_reranker.py:53` — calls `mlx_lm.load()` which may hang

---

### 🚫 **Cross-Encoder Model Unused**

**Issue**: A working cross-encoder model exists (`mlx-models/cross-encoder-ms-marco-MiniLM-L-6-v2/`) but no Python wrapper.

**Impact**: Reranking requires the problematic Qwen approach instead of the simpler cross-encoder scoring.

**Potential fix**: Restore or create a `CrossEncoderReranker` class that uses the `weights.npz` directly.

---

## Fixes Needed for Real Use

### Priority 1: Make Reranker Optional

**Goal**: Let users query the RAG system without reranking (use raw VectorDB scores).

**Change**: Add `--no-reranker` flag to `apps/rag_cli.py`:

```python
# apps/rag_cli.py
parser.add_argument("--no-reranker", action="store_true", help="Skip reranking step")

# In main():
if args.no_reranker:
    reranker = None
    selected = retrieved[:args.top_k]
else:
    reranker = QwenReranker(args.reranker_id)
    # ... existing reranking logic
```

### Priority 2: Document Flux Usage

**Goal**: Confirm Flux CLI works on Metal-ready machines.

**Test**: Run a minimal image generation:
```bash
uv run flux-cli --prompt "test render" --steps 1 --image-size 256 --model schnell
```

Expected: Image saves to `outputs/flux/` without errors (Metal NSRangeException may still occur on some machines).

### Priority 3: Create End-to-End Examples

**Goal**: Provide copy-paste workflows for common tasks.

**Examples needed**:
1. **Build VDB from PDFs**: `var/source_docs/*.pdf` → `models/indexes/my_docs.npz`
2. **Query without reranker**: Simple CLI one-liner for testing
3. **Flux portrait generation**: Non-square aspect ratios (e.g., `512x768`)

---

## Next Steps for Agents

1. **Apply reranker fix** (Priority 1 above) and test RAG CLI end-to-end
2. **Run Flux smoke test** on a Metal-capable Mac (document results in `LAB_STATUS.md`)
3. **Create `docs/QUICK_START.md`** with the working examples from this doc
4. **Investigate semaphore leak** (may require Python 3.11 downgrade or HF Hub settings)
5. **Restore CrossEncoderReranker** if Qwen approach remains problematic

---

## For David

You asked about making real use of the apps — here's the path forward:

**Today you can**:
- ✅ Query your existing VectorDB directly (no reranker needed)
- ✅ Generate text with Phi-3 via `MLXModelEngine`
- ✅ Build new indexes from PDFs (ingestion works)

**To unblock RAG CLI**:
- Apply the `--no-reranker` flag (I can do this now if you want)
- Or wait for the Qwen model download to complete (may take 5-10 min depending on connection)

**For data transformation workflows**:
- The VectorDB + embeddings pipeline is solid
- You can script custom flows by importing `VectorDB`, `MLXModelEngine`, and `create_vdb` directly
- Example: Batch-process docs → generate summaries → store in new VDB

Want me to apply the reranker fix now so you can start querying immediately?

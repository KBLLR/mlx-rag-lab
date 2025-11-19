# FUSION_PHASE0.md – mlx-rag-lab (Tier 3B RAG Engine)

**Repository**: mlx-rag-lab
**Tier**: 3B (RAG Engine – chunking, embeddings, document ingestion, retrieval, stats)
**Phase**: 0 – Deep Mapping (ZERO refactors)
**Date**: 2025-11-16
**Branch**: `claude/phase0-rag-mapping-01E8y3ueFLDFNa2KZPBy3jdr`

---

## 1. Executive Summary

**mlx-rag-lab** is Tier 3B in the 3-tier local-first architecture, serving as the **RAG Engine** for document ingestion, chunking, embedding generation, vector storage, and retrieval. It is designed to run locally on Apple Silicon using MLX (Apple's ML framework) with no cloud dependencies.

### Current State
- **Hybrid architecture**: Contains both a CLI-driven tool suite (fully functional) and incomplete RAG primitives
- **Multiple domains**: RAG, Voice (STT/TTS), Imaging (Flux), Music (MusicGen), and Chat
- **Target fusion role**: Pure RAG engine exposing stateless API endpoints for document ingestion (`/rag_upsert`), querying (`/rag_query`), and stats (`/rag_stats`)

### Critical Finding
The repository is **NOT a pure RAG engine**—it's a **multi-domain MLX lab** with:
- ✅ Working CLI tools for RAG, voice chat, STS avatars, Flux image generation, and MusicGen
- ⚠️ **Incomplete RAG primitives**: Missing `rag.models.model.Model` class (declared but not implemented)
- ⚠️ **Stateful patterns**: `ChatSession` class assumes persistent conversation state
- ⚠️ **Hardcoded paths**: Assumes local filesystem (`var/indexes/`, `var/voice_chat/`, etc.)

### Fusion Vision (Phase 3)
Transform the RAG components into a **stateless FastAPI service** exposing:
- `POST /rag_upsert` – Document ingestion + chunking + embedding + index update
- `POST /rag_query` – Query vector store + return ranked chunks
- `GET /rag_stats` – Return index statistics (# chunks, # documents, model info)
- Optional: `POST /embeddings_create` – Generate embeddings for arbitrary text

---

## 2. High-Level Architecture Map

### 2.1 Repository Structure

```
mlx-rag-lab/
├── apps/                    # CLI entrypoints (11 CLIs)
│   ├── rag_cli.py          # RAG query interface (245 lines)
│   ├── ingest_cli.py       # Document ingestion (105 lines)
│   ├── chat_cli.py         # Text chat with MLX LLMs (447 lines)
│   ├── voice_chat_cli.py   # Voice chat with STT/TTS (545 lines)
│   ├── sts_avatar_cli.py   # Speech-to-speech avatar (745 lines)
│   ├── flux_cli.py         # Flux text-to-image (75 lines)
│   ├── musicgen_cli.py     # Music generation (233 lines)
│   ├── whisper_cli.py      # Audio transcription (175 lines)
│   ├── classify_cli.py     # Text classification (405 lines)
│   ├── bench_cli.py        # Benchmarking harness (26 lines)
│   └── mlxlab_cli.py       # Unified launcher menu (1,879 lines)
│
├── src/
│   ├── rag/                # RAG engine core (3,394 lines total)
│   │   ├── ingestion/      # Document ingestion pipeline
│   │   │   └── create_vdb.py (229 lines) – PDF extraction, chunking, embedding
│   │   ├── retrieval/      # Vector DB and query
│   │   │   ├── vdb.py (139 lines) – VectorDB class (NPZ-based storage)
│   │   │   └── query_vdb.py (88 lines) – Query script with LLM response
│   │   ├── chat/           # Chat wrapper for MLX LLMs
│   │   │   ├── gpt_oss_wrapper.py (302 lines) – ChatSession class
│   │   │   └── templates.py (66 lines) – Prompt templates, string utils
│   │   ├── cli/            # CLI utilities and scripts (1,094 lines total)
│   │   │   ├── entrypoints.py (43 lines) – Console script wrappers
│   │   │   ├── app_launcher.py (306 lines) – App launcher utilities
│   │   │   ├── flux_*.py (494 lines) – Flux image generation
│   │   │   ├── benchmark.py (97 lines) – Benchmark utilities
│   │   │   └── download_*.py (147 lines) – Model download scripts
│   │   ├── tts/            # Text-to-speech engines
│   │   │   ├── kokoro_tts.py (233 lines) – Kokoro TTS wrapper
│   │   │   ├── marvis_tts.py (300 lines) – Marvis TTS wrapper
│   │   │   └── viseme_mapper.py (285 lines) – Viseme generation for avatars
│   │   ├── stt/            # Speech-to-text
│   │   │   └── whisperx_client.py (290 lines) – WhisperX MLX wrapper
│   │   └── config/         # Configuration
│   │       └── config.json (10 lines) – BERT-style config (legacy)
│   │
│   ├── libs/               # Supporting libraries
│   │   ├── mlx_core/
│   │   │   └── model_engine.py (84 lines) – MLXModelEngine (text generation)
│   │   ├── ollama_core/
│   │   │   └── embedding_engine.py (26 lines) – OllamaEmbeddingEngine
│   │   └── musicgen_core/  # MusicGen model implementation
│   │
│   ├── core/               # Empty core utilities (future)
│   └── pipelines/          # Empty pipeline definitions (future)
│
├── examples/               # Upstream MLX examples (BERT, CLIP, Whisper, etc.)
├── experiments/            # Experimental ingestion and benchmarking scripts
├── benchmarks/             # Benchmarking results and scripts
├── tests/                  # Test suites
├── docs/                   # Existing pipeline documentation
├── ui/                     # UI components (Rich-based)
├── mlx-models/             # Model download instructions (README.md)
└── pyproject.toml          # Package configuration
```

### 2.2 Ingestion Pipeline

**Flow**: PDF → Text Extraction → Chunking → Embedding → Vector Index

```
User provides PDF(s)
    ↓
apps/ingest_cli.py
    ↓
rag.ingestion.create_vdb.gather_pdf_paths()
    ↓
rag.ingestion.create_vdb.extract_text(pdf_path)
    Uses: unstructured.partition.pdf
    ↓
rag.ingestion.create_vdb.ingest_bank()
    ↓
VectorDB.ingest(content, document_name)
    ↓
rag.retrieval.vdb.split_text_into_chunks()
    CHUNK_SIZE = 256 tokens
    CHUNK_OVERLAP = 50 tokens
    ↓
Model.run(chunks) → embeddings
    ⚠️ MISSING: rag.models.model.Model class does not exist
    Alternative: OllamaEmbeddingEngine (experiments only)
    ↓
VectorDB.embeddings ← mx.concatenate()
VectorDB.content ← [{"text": chunk, "source": doc_name}, ...]
    ↓
VectorDB.savez(vdb_path)
    Saves: embeddings, chunk_data, chunk_lengths, source_data, source_lengths
    Format: .npz (NumPy compressed archive via MLX)
    ↓
write_metadata(vdb_path)
    Creates: vdb.npz.meta.json
    Contains: bank name, chunk params, embedding model, timestamp
```

**Key Modules**:
- `src/rag/ingestion/create_vdb.py` (229 lines)
  - `extract_text()` – PDF → text via `unstructured`
  - `gather_pdf_paths()` – Collect PDFs from directories
  - `ingest_bank()` – Process single knowledge bank
  - `ingest_multiple_banks()` – Batch process subfolders
  - `write_metadata()` – Save index metadata

- `src/rag/retrieval/vdb.py` (139 lines)
  - `VectorDB` class – Vector database with NPZ storage
  - `split_text_into_chunks()` – Fixed-size chunking with overlap
  - `chunks_to_mx_array()` / `mx_array_to_chunks()` – String ↔ MLX array conversion

### 2.3 Retrieval Pipeline

**Flow**: Query → Embedding → Vector Search → Reranking → Context → LLM Response

```
User query
    ↓
apps/rag_cli.py
    ↓
VectorDB(vdb_path)
    Loads: vdb.npz → embeddings, content
    ↓
VectorDB.query(question, k=20)
    ↓
Model.run(query) → query_embedding
    ⚠️ MISSING: Uses same broken Model class
    ↓
scores = mx.matmul(query_emb, embeddings.T) * 100
    ↓
mx.argsort() → top_k_indices
    ↓
Retrieved chunks: [{"text": ..., "source": ...}, ...]
    ↓
[OPTIONAL] QwenReranker.rank(question, chunks)
    ⚠️ MISSING: rag.models.qwen_reranker.QwenReranker class referenced but not found
    Imported in apps/rag_cli.py but file does not exist
    ↓
format_context(selected_chunks)
    ↓
build_prompt(context, question)
    ↓
MLXModelEngine.generate(prompt, max_tokens=512)
    Uses: mlx_lm.generate()
    ↓
Display answer + sources
```

**Key Modules**:
- `apps/rag_cli.py` (245 lines)
  - Interactive RAG CLI with Rich UI
  - Loads VectorDB, reranker, and LLM
  - Query loop with context formatting
  - **Stateful**: Keeps models in memory across queries

- `src/rag/retrieval/query_vdb.py` (88 lines)
  - Standalone query script
  - JSON-formatted response template
  - Bank-based index loading

- `src/rag/retrieval/vdb.py` (139 lines)
  - `VectorDB.query()` – Cosine similarity search
  - Returns list of `{"text": chunk, "source": doc_name}` dicts

### 2.4 Chat / LLM Interface

**Flow**: Messages → Chat Template → MLX Model → Response

```
User message
    ↓
ChatSession.chat(message)
    ↓
messages.append(Message(Role.USER, message))
    ↓
_format_prompt(messages)
    Uses: tokenizer.chat_template (if available)
    Fallback: Manual formatting
    ↓
mlx_lm.generate() OR mlx_lm.stream_generate()
    ↓
_normalize_output(raw_response)
    Attempts JSON parsing
    Strips channel control characters
    ↓
messages.append(Message(Role.ASSISTANT, response))
    ⚠️ STATEFUL: Conversation history stored in ChatSession
    ↓
Return response
```

**Key Modules**:
- `src/rag/chat/gpt_oss_wrapper.py` (302 lines)
  - `ChatSession` class – Manages conversation history
  - `Message` dataclass – Role + content + optional tool calls
  - `Role` enum – system, user, assistant, tool
  - Supports streaming and function calling hooks (future)
  - **Critical State Issue**: Assumes persistent session across multiple turns

- `src/libs/mlx_core/model_engine.py` (84 lines)
  - `MLXModelEngine` class – Wrapper for `mlx_lm.load()` and `mlx_lm.generate()`
  - Supports text models only (extensible to other types)
  - JSON parsing fallback
  - Strips control characters

### 2.5 Embedding Models

**Current State**: **BROKEN / INCOMPLETE**

**Declared Locations**:
1. `src/rag/retrieval/vdb.py:6` → `from rag.models.model import Model`
2. `pyproject.toml` → `packages = ["rag.models", "rag.models.flux"]`

**Actual State**:
- ✗ `src/rag/models/` directory **DOES NOT EXIST**
- ✗ `rag.models.model.Model` class **NOT IMPLEMENTED**
- ✗ `rag.models.qwen_reranker.QwenReranker` class **NOT IMPLEMENTED** (referenced in `apps/rag_cli.py:16`)

**Workarounds**:
- `src/libs/ollama_core/embedding_engine.py` (26 lines) – OllamaEmbeddingEngine
  - Used in `experiments/ingestion/build_vdb_from_generated_dataset.py`
  - Calls external Ollama service (not local MLX)
  - Interface: `run(texts) → mx.array`

**Hardcoded Reference**:
- `src/rag/ingestion/create_vdb.py:42` → `"embedding_model": "vegaluisjose/mlx-rag"`
  - HuggingFace model ID (no corresponding MLX implementation found)

**Available Examples** (not integrated):
- `examples/bert/model.py` (168 lines) – BERT embeddings in MLX
  - Implements `Bert` class with `BertEmbeddings`, `TransformerEncoder`
  - Requires separate weight conversion
  - Not wired into RAG pipeline

### 2.6 Supporting Libraries

**libs/mlx_core/model_engine.py** (84 lines)
- `MLXModelEngine` – Unified wrapper for MLX text generation models
- Uses `mlx_lm.load()` and `mlx_lm.generate()`
- Output normalization (JSON parsing, text cleanup)
- Streaming support via `stream_generate()`

**libs/ollama_core/embedding_engine.py** (26 lines)
- `OllamaEmbeddingEngine` – External Ollama client for embeddings
- Not local (calls Ollama HTTP API)
- Interface mimics expected `Model.run()` signature

**libs/musicgen_core/** (6 files, ~1,500 lines)
- MusicGen model implementation (MLX port)
- EnCodec audio codec
- T5 text encoder
- Not relevant to RAG fusion

---

## 3. Fusion Primitives

These are the **core RAG operations** that must become Tier 3 FastAPI endpoints in Phase 1+.

### 3.1 `rag_upsert(documents, bank_name, options) → stats`

**Current Implementation**: `rag.ingestion.create_vdb.ingest_bank()`

**Signature** (proposed):
```python
def rag_upsert(
    documents: List[Dict[str, Any]],  # [{"content": str, "source": str, "metadata": dict}, ...]
    bank_name: str,
    options: Optional[Dict[str, Any]] = None  # {"chunk_size": 256, "chunk_overlap": 50, ...}
) → Dict[str, Any]:  # {"chunks_added": int, "documents_processed": int, "index_path": str}
```

**Required Changes** (Phase 1):
- Remove filesystem assumptions (no `Path.rglob()`)
- Accept in-memory documents (base64-encoded PDFs or pre-extracted text)
- Decouple PDF extraction from ingestion (extract upstream in Tier 2)
- Make embedding model configurable (env var or parameter)
- Return structured stats (no console output)
- Support incremental updates (append to existing index)

**Current Dependencies**:
- `unstructured[pdf]` – PDF extraction (move to Tier 2?)
- `mlx-data` – Data pipeline (currently unused due to bugs)
- `rag.models.model.Model` – **MISSING** (must implement first)

**Stateful Issues**:
- Writes to `var/indexes/<bank_name>/vdb.npz` (hardcoded path)
- Creates `.meta.json` sidecar files (assumes filesystem)

### 3.2 `rag_query(query, bank_name, options) → results`

**Current Implementation**: `rag.retrieval.vdb.VectorDB.query()`

**Signature** (proposed):
```python
def rag_query(
    query: str,
    bank_name: str,
    options: Optional[Dict[str, Any]] = None  # {"top_k": 5, "rerank": True, "threshold": 0.5}
) → List[Dict[str, Any]]:  # [{"text": str, "source": str, "score": float, "metadata": dict}, ...]
```

**Required Changes** (Phase 1):
- Remove LLM response generation (return raw chunks only)
- Make reranking optional (move QwenReranker to optional dependency)
- Accept bank_name parameter (resolve to index path via config)
- Return scores with results
- Support metadata filtering (future)

**Current Dependencies**:
- `rag.models.model.Model` – **MISSING** (query embeddings)
- `rag.models.qwen_reranker.QwenReranker` – **MISSING** (optional reranking)
- `mlx.core` – Vector operations

**Stateful Issues**:
- Loads entire index into memory (VectorDB instance)
- No pooling/caching strategy for multiple queries

### 3.3 `rag_stats(bank_name) → stats`

**Current Implementation**: **NONE** (must create)

**Signature** (proposed):
```python
def rag_stats(bank_name: str) → Dict[str, Any]:
    # {
    #   "bank_name": str,
    #   "num_chunks": int,
    #   "num_documents": int,
    #   "chunk_size": int,
    #   "chunk_overlap": int,
    #   "embedding_model": str,
    #   "embedding_dim": int,
    #   "created_at": str,
    #   "updated_at": str,
    #   "index_size_bytes": int
    # }
```

**Implementation Notes**:
- Read from `.meta.json` if available
- Lazy-load index to get embedding shape
- Add index size calculation
- Cache stats (update on upsert only)

### 3.4 `embeddings_create(texts, model_id) → embeddings` (Optional)

**Current Implementation**: `Model.run()` (missing) or `OllamaEmbeddingEngine.embed()`

**Signature** (proposed):
```python
def embeddings_create(
    texts: List[str],
    model_id: Optional[str] = None  # Default from env
) → Dict[str, Any]:
    # {
    #   "embeddings": List[List[float]],  # OR base64-encoded array
    #   "model": str,
    #   "dimensions": int
    # }
```

**Decision Point**:
- Should this be in Tier 3B (RAG) or Tier 3A (MLX OpenAI Server)?
- If duplicated, ensure consistent embedding models across tiers

---

## 4. State Considerations

### 4.1 Current Stateful Patterns

**ChatSession** (`src/rag/chat/gpt_oss_wrapper.py:44`)
```python
class ChatSession:
    def __init__(self, model_id, system_prompt=None, ...):
        self.model, self.tokenizer = load(model_id)
        self.messages: List[Message] = []  # ← Conversation history in memory
```
- **Issue**: Assumes persistent session across multiple user turns
- **Fusion Impact**: Cannot use for stateless API (Tier 3)
- **Solution**: Move conversation history to Tier 2 (MCP) or client-side
- **Phase 1 Action**: Extract stateless `format_and_generate(messages, model)` function

**VectorDB Instance** (`src/rag/retrieval/vdb.py:62`)
```python
class VectorDB:
    def __init__(self, vdb_file=None):
        if vdb_file:
            vdb = mx.load(vdb_file)
            self.embeddings = vdb["embeddings"]  # ← Entire index in memory
            self.content = [...]
```
- **Issue**: Loads entire index into GPU memory on init
- **Fusion Impact**: No pooling or lazy loading for multiple banks
- **Solution**: Implement index pool with LRU eviction
- **Phase 1 Action**: Add configurable index cache (max_banks, max_memory)

**Hardcoded Filesystem Paths**
- `var/indexes/` – Vector index storage
- `var/voice_chat/` – Audio response storage
- `var/source_audios/` – Input audio storage
- `mlx-models/` – Model weight downloads

**Environment Dependencies**
- Assumes local MLX models in `~/.cache/huggingface/`
- No remote model serving
- Requires Apple Silicon (Metal GPU)

### 4.2 What Is Already Stateless

**Text Chunking** (`src/rag/retrieval/vdb.py:13`)
```python
def split_text_into_chunks(text, chunk_size, overlap):
    # Pure function: text → chunks
```

**Embedding Encoding** (when implemented)
```python
Model.run(texts: List[str]) → mx.array
# Pure function: texts → embeddings
```

**Vector Search** (`src/rag/retrieval/vdb.py:98`)
```python
def query(self, text: str, k: int = 3) → List[Dict[str, str]]:
    query_emb = self.model.run(text)
    scores = mx.matmul(query_emb, self.embeddings.T) * 100
    # Pure computation (assuming self.embeddings is immutable)
```

### 4.3 Required Changes for Tier 3 Statelessness

1. **Remove ChatSession dependency**
   - Extract `generate_response(prompt, model_id, max_tokens)` function
   - Accept pre-formatted prompts (history managed by Tier 2)

2. **Implement VectorDB connection pool**
   - LRU cache for loaded indexes
   - Configurable memory budget
   - Thread-safe access

3. **Environment-based configuration**
   - `EMBEDDING_MODEL_ID` (default: HF model path)
   - `INDEX_ROOT_PATH` (default: `var/indexes`)
   - `MAX_INDEX_CACHE_SIZE` (default: 3 banks in memory)
   - `CHUNK_SIZE`, `CHUNK_OVERLAP` (default: 256, 50)

4. **Structured error handling**
   - No `console.print()` in library code
   - Return typed responses with error codes
   - Log to structured logger (not stdout)

5. **Remove mlx.data dependency** (currently broken)
   - Sequential PDF processing works fine
   - Defer mlx.data integration to Phase 2 optimization

---

## 5. Cloud/Local Dependencies

### 5.1 Local-Only Dependencies (Apple Silicon Required)

**MLX Framework** (`mlx~=0.29.3`)
- Metal GPU acceleration
- Requires macOS 13.3+ with Apple Silicon (M1/M2/M3/M4)
- No CPU fallback

**MLX-LM** (`mlx-lm`)
- Text generation models (Phi-3, GPT-OSS, etc.)
- Model loading: `mlx_lm.load(model_id)` → reads from `~/.cache/huggingface/`

**MLX-Data** (`mlx-data>=0.2.0`)
- Data pipeline framework (currently broken, not used)

### 5.2 HuggingFace Model Dependencies

**Embedding Model** (declared but not implemented)
- `vegaluisjose/mlx-rag` – HF model ID in metadata
- No corresponding MLX weights or loader

**LLM Models** (user-configurable)
- Default: `mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit`
- Alternative: `mlx-community/NeuralBeagle14-7B-4bit-mlx`
- Alternative: `mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx`

**Reranker Model** (missing implementation)
- `mlx-community/mxbai-rerank-large-v2` – Cross-encoder for reranking

**Tokenizers** (`transformers~=4.57.1`)
- HuggingFace tokenizers for all models
- Chat templates (if available)

### 5.3 External Service Dependencies

**Ollama** (optional, experiments only)
- `ollama` Python client
- Requires external Ollama server (HTTP API)
- Used in `experiments/ingestion/build_vdb_from_generated_dataset.py`
- **NOT** part of production RAG pipeline

**Unstructured** (`unstructured[pdf]~=0.18.15`)
- PDF text extraction
- May download models on first use
- Should be moved to Tier 2 (MCP) for fusion

### 5.4 Configurable Paths (Phase 1 Requirements)

**Model Weights**
- Current: `~/.cache/huggingface/hub/models--<org>--<name>/`
- Needed: `HUGGINGFACE_HUB_CACHE` env var (already supported)

**Vector Indexes**
- Current: `var/indexes/<bank_name>/vdb.npz`
- Needed: `INDEX_ROOT_PATH` env var

**Audio Files** (not relevant to RAG fusion)
- `var/voice_chat/`, `var/source_audios/`
- Keep as-is (not part of Tier 3B)

---

## 6. Fusion Gaps

### 6.1 Critical Gaps (Phase 1 Blockers)

1. **Missing Embedding Model Implementation**
   - `rag.models.model.Model` class declared but not implemented
   - VectorDB imports this class but it does not exist
   - **Impact**: Document ingestion and querying are completely broken
   - **Solution**: Implement MLX-based embedding model (BERT or sentence-transformers port)
   - **Estimated Effort**: 2-3 days (adapt `examples/bert/model.py`)

2. **Missing Reranker Implementation**
   - `rag.models.qwen_reranker.QwenReranker` referenced but not implemented
   - apps/rag_cli.py imports it (line 16) but file does not exist
   - **Impact**: Reranking step fails (workaround: use `--no-reranker` flag)
   - **Solution**: Implement cross-encoder reranker in MLX or make optional
   - **Estimated Effort**: 3-4 days (new model architecture)

3. **ChatSession is Stateful**
   - Conversation history stored in memory
   - Cannot be used in stateless Tier 3 API
   - **Impact**: Chat functionality must be redesigned
   - **Solution**: Extract stateless prompt formatting + generation function
   - **Estimated Effort**: 1 day

4. **No FastAPI Skeleton**
   - Repository has CLI tools only
   - No HTTP API layer
   - **Impact**: Cannot integrate with Tier 2 (MCP) yet
   - **Solution**: Create minimal FastAPI app with health check
   - **Estimated Effort**: 1 day

5. **Hardcoded File Paths**
   - All indexes stored in `var/indexes/`
   - No environment-based configuration
   - **Impact**: Cannot deploy to containerized environment
   - **Solution**: Replace all hardcoded paths with env vars
   - **Estimated Effort**: 1 day

### 6.2 High Priority Gaps (Phase 1 Nice-to-Have)

6. **No Stats Endpoint**
   - Must implement `rag_stats()` from scratch
   - Read metadata from `.meta.json` or index
   - **Estimated Effort**: 0.5 day

7. **No Index Pooling / Caching**
   - Each query loads entire index into memory
   - No LRU eviction for multiple banks
   - **Impact**: Memory usage grows unbounded
   - **Solution**: Implement configurable index cache
   - **Estimated Effort**: 2 days

8. **No Structured Error Handling**
   - Code uses `console.print()` for errors
   - No HTTP status codes or typed exceptions
   - **Impact**: Cannot return proper API responses
   - **Solution**: Define error schema + FastAPI exception handlers
   - **Estimated Effort**: 1 day

9. **PDF Extraction in Wrong Tier**
   - `unstructured[pdf]` used in Tier 3B (RAG engine)
   - Should be in Tier 2 (MCP orchestration)
   - **Impact**: Tier 3B has unnecessary dependency
   - **Solution**: Accept pre-extracted text in `rag_upsert()`
   - **Estimated Effort**: 1 day (refactor ingestion interface)

### 6.3 Medium Priority Gaps (Phase 2)

10. **No Incremental Index Updates**
    - `VectorDB.savez()` overwrites entire index
    - Cannot append new documents efficiently
    - **Impact**: Re-indexing full banks on every update
    - **Solution**: Implement append mode or index merging
    - **Estimated Effort**: 2-3 days

11. **No Metadata Filtering**
    - Queries return chunks without filtering by document type, date, etc.
    - **Impact**: Cannot implement filtered search
    - **Solution**: Add metadata fields to chunks, filter in query
    - **Estimated Effort**: 2 days

12. **No Multi-Bank Querying**
    - Each query targets a single bank
    - **Impact**: Cannot search across all knowledge
    - **Solution**: Implement federated search with score normalization
    - **Estimated Effort**: 3 days

13. **mlx.data Pipeline Broken**
    - Sequential processing works, but mlx.data pipeline has string/bytes issues
    - **Impact**: Cannot leverage MLX data prefetching
    - **Solution**: Debug mlx.data or remove dependency
    - **Estimated Effort**: 2-4 days (upstream bug?)

### 6.4 Low Priority Gaps (Phase 3+)

14. **No Semantic Caching**
    - Repeated queries re-compute embeddings
    - **Solution**: Cache query embeddings (short TTL)
    - **Estimated Effort**: 1 day

15. **No Hybrid Search**
    - Dense retrieval only (no BM25/keyword search)
    - **Solution**: Add optional BM25 reranking
    - **Estimated Effort**: 3 days

16. **No Async Support**
    - All operations are synchronous
    - **Solution**: Wrap MLX calls in asyncio executor
    - **Estimated Effort**: 2 days

---

## 7. File-by-File Architecture Map

### 7.1 Core RAG Files

| File Path | Lines | Purpose | Fusion Role | Gaps |
|-----------|-------|---------|-------------|------|
| `src/rag/ingestion/create_vdb.py` | 229 | PDF extraction, chunking, embedding, index creation | Core `rag_upsert()` logic | Missing Model class, hardcoded paths |
| `src/rag/retrieval/vdb.py` | 139 | VectorDB class, chunking, query | Core `rag_query()` logic | Missing Model class, no caching |
| `src/rag/retrieval/query_vdb.py` | 88 | Standalone query script | Reference implementation | Couples retrieval + LLM response |
| `apps/rag_cli.py` | 245 | Interactive RAG CLI | Demo of full pipeline | Stateful (keeps models in memory) |
| `apps/ingest_cli.py` | 105 | Ingestion CLI wrapper | Demo of ingestion | Filesystem-based |

### 7.2 Supporting Files

| File Path | Lines | Purpose | Fusion Role | Notes |
|-----------|-------|---------|-------------|-------|
| `src/libs/mlx_core/model_engine.py` | 84 | MLX text generation wrapper | LLM response generation | Stateless, good candidate for Tier 3A |
| `src/libs/ollama_core/embedding_engine.py` | 26 | Ollama embedding client | Alternative embedding backend | External dependency (not local) |
| `src/rag/chat/gpt_oss_wrapper.py` | 302 | Chat session management | NOT used in RAG (separate domain) | Stateful, must extract stateless function |
| `src/rag/chat/templates.py` | 66 | Prompt templates, string utils | Shared utilities | Stateless, can keep |
| `src/rag/cli/entrypoints.py` | 43 | Console script wrappers | Package entrypoints | Not needed in API |

### 7.3 Non-RAG Files (Exclude from Fusion)

These files are part of the multi-domain MLX lab but **NOT** part of the RAG engine fusion:

| Domain | Files | Lines | Purpose |
|--------|-------|-------|---------|
| **Voice/Audio** | `src/rag/stt/whisperx_client.py` | 290 | WhisperX STT client |
| | `src/rag/tts/kokoro_tts.py` | 233 | Kokoro TTS wrapper |
| | `src/rag/tts/marvis_tts.py` | 300 | Marvis TTS wrapper |
| | `src/rag/tts/viseme_mapper.py` | 285 | Viseme generation for avatars |
| | `apps/voice_chat_cli.py` | 545 | Voice chat CLI |
| | `apps/sts_avatar_cli.py` | 745 | Speech-to-speech avatar CLI |
| | `apps/whisper_cli.py` | 175 | Whisper transcription CLI |
| **Imaging** | `src/rag/cli/flux_txt2image.py` | 196 | Flux text-to-image generation |
| | `src/rag/cli/flux_dreambooth.py` | 298 | Flux DreamBooth training |
| | `src/rag/cli/flux.py` | 21 | Flux utilities |
| | `apps/flux_cli.py` | 75 | Flux CLI wrapper |
| **Music** | `src/libs/musicgen_core/*` | ~1,500 | MusicGen model implementation |
| | `src/rag/cli/generate_music.py` | 36 | Music generation script |
| | `apps/musicgen_cli.py` | 233 | MusicGen CLI |
| **Benchmarking** | `src/rag/cli/benchmark.py` | 97 | Benchmark utilities |
| | `apps/bench_cli.py` | 26 | Benchmark CLI |
| | `benchmarks/*` | ~500 | Benchmark results and scripts |
| **Classification** | `apps/classify_cli.py` | 405 | Text classification CLI |
| **Chat** | `apps/chat_cli.py` | 447 | Text chat CLI |
| **Launcher** | `apps/mlxlab_cli.py` | 1,879 | Unified CLI launcher menu |

**Fusion Strategy**: These files should remain in mlx-rag-lab but are **out of scope** for Tier 3B RAG API. They may become separate microservices (Tier 3C, 3D, etc.) or remain as CLI tools.

### 7.4 Example Files (Reference Only)

The `examples/` directory contains upstream MLX examples (not custom code):
- `examples/bert/model.py` (168 lines) – BERT embeddings (can be adapted)
- `examples/clip/model.py` – CLIP embeddings
- `examples/whisper/` – Whisper STT reference
- `examples/lora/` – LoRA fine-tuning
- `examples/segment_anything/` – SAM model

**Fusion Note**: The BERT example is the **closest reference** for implementing the missing `rag.models.model.Model` class.

---

## 8. Critical Risks

### 8.1 Broken Core Functionality

**Risk**: The RAG pipeline **cannot run** in its current state.
- `VectorDB.__init__()` imports `rag.models.model.Model` which does not exist
- Any attempt to run `ingest_cli.py` or `rag_cli.py` will fail with `ModuleNotFoundError`

**Evidence**:
```python
# src/rag/retrieval/vdb.py:6
from rag.models.model import Model  # ← This import fails
```

**Mitigation**:
- Verify if there's a working branch or commit with Model implementation
- Check if Model is in a different location (symlink, alternate package name)
- If truly missing, implement BERT-based embeddings as Phase 1 priority

### 8.2 Package Configuration Mismatch

**Risk**: `pyproject.toml` declares packages that don't exist in the filesystem.

**Evidence**:
```toml
packages = [
    "rag.models",        # ← Directory does not exist
    "rag.models.flux",   # ← Directory does not exist
]
```

**Impact**: Package installation may succeed but imports will fail at runtime.

**Mitigation**: Remove non-existent packages from `pyproject.toml` or create stub `__init__.py` files.

### 8.3 Mixed Concerns (RAG + Voice + Imaging)

**Risk**: Repository has conflated multiple domains (RAG, TTS, STT, Flux, MusicGen) into one package.

**Impact**:
- Unclear scope for Tier 3B fusion
- Dependencies pulled in for non-RAG features
- Potential confusion about what gets deployed

**Mitigation**:
- Clearly document which modules are RAG-only
- Consider splitting into separate packages in Phase 2
- Use optional dependencies for non-RAG features

### 8.4 No Test Coverage for RAG

**Risk**: No tests found for RAG ingestion or retrieval.

**Evidence**:
- `tests/` directory exists but no RAG-specific tests visible
- No CI/CD configuration found

**Impact**: Cannot verify RAG functionality works before refactoring.

**Mitigation**: Add minimal smoke tests in Phase 1 (ingest sample doc, query, verify results).

### 8.5 Unstructured Dependency Size

**Risk**: `unstructured[pdf]` has large dependency tree (tesseract, poppler, etc.).

**Impact**:
- Slow container builds
- Potential conflicts with MLX environment
- Should be in Tier 2 (MCP), not Tier 3B

**Mitigation**: Move PDF extraction to Tier 2 in Phase 1. Accept pre-extracted text in `rag_upsert()`.

---

## 9. Open Questions

1. **Where is the Model class?**
   - Is there a working branch with `rag.models.model.Model` implemented?
   - Was it accidentally deleted or never completed?
   - Should we use BERT example as template?

2. **Embedding model strategy**
   - Use local MLX BERT/sentence-transformers port?
   - Use external Ollama (breaks local-first constraint)?
   - Use HuggingFace transformers (slower, not Metal-optimized)?

3. **Reranker necessity**
   - Is reranking critical for production RAG?
   - Can we defer to Phase 2?
   - Should it be optional (flag in query options)?

4. **Multi-domain future**
   - Should voice/imaging features stay in this repo?
   - Split into separate packages (mlx-rag, mlx-voice, mlx-imaging)?
   - Or keep as unified MLX lab?

5. **Tier 3A vs Tier 3B overlap**
   - Should embeddings generation be in RAG engine (3B) or OpenAI server (3A)?
   - Should LLM response generation stay in RAG or move to 3A?
   - Where does reranking live?

6. **Index storage format**
   - Continue using NPZ (NumPy archives)?
   - Migrate to FAISS, Hnswlib, or other vector DB?
   - Keep simple for Phase 1, optimize in Phase 2?

7. **Model download strategy**
   - Require manual model download before API start?
   - Auto-download on first request (slow first call)?
   - Preload models in container build?

8. **Apple Silicon requirement**
   - Can Tier 3B run on non-Apple hardware (CPU-only MLX)?
   - Or is Metal GPU mandatory?
   - What's the fallback for cloud deployment (if any)?

---

## 10. Recommended Phase 1 Actions

See `docs/HANDOFFS.md` for the full prioritized Phase 1 TODO list.

**Summary**:
1. Implement `rag.models.model.Model` class (BERT-based embeddings)
2. Create FastAPI skeleton with health check
3. Implement `/rag_upsert` endpoint (stateless document ingestion)
4. Implement `/rag_query` endpoint (stateless retrieval, no LLM response)
5. Implement `/rag_stats` endpoint
6. Add environment-based configuration (paths, model IDs)
7. Remove `ChatSession` dependency from RAG pipeline
8. Add structured error handling
9. Add minimal smoke tests
10. Document API schema (OpenAPI spec)

---

**End of FUSION_PHASE0.md**

# HANDOFFS.md – mlx-rag-lab Phase 0

---

## Phase 0 – Session 1

**Date**: 2025-11-16
**Branch**: `claude/phase0-rag-mapping-01E8y3ueFLDFNa2KZPBy3jdr`
**Tier**: 3B (RAG Engine – chunking, embeddings, document ingestion, retrieval, stats)
**Session Type**: Deep Mapping (ZERO code changes, documentation only)

### Summary of What Was Mapped

This Phase 0 session conducted a comprehensive architectural analysis of **mlx-rag-lab** to understand its role as Tier 3B (RAG Engine) in the 3-tier local-first fusion architecture. The repository was explored in detail to identify:

1. **All entrypoints** – 11 CLI applications (rag_cli, ingest_cli, chat_cli, voice_chat_cli, sts_avatar_cli, flux_cli, musicgen_cli, whisper_cli, classify_cli, bench_cli, mlxlab_cli)
2. **Core RAG modules** – Ingestion pipeline (`create_vdb.py`), retrieval engine (`vdb.py`, `query_vdb.py`), and supporting libraries
3. **Fusion primitives** – The critical functions that must become stateless API endpoints: `rag_upsert()`, `rag_query()`, `rag_stats()`
4. **State patterns** – Identified stateful components (ChatSession, VectorDB instance caching, hardcoded file paths) that prevent Tier 3 deployment
5. **Dependencies** – Mapped local MLX dependencies, HuggingFace models, external services, and configuration requirements
6. **Gaps** – Discovered **critical missing implementations** (embedding model, reranker) and architectural issues (mixed concerns, no API layer)

### Key Findings (Critical Issues)

1. **Missing Embedding Model Implementation (BLOCKER)**
   - `rag.models.model.Model` class is imported in `src/rag/retrieval/vdb.py:6` but **does not exist**
   - The `src/rag/models/` directory is **not present** in the filesystem
   - `pyproject.toml` declares `rag.models` package, but it's not implemented
   - **Impact**: Document ingestion and querying are completely broken (cannot run)
   - **Evidence**: `from rag.models.model import Model` will fail with `ModuleNotFoundError`
   - **Root Cause**: Code was written assuming this module exists, but it was never implemented

2. **Missing Reranker Implementation (HIGH)**
   - `rag.models.qwen_reranker.QwenReranker` is imported in `apps/rag_cli.py:16` but **does not exist**
   - Reranking step will fail unless `--no-reranker` flag is used
   - **Impact**: Cannot use reranking to improve retrieval quality
   - **Workaround**: Pass `--no-reranker` flag to RAG CLI

3. **Repository is Multi-Domain, Not Pure RAG**
   - Contains RAG (ingestion, retrieval), Voice (STT/TTS), Imaging (Flux), Music (MusicGen), and Chat
   - ~60% of code is non-RAG (voice_chat, sts_avatar, flux, musicgen, etc.)
   - **Impact**: Unclear scope for Tier 3B fusion—must separate RAG from other domains
   - **Decision Needed**: Keep as unified MLX lab or split into separate packages?

4. **ChatSession is Stateful**
   - `src/rag/chat/gpt_oss_wrapper.py:44` stores conversation history in memory (`self.messages`)
   - Cannot be used in stateless Tier 3 API
   - **Impact**: Must extract stateless prompt formatting function for RAG responses

5. **No FastAPI API Layer**
   - Repository has CLI tools only (no HTTP server)
   - **Impact**: Cannot integrate with Tier 2 (MCP) until API skeleton is created

6. **Hardcoded Filesystem Paths**
   - All indexes stored in `var/indexes/` (hardcoded)
   - Audio files in `var/voice_chat/`, `var/source_audios/`
   - **Impact**: Cannot deploy to containerized environment without env-based config

7. **PDF Extraction in Wrong Tier**
   - `unstructured[pdf]` is used in Tier 3B (RAG engine)
   - Should be in Tier 2 (MCP orchestration layer)
   - **Impact**: Tier 3B has unnecessary large dependency (tesseract, poppler, etc.)

8. **No Index Pooling or Caching**
   - Each query loads entire index into GPU memory
   - No LRU eviction for multiple knowledge banks
   - **Impact**: Memory usage grows unbounded with multiple banks

9. **No Test Coverage for RAG**
   - No tests found for ingestion or retrieval pipelines
   - **Impact**: Cannot verify functionality before refactoring

10. **Package Configuration Mismatch**
    - `pyproject.toml` declares `rag.models` and `rag.models.flux` packages
    - These directories do not exist in the filesystem
    - **Impact**: Package installation succeeds but imports fail at runtime

11. **Embedding Model Inconsistency**
    - Metadata references `vegaluisjose/mlx-rag` HuggingFace model (hardcoded in `create_vdb.py:42`)
    - No corresponding MLX implementation found
    - Experiments use `OllamaEmbeddingEngine` instead (external HTTP service, not local)
    - **Impact**: No clear embedding strategy for production

12. **Mixed Stateless and Stateful Patterns**
    - Chunking and vector search are stateless (good)
    - VectorDB instance, ChatSession, and file paths are stateful (bad)
    - **Impact**: Need surgical refactoring to separate concerns

### Critical Risks

1. **Broken Core Functionality**
   - RAG pipeline cannot run due to missing `rag.models.model.Model` class
   - This is a **showstopper** for any testing or validation
   - **Mitigation**: Implement BERT-based embeddings immediately (Priority 1)

2. **No Clear Ownership**
   - Repository mixes RAG, voice, imaging, and music generation
   - Unclear which team owns which domain
   - **Risk**: Scope creep, conflicting priorities
   - **Mitigation**: Define clear boundaries (RAG only for Tier 3B)

3. **Apple Silicon Lock-In**
   - MLX requires macOS 13.3+ with Apple Silicon (M1/M2/M3/M4)
   - No CPU fallback, no cloud deployment option
   - **Risk**: Cannot run on standard cloud infrastructure
   - **Mitigation**: Document hardware requirements, consider CPU fallback in Phase 2

4. **Large Dependency Footprint**
   - `unstructured[pdf]` pulls in tesseract, poppler, etc. (hundreds of MB)
   - Slows container builds, conflicts with MLX environment
   - **Risk**: Deployment complexity
   - **Mitigation**: Move to Tier 2 (MCP) in Phase 1

5. **No API Contract**
   - No OpenAPI spec, no typed request/response schemas
   - **Risk**: Integration with Tier 2 will require trial-and-error
   - **Mitigation**: Define API schema in Phase 1 before implementation

### Open Questions

1. **Where is the Model class?**
   - Was it implemented in a different branch?
   - Was it accidentally deleted?
   - Or was it never completed?
   - **Action**: Check git history for `rag/models/model.py`

2. **Embedding Strategy**
   - Should we use local MLX BERT (from `examples/bert/model.py`)?
   - Or use external Ollama (breaks local-first constraint)?
   - Or use HuggingFace transformers (slower, not Metal-optimized)?
   - **Decision Needed**: Prioritize local MLX for Phase 1

3. **Reranker Necessity**
   - Is cross-encoder reranking critical for production RAG?
   - Can we defer to Phase 2?
   - Or make it optional (query parameter)?
   - **Decision**: Make optional in Phase 1

4. **Multi-Domain Future**
   - Keep voice/imaging/music in this repo?
   - Or split into separate packages (mlx-rag, mlx-voice, mlx-imaging)?
   - **Decision**: Document non-RAG modules as out-of-scope for Tier 3B

5. **Tier 3A vs Tier 3B Overlap**
   - Should embeddings generation be in RAG engine (3B) or OpenAI server (3A)?
   - Should LLM response generation stay in RAG or move to 3A?
   - **Decision**: RAG engine returns chunks only (no LLM response), embeddings stay in 3B

6. **Index Storage Format**
   - Continue using NPZ (NumPy archives via MLX)?
   - Or migrate to FAISS, Hnswlib, or other vector DB?
   - **Decision**: Keep NPZ for Phase 1, evaluate alternatives in Phase 2

7. **Model Preloading**
   - Require manual model download before API start?
   - Or auto-download on first request (slow first call)?
   - **Decision**: Document model download requirements, add health check to verify

8. **Cloud Deployment**
   - Can Tier 3B run on non-Apple hardware (CPU-only MLX)?
   - Or is Metal GPU mandatory?
   - **Decision**: Metal required for Phase 1, CPU fallback in Phase 2 if feasible

---

## Phase 1 – TODO (RAG Engine)

This is the **prioritized task list** for transforming mlx-rag-lab into a production-ready Tier 3B RAG Engine with stateless FastAPI endpoints.

### Priority 1 (Critical – Must Complete)

These are **blockers** that prevent any Tier 3 integration. Phase 1 cannot proceed without these.

1. **Implement `rag.models.model.Model` class**
   - Create `src/rag/models/__init__.py`
   - Create `src/rag/models/model.py` with `Model` class
   - Interface: `run(texts: List[str]) → mx.array` (embeddings)
   - Use `examples/bert/model.py` as reference implementation
   - Default model: BERT-based sentence embeddings (e.g., `sentence-transformers/all-MiniLM-L6-v2` port to MLX)
   - Add model loading from HuggingFace or local weights
   - **Estimated Effort**: 2-3 days
   - **Validation**: Run `ingest_cli.py` and `rag_cli.py` without errors

2. **Create FastAPI skeleton with health check**
   - Create `src/rag/api/__init__.py`
   - Create `src/rag/api/main.py` with FastAPI app
   - Add `GET /health` endpoint (returns `{"status": "ok", "models_loaded": bool}`)
   - Add basic CORS and error handling
   - Add structured logging (not console.print)
   - **Estimated Effort**: 1 day
   - **Validation**: `curl http://localhost:8000/health` returns 200

3. **Implement `POST /rag_upsert` endpoint**
   - Convert `rag.ingestion.create_vdb.ingest_bank()` to stateless function
   - Accept request body: `{"documents": [{"content": str, "source": str}], "bank_name": str, "options": {...}}`
   - Return response: `{"chunks_added": int, "documents_processed": int, "bank_name": str}`
   - Remove PDF extraction (accept pre-extracted text only)
   - Use env var for index root path (`INDEX_ROOT_PATH`)
   - Add structured error responses (400, 500)
   - **Estimated Effort**: 2 days
   - **Validation**: POST sample document, verify index created in `INDEX_ROOT_PATH/<bank_name>/vdb.npz`

4. **Implement `POST /rag_query` endpoint**
   - Convert `rag.retrieval.vdb.VectorDB.query()` to stateless function
   - Accept request body: `{"query": str, "bank_name": str, "options": {"top_k": int, "rerank": bool}}`
   - Return response: `{"results": [{"text": str, "source": str, "score": float}]}`
   - Do NOT generate LLM response (return chunks only)
   - Make reranking optional (skip if not implemented)
   - Use env var for index root path
   - **Estimated Effort**: 1.5 days
   - **Validation**: POST query, verify top-k chunks returned with sources

5. **Remove or isolate all stateful ChatSession patterns**
   - Extract stateless `format_prompt(messages, template)` function from `gpt_oss_wrapper.py`
   - Extract stateless `generate_response(prompt, model_id, max_tokens)` function
   - Document that conversation history is managed by Tier 2 (MCP)
   - **Estimated Effort**: 1 day
   - **Validation**: No class instances persist across API requests

6. **Introduce environment-based configuration**
   - Add `src/rag/config/settings.py` with Pydantic BaseSettings
   - Environment variables:
     - `INDEX_ROOT_PATH` (default: `var/indexes`)
     - `EMBEDDING_MODEL_ID` (default: local BERT path)
     - `MAX_INDEX_CACHE_SIZE` (default: 3)
     - `CHUNK_SIZE` (default: 256)
     - `CHUNK_OVERLAP` (default: 50)
   - Replace all hardcoded paths with settings
   - **Estimated Effort**: 1 day
   - **Validation**: Start API with env vars, verify paths used

7. **Add structured error handling**
   - Define typed exceptions: `EmbeddingError`, `IndexNotFoundError`, `InvalidRequestError`
   - Add FastAPI exception handlers
   - Return proper HTTP status codes (400, 404, 500)
   - Remove all `console.print()` from library code
   - Use structured logger (`logging` module)
   - **Estimated Effort**: 1 day
   - **Validation**: Trigger error (e.g., query missing bank), verify JSON error response

### Priority 2 (High – Phase 1 Targets)

These enable production use and Tier 2 integration.

8. **Implement `GET /rag_stats` endpoint**
   - Accept query param: `bank_name`
   - Return: `{"bank_name": str, "num_chunks": int, "num_documents": int, "chunk_size": int, "embedding_model": str, "created_at": str}`
   - Read from `.meta.json` if available
   - Lazy-load index to get embedding shape if metadata missing
   - **Estimated Effort**: 0.5 day
   - **Validation**: GET stats for existing bank, verify correct counts

9. **Create unified VectorDB index pool with LRU eviction**
   - Create `src/rag/retrieval/index_pool.py`
   - Implement `IndexPool` class with configurable max size (env var)
   - Thread-safe access (asyncio-compatible locks)
   - LRU eviction when memory budget exceeded
   - **Estimated Effort**: 2 days
   - **Validation**: Query multiple banks, verify only N loaded in memory

10. **Create module_contracts for Tier 2 integration**
    - Define API contract (OpenAPI spec) in `docs/API_SPEC.md`
    - Document request/response schemas (JSON)
    - Document error codes and retry behavior
    - Document model download requirements
    - **Estimated Effort**: 1 day
    - **Validation**: Generate OpenAPI spec from FastAPI app

11. **Add minimal smoke tests**
    - Create `tests/test_rag_api.py`
    - Test: Ingest sample document, query it, verify chunks returned
    - Test: Query non-existent bank, verify 404 error
    - Test: Health check returns 200
    - Use pytest + FastAPI TestClient
    - **Estimated Effort**: 1.5 days
    - **Validation**: `pytest tests/test_rag_api.py` passes

12. **Remove unstructured[pdf] dependency from Tier 3B**
    - Refactor `rag_upsert()` to accept pre-extracted text only
    - Document that PDF extraction happens in Tier 2 (MCP)
    - Move PDF extraction examples to `experiments/` or separate script
    - **Estimated Effort**: 1 day
    - **Validation**: `pyproject.toml` no longer lists `unstructured[pdf]` in core dependencies

### Priority 3 (Medium – Phase 2 Preparation)

These improve robustness and performance.

13. **Add health checks for model availability**
    - Extend `GET /health` to verify embedding model loaded
    - Add optional `GET /health/ready` (models loaded + index accessible)
    - Return model metadata (name, dimensions, status)
    - **Estimated Effort**: 0.5 day

14. **Implement optional reranker support**
    - Create `src/rag/models/qwen_reranker.py` (stub or full implementation)
    - If not implemented, gracefully skip reranking when `rerank: true` requested
    - Return warning in response if reranker unavailable
    - **Estimated Effort**: 3-4 days (full implementation) OR 0.5 day (stub)

15. **Add incremental index updates (append mode)**
    - Modify `VectorDB.savez()` to support append (not overwrite)
    - Or implement index merging function
    - Update metadata with `updated_at` timestamp
    - **Estimated Effort**: 2-3 days

16. **Add metadata fields to chunks**
    - Extend chunk storage to include: `{"text": str, "source": str, "metadata": dict}`
    - Support metadata filtering in query (e.g., filter by date, document type)
    - **Estimated Effort**: 2 days

17. **Add optional semantic caching for queries**
    - Cache query embeddings with short TTL (e.g., 5 minutes)
    - Use LRU cache for repeated queries
    - **Estimated Effort**: 1 day

### Priority 4 (Low – Future Enhancements)

These are nice-to-have optimizations for Phase 3+.

18. **Implement async support for API endpoints**
    - Wrap MLX calls in `asyncio.to_thread()` or `run_in_executor()`
    - Enable concurrent query processing
    - **Estimated Effort**: 2 days

19. **Add hybrid search (dense + sparse)**
    - Implement optional BM25 reranking
    - Combine dense (vector) and sparse (keyword) scores
    - **Estimated Effort**: 3 days

20. **Add multi-bank federated search**
    - Allow querying across multiple banks in single request
    - Normalize scores across banks
    - **Estimated Effort**: 3 days

21. **Debug or remove mlx.data dependency**
    - Current issue: String/bytes handling broken in mlx.data pipeline
    - Options: Fix upstream bug OR remove dependency entirely
    - **Estimated Effort**: 2-4 days (if debugging) OR 0.5 day (if removing)

22. **Add Prometheus metrics endpoint**
    - Track: API requests, latency, index size, cache hit rate
    - Export as `GET /metrics` (Prometheus format)
    - **Estimated Effort**: 1 day

23. **Create Dockerfile and docker-compose setup**
    - Multi-stage build for smaller image
    - Preload models in build step
    - Volume mount for indexes
    - **Estimated Effort**: 1 day

24. **Add API authentication (optional)**
    - API key authentication for production use
    - Rate limiting per client
    - **Estimated Effort**: 1.5 days

25. **Document non-RAG modules as out-of-scope**
    - Update README to clarify Tier 3B RAG scope
    - Document voice/imaging/music as separate domains
    - Consider splitting into separate repos in Phase 3
    - **Estimated Effort**: 0.5 day

---

## Phase 2 – Anticipated Scope (Planning Only)

Not implemented in Phase 1, but prepare for:
- Advanced reranking (cross-encoder models in MLX)
- Multi-bank search and score normalization
- Metadata filtering and faceted search
- Incremental index updates (append without full reindex)
- Performance optimization (async, caching, batching)
- CPU fallback for non-Apple hardware (if MLX supports)
- Split multi-domain codebase into separate packages
- Integration tests with Tier 2 (MCP)

---

## Phase 3 – Deployment & Scaling (Future)

Not scoped yet, but consider:
- Kubernetes deployment on Apple Silicon nodes
- Horizontal scaling (multiple API instances with shared index storage)
- Model versioning and A/B testing
- Advanced monitoring and observability
- Cost optimization (model quantization, index compression)

---

**End of HANDOFFS.md**

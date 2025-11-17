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

## Phase 4 – Fusion Orchestrator Readiness Assessment

**Date**: 2025-11-17
**Branch**: `claude/phase4-repo-snapshot-013r33BxiNo1VpoWd1VVYGKg`
**Tier**: Full Stack (Tier 2 MCP + Tier 3A MLX Provider + Tier 3B RAG Engine)
**Session Type**: Repository Snapshot & Readiness Analysis (ZERO code changes, assessment only)
**Agent Alias**: Phase-4 Fusion Orchestrator Assistant

### Executive Summary

This Phase-4 session conducted a comprehensive **current-state repository snapshot** to assess readiness for fusion orchestration implementation. The analysis covered:

1. **Git State & Branch Management** - Verified working tree cleanliness, identified unmerged Phase 3 validation branch with critical enhancements
2. **Service Architecture Audit** - Mapped existing Tier 3B RAG API, identified missing Tier 2/3A components
3. **API Surface Analysis** - Documented all implemented routes, identified gaps vs. fusion blueprint
4. **Registry System Assessment** - Confirmed registry directories exist but are empty (blocker)
5. **Test & Tooling Review** - Identified test collection errors, linting issues, missing dependencies
6. **Readiness Scoring** - Calculated objective Phase-4 readiness score: **4/10**

**Full Report**: See `docs/PHASE4_READINESS_REPORT.md` (comprehensive 500+ line analysis)

### Critical Findings

#### 🚨 **BLOCKER 1: Stub Embedding Model (Non-Functional RAG)**
- **Location**: `src/rag/models/model.py:18-39`
- **Issue**: Embedding model generates deterministic hash-based vectors (text length, byte sum, vowels, tokens), NOT semantic embeddings
- **Impact**: RAG semantic search is broken - similarity scores are meaningless
- **Evidence**: Model class docstring explicitly states: "This is a deterministic stub implementation... In production, this should be replaced with a real embedding model"
- **Action Required**: Replace with real BERT/sentence-transformer using MLX (2-4 hours)

#### 🚨 **BLOCKER 2: Empty Registry Systems**
- **Location**: `src/core/registry/` (only contains empty `__init__.py`)
- **Issue**: Model/Tool/App registries declared in architecture but not implemented
- **Impact**: No dynamic capability discovery, hardcoded model references
- **Action Required**: Implement registry classes with CRUD operations and REST endpoints (1-2 days)

#### 🚨 **BLOCKER 3: Missing Tier 2/3A Services**
- **Missing Components**:
  - ❌ MCP Server (Tier 2 orchestration layer)
  - ❌ MLX Provider Service (Tier 3A with `/v1/chat/completions`)
  - ❌ Fusion Orchestrator (`/api/fusion/*` routes)
  - ❌ Internal diagnostics (`/internal/*` routes)
- **Impact**: Cannot implement multi-service workflows
- **Action Required**: Design and build 3-tier architecture (3-5 days for Tier 2, 2-3 days for Tier 3A)

#### ⚠️ **ISSUE 4: Unmerged Phase 3 Validation Branch**
- **Branch**: `origin/claude/validate-phase3-prep-phase4-01FPWzmBChzoiPSTHctgTRDr`
- **Status**: AHEAD by 1 commit (commit `45c80f1`)
- **Contains**:
  - Request ID tracking across all endpoints (X-Request-ID header)
  - Enhanced `/health` endpoint with `index_available` field
  - Enhanced `/stats` endpoint with `index_path`, `created_at` timestamps
  - Comprehensive metadata filtering documentation
  - Additional test coverage (`test_stats_api.py`, `test_similarity.py` enhancements)
  - 568 lines added, 88 deleted across 8 files
- **Action Required**: Merge immediately before Phase-4 work (30 min)

#### ⚠️ **ISSUE 5: API Route Naming Mismatch**
- **Documented** (API_CONTRACT.md): `/rag_query`, `/rag_upsert`, `/rag_stats`
- **Actual** (code): `/query`, `/upsert`, `/stats`
- **Impact**: Contract vs. implementation divergence
- **Action Required**: Either update routes or update docs (30 min)

### What Works ✅

1. **Tier 3B RAG API is Functional**
   - FastAPI server runs (`src/rag/api/main.py`)
   - All 6 endpoints implemented: `/`, `/health`, `/query`, `/upsert`, `/delete`, `/stats`
   - VectorDB with NPZ storage works correctly
   - Metadata filtering implemented and tested
   - Cosine similarity scoring functional
   - Request/response schemas defined with Pydantic

2. **100% Local-First Architecture**
   - Zero cloud provider dependencies in production code
   - All models from HuggingFace Hub or local paths
   - Ollama integration only in experimental scripts (not production)

3. **Configuration Management**
   - Environment-based config with Pydantic (`src/rag/config/settings.py`)
   - `.env.example` template with all required vars
   - Proper CORS, error handling, structured logging

4. **Test Infrastructure**
   - 14 tests across RAG, CLI, Flux, MusicGen modules
   - Test fixtures and conftest.py present
   - Pytest configured in pyproject.toml

### What's Missing ❌

1. **Service Layer Architecture**
   - No provider abstraction (VectorDB called directly from routes)
   - No service layer separation
   - Monolithic FastAPI app

2. **Registry Systems**
   - Model registry: Empty
   - Tool registry: Empty
   - App registry: Empty

3. **Tier 2 Orchestration**
   - No MCP server implementation
   - No multi-service coordination
   - No PDF extraction service (currently in Tier 3B CLI tools)

4. **Tier 3A MLX Provider**
   - LLM generation is CLI-only (`apps/chat_cli.py`)
   - No OpenAI-compatible API wrapper
   - No `/v1/chat/completions` endpoint

5. **Observability & Diagnostics**
   - No `/internal/*` routes
   - No Prometheus metrics
   - No request tracing (in current branch - fixed in unmerged branch)
   - No performance monitoring

6. **Production Embedding Model**
   - Current model is a stub (hash-based, not semantic)
   - Declared model (`sentence-transformers/all-MiniLM-L6-v2`) not actually loaded

### Repository Structure Summary

```
mlx-rag-lab/
├── src/rag/                       # Tier 3B RAG Engine ✅
│   ├── api/                       # FastAPI application ✅
│   │   ├── main.py               # App with health check ✅
│   │   ├── routes/rag.py         # 6 endpoints implemented ✅
│   │   ├── schemas.py            # Pydantic models ✅
│   │   └── exceptions.py         # Custom errors ✅
│   ├── config/settings.py        # Env-based config ✅
│   ├── models/model.py           # ⚠️ STUB embedding model
│   ├── retrieval/vdb.py          # VectorDB (NPZ storage) ✅
│   ├── ingestion/create_vdb.py   # Document ingestion ✅
│   └── chat/                      # Stateful ChatSession (not API-ready) ⚠️
├── src/libs/
│   ├── mlx_core/                 # MLX text generation (CLI-only) ⚠️
│   └── ollama_core/              # Experimental only ⚠️
├── src/core/
│   └── registry/                 # ❌ EMPTY (only __init__.py)
├── apps/                          # 11 CLI applications (out of scope for API)
├── tests/                         # 14 tests (5 import errors) ⚠️
└── docs/
    ├── API_CONTRACT.md           # Tier 3B contract ✅
    ├── FUSION_PHASE0.md          # Architecture blueprint ✅
    └── PHASE4_READINESS_REPORT.md # This assessment ✅
```

### Phase-4 Readiness Score: **4/10**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Architecture Cleanliness | 5/10 | Monolithic app, mixed domains (RAG+Voice+Imaging) |
| Local-First Purity | 10/10 | ✅ Perfect - zero cloud dependencies |
| Registry Correctness | 0/10 | ❌ Empty stubs only |
| Provider Health | 3/10 | RAG API works but stub embeddings; no Tier 2/3A |
| API Contract Stability | 6/10 | Route naming mismatch, unmerged enhancements |
| Observability | 4/10 | Basic health check; no tracing/metrics |
| Test Coverage | 5/10 | Tests exist but import errors |

**Weighted Total**: 4.75/10 → **4/10**

### Recommended Phase-4 Approach

**Option A: Fast-Track Minimal Phase-4 (2-3 weeks)**
- Merge validation branch
- Fix embedding model (real BERT/sentence-transformer)
- Build minimal model registry only
- Thin MLX Provider wrapper
- Basic MCP orchestrator for RAG+LLM
- **Defer**: Fusion routes, full observability

**Option B: Full Architecture Rebuild (4-6 weeks)**
- Separate RAG from multi-domain toolkit
- Implement full 3-tier architecture
- Complete registry system (models, tools, apps)
- All missing services (MCP, MLX Provider, Fusion)
- Production observability and metrics
- Full test coverage

**Recommendation**: **Option A** for timeline adherence

---

## Phase 4 – Task Breakdown for Next Agent

**Assigned To**: Next Phase-4 Implementation Agent
**Estimated Duration**: 2-3 weeks (Option A) or 4-6 weeks (Option B)
**Prerequisites**: Read `docs/PHASE4_READINESS_REPORT.md` in full

### 🔴 **Priority 0: Pre-Implementation Fixes (MUST DO FIRST)**

#### Task P0.1: Merge Phase 3 Validation Branch
**Estimated Effort**: 30 minutes
**Why**: Brings request ID tracking, enhanced observability, API improvements
**How**:
```bash
git fetch origin
git merge origin/claude/validate-phase3-prep-phase4-01FPWzmBChzoiPSTHctgTRDr
# Resolve any conflicts (likely none - fast-forward merge)
git push origin claude/phase4-repo-snapshot-013r33BxiNo1VpoWd1VVYGKg
```
**Validation**: Check that `/health` returns `request_id` field, `/stats` includes timestamps

#### Task P0.2: Replace Stub Embedding Model
**Estimated Effort**: 2-4 hours
**Critical**: Current hash-based model breaks semantic search
**Implementation**:
1. Create real embedding model class in `src/rag/models/model.py`
2. Load `sentence-transformers/all-MiniLM-L6-v2` from HuggingFace
3. Use MLX for inference (see `examples/bert/model.py` for reference)
4. Update `Model.__init__()` to accept `model_id` parameter
5. Update `Model.run()` to return real sentence embeddings (384-dim)
6. Test with sample text: embedding should differ semantically

**Validation**:
```python
from rag.models.model import Model
model = Model("sentence-transformers/all-MiniLM-L6-v2")
emb1 = model.run(["The cat sat on the mat"])
emb2 = model.run(["A feline rested on the rug"])
emb3 = model.run(["The stock market crashed"])
# Verify: cosine_sim(emb1, emb2) > cosine_sim(emb1, emb3)
```

#### Task P0.3: Fix API Route Naming
**Estimated Effort**: 30 minutes
**Decision Required**: Update code to match docs OR update docs to match code
**Recommendation**: Update code (routes) to match API_CONTRACT.md
**Changes**:
- `/query` → `/rag_query`
- `/upsert` → `/rag_upsert`
- `/delete` → `/rag_delete`
- `/stats` → `/rag_stats`

**Files to Modify**:
- `src/rag/api/routes/rag.py` (update `@router.post()` decorators)
- `tests/rag/test_*.py` (update test URLs)

#### Task P0.4: Fix Test Dependencies
**Estimated Effort**: 15 minutes
**Commands**:
```bash
uv sync --dev  # Install dev dependencies
# Add httpx to dev dependencies if missing:
# Add to pyproject.toml: dependency-groups.dev = ["httpx", ...]
pytest tests/ --collect-only  # Verify 0 collection errors
```

---

### 🟠 **Priority 1: Registry System Implementation**

#### Task P1.1: Design Registry Architecture
**Estimated Effort**: 1 day
**Deliverables**:
1. Registry schema design (SQLite? JSON files? In-memory?)
2. API contract for registry endpoints
3. Data models for Model/Tool/App entries

**Schema Example**:
```python
# Model Registry Entry
{
  "id": "bert-base-uncased-mlx",
  "name": "BERT Base Uncased (MLX)",
  "type": "embedding",
  "provider": "huggingface",
  "model_path": "sentence-transformers/all-MiniLM-L6-v2",
  "capabilities": ["embedding"],
  "metadata": {
    "embedding_dim": 384,
    "max_seq_length": 512,
    "backend": "mlx"
  },
  "status": "active",
  "created_at": "2025-11-17T10:00:00Z"
}
```

#### Task P1.2: Implement Model Registry
**Estimated Effort**: 1-2 days
**Location**: `src/core/registry/model_registry.py`
**Requirements**:
- CRUD operations: `register()`, `list()`, `get()`, `update()`, `delete()`
- Persistence (recommend JSON file in `var/registry/models.json`)
- Thread-safe access
- Validation (Pydantic models)

**API Endpoints** (add to FastAPI app):
- `POST /registry/models` - Register new model
- `GET /registry/models` - List all models
- `GET /registry/models/{id}` - Get model details
- `PUT /registry/models/{id}` - Update model
- `DELETE /registry/models/{id}` - Remove model

#### Task P1.3: Implement Tool Registry
**Estimated Effort**: 1 day
**Location**: `src/core/registry/tool_registry.py`
**Similar to model registry but for tools/capabilities**

#### Task P1.4: Implement App Registry
**Estimated Effort**: 1 day
**Location**: `src/core/registry/app_registry.py`
**Track available applications and their metadata**

---

### 🟠 **Priority 1: Tier 3A MLX Provider Service**

#### Task P1.5: Design MLX Provider API
**Estimated Effort**: 0.5 day
**Deliverables**:
- OpenAPI spec for `/v1/chat/completions` (OpenAI-compatible)
- Request/response schemas
- Streaming vs. non-streaming support decision

#### Task P1.6: Implement MLX Provider FastAPI App
**Estimated Effort**: 2-3 days
**Location**: New directory `src/mlx_provider/`
**Structure**:
```
src/mlx_provider/
├── api/
│   ├── main.py              # FastAPI app for Tier 3A
│   ├── routes/
│   │   └── chat.py          # /v1/chat/completions endpoint
│   └── schemas.py           # OpenAI-compatible schemas
├── models/
│   └── llm_engine.py        # Wrap libs/mlx_core/model_engine.py
└── config/
    └── settings.py          # Tier 3A config
```

**Features**:
- Wrap `libs/mlx_core/model_engine.py` in stateless API
- Support model selection via request body
- Optional streaming support (SSE)
- Health check endpoint

**Validation**:
```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/gpt-oss-20b-mlx",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

---

### 🟠 **Priority 1: Tier 2 MCP Orchestration Server**

#### Task P1.7: Design MCP Server Architecture
**Estimated Effort**: 1 day
**Deliverables**:
- MCP server API contract
- Workflow orchestration patterns (RAG+LLM)
- State management strategy (sessions, conversations)

#### Task P1.8: Implement MCP Server
**Estimated Effort**: 3-5 days
**Location**: New directory `src/mcp_server/`
**Structure**:
```
src/mcp_server/
├── api/
│   ├── main.py              # FastAPI app for Tier 2
│   ├── routes/
│   │   ├── chat.py          # High-level chat endpoint
│   │   └── mcp.py           # MCP protocol routes
│   └── schemas.py           # MCP request/response models
├── orchestration/
│   ├── rag_llm_workflow.py  # RAG retrieval + LLM generation
│   └── session_manager.py   # Conversation state management
├── clients/
│   ├── mlx_client.py        # Client for Tier 3A
│   └── rag_client.py        # Client for Tier 3B
└── config/
    └── settings.py          # Tier 2 config (service URLs)
```

**Core Workflow** (RAG+LLM):
1. Accept user query
2. Call Tier 3B `/rag_query` to retrieve relevant chunks
3. Format prompt with retrieved context
4. Call Tier 3A `/v1/chat/completions` to generate response
5. Return response with sources

**Validation**:
```bash
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does MLX handle embeddings?",
    "bank_name": "technical_docs",
    "session_id": "user-123"
  }'
```

---

### 🟡 **Priority 2: Fusion Orchestrator Routes**

#### Task P2.1: Implement `/api/fusion/*` Endpoints
**Estimated Effort**: 2-3 days
**Location**: `src/mcp_server/api/routes/fusion.py`
**Endpoints**:
- `POST /api/fusion/ingest` - Full PDF extraction + RAG upsert workflow
- `POST /api/fusion/chat` - RAG retrieval + LLM generation
- `POST /api/fusion/summarize` - Document summarization pipeline
- `GET /api/fusion/workflows` - List available workflows

---

### 🟡 **Priority 2: Internal Diagnostics Routes**

#### Task P2.2: Implement `/internal/*` Endpoints
**Estimated Effort**: 1 day
**Endpoints**:
- `GET /internal/health` - Deep health check (all services)
- `GET /internal/metrics` - Prometheus-compatible metrics
- `GET /internal/indexes` - List all vector indexes
- `GET /internal/models` - List loaded models
- `GET /internal/sessions` - Active conversation sessions

---

### 🟡 **Priority 2: Testing & Quality**

#### Task P2.3: Fix Test Collection Errors
**Estimated Effort**: 30 minutes
**Actions**:
- Install missing dependencies (`httpx`, verify `mlx` in dev env)
- Fix import errors in test files
- Run `pytest tests/ --collect-only` until 0 errors

#### Task P2.4: Add Integration Tests
**Estimated Effort**: 1 day
**Coverage**:
- End-to-end RAG workflow (ingest → query)
- Tier 2 → Tier 3A → Tier 3B integration
- Registry CRUD operations
- Error handling and retry logic

---

### 🟢 **Priority 3: Documentation & Cleanup**

#### Task P3.1: Update API_CONTRACT.md
**Estimated Effort**: 1 hour
**Updates**:
- Fix route naming (`/rag_query` vs. `/query`)
- Document request ID tracking
- Add Tier 3A contract (`/v1/chat/completions`)
- Add Tier 2 contract (MCP routes)

#### Task P3.2: Add Architecture Diagrams
**Estimated Effort**: 2 hours
**Diagrams**:
- 3-tier architecture overview
- RAG+LLM workflow sequence diagram
- Registry system architecture
- Service communication flow

#### Task P3.3: Document Embedding Model Replacement
**Estimated Effort**: 1 hour
**Content**:
- How to load custom embedding models
- Performance benchmarks (CPU vs. GPU)
- Model selection guidelines

---

### Completion Criteria for Phase-4

✅ **Minimal (Option A)**:
- [ ] Phase 3 validation branch merged
- [ ] Real embedding model implemented (BERT/sentence-transformers)
- [ ] Model registry functional with REST API
- [ ] Tier 3A MLX Provider service running on port 8001
- [ ] Tier 2 MCP Server running on port 8002
- [ ] End-to-end RAG+LLM workflow working
- [ ] Integration tests passing
- [ ] API contracts updated

✅ **Full (Option B)**:
- All of Option A, plus:
- [ ] Tool and App registries implemented
- [ ] Fusion orchestrator routes (`/api/fusion/*`)
- [ ] Internal diagnostics routes (`/internal/*`)
- [ ] Prometheus metrics endpoint
- [ ] RAG separated from multi-domain toolkit
- [ ] Full test coverage (unit + integration + e2e)
- [ ] Architecture diagrams and documentation

---

### Handoff Notes for Next Agent

1. **Start Here**: Read `docs/PHASE4_READINESS_REPORT.md` completely
2. **Decision Required**: Choose Option A (fast-track) or Option B (full rebuild)
3. **Critical Path**: P0 tasks MUST be completed before any P1 work
4. **Embedding Model**: This is the #1 blocker - current stub breaks RAG semantically
5. **Branch Management**: Work on a new `claude/phase4-implementation-*` branch
6. **Service Ports**:
   - Tier 3B (RAG): 8000
   - Tier 3A (MLX): 8001 (recommend)
   - Tier 2 (MCP): 8002 (recommend)
7. **Testing**: Fix test dependencies before writing new tests
8. **Architecture**: Follow service layer pattern, avoid direct database calls in routes
9. **Documentation**: Update API_CONTRACT.md as you implement new routes
10. **Commit Strategy**: Frequent small commits with clear messages

**Questions?** Check existing docs:
- `docs/FUSION_PHASE0.md` - Original architecture blueprint
- `docs/API_CONTRACT.md` - Tier 3B API spec
- `docs/PHASE4_READINESS_REPORT.md` - This assessment
- `README.md` - Project overview

**Good luck! The foundation is solid - just needs the missing layers.** 🚀

---

**End of HANDOFFS.md**

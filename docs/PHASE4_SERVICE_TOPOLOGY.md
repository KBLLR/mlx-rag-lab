# Phase-4 Service Topology

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Tier-2: gen-idea-lab                       │
│                  (Orchestration / Gateway)                   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  OpenAI-Compatible Routes                          │    │
│  │  /v1/chat/completions                              │    │
│  │  /v1/embeddings                                    │    │
│  │  /v1/models                                        │    │
│  └─────────────┬──────────────────────────────┬───────┘    │
│                │                              │             │
│  ┌─────────────▼──────────┐    ┌─────────────▼──────────┐  │
│  │  MLX Provider          │    │  RAG Provider          │  │
│  │  (mlx-provider.ts)     │    │  (rag-provider.ts)     │  │
│  └─────────────┬──────────┘    └─────────────┬──────────┘  │
│                │                              │             │
│  ┌─────────────▼──────────────────────────────▼──────────┐  │
│  │  Fusion Orchestrator                                  │  │
│  │  - rag_only, mlx_only, fusion_full modes             │  │
│  │  - Multi-step reasoning flows                        │  │
│  │  - Graceful degradation                              │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬──────────────────────────────┬────────────────┘
             │                              │
             │                              │
   ┌─────────▼──────────┐        ┌─────────▼──────────┐
   │  Tier-3A: MLX      │        │  Tier-3B: RAG      │
   │  mlx-openai-server │        │  mlx-rag-lab       │
   │                    │        │                    │
   │  Port: 5001        │        │  Port: 8000        │
   │  /v1/chat/...      │        │  /health           │
   │  /v1/embeddings    │        │  /rag_query        │
   │  /v1/models        │        │  /rag_upsert       │
   │  /health           │        │  /rag_delete       │
   └────────────────────┘        │  /rag_stats        │
                                 └────────────────────┘
```

---

## Service Details

### Tier-2: gen-idea-lab (Orchestrator)
- **Port:** 3000 (default)
- **Role:** Gateway, fusion orchestrator, MCP host
- **Technology:** Node.js / TypeScript / Express or Fastify
- **Key Responsibilities:**
  - Expose OpenAI-compatible API surface
  - Route requests to MLX (Tier-3A) and RAG (Tier-3B)
  - Implement fusion modes (rag_only, mlx_only, fusion_full)
  - Manage MCP servers and tools
  - Provide observability and diagnostics

### Tier-3A: mlx-openai-server-lab (MLX LLM)
- **Port:** 5001 (default)
- **Role:** Local LLM inference and embeddings
- **Technology:** Python / MLX / FastAPI
- **API Contract:** OpenAI-compatible
  - `POST /v1/chat/completions`
  - `POST /v1/embeddings`
  - `GET /v1/models`
  - `GET /health`
- **Models:** GPT-OSS 20B, Phi-3, Qwen, etc.
- **Response Shape:** Strict OpenAI JSON compliance

### Tier-3B: mlx-rag-lab (RAG Engine)
- **Port:** 8000 (default)
- **Role:** Document ingestion, vector search, retrieval
- **Technology:** Python / MLX / FastAPI
- **API Contract:** Custom RAG endpoints
  - `GET /health` → `{ ok, latency_ms, ... }`
  - `POST /rag_query` → Query collections
  - `POST /rag_upsert` → Ingest documents
  - `POST /rag_delete` → Delete by metadata
  - `GET /rag_stats` → Collection statistics
- **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2 (384-dim)
- **Vector DB:** Custom MLX-based VectorDB (`.npz` files)

---

## Request Flow Examples

### Example 1: Fusion Full (RAG → MLX → Response)

**User Request:**
```
"What is MLX and how does it handle embeddings?"
```

**Flow:**
1. **Tier-2** receives request with `requestId: abc-123`
2. **Tier-2** calls **Tier-3B** RAG:
   ```http
   POST http://localhost:8000/rag_query
   X-Request-ID: abc-123

   {
     "query": "What is MLX and how does it handle embeddings?",
     "collection": "mlx_docs",
     "k": 5,
     "threshold": 0.5
   }
   ```
3. **Tier-3B** returns relevant chunks:
   ```json
   {
     "results": [
       {
         "text": "MLX uses L2-normalized embeddings...",
         "score": 0.87,
         "source": "mlx_embeddings.md"
       }
     ],
     "latency_ms": 45.2,
     "request_id": "abc-123"
   }
   ```
4. **Tier-2** constructs augmented prompt:
   ```
   Context:
   - MLX uses L2-normalized embeddings...

   User Question: What is MLX and how does it handle embeddings?
   ```
5. **Tier-2** calls **Tier-3A** MLX:
   ```http
   POST http://localhost:5001/v1/chat/completions
   X-Request-ID: abc-123

   {
     "model": "gpt-oss-20b",
     "messages": [
       {
         "role": "user",
         "content": "Context:\n- MLX uses L2-normalized embeddings...\n\nUser Question: ..."
       }
     ]
   }
   ```
6. **Tier-3A** returns LLM response:
   ```json
   {
     "choices": [
       {
         "message": {
           "role": "assistant",
           "content": "MLX is Apple's machine learning framework..."
         }
       }
     ],
     "latency_ms": 1234.5
   }
   ```
7. **Tier-2** returns final response to user with fusion metadata:
   ```json
   {
     "answer": "MLX is Apple's machine learning framework...",
     "sources": ["mlx_embeddings.md"],
     "latency": {
       "rag_ms": 45.2,
       "mlx_ms": 1234.5,
       "total_ms": 1279.7
     },
     "request_id": "abc-123"
   }
   ```

---

### Example 2: RAG Only (Direct Retrieval)

**User Request:**
```
"Find documents about embeddings"
```

**Flow:**
1. **Tier-2** receives request with `requestId: xyz-456`
2. **Tier-2** determines this is a simple retrieval task (no LLM needed)
3. **Tier-2** calls **Tier-3B** RAG:
   ```http
   POST http://localhost:8000/rag_query
   X-Request-ID: xyz-456

   {
     "query": "embeddings",
     "collection": "mlx_docs",
     "k": 10,
     "threshold": 0.3
   }
   ```
4. **Tier-3B** returns chunks
5. **Tier-2** returns formatted results directly (no MLX call)

---

### Example 3: MLX Only (No RAG Context)

**User Request:**
```
"Write a Python function to calculate fibonacci numbers"
```

**Flow:**
1. **Tier-2** receives request with `requestId: def-789`
2. **Tier-2** determines no RAG context is needed (code generation task)
3. **Tier-2** calls **Tier-3A** MLX directly:
   ```http
   POST http://localhost:5001/v1/chat/completions
   X-Request-ID: def-789
   ```
4. **Tier-3A** returns LLM response
5. **Tier-2** returns response with metadata

---

## Health Check Strategy

### Tier-2 Startup Health Checks
```typescript
async function ensureTier3Healthy(): Promise<void> {
  const mlxHealth = await fetch('http://localhost:5001/health');
  const ragHealth = await fetch('http://localhost:8000/health');

  const mlx = await mlxHealth.json();
  const rag = await ragHealth.json();

  if (!mlx.ok || !rag.ok) {
    throw new Error('Tier-3 services not ready');
  }

  console.log(`MLX latency: ${mlx.latency_ms}ms`);
  console.log(`RAG latency: ${rag.latency_ms}ms`);
}
```

### Graceful Degradation
```typescript
async function queryWithFallback(query: string, requestId: string) {
  try {
    // Try fusion_full mode
    const ragResults = await ragProvider.query(query, 'default', requestId);
    const mlxResponse = await mlxProvider.chat(augmentPrompt(ragResults), requestId);
    return { mode: 'fusion_full', ...mlxResponse };
  } catch (ragError) {
    // Fall back to mlx_only
    console.warn('RAG unavailable, falling back to MLX-only mode');
    const mlxResponse = await mlxProvider.chat(query, requestId);
    return { mode: 'mlx_only', ...mlxResponse };
  }
}
```

---

## Request ID Propagation

All requests MUST include `X-Request-ID` header:
```
User Request → Tier-2 (generates requestId)
  ├─ Tier-3A (MLX) with X-Request-ID: abc-123
  └─ Tier-3B (RAG) with X-Request-ID: abc-123
```

This enables:
- End-to-end tracing across all tiers
- Latency attribution by service
- Debugging multi-step fusion flows

---

## Latency Budgets (Target)

| Operation | Target Latency | Notes |
|-----------|----------------|-------|
| RAG Query | < 100ms | Simple vector search |
| MLX Chat Completion | < 2000ms | Depends on model size |
| Fusion Full | < 2500ms | RAG + MLX combined |
| Health Check | < 50ms | All tiers |

---

## Configuration

### Environment Variables

**Tier-2 (gen-idea-lab):**
```env
MLX_URL=http://localhost:5001
RAG_URL=http://localhost:8000
FUSION_MODE=fusion_full  # or: mlx_only, rag_only
LOCAL_MODE=true
```

**Tier-3A (mlx-openai-server-lab):**
```env
PORT=5001
MLX_MODEL_PATH=/path/to/models/gpt-oss-20b
```

**Tier-3B (mlx-rag-lab):**
```env
PORT=8000
INDEX_ROOT_PATH=var/indexes
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## Development Workflow

### Start All Services

**Terminal 1 (Tier-3B RAG):**
```bash
cd mlx-rag-lab
uv run uvicorn rag.api.main:app --reload --port 8000
```

**Terminal 2 (Tier-3A MLX):**
```bash
cd mlx-openai-server-lab
python -m mlx_server --port 5001
```

**Terminal 3 (Tier-2 Orchestrator):**
```bash
cd gen-idea-lab
npm run dev
```

### Verify Integration
```bash
# Check health
curl http://localhost:8000/health  # RAG
curl http://localhost:5001/health  # MLX
curl http://localhost:3000/health  # Orchestrator

# Test fusion flow
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-123" \
  -d '{
    "model": "gpt-oss-20b",
    "messages": [{"role": "user", "content": "What is MLX?"}],
    "fusion_mode": "fusion_full"
  }'
```

---

## Observability

### Structured Logging
All tiers log in this format:
```
2025-11-17T12:34:56 - rag.api.routes.rag - INFO - Query request for collection 'mlx_docs' (k=5, threshold=0.5) [request_id=abc-123]
2025-11-17T12:34:56 - rag.api.routes.rag - INFO - Query returned 3 results in 45.20ms [request_id=abc-123]
```

### Metrics to Track
- Request latency by tier (p50, p95, p99)
- RAG hit rate (requests with relevant results)
- MLX token throughput
- Fusion mode distribution (rag_only vs mlx_only vs fusion_full)

---

## Next Steps

1. **Tier-2 Implementation:** Implement providers (mlx-provider.ts, rag-provider.ts)
2. **Fusion Logic:** Build orchestration layer with mode selection
3. **MCP Integration:** Expose MLX + RAG capabilities as MCP tools
4. **Testing:** Phase-4 integration tests (health → fusion → degradation)
5. **Documentation:** API surface docs, deployment guides

---

## Version History

- **v0.1.0** (2025-11-17): Phase-4 initial topology with 3-tier architecture

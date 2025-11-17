# Phase-4 RAG Provider Contract (Tier-3B)

## Overview

This document defines the **Phase-4 provider contract** for the MLX RAG Engine (Tier-3B). This contract ensures predictable, traceable, and observable interactions between the Tier-2 orchestrator (gen-idea-lab) and the Tier-3B RAG service (mlx-rag-lab).

**Service Information:**
- **Tier:** 3B
- **Name:** MLX RAG Engine
- **Base URL:** `http://localhost:8000` (default)
- **Protocol:** HTTP/REST (FastAPI)
- **Data Format:** JSON

---

## Core Principles

### 1. Request ID Propagation
All requests MUST support the `X-Request-ID` header for distributed tracing:
```http
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```
- If not provided, the server generates a UUID
- The same `request_id` is returned in the response

### 2. Latency Measurement
All responses MUST include a `latency_ms` field:
```json
{
  "latency_ms": 45.2
}
```
- Measured using `time.perf_counter()` (high-precision timer)
- Includes all processing time from request receipt to response generation

### 3. Consistent Error Handling
All errors follow this shape:
```json
{
  "error": {
    "code": "IndexNotFoundError",
    "message": "Collection 'my_collection' does not exist",
    "status_code": 404
  }
}
```

---

## API Endpoints

### 1. Health Check
**GET `/health`**

**Phase-4 Contract:**
```json
{
  "ok": true,
  "latency_ms": 12.5,
  "tier": "3B",
  "models_loaded": true,
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "index_available": true,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Fields:**
- `ok` (bool): Overall operational status (models_loaded AND index_available)
- `latency_ms` (float): Health check latency in milliseconds
- `tier` (string): Always "3B" for RAG engine
- `models_loaded` (bool): Whether embedding model is loaded
- `embedding_model` (string | null): Model ID if loaded
- `index_available` (bool): Whether index storage is accessible
- `request_id` (string): Request trace ID

**Usage from Tier-2:**
```typescript
async function checkRAGHealth(requestId?: string): Promise<HealthResponse> {
  const response = await fetch('http://localhost:8000/health', {
    headers: requestId ? { 'X-Request-ID': requestId } : {}
  });
  return response.json();
}
```

---

### 2. Query Collection
**POST `/rag_query`**

**Request:**
```json
{
  "query": "How does MLX handle embeddings?",
  "collection": "technical_docs",
  "k": 5,
  "threshold": 0.5,
  "filter": {
    "author": "alice",
    "category": "physics"
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "text": "MLX uses L2-normalized embeddings for cosine similarity...",
      "source": "mlx_embeddings.md",
      "score": 0.87,
      "metadata": {
        "author": "alice",
        "category": "physics"
      }
    }
  ],
  "query": "How does MLX handle embeddings?",
  "collection": "technical_docs",
  "latency_ms": 45.2,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Fields:**
- `query` (string): User's search query
- `collection` (string): Target collection name
- `k` (int): Number of results to return (1-100, default: 5)
- `threshold` (float): Minimum cosine similarity score in range [-1, 1] (default: 0.5, typically use 0.3-0.85)
- `filter` (object | null): Metadata filter (AND logic for multiple keys)

**Response Fields:**
- `results` (array): Ranked chunks by similarity
  - `text` (string): Chunk content
  - `source` (string): Source document identifier
  - `score` (float): Cosine similarity score in range [-1, 1] (L2-normalized embeddings)
  - `metadata` (object | null): Associated metadata
- `latency_ms` (float): Query execution time

**Usage from Tier-2:**
```typescript
async function queryRAG(query: string, collection: string, requestId: string): Promise<QueryResponse> {
  const response = await fetch('http://localhost:8000/rag_query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': requestId
    },
    body: JSON.stringify({
      query,
      collection,
      k: 5,
      threshold: 0.5
    })
  });
  return response.json();
}
```

---

### 3. Upsert Documents
**POST `/rag_upsert`**

**Request:**
```json
{
  "documents": [
    {
      "content": "MLX is Apple's machine learning framework for Apple Silicon.",
      "source": "mlx_intro.md",
      "metadata": {
        "author": "alice",
        "category": "mlx"
      }
    }
  ],
  "collection": "technical_docs"
}
```

**Response:**
```json
{
  "chunks_added": 12,
  "documents_processed": 1,
  "collection": "technical_docs",
  "index_path": "var/indexes/technical_docs/vdb.npz",
  "latency_ms": 234.5,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Chunking Strategy:**
- Deterministic chunking with fixed parameters:
  - `chunk_size`: 256 characters
  - `chunk_overlap`: 50 characters
- Metadata is preserved for each chunk

**Usage from Tier-2:**
```typescript
async function upsertToRAG(documents: Document[], collection: string, requestId: string): Promise<UpsertResponse> {
  const response = await fetch('http://localhost:8000/rag_upsert', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': requestId
    },
    body: JSON.stringify({ documents, collection })
  });
  return response.json();
}
```

---

### 4. Delete Documents
**POST `/rag_delete`**

**Request:**
```json
{
  "filter": {
    "author": "alice"
  },
  "collection": "technical_docs"
}
```

**Response:**
```json
{
  "deleted_count": 5,
  "collection": "technical_docs",
  "latency_ms": 15.7,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Filter Logic:**
- AND logic for multiple keys (all criteria must match)
- Exact string matching on metadata fields
- Filter cannot be empty

---

### 5. Collection Statistics
**GET `/rag_stats?collection=technical_docs`**

**Response:**
```json
{
  "collection": "technical_docs",
  "num_chunks": 352,
  "num_documents": 12,
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "embedding_dim": 384,
  "index_path": "var/indexes/technical_docs/vdb.npz",
  "created_at": "2025-11-16T10:30:00Z",
  "updated_at": "2025-11-16T14:22:00Z",
  "latency_ms": 8.3,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Usage from Tier-2:**
```typescript
async function getRAGStats(collection: string, requestId: string): Promise<StatsResponse> {
  const response = await fetch(`http://localhost:8000/rag_stats?collection=${collection}`, {
    headers: { 'X-Request-ID': requestId }
  });
  return response.json();
}
```

---

## Embedding Model Contract

### Current Model
- **Model ID:** `sentence-transformers/all-MiniLM-L6-v2`
- **Embedding Dimension:** 384
- **Normalization:** L2 normalized for cosine similarity
- **Similarity Metric:** Cosine similarity (range: -1 to 1)

### Embeddings Alignment
- RAG embeddings are **fully compatible** with MLX-based embedding models
- Uses HuggingFace Transformers with mean pooling
- Outputs as MLX arrays (mx.float32) or NumPy fallback

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `IndexNotFoundError` | 404 | Collection does not exist |
| `InvalidRequestError` | 400 | Invalid request parameters |
| `InternalServerError` | 500 | Unexpected server error |

---

## Observability

### Request Tracing
All operations log:
```
Query request for collection 'technical_docs' (k=5, threshold=0.5) [request_id=550e8400-e29b-41d4-a716-446655440000]
Query returned 3 results in 45.20ms [request_id=550e8400-e29b-41d4-a716-446655440000]
```

### Latency Breakdown
- `latency_ms` includes:
  - Request parsing
  - Collection loading
  - Embedding generation (for queries)
  - Vector similarity computation
  - Response serialization

---

## Phase-4 Integration Example

### Tier-2 RAG Provider (gen-idea-lab)
```typescript
// src/providers/rag-provider.ts

export interface RAGProvider {
  query(query: string, collection: string, requestId: string): Promise<QueryResponse>;
  upsert(documents: Document[], collection: string, requestId: string): Promise<UpsertResponse>;
  delete(filter: Record<string, string>, collection: string, requestId: string): Promise<DeleteResponse>;
  stats(collection: string, requestId: string): Promise<StatsResponse>;
  health(requestId?: string): Promise<HealthResponse>;
}

export function getRAGProvider(baseUrl: string = 'http://localhost:8000'): RAGProvider {
  return {
    async query(query, collection, requestId) {
      const response = await fetch(`${baseUrl}/rag_query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Request-ID': requestId
        },
        body: JSON.stringify({ query, collection, k: 5, threshold: 0.5 })
      });

      if (!response.ok) {
        throw new Error(`RAG query failed: ${response.statusText}`);
      }

      return response.json();
    },

    async health(requestId) {
      const response = await fetch(`${baseUrl}/health`, {
        headers: requestId ? { 'X-Request-ID': requestId } : {}
      });
      return response.json();
    }

    // ... other methods
  };
}
```

---

## Testing Contract Compliance

Run the contract validation script:
```bash
# Start the RAG API server
uv run uvicorn rag.api.main:app --reload

# In another terminal, validate the contract
python scripts/test_rag_contracts.py
```

Or use the existing test suite:
```bash
uv run pytest tests/rag -v
```

---

## Version History

- **v0.1.0** (2025-11-17): Phase-4 initial contract with `ok`, `latency_ms`, and full requestId tracing

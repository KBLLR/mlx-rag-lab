# MLX RAG Engine API Contract (Tier 3B)

**Version**: 0.1.0
**Base URL**: `http://localhost:8000` (development)
**Tier**: 3B (Stateless RAG Engine)

---

## Overview

The MLX RAG Engine provides a stateless FastAPI-based service for document ingestion, retrieval, and knowledge bank statistics. This API is designed to integrate with Tier 2 (MCP orchestration layer) and does NOT handle:

- PDF extraction (pre-extracted text only)
- LLM response generation (returns raw chunks only)
- Conversation history (managed by Tier 2)
- Authentication (to be added in Phase 2)

---

## Table of Contents

1. [Health Check](#health-check)
2. [Document Ingestion (Upsert)](#document-ingestion-upsert)
3. [Query Retrieval](#query-retrieval)
4. [Knowledge Bank Statistics](#knowledge-bank-statistics)
5. [Error Responses](#error-responses)

---

## Health Check

### `GET /health`

Check API availability and model loading status.

**Request:**
```bash
curl -X GET http://localhost:8000/health
```

**Response:** `200 OK`
```json
{
  "status": "ok",
  "tier": "3B",
  "models_loaded": true,
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

**Response Fields:**
- `status` (string): Service status (`"ok"` or `"error"`)
- `tier` (string): Service tier identifier (`"3B"`)
- `models_loaded` (boolean): Whether embedding models are loaded and ready
- `embedding_model` (string|null): Currently loaded embedding model ID

---

## Document Ingestion (Upsert)

### `POST /rag_upsert`

Ingest documents into a knowledge bank. Creates or updates the vector index with new chunks.

**Important**: Documents must contain **pre-extracted text**. PDF extraction should be done by Tier 2 (MCP) before calling this endpoint.

**Request:**
```bash
curl -X POST http://localhost:8000/rag_upsert \
  -H "Content-Type: application/json" \
  -d '{
    "bank_name": "technical_docs",
    "documents": [
      {
        "content": "MLX is Apple'\''s machine learning framework for Apple Silicon...",
        "source": "mlx_overview.md",
        "metadata": {"category": "documentation", "version": "0.29.3"}
      },
      {
        "content": "Vector embeddings are dense representations of text...",
        "source": "embeddings_guide.md",
        "metadata": {"category": "tutorial"}
      }
    ],
    "options": {
      "chunk_size": 256,
      "chunk_overlap": 50
    }
  }'
```

**Request Body Schema:**
```typescript
{
  bank_name: string;           // Knowledge bank identifier
  documents: Array<{
    content: string;           // Pre-extracted document text
    source: string;            // Document identifier (filename, URL, etc.)
    metadata?: object;         // Optional metadata for filtering
  }>;
  options?: {
    chunk_size?: number;       // Token size for chunks (default: 256)
    chunk_overlap?: number;    // Overlap tokens (default: 50)
  };
}
```

**Response:** `200 OK`
```json
{
  "chunks_added": 142,
  "documents_processed": 2,
  "bank_name": "technical_docs",
  "index_path": "var/indexes/technical_docs/vdb.npz"
}
```

**Response Fields:**
- `chunks_added` (integer): Number of text chunks added to index
- `documents_processed` (integer): Number of documents successfully processed
- `bank_name` (string): Knowledge bank name
- `index_path` (string|null): Path to the created/updated vector index

**Error Responses:**
- `400 Bad Request`: Invalid request body or parameters
- `500 Internal Server Error`: Embedding generation or index write failure
- `503 Service Unavailable`: Embedding model not loaded

---

## Query Retrieval

### `POST /rag_query`

Retrieve relevant chunks from a knowledge bank based on semantic similarity.

**Important**: This endpoint returns **raw chunks only**. LLM response generation should be done by Tier 2 (MCP) using the retrieved context.

**Request:**
```bash
curl -X POST http://localhost:8000/rag_query \
  -H "Content-Type: application/json" \
  -d '{
    "bank_name": "technical_docs",
    "query": "How does MLX handle embeddings?",
    "options": {
      "top_k": 5,
      "rerank": false,
      "threshold": 0.5
    }
  }'
```

**Request Body Schema:**
```typescript
{
  bank_name: string;           // Knowledge bank to query
  query: string;               // Query text
  options?: {
    top_k?: number;            // Number of chunks to retrieve (1-100, default: 5)
    rerank?: boolean;          // Apply reranking if available (default: false)
    threshold?: number;        // Min similarity score 0-1 (default: null)
  };
}
```

**Response:** `200 OK`
```json
{
  "query": "How does MLX handle embeddings?",
  "bank_name": "technical_docs",
  "results": [
    {
      "text": "MLX provides efficient embedding generation using Metal GPU acceleration...",
      "source": "mlx_overview.md",
      "score": 0.87,
      "metadata": {"category": "documentation", "version": "0.29.3"}
    },
    {
      "text": "Vector embeddings in MLX use the mx.array format for efficient computation...",
      "source": "embeddings_guide.md",
      "score": 0.74,
      "metadata": {"category": "tutorial"}
    }
  ]
}
```

**Response Fields:**
- `query` (string): Original query text
- `bank_name` (string): Knowledge bank queried
- `results` (array): Retrieved chunks ranked by relevance
  - `text` (string): Chunk text content
  - `source` (string): Source document identifier
  - `score` (float): Similarity score (0-1, higher is more relevant)
  - `metadata` (object|null): Chunk metadata if available

**Error Responses:**
- `400 Bad Request`: Invalid query or parameters
- `404 Not Found`: Knowledge bank does not exist
- `500 Internal Server Error`: Embedding generation or query failure
- `503 Service Unavailable`: Embedding model not loaded

---

## Knowledge Bank Statistics

### `GET /rag_stats`

Retrieve statistics about a knowledge bank.

**Request:**
```bash
curl -X GET "http://localhost:8000/rag_stats?bank_name=technical_docs"
```

**Query Parameters:**
- `bank_name` (string, required): Knowledge bank name

**Response:** `200 OK`
```json
{
  "bank_name": "technical_docs",
  "num_chunks": 352,
  "num_documents": 12,
  "chunk_size": 256,
  "chunk_overlap": 50,
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "embedding_dim": 384,
  "created_at": "2025-11-16T10:30:00Z",
  "updated_at": "2025-11-16T14:22:00Z"
}
```

**Response Fields:**
- `bank_name` (string): Knowledge bank name
- `num_chunks` (integer): Total chunks in index
- `num_documents` (integer): Number of source documents
- `chunk_size` (integer): Chunk size in tokens
- `chunk_overlap` (integer): Overlap tokens between chunks
- `embedding_model` (string): Embedding model used
- `embedding_dim` (integer|null): Embedding vector dimensions
- `created_at` (string|null): Index creation timestamp (ISO 8601)
- `updated_at` (string|null): Last update timestamp (ISO 8601)

**Error Responses:**
- `404 Not Found`: Knowledge bank does not exist
- `500 Internal Server Error`: Failed to read index metadata

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "IndexNotFoundError",
    "message": "Knowledge bank 'invalid_bank' does not exist",
    "status_code": 404
  }
}
```

### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `InvalidRequestError` | Malformed request body or invalid parameters |
| 404 | `IndexNotFoundError` | Requested knowledge bank does not exist |
| 500 | `EmbeddingError` | Embedding model operation failed |
| 500 | `IndexWriteError` | Failed to write vector index to disk |
| 500 | `ChunkingError` | Text chunking operation failed |
| 500 | `InternalServerError` | Unhandled internal server error |
| 503 | `ModelNotLoadedError` | Embedding model not available |

---

## Integration Notes

### Tier 2 (MCP) Responsibilities

The MCP orchestration layer should handle:

1. **PDF Extraction**: Use `unstructured[pdf]` or similar to extract text before calling `/rag_upsert`
2. **LLM Response Generation**: Call `/rag_query` to get chunks, then use Tier 3A (MLX OpenAI Server) to generate responses
3. **Conversation History**: Maintain chat history and format prompts with retrieved context
4. **State Management**: Track knowledge bank mappings and user sessions
5. **Error Handling**: Implement retry logic and fallback strategies

### Environment Configuration

The API can be configured via environment variables (see `.env.example`):

- `INDEX_ROOT_PATH`: Where vector indexes are stored
- `EMBEDDING_MODEL_ID`: HuggingFace model ID or local path
- `MAX_INDEX_CACHE_SIZE`: Max banks in GPU memory
- `CHUNK_SIZE`, `CHUNK_OVERLAP`: Default chunking parameters

### Model Requirements

- **Embedding Model**: Must be downloaded before API start (or auto-downloaded on first request)
- **Apple Silicon**: MLX requires macOS 13.3+ with M1/M2/M3/M4 processors
- **VRAM**: Typical embedding models use 200-500MB; 8GB+ recommended for multiple banks

---

## OpenAPI Specification

The interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Future Enhancements (Phase 2+)

- Async endpoint support for concurrent requests
- Incremental index updates (append mode)
- Metadata filtering in queries
- Multi-bank federated search
- API key authentication
- Prometheus metrics endpoint
- Semantic query caching

---

**End of API Contract**

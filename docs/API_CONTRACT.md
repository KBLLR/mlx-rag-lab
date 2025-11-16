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
4. [Document Deletion](#document-deletion)
5. [Collection Statistics](#collection-statistics)
6. [Metadata Filtering and Scoring](#metadata-filtering-and-scoring)
7. [Error Responses](#error-responses)

---

## Health Check

### `GET /health`

Check API availability, model loading status, and index storage accessibility.

**Request:**
```bash
curl -X GET http://localhost:8000/health
```

**Request Headers (Optional):**
- `X-Request-ID`: Optional request ID for distributed tracing

**Response:** `200 OK`
```json
{
  "status": "ok",
  "tier": "3B",
  "models_loaded": true,
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "index_available": true,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response Fields:**
- `status` (string): Service status (`"ok"`, `"degraded"`, or `"error"`)
  - `"ok"`: All systems operational
  - `"degraded"`: Partial functionality (e.g., models loaded but index storage inaccessible)
  - `"error"`: Critical failure (models not loaded and/or index unavailable)
- `tier` (string): Service tier identifier (`"3B"`)
- `models_loaded` (boolean): Whether embedding models are loaded and ready
- `embedding_model` (string|null): Currently loaded embedding model ID
- `index_available` (boolean): Whether index storage is accessible and writable
- `request_id` (string): Request ID for tracing (generated if not provided)

**Use for Tier 2 Integration:**
- Use `/health` for health checks before routing requests
- Monitor `index_available` to detect storage issues
- Check `models_loaded` before attempting embedding operations

---

## Document Ingestion (Upsert)

### `POST /upsert`

Ingest documents into a collection. Creates or updates the vector index with new chunks.

**Important**: Documents must contain **pre-extracted text**. PDF extraction should be done by Tier 2 (MCP) before calling this endpoint.

**Request:**
```bash
curl -X POST http://localhost:8000/upsert \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: my-request-123" \
  -d '{
    "collection": "technical_docs",
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
    ]
  }'
```

**Request Headers (Optional):**
- `X-Request-ID`: Optional request ID for distributed tracing

**Request Body Schema:**
```typescript
{
  collection: string;           // Collection identifier
  documents: Array<{
    content: string;            // Pre-extracted document text
    source: string;             // Document identifier (filename, URL, etc.)
    metadata?: object;          // Optional metadata for filtering (key-value pairs)
  }>;
}
```

**Response:** `200 OK`
```json
{
  "chunks_added": 142,
  "documents_processed": 2,
  "collection": "technical_docs",
  "index_path": "var/indexes/technical_docs/vdb.npz",
  "request_id": "my-request-123"
}
```

**Response Fields:**
- `chunks_added` (integer): Number of text chunks added to index
- `documents_processed` (integer): Number of documents successfully processed
- `collection` (string): Collection name
- `index_path` (string|null): Path to the created/updated vector index
- `request_id` (string): Request ID for tracing

**Error Responses:**
- `400 Bad Request`: Invalid request body or parameters
- `500 Internal Server Error`: Embedding generation or index write failure
- `503 Service Unavailable`: Embedding model not loaded

---

## Query Retrieval

### `POST /query`

Retrieve relevant chunks from a collection based on semantic similarity.

**Important**: This endpoint returns **raw chunks only**. LLM response generation should be done by Tier 2 (MCP) using the retrieved context.

**Request:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: my-query-456" \
  -d '{
    "collection": "technical_docs",
    "query": "How does MLX handle embeddings?",
    "k": 5,
    "threshold": 0.5,
    "filter": {"category": "documentation"}
  }'
```

**Request Headers (Optional):**
- `X-Request-ID`: Optional request ID for distributed tracing

**Request Body Schema:**
```typescript
{
  collection: string;          // Collection to query
  query: string;               // Query text
  k?: number;                  // Number of chunks to retrieve (1-100, default: 5)
  threshold?: number;          // Min similarity score -1 to 1 (default: 0.5)
  filter?: object;             // Metadata filter (AND logic, key-value pairs)
}
```

**Response:** `200 OK`
```json
{
  "query": "How does MLX handle embeddings?",
  "collection": "technical_docs",
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
      "metadata": {"category": "documentation"}
    }
  ],
  "request_id": "my-query-456"
}
```

**Response Fields:**
- `query` (string): Original query text
- `collection` (string): Collection queried
- `results` (array): Retrieved chunks ranked by similarity (descending)
  - `text` (string): Chunk text content
  - `source` (string): Source document identifier
  - `score` (float): Cosine similarity score (-1 to 1, higher is more similar)
  - `metadata` (object|null): Chunk metadata if available
- `request_id` (string): Request ID for tracing

**Error Responses:**
- `400 Bad Request`: Invalid query or parameters
- `404 Not Found`: Knowledge bank does not exist
- `500 Internal Server Error`: Embedding generation or query failure
- `503 Service Unavailable`: Embedding model not loaded

---

## Collection Statistics

### `GET /stats`

Retrieve statistics about a collection.

**Request:**
```bash
curl -X GET "http://localhost:8000/stats?collection=technical_docs" \
  -H "X-Request-ID: my-stats-789"
```

**Query Parameters:**
- `collection` (string, required): Collection name

**Request Headers (Optional):**
- `X-Request-ID`: Optional request ID for distributed tracing

**Response:** `200 OK`
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
  "request_id": "my-stats-789"
}
```

**Response Fields:**
- `collection` (string): Collection name
- `num_chunks` (integer): Total chunks in index
- `num_documents` (integer): Number of unique source documents
- `embedding_model` (string): Embedding model identifier
- `embedding_dim` (integer|null): Embedding vector dimensions
- `index_path` (string|null): Path to the vector index file
- `created_at` (string|null): Index creation timestamp (ISO 8601 format)
- `updated_at` (string|null): Last update timestamp (ISO 8601 format)
- `request_id` (string): Request ID for tracing

**Error Responses:**
- `404 Not Found`: Collection does not exist
- `500 Internal Server Error`: Failed to read index metadata

---

## Document Deletion

### `POST /delete`

Delete documents from a collection based on metadata filter criteria.

**Request:**
```bash
curl -X POST http://localhost:8000/delete \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: my-delete-999" \
  -d '{
    "collection": "technical_docs",
    "filter": {"author": "bob", "category": "outdated"}
  }'
```

**Request Headers (Optional):**
- `X-Request-ID`: Optional request ID for distributed tracing

**Request Body Schema:**
```typescript
{
  collection: string;          // Collection name
  filter: object;              // Metadata filter (AND logic, key-value pairs, must not be empty)
}
```

**Response:** `200 OK`
```json
{
  "deleted_count": 5,
  "collection": "technical_docs",
  "request_id": "my-delete-999"
}
```

**Response Fields:**
- `deleted_count` (integer): Number of chunks deleted
- `collection` (string): Collection name
- `request_id` (string): Request ID for tracing

**Error Responses:**
- `400 Bad Request`: Empty filter or invalid request
- `404 Not Found`: Collection does not exist
- `500 Internal Server Error`: Delete operation failed

**Important**:
- Filter criteria cannot be empty (safety measure)
- Only chunks matching ALL filter key-value pairs are deleted (AND logic)
- Changes are persisted to disk immediately

---

## Metadata Filtering and Scoring

### Metadata Filtering Semantics

The RAG engine supports metadata-based filtering during query and delete operations.

**Filter Logic:**
- Filters use **AND logic**: All specified key-value pairs must match
- Example: `{"author": "alice", "category": "physics"}` matches only chunks where BOTH conditions are true
- OR logic is not currently supported (Phase 4+)

**Filter Matching Rules:**
1. **Exact Match**: String values must match exactly (case-sensitive)
2. **Missing Fields**: If a chunk doesn't have a filter key, it won't match
3. **Empty Filter**: `null` or `{}` matches all chunks (no filtering)
4. **Type Matching**: Values are compared as strings

**Examples:**

```bash
# Filter by single field
{"author": "alice"}

# Filter by multiple fields (AND logic)
{"author": "alice", "category": "physics", "year": "2024"}

# No filter (returns all results)
{}
```

### Similarity Scoring

The RAG engine uses **cosine similarity** for semantic matching between queries and document chunks.

**Score Range and Meaning:**
- **Range**: -1.0 to 1.0
- **1.0**: Identical vectors (perfect semantic match)
- **0.0**: Orthogonal vectors (no semantic relationship)
- **-1.0**: Opposite vectors (inverse semantic relationship)
- **Typical Range**: Most practical text similarities fall between 0.5 and 0.95

**Score Interpretation:**
- **> 0.8**: High relevance (strong semantic match)
- **0.6 - 0.8**: Moderate relevance (related concepts)
- **0.4 - 0.6**: Low relevance (weak connection)
- **< 0.4**: Minimal relevance (consider filtering out)

**Threshold Filtering:**
- Use the `threshold` parameter to filter results by minimum score
- Default: 0.5 (moderate relevance cutoff)
- Example: `"threshold": 0.7` returns only high-relevance results
- Threshold is applied AFTER metadata filtering

**Result Ordering:**
- Results are **always sorted by similarity score (descending)**
- Most relevant chunks appear first
- Ordering is preserved after threshold filtering

**Example Score Distribution:**
```json
{
  "results": [
    {"text": "...", "score": 0.89},  // High relevance
    {"text": "...", "score": 0.76},  // Moderate relevance
    {"text": "...", "score": 0.62},  // Low relevance
    {"text": "...", "score": 0.54}   // Marginal relevance
  ]
}
```

**For Tier 2 Integration:**
- Use `/stats` to understand collection size before querying
- Adjust `threshold` based on result quality in your domain
- Combine metadata filtering + threshold for precise retrieval
- Monitor score distribution to tune relevance cutoffs

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

## Future Enhancements (Phase 4+)

- Async endpoint support for concurrent requests
- OR logic for metadata filters (currently AND-only)
- Multi-collection federated search
- Incremental index updates without full reload
- API key authentication
- Prometheus metrics endpoint
- Semantic query caching
- Advanced reranking algorithms

---

**End of API Contract**

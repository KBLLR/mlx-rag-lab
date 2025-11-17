# Phase-4 Integration Examples

## Overview

This document provides **concrete integration examples** for connecting Tier-2 (gen-idea-lab) with Tier-3B (mlx-rag-lab) RAG API.

---

## 1. TypeScript Provider Implementation (Tier-2)

### File: `src/providers/rag-provider.ts`

```typescript
import fetch from 'node-fetch';

// Phase-4 Response Types
interface HealthResponse {
  ok: boolean;
  latency_ms: number;
  tier: string;
  models_loaded: boolean;
  embedding_model: string | null;
  index_available: boolean;
  request_id: string;
}

interface ChunkResult {
  text: string;
  source: string;
  score: number;
  metadata?: Record<string, any>;
}

interface QueryResponse {
  results: ChunkResult[];
  query: string;
  collection: string;
  latency_ms: number;
  request_id: string;
}

interface UpsertResponse {
  chunks_added: number;
  documents_processed: number;
  collection: string;
  index_path: string;
  latency_ms: number;
  request_id: string;
}

interface StatsResponse {
  collection: string;
  num_chunks: number;
  num_documents: number;
  embedding_model: string;
  embedding_dim: number | null;
  index_path: string;
  created_at: string | null;
  updated_at: string | null;
  latency_ms: number;
  request_id: string;
}

interface DeleteResponse {
  deleted_count: number;
  collection: string;
  latency_ms: number;
  request_id: string;
}

interface Document {
  content: string;
  source: string;
  metadata?: Record<string, any>;
}

// RAG Provider Interface
export interface RAGProvider {
  health(requestId?: string): Promise<HealthResponse>;
  query(
    query: string,
    collection: string,
    requestId: string,
    k?: number,
    threshold?: number,
    filter?: Record<string, string>
  ): Promise<QueryResponse>;
  upsert(
    documents: Document[],
    collection: string,
    requestId: string
  ): Promise<UpsertResponse>;
  delete(
    filter: Record<string, string>,
    collection: string,
    requestId: string
  ): Promise<DeleteResponse>;
  stats(collection: string, requestId: string): Promise<StatsResponse>;
}

// RAG Provider Implementation
export class MLXRAGProvider implements RAGProvider {
  private baseUrl: string;

  constructor(baseUrl: string = process.env.RAG_URL || 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async health(requestId?: string): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`, {
      headers: requestId ? { 'X-Request-ID': requestId } : {}
    });

    if (!response.ok) {
      throw new Error(`RAG health check failed: ${response.statusText}`);
    }

    return response.json() as Promise<HealthResponse>;
  }

  async query(
    query: string,
    collection: string,
    requestId: string,
    k: number = 5,
    threshold: number = 0.5,
    filter?: Record<string, string>
  ): Promise<QueryResponse> {
    const response = await fetch(`${this.baseUrl}/rag_query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId
      },
      body: JSON.stringify({
        query,
        collection,
        k,
        threshold,
        filter
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`RAG query failed: ${error.error?.message || response.statusText}`);
    }

    return response.json() as Promise<QueryResponse>;
  }

  async upsert(
    documents: Document[],
    collection: string,
    requestId: string
  ): Promise<UpsertResponse> {
    const response = await fetch(`${this.baseUrl}/rag_upsert`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId
      },
      body: JSON.stringify({
        documents,
        collection
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`RAG upsert failed: ${error.error?.message || response.statusText}`);
    }

    return response.json() as Promise<UpsertResponse>;
  }

  async delete(
    filter: Record<string, string>,
    collection: string,
    requestId: string
  ): Promise<DeleteResponse> {
    const response = await fetch(`${this.baseUrl}/rag_delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId
      },
      body: JSON.stringify({
        filter,
        collection
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`RAG delete failed: ${error.error?.message || response.statusText}`);
    }

    return response.json() as Promise<DeleteResponse>;
  }

  async stats(collection: string, requestId: string): Promise<StatsResponse> {
    const response = await fetch(
      `${this.baseUrl}/rag_stats?collection=${encodeURIComponent(collection)}`,
      {
        headers: { 'X-Request-ID': requestId }
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`RAG stats failed: ${error.error?.message || response.statusText}`);
    }

    return response.json() as Promise<StatsResponse>;
  }
}

// Factory function
export function getRAGProvider(): RAGProvider {
  return new MLXRAGProvider();
}
```

---

## 2. Fusion Orchestration Example

### File: `src/fusion/orchestrator.ts`

```typescript
import { v4 as uuidv4 } from 'uuid';
import { getRAGProvider, type RAGProvider } from '../providers/rag-provider';
import { getMLXProvider, type MLXProvider } from '../providers/mlx-provider';

interface FusionConfig {
  mode: 'rag_only' | 'mlx_only' | 'fusion_full';
  collection: string;
  ragK: number;
  ragThreshold: number;
}

interface FusionResponse {
  answer: string;
  sources?: string[];
  latency: {
    rag_ms?: number;
    mlx_ms?: number;
    total_ms: number;
  };
  mode: string;
  request_id: string;
}

export class FusionOrchestrator {
  private ragProvider: RAGProvider;
  private mlxProvider: MLXProvider;

  constructor() {
    this.ragProvider = getRAGProvider();
    this.mlxProvider = getMLXProvider();
  }

  async query(
    userQuery: string,
    config: FusionConfig,
    requestId?: string
  ): Promise<FusionResponse> {
    const reqId = requestId || uuidv4();
    const startTime = performance.now();

    // Mode selection
    switch (config.mode) {
      case 'rag_only':
        return this.ragOnlyMode(userQuery, config, reqId, startTime);
      case 'mlx_only':
        return this.mlxOnlyMode(userQuery, reqId, startTime);
      case 'fusion_full':
        return this.fusionFullMode(userQuery, config, reqId, startTime);
      default:
        throw new Error(`Unknown fusion mode: ${config.mode}`);
    }
  }

  private async ragOnlyMode(
    query: string,
    config: FusionConfig,
    requestId: string,
    startTime: number
  ): Promise<FusionResponse> {
    // Query RAG directly
    const ragResponse = await this.ragProvider.query(
      query,
      config.collection,
      requestId,
      config.ragK,
      config.ragThreshold
    );

    // Format results as answer
    const answer = ragResponse.results
      .map((r, i) => `[${i + 1}] ${r.text} (source: ${r.source}, score: ${r.score.toFixed(2)})`)
      .join('\n\n');

    const sources = ragResponse.results.map(r => r.source);
    const totalLatency = performance.now() - startTime;

    return {
      answer,
      sources,
      latency: {
        rag_ms: ragResponse.latency_ms,
        total_ms: totalLatency
      },
      mode: 'rag_only',
      request_id: requestId
    };
  }

  private async mlxOnlyMode(
    query: string,
    requestId: string,
    startTime: number
  ): Promise<FusionResponse> {
    // Query MLX directly (no RAG context)
    const mlxResponse = await this.mlxProvider.chat(
      [{ role: 'user', content: query }],
      requestId
    );

    const totalLatency = performance.now() - startTime;

    return {
      answer: mlxResponse.choices[0].message.content,
      latency: {
        mlx_ms: mlxResponse.latency_ms,
        total_ms: totalLatency
      },
      mode: 'mlx_only',
      request_id: requestId
    };
  }

  private async fusionFullMode(
    query: string,
    config: FusionConfig,
    requestId: string,
    startTime: number
  ): Promise<FusionResponse> {
    // Step 1: Query RAG for context
    const ragResponse = await this.ragProvider.query(
      query,
      config.collection,
      requestId,
      config.ragK,
      config.ragThreshold
    );

    // Step 2: Augment prompt with RAG context
    const context = ragResponse.results
      .map(r => `- ${r.text} (source: ${r.source})`)
      .join('\n');

    const augmentedPrompt = `Context from knowledge base:\n${context}\n\nUser Question: ${query}\n\nPlease answer the question using the provided context.`;

    // Step 3: Query MLX with augmented prompt
    const mlxResponse = await this.mlxProvider.chat(
      [{ role: 'user', content: augmentedPrompt }],
      requestId
    );

    const sources = ragResponse.results.map(r => r.source);
    const totalLatency = performance.now() - startTime;

    return {
      answer: mlxResponse.choices[0].message.content,
      sources,
      latency: {
        rag_ms: ragResponse.latency_ms,
        mlx_ms: mlxResponse.latency_ms,
        total_ms: totalLatency
      },
      mode: 'fusion_full',
      request_id: requestId
    };
  }

  async ensureHealthy(): Promise<void> {
    const [ragHealth, mlxHealth] = await Promise.all([
      this.ragProvider.health(),
      this.mlxProvider.health()
    ]);

    if (!ragHealth.ok) {
      throw new Error('RAG service is not healthy');
    }

    if (!mlxHealth.ok) {
      throw new Error('MLX service is not healthy');
    }

    console.log(`✓ RAG ready (latency: ${ragHealth.latency_ms.toFixed(2)}ms)`);
    console.log(`✓ MLX ready (latency: ${mlxHealth.latency_ms.toFixed(2)}ms)`);
  }
}
```

---

## 3. Express.js Route Integration

### File: `src/routes/chat.ts`

```typescript
import express from 'express';
import { FusionOrchestrator } from '../fusion/orchestrator';
import { v4 as uuidv4 } from 'uuid';

const router = express.Router();
const orchestrator = new FusionOrchestrator();

// OpenAI-compatible chat completions endpoint
router.post('/v1/chat/completions', async (req, res) => {
  try {
    const requestId = req.headers['x-request-id']?.toString() || uuidv4();
    const { messages, fusion_mode = 'fusion_full', collection = 'default' } = req.body;

    // Extract user query from messages
    const userMessage = messages.find((m: any) => m.role === 'user');
    if (!userMessage) {
      return res.status(400).json({
        error: { message: 'No user message found', code: 'invalid_request' }
      });
    }

    // Query fusion orchestrator
    const response = await orchestrator.query(
      userMessage.content,
      {
        mode: fusion_mode,
        collection,
        ragK: 5,
        ragThreshold: 0.5
      },
      requestId
    );

    // Return OpenAI-compatible response
    res.json({
      id: requestId,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: 'fusion',
      choices: [
        {
          index: 0,
          message: {
            role: 'assistant',
            content: response.answer
          },
          finish_reason: 'stop'
        }
      ],
      usage: {
        prompt_tokens: 0, // TODO: calculate
        completion_tokens: 0, // TODO: calculate
        total_tokens: 0
      },
      fusion_metadata: {
        mode: response.mode,
        sources: response.sources,
        latency: response.latency
      }
    });
  } catch (error: any) {
    console.error('Chat completion error:', error);
    res.status(500).json({
      error: {
        message: error.message || 'Internal server error',
        code: 'internal_error'
      }
    });
  }
});

// Health check endpoint
router.get('/health', async (req, res) => {
  try {
    const requestId = req.headers['x-request-id']?.toString() || uuidv4();
    await orchestrator.ensureHealthy();

    res.json({
      ok: true,
      tier: '2',
      request_id: requestId
    });
  } catch (error: any) {
    res.status(503).json({
      ok: false,
      error: error.message,
      tier: '2'
    });
  }
});

export default router;
```

---

## 4. Python Integration Example (Alternative)

### File: `fusion_client.py`

```python
import requests
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import uuid

@dataclass
class ChunkResult:
    text: str
    source: str
    score: float
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class QueryResponse:
    results: List[ChunkResult]
    query: str
    collection: str
    latency_ms: float
    request_id: str

class RAGClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def health(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        headers = {"X-Request-ID": request_id} if request_id else {}
        response = requests.get(f"{self.base_url}/health", headers=headers)
        response.raise_for_status()
        return response.json()

    def query(
        self,
        query: str,
        collection: str,
        request_id: str,
        k: int = 5,
        threshold: float = 0.5,
        metadata_filter: Optional[Dict[str, str]] = None
    ) -> QueryResponse:
        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": request_id
        }
        payload = {
            "query": query,
            "collection": collection,
            "k": k,
            "threshold": threshold,
            "filter": metadata_filter
        }

        response = requests.post(
            f"{self.base_url}/rag_query",
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        return QueryResponse(
            results=[ChunkResult(**r) for r in data["results"]],
            query=data["query"],
            collection=data["collection"],
            latency_ms=data["latency_ms"],
            request_id=data["request_id"]
        )

    def upsert(
        self,
        documents: List[Dict[str, Any]],
        collection: str,
        request_id: str
    ) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": request_id
        }
        payload = {
            "documents": documents,
            "collection": collection
        }

        response = requests.post(
            f"{self.base_url}/rag_upsert",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Usage example
if __name__ == "__main__":
    client = RAGClient()

    # Check health
    health = client.health(request_id="test-health")
    print(f"RAG Health: ok={health['ok']}, latency={health['latency_ms']}ms")

    # Query
    request_id = str(uuid.uuid4())
    result = client.query(
        query="What is MLX?",
        collection="mlx_docs",
        request_id=request_id,
        k=3,
        threshold=0.5
    )

    print(f"\nQuery Results (latency: {result.latency_ms:.2f}ms):")
    for i, chunk in enumerate(result.results, 1):
        print(f"{i}. {chunk.text[:100]}... (score: {chunk.score:.2f}, source: {chunk.source})")
```

---

## 5. cURL Examples (Quick Testing)

### Health Check
```bash
curl -X GET http://localhost:8000/health \
  -H "X-Request-ID: test-123"
```

### Query
```bash
curl -X POST http://localhost:8000/rag_query \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-query-456" \
  -d '{
    "query": "How does MLX handle embeddings?",
    "collection": "mlx_docs",
    "k": 5,
    "threshold": 0.5,
    "filter": {"category": "embeddings"}
  }'
```

### Upsert
```bash
curl -X POST http://localhost:8000/rag_upsert \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-upsert-789" \
  -d '{
    "documents": [
      {
        "content": "MLX is Apples machine learning framework for Apple Silicon.",
        "source": "mlx_intro.md",
        "metadata": {"author": "alice", "category": "mlx"}
      }
    ],
    "collection": "mlx_docs"
  }'
```

### Delete
```bash
curl -X POST http://localhost:8000/rag_delete \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-delete-101" \
  -d '{
    "filter": {"author": "alice"},
    "collection": "mlx_docs"
  }'
```

### Stats
```bash
curl -X GET "http://localhost:8000/rag_stats?collection=mlx_docs" \
  -H "X-Request-ID: test-stats-202"
```

---

## 6. Error Handling Example

```typescript
async function robustQuery(query: string, collection: string) {
  const ragProvider = getRAGProvider();
  const requestId = uuidv4();

  try {
    const response = await ragProvider.query(query, collection, requestId);
    return response;
  } catch (error: any) {
    // Parse RAG error
    if (error.message.includes('does not exist')) {
      console.error(`Collection '${collection}' not found`);
      // Create collection or use fallback
      return null;
    }

    // Log and re-throw
    console.error(`RAG query failed [request_id=${requestId}]:`, error);
    throw error;
  }
}
```

---

## Next Steps

1. Copy `rag-provider.ts` to your Tier-2 project
2. Implement MLX provider with similar interface
3. Build fusion orchestrator with mode selection
4. Add OpenAI-compatible routes
5. Test end-to-end flows with requestId tracing

---

**Phase-4 Integration Complete! 🚀**

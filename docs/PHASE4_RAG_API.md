# Phase-4 Fusion RAG API

**Status:** ✅ **Production Ready**
**Repository:** mlx-rag-lab (Tier-3B)
**API Version:** v1
**Date:** 2025-11-20

---

## Executive Summary

This document describes the **Fusion RAG API** – a profile-based interface for RAG queries designed for integration with:

- **mlx-openai-server** (Tier-3A) - as a tool backend
- **Smart Campus** - for classroom content retrieval
- **gen-idea-lab** (Tier-2) - fusion orchestration

The Fusion API provides a higher-level abstraction over the low-level collection-based RAG endpoints, using **profile_id** for multi-tenant scoping and applying sensible defaults per use case.

---

## API Overview

### Base URL

```
http://localhost:8000  # Default for local development
```

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/fusion/query` | POST | Profile-based RAG query |
| `/v1/fusion/profiles` | GET | List available profiles |
| `/health` | GET | Health check (existing) |

### Profiles

Pre-configured profiles provide scoping and defaults:

| Profile ID | Collection | Use Case | Default k | Default Threshold |
|-----------|-----------|----------|-----------|-------------------|
| `campus` | `campus_classroom_data` | Smart Campus classroom content | 5 | 0.6 |
| `avatar` | `avatar_knowledge_base` | STS avatar knowledge | 3 | 0.7 |
| `default` | `general_knowledge` | General purpose | 5 | 0.5 |

---

## Fusion Query Endpoint

### `POST /v1/fusion/query`

Profile-based RAG query designed for tool backends and orchestrators.

**Request Body:**

```json
{
  "profile_id": "campus",
  "query": "What did we learn about photosynthesis?",
  "filters": {
    "classroom_id": "bio-101",
    "subject": "biology"
  },
  "top_k": 5,
  "threshold": 0.6,
  "user_id": "student-123",
  "classroom_id": "bio-101"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `profile_id` | string | ✅ | Profile identifier (`campus`, `avatar`, `default`) |
| `query` | string | ✅ | User query text |
| `filters` | object | ❌ | Metadata filters (AND logic) |
| `top_k` | integer | ❌ | Number of results (uses profile default if omitted) |
| `threshold` | float | ❌ | Minimum similarity score (uses profile default if omitted) |
| `user_id` | string | ❌ | User identifier for logging/attribution |
| `classroom_id` | string | ❌ | Shortcut for `filters.classroom_id` (campus profile) |

**Response:**

```json
{
  "results": [
    {
      "text": "Photosynthesis is the process by which plants convert...",
      "source": "biology_lesson_2024-03-15.md",
      "score": 0.87,
      "metadata": {
        "classroom_id": "bio-101",
        "subject": "biology",
        "date": "2024-03-15"
      }
    }
  ],
  "trace": {
    "profile_id": "campus",
    "collection_used": "campus_classroom_data",
    "latency_ms": 45.2,
    "filters_applied": {
      "classroom_id": "bio-101",
      "subject": "biology"
    }
  },
  "tokens": null,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `results` | array | Ranked chunks (text, source, score, metadata) |
| `trace` | object | Query execution metadata |
| `trace.profile_id` | string | Profile used |
| `trace.collection_used` | string | Underlying collection queried |
| `trace.latency_ms` | float | Query latency in milliseconds |
| `trace.filters_applied` | object | Filters that were applied |
| `tokens` | integer\|null | Token count for results (reserved for future use) |
| `request_id` | string | Request ID for distributed tracing |

---

## Profiles Endpoint

### `GET /v1/fusion/profiles`

List all available profiles with their configurations.

**Response:**

```json
{
  "profiles": [
    {
      "profile_id": "campus",
      "collection": "campus_classroom_data",
      "default_k": 5,
      "default_threshold": 0.6,
      "metadata_schema": [
        "classroom_id",
        "subject",
        "teacher_id",
        "date",
        "document_type"
      ],
      "description": "Smart Campus classroom content and learning materials"
    },
    {
      "profile_id": "avatar",
      "collection": "avatar_knowledge_base",
      "default_k": 3,
      "default_threshold": 0.7,
      "metadata_schema": [
        "avatar_id",
        "topic",
        "personality_trait"
      ],
      "description": "Avatar knowledge base for speech-to-speech interactions"
    }
  ],
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Integration Examples

### 1. mlx-openai-server Tool Integration

**Use Case:** Expose campus RAG search as a tool that the LLM can call.

**Tool Schema (Python - mlx-openai-server):**

```python
# File: src/tools/campus_rag_tool.py

import requests
from typing import Dict, List, Optional

class CampusRAGTool:
    """Tool for searching Smart Campus classroom content."""

    def __init__(self, rag_url: str = "http://localhost:8000"):
        self.rag_url = rag_url

    def get_schema(self) -> Dict:
        """Return tool schema for LLM."""
        return {
            "type": "function",
            "function": {
                "name": "campus_rag_search",
                "description": "Search Smart Campus classroom content and learning materials",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query about classroom content"
                        },
                        "classroom_id": {
                            "type": "string",
                            "description": "Optional classroom identifier to filter results"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Optional subject filter (e.g., 'biology', 'math')"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)"
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    def execute(
        self,
        query: str,
        classroom_id: Optional[str] = None,
        subject: Optional[str] = None,
        top_k: int = 5,
        request_id: Optional[str] = None
    ) -> Dict:
        """Execute campus RAG search.

        Args:
            query: Search query
            classroom_id: Optional classroom filter
            subject: Optional subject filter
            top_k: Number of results
            request_id: Optional request ID for tracing

        Returns:
            RAG search results with sources and scores
        """
        # Build filters
        filters = {}
        if classroom_id:
            filters["classroom_id"] = classroom_id
        if subject:
            filters["subject"] = subject

        # Call fusion API
        response = requests.post(
            f"{self.rag_url}/v1/fusion/query",
            headers={
                "Content-Type": "application/json",
                "X-Request-ID": request_id or "default-request-id"
            },
            json={
                "profile_id": "campus",
                "query": query,
                "filters": filters if filters else None,
                "top_k": top_k
            }
        )
        response.raise_for_status()

        data = response.json()

        # Format for LLM consumption
        return {
            "results": [
                {
                    "text": r["text"],
                    "source": r["source"],
                    "score": r["score"],
                    "classroom_id": r.get("metadata", {}).get("classroom_id"),
                    "subject": r.get("metadata", {}).get("subject")
                }
                for r in data["results"]
            ],
            "count": len(data["results"]),
            "latency_ms": data["trace"]["latency_ms"]
        }


# Usage in mlx-openai-server
def register_tools():
    campus_tool = CampusRAGTool()
    return [campus_tool.get_schema()]

def execute_tool(tool_name: str, arguments: Dict) -> Dict:
    if tool_name == "campus_rag_search":
        tool = CampusRAGTool()
        return tool.execute(**arguments)
    # ... other tools
```

**Example Tool Call Flow:**

1. User asks: *"What did we cover in bio-101 about photosynthesis?"*
2. LLM decides to call `campus_rag_search` with:
   ```json
   {
     "query": "photosynthesis",
     "classroom_id": "bio-101"
   }
   ```
3. mlx-openai-server executes tool → calls `/v1/fusion/query`
4. RAG returns relevant chunks
5. mlx-openai-server injects chunks into LLM context
6. LLM generates answer using RAG context

---

### 2. Smart Campus Direct Integration

**Use Case:** Classroom chat interface directly queries RAG for student questions.

**TypeScript Client (Smart Campus):**

```typescript
// File: src/services/rag-service.ts

interface FusionQueryRequest {
  profile_id: string;
  query: string;
  filters?: Record<string, string>;
  top_k?: number;
  threshold?: number;
  classroom_id?: string;
  user_id?: string;
}

interface ChunkResult {
  text: string;
  source: string;
  score: number;
  metadata?: Record<string, any>;
}

interface FusionQueryResponse {
  results: ChunkResult[];
  trace: {
    profile_id: string;
    collection_used: string;
    latency_ms: number;
    filters_applied?: Record<string, string>;
  };
  tokens: number | null;
  request_id: string;
}

export class CampusRAGService {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async searchClassroomContent(
    query: string,
    classroomId: string,
    userId?: string,
    options?: { top_k?: number; subject?: string }
  ): Promise<FusionQueryResponse> {
    const filters: Record<string, string> = {};
    if (options?.subject) {
      filters.subject = options.subject;
    }

    const requestId = `campus-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    const response = await fetch(`${this.baseUrl}/v1/fusion/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId
      },
      body: JSON.stringify({
        profile_id: 'campus',
        query,
        classroom_id: classroomId,
        filters: Object.keys(filters).length > 0 ? filters : undefined,
        top_k: options?.top_k || 5,
        user_id: userId
      } as FusionQueryRequest)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`RAG query failed: ${error.error?.message || response.statusText}`);
    }

    return response.json();
  }

  async health(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }
}

// Usage in React component
export function ClassroomChat({ classroomId, userId }: Props) {
  const ragService = new CampusRAGService();

  const handleSearch = async (query: string) => {
    try {
      const results = await ragService.searchClassroomContent(
        query,
        classroomId,
        userId,
        { top_k: 5 }
      );

      // Display results in UI
      console.log(`Found ${results.results.length} results in ${results.trace.latency_ms}ms`);
      results.results.forEach(r => {
        console.log(`- ${r.source} (score: ${r.score.toFixed(2)}): ${r.text.substring(0, 100)}...`);
      });
    } catch (error) {
      console.error('RAG search failed:', error);
    }
  };

  return (
    <div>
      <SearchBar onSearch={handleSearch} />
      {/* ... rest of UI */}
    </div>
  );
}
```

---

### 3. gen-idea-lab (Tier-2) Orchestrator Integration

**Use Case:** Fusion orchestrator combining RAG + MLX LLM.

**TypeScript Provider (gen-idea-lab):**

```typescript
// File: src/providers/rag-provider.ts (extended for fusion)

import fetch from 'node-fetch';

interface FusionQueryRequest {
  profile_id: string;
  query: string;
  filters?: Record<string, string>;
  top_k?: number;
  threshold?: number;
}

interface FusionQueryResponse {
  results: Array<{
    text: string;
    source: string;
    score: number;
    metadata?: Record<string, any>;
  }>;
  trace: {
    profile_id: string;
    collection_used: string;
    latency_ms: number;
  };
  request_id: string;
}

export class FusionRAGProvider {
  private baseUrl: string;

  constructor(baseUrl: string = process.env.RAG_URL || 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async fusionQuery(
    profileId: string,
    query: string,
    requestId: string,
    filters?: Record<string, string>,
    topK?: number
  ): Promise<FusionQueryResponse> {
    const response = await fetch(`${this.baseUrl}/v1/fusion/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId
      },
      body: JSON.stringify({
        profile_id: profileId,
        query,
        filters,
        top_k: topK
      } as FusionQueryRequest)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Fusion query failed: ${error.error?.message || response.statusText}`);
    }

    return response.json() as Promise<FusionQueryResponse>;
  }
}

// Usage in orchestrator
async function handleCampusQuery(userQuery: string, classroomId: string, requestId: string) {
  const ragProvider = new FusionRAGProvider();
  const mlxProvider = new MLXProvider();

  // Step 1: Query RAG with campus profile
  const ragResults = await ragProvider.fusionQuery(
    'campus',
    userQuery,
    requestId,
    { classroom_id: classroomId }
  );

  // Step 2: Build augmented prompt
  const context = ragResults.results
    .map(r => `[${r.source}] ${r.text}`)
    .join('\n\n');

  const augmentedPrompt = `
Context from classroom ${classroomId}:
${context}

Student Question: ${userQuery}

Please answer using the provided classroom context.
  `.trim();

  // Step 3: Query MLX LLM
  const mlxResponse = await mlxProvider.chat(
    [{ role: 'user', content: augmentedPrompt }],
    requestId
  );

  return {
    answer: mlxResponse.choices[0].message.content,
    sources: ragResults.results.map(r => r.source),
    latency: {
      rag_ms: ragResults.trace.latency_ms,
      mlx_ms: mlxResponse.latency_ms,
      total_ms: ragResults.trace.latency_ms + mlxResponse.latency_ms
    },
    request_id: requestId
  };
}
```

---

## cURL Examples

### Query Campus Profile

```bash
curl -X POST http://localhost:8000/v1/fusion/query \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-campus-query-001" \
  -d '{
    "profile_id": "campus",
    "query": "What did we learn about photosynthesis?",
    "classroom_id": "bio-101",
    "top_k": 5
  }' | jq
```

### Query with Filters

```bash
curl -X POST http://localhost:8000/v1/fusion/query \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-filter-query-002" \
  -d '{
    "profile_id": "campus",
    "query": "cell division",
    "filters": {
      "classroom_id": "bio-101",
      "subject": "biology",
      "date": "2024-03-15"
    },
    "top_k": 3,
    "threshold": 0.7
  }' | jq
```

### List Profiles

```bash
curl -X GET http://localhost:8000/v1/fusion/profiles \
  -H "X-Request-ID: test-profiles-003" | jq
```

### Health Check

```bash
curl -X GET http://localhost:8000/health \
  -H "X-Request-ID: test-health-004" | jq
```

---

## Campus Profile Metadata Schema

When ingesting documents into the `campus` profile, use this metadata structure:

```python
# Example document ingestion (low-level API)
import requests

documents = [
    {
        "content": "Photosynthesis is the process by which plants convert light energy into chemical energy...",
        "source": "biology_lesson_2024-03-15.md",
        "metadata": {
            "classroom_id": "bio-101",          # Required
            "subject": "biology",                # Recommended
            "teacher_id": "prof-smith",          # Optional
            "date": "2024-03-15",                # Recommended (ISO 8601)
            "document_type": "lesson_notes"      # Optional (lesson_notes, homework, quiz, etc.)
        }
    }
]

# Use low-level API for ingestion
response = requests.post(
    "http://localhost:8000/rag_upsert",
    json={
        "collection": "campus_classroom_data",
        "documents": documents
    }
)
```

---

## Error Handling

All endpoints return structured errors:

```json
{
  "error": {
    "code": "InvalidRequestError",
    "message": "Profile 'unknown' not found. Available profiles: ['campus', 'avatar', 'default']",
    "status_code": 400
  }
}
```

**Common Error Codes:**

| Code | Status | Description |
|------|--------|-------------|
| `InvalidRequestError` | 400 | Profile not found or invalid parameters |
| `IndexNotFoundError` | 404 | Profile's collection does not exist |
| `InternalServerError` | 500 | Unexpected server error |

---

## Observability

### Request Tracing

All requests support `X-Request-ID` header:

```http
X-Request-ID: campus-query-abc123
```

If not provided, a UUID is auto-generated and returned in the response.

### Structured Logging

```
2025-11-20T12:34:56 - rag.api.routes.fusion - INFO - Fusion query request for profile 'campus' [request_id=campus-query-abc123]
2025-11-20T12:34:56 - rag.api.routes.fusion - INFO - Profile 'campus' → collection 'campus_classroom_data' (k=5, threshold=0.6, filters={'classroom_id': 'bio-101'}) [request_id=campus-query-abc123]
2025-11-20T12:34:56 - rag.api.routes.fusion - INFO - Fusion query returned 3 results in 45.20ms [request_id=campus-query-abc123]
```

### Latency Tracking

All responses include `trace.latency_ms` for query execution time:

```json
{
  "trace": {
    "latency_ms": 45.2
  }
}
```

---

## Profile Configuration

Profiles are defined in `src/rag/api/profiles.py`:

```python
PROFILES = {
    "campus": ProfileConfig(
        profile_id="campus",
        collection="campus_classroom_data",
        default_k=5,
        default_threshold=0.6,
        metadata_schema=["classroom_id", "subject", "teacher_id", "date", "document_type"],
        description="Smart Campus classroom content and learning materials",
    ),
    # ... more profiles
}
```

To add a new profile, edit this file and restart the API server.

---

## Deployment

### Start the API Server

```bash
cd mlx-rag-lab
uv run uvicorn rag.api.main:app --reload --port 8000
```

### Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# List profiles
curl http://localhost:8000/v1/fusion/profiles

# Check API docs
open http://localhost:8000/docs
```

---

## Next Steps

### For mlx-openai-server Team:

1. Implement `CampusRAGTool` using the Python example above
2. Register tool in mlx-openai-server's tool registry
3. Test tool calls with example queries
4. Add request ID propagation for distributed tracing

### For Smart Campus Team:

1. Implement `CampusRAGService` using the TypeScript example above
2. Integrate with classroom chat UI
3. Display sources alongside AI responses
4. Add filters for subject, date, teacher

### For gen-idea-lab Team:

1. Implement `FusionRAGProvider` with `/v1/fusion/query` support
2. Build orchestration logic (RAG → MLX flow)
3. Add fusion mode selection (fusion_full, rag_only, mlx_only)
4. Implement graceful degradation

---

## API Compatibility

### Backward Compatibility

The new Fusion API (`/v1/fusion/*`) **does not replace** the existing low-level API (`/rag_*`).

Both APIs are supported:

- **Fusion API** (`/v1/fusion/*`): Profile-based, high-level, designed for tools/orchestrators
- **Low-level API** (`/rag_*`): Collection-based, low-level, for direct VectorDB access

### Migration Path

If you're currently using `/rag_query`:

**Before (low-level):**
```bash
POST /rag_query
{
  "query": "...",
  "collection": "campus_classroom_data",
  "k": 5,
  "threshold": 0.6
}
```

**After (fusion):**
```bash
POST /v1/fusion/query
{
  "profile_id": "campus",
  "query": "...",
  "top_k": 5  # threshold uses profile default
}
```

---

## Support

- **API Documentation:** http://localhost:8000/docs (OpenAPI/Swagger)
- **Contract Spec:** `docs/PHASE4_PROVIDER_CONTRACT.md`
- **Integration Examples:** `docs/PHASE4_INTEGRATION_EXAMPLES.md`
- **Source Code:** `src/rag/api/routes/fusion.py`

---

**Document Version:** 1.0
**Last Updated:** 2025-11-20
**Status:** ✅ Production Ready

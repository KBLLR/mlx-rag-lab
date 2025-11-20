# Smart Campus Integration Guide (Phase-4)

This guide explains how to integrate mlx-rag-lab with Smart Campus for room-aware RAG queries.

---

## Overview

The Phase-4 Smart Campus integration provides:

- **Room-aware RAG**: Query room-specific knowledge (personalities, rules, atmosphere)
- **Entity context**: Retrieve information about specific entities (sensors, devices, automations)
- **Profile-based access**: Higher-level API with Smart Campus profiles
- **Distributed tracing**: Request ID propagation across services

---

## Architecture

```
Smart Campus (Tier-1 / Orchestrator)
         |
         | HTTP/REST
         v
mlx-rag-lab (Tier-3B RAG Provider)
    ├── /query_room       → Room-aware queries
    ├── /entity_context   → Entity-specific context
    ├── /rag_query        → General RAG
    └── /v1/fusion/query  → Profile-based access
```

---

## Step 1: Prepare Room Data

### Export Format

Create JSON files for each room with this structure:

```json
{
  "room_id": "peace",
  "name": "Peace Room",
  "personality": "The Peace room is designed for quiet, focused individual work...",
  "rules": [
    "Maintain absolute silence at all times",
    "Use headphones for any audio"
  ],
  "atmosphere": "Calm, minimal distractions, soft lighting",
  "entities": [
    {
      "entity_id": "sensor.peace_temperature",
      "description": "Monitors room temperature for optimal study conditions"
    }
  ]
}
```

### Example Directory Structure

```
smart-campus-data/
└── rooms/
    ├── peace.json
    ├── focus.json
    └── collab.json
```

---

## Step 2: Ingest Room Data

Use the `ingest-rooms-cli` tool to populate the RAG database:

```bash
# Ingest all room files from a directory
uv run ingest-rooms-cli \
  --rooms-dir /path/to/smart-campus-data/rooms \
  --collection rooms \
  --output var/indexes/rooms/vdb.npz
```

**Output:**
```
Ingesting Smart Campus Rooms
Source: /path/to/smart-campus-data/rooms
Collection: rooms
Output: var/indexes/rooms/vdb.npz
Found: 3 room file(s)

Processing rooms... ████████████████████ 100% 0:00:05

✓ Ingestion complete!
  • Files processed: 3
  • Chunks created: 24
  • Index saved: var/indexes/rooms/vdb.npz
  • Metadata saved: var/indexes/rooms/metadata.json
```

### What Gets Ingested

For each room, the CLI extracts and chunks:

1. **Personality** section → `section: "personality"`
2. **Rules** (joined into text) → `section: "rules"`
3. **Atmosphere** description → `section: "atmosphere"`
4. **Entity descriptions** → `section: "entity"`, with `entity_id` metadata

Each chunk includes metadata:
- `room_id`: "peace", "focus", "collab", etc.
- `source_file`: Original JSON filename
- `section`: Content type
- `entity_id`: (for entity chunks only)
- `tags`: Descriptive tags

---

## Step 3: Start the RAG API Server

```bash
# Start the FastAPI server
uv run uvicorn rag.api.main:app --reload --port 8000

# Check health
curl http://localhost:8000/health
```

**Expected Response:**
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

---

## Step 4: Query Room Information

### Example 1: Room Query

```bash
curl -X POST http://localhost:8000/query_room \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: req-test-123" \
  -d '{
    "requestId": "req-test-123",
    "source": "smart-campus",
    "timestamp": "2025-11-20T12:00:00Z",
    "type": "room_query",
    "room": "peace",
    "query": "What are the rules of this room?",
    "includeRag": true,
    "includeEntities": false
  }'
```

**Response:**
```json
{
  "requestId": "req-test-123",
  "room": "peace",
  "answer": "Based on peace room information:\n1. Rules:\n- Maintain absolute silence at all times\n- Use headphones for any audio...",
  "entities": [],
  "ragContext": {
    "collection": "rooms",
    "query": "peace: What are the rules of this room?",
    "results": [
      {
        "text": "Room: Peace Room\n\nRules:\n- Maintain absolute silence at all times\n- Use headphones for any audio",
        "score": 0.92,
        "metadata": {
          "room_id": "peace",
          "source_file": "peace.json",
          "section": "rules"
        }
      }
    ],
    "latencyMs": 18.4,
    "requestId": "req-test-123"
  },
  "latencyMs": 20.1,
  "modelUsed": "rag-only"
}
```

### Example 2: Entity Context

```bash
curl -X POST http://localhost:8000/entity_context \
  -H "Content-Type: application/json" \
  -d '{
    "requestId": "req-test-456",
    "source": "smart-campus",
    "timestamp": "2025-11-20T12:00:00Z",
    "entityId": "sensor.peace_temperature",
    "room": "peace",
    "k": 3,
    "threshold": 0.5
  }'
```

**Response:**
```json
{
  "collection": "rooms",
  "query": "sensor.peace_temperature",
  "results": [
    {
      "text": "Entity: sensor.peace_temperature\nMonitors room temperature to maintain optimal study conditions between 20-22°C",
      "score": 0.95,
      "metadata": {
        "room_id": "peace",
        "entity_id": "sensor.peace_temperature",
        "source_file": "peace.json",
        "section": "entity"
      }
    }
  ],
  "latencyMs": 12.3,
  "requestId": "req-test-456"
}
```

### Example 3: General RAG Query (with Phase-4 fields)

```bash
curl -X POST http://localhost:8000/rag_query \
  -H "Content-Type: application/json" \
  -d '{
    "requestId": "req-test-789",
    "source": "smart-campus",
    "timestamp": "2025-11-20T12:00:00Z",
    "query": "What rooms are good for group work?",
    "collection": "rooms",
    "k": 5,
    "threshold": 0.6,
    "filter": {}
  }'
```

---

## Integration Patterns

### Pattern 1: Direct HTTP Client (TypeScript)

```typescript
// src/services/rag-client.ts

export interface RAGClient {
  queryRoom(room: string, query: string, requestId: string): Promise<RoomQueryResponse>;
  getEntityContext(entityId: string, room: string | null, requestId: string): Promise<RAGContext>;
}

export function createRAGClient(baseUrl: string = 'http://localhost:8000'): RAGClient {
  return {
    async queryRoom(room, query, requestId) {
      const response = await fetch(`${baseUrl}/query_room`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Request-ID': requestId
        },
        body: JSON.stringify({
          requestId,
          source: 'smart-campus',
          timestamp: new Date().toISOString(),
          type: 'room_query',
          room,
          query,
          includeRag: true,
          includeEntities: false
        })
      });

      if (!response.ok) {
        throw new Error(`RAG query failed: ${response.statusText}`);
      }

      return response.json();
    },

    async getEntityContext(entityId, room, requestId) {
      const response = await fetch(`${baseUrl}/entity_context`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Request-ID': requestId
        },
        body: JSON.stringify({
          requestId,
          source: 'smart-campus',
          timestamp: new Date().toISOString(),
          entityId,
          room,
          k: 3,
          threshold: 0.5
        })
      });

      if (!response.ok) {
        throw new Error(`Entity context query failed: ${response.statusText}`);
      }

      return response.json();
    }
  };
}

// Usage
const rag = createRAGClient();
const result = await rag.queryRoom('peace', 'What are the rules?', 'req-123');
console.log(result.answer);
```

### Pattern 2: Profile-Based Access (Fusion API)

```typescript
// Higher-level API using profiles
async function queryWithProfile(profileId: string, query: string, filters: Record<string, string>) {
  const response = await fetch('http://localhost:8000/v1/fusion/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      profile_id: profileId,
      query,
      filters,
      top_k: 5,
      threshold: 0.6
    })
  });

  return response.json();
}

// Query rooms profile
const result = await queryWithProfile('rooms', 'What are quiet rooms?', { section: 'personality' });
```

---

## Monitoring & Tracing

### Request ID Flow

1. Smart Campus generates `requestId` (e.g., `req_${uuid}`)
2. Includes `requestId` in body + `X-Request-ID` header
3. mlx-rag-lab logs all operations with `requestId`
4. Response includes same `requestId` for correlation

### Latency Metrics

All responses include `latencyMs`:
- Room queries: ~20-50ms (RAG only)
- Entity context: ~10-30ms (filtered queries)
- General RAG: ~30-100ms (larger collections)

### Health Monitoring

```bash
# Continuous health check
watch -n 5 'curl -s http://localhost:8000/health | jq .'
```

---

## Troubleshooting

### Issue: "Rooms collection does not exist"

**Solution:** Ingest room data first:
```bash
uv run ingest-rooms-cli --rooms-dir /path/to/rooms
```

### Issue: Empty results for room queries

**Causes:**
1. Threshold too high (try 0.5 instead of 0.8)
2. Room ID mismatch (check `room_id` in JSON files)
3. Query too specific (broaden query terms)

**Debug:**
```bash
# Check collection stats
curl 'http://localhost:8000/rag_stats?collection=rooms'

# Test with lower threshold
curl -X POST http://localhost:8000/rag_query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "peace room",
    "collection": "rooms",
    "k": 10,
    "threshold": 0.3
  }' | jq '.results | length'
```

### Issue: Slow queries

**Optimization:**
1. Reduce `k` value (try k=3 instead of k=10)
2. Use metadata filters to narrow scope
3. Increase threshold to reduce post-processing

---

## Advanced Usage

### Custom Answer Generation

The default implementation uses deterministic concatenation. To use a local LLM:

```python
# In src/rag/api/routes/rooms.py

def _generate_answer_from_rag(query, rag_context, room):
    # Option 1: Deterministic (current)
    return concatenate_top_results(rag_context.results)

    # Option 2: Local LLM (future)
    from libs.mlx_core.model_engine import MLXModelEngine
    model = MLXModelEngine("mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit")
    prompt = build_prompt(query, rag_context)
    return model.generate(prompt, max_tokens=256)
```

### Bulk Room Queries

```typescript
async function queryMultipleRooms(rooms: string[], query: string): Promise<Map<string, RoomQueryResponse>> {
  const promises = rooms.map(room =>
    rag.queryRoom(room, query, `req-${room}-${Date.now()}`)
  );

  const results = await Promise.all(promises);
  return new Map(rooms.map((room, i) => [room, results[i]]));
}

// Query all rooms
const responses = await queryMultipleRooms(['peace', 'focus', 'collab'], 'What is the atmosphere?');
```

---

## Next Steps

1. **Deploy to production**: Configure CORS, add rate limiting
2. **Add authentication**: Implement API keys or JWT tokens
3. **Scale horizontally**: Run multiple RAG server instances
4. **Monitor performance**: Set up Prometheus metrics
5. **Enhance answers**: Integrate local LLM for better summarization

---

## Reference

- **API Contract:** `docs/PHASE4_PROVIDER_CONTRACT.md`
- **Protocol Models:** `shared/phase4_protocol.py`
- **Ingestion CLI:** `apps/ingest_rooms_cli.py`
- **Sample Data:** `tests/fixtures/rooms/`

For support, see [GitHub Issues](https://github.com/KBLLR/mlx-rag-lab/issues).

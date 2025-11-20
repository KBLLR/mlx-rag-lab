# Testing the Fusion RAG API

**Prerequisites:** Apple Silicon Mac (M1/M2/M3/M4) for MLX support

---

## Quick Start

### 1. Start the RAG API Server

```bash
cd mlx-rag-lab

# Ensure dependencies are installed
uv sync

# Start the FastAPI server
uv run uvicorn rag.api.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

### 2. Verify Server Health

```bash
curl http://localhost:8000/health | jq
```

**Expected response:**
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

### 3. List Available Profiles

```bash
curl http://localhost:8000/v1/fusion/profiles | jq
```

**Expected response:**
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
    },
    {
      "profile_id": "default",
      "collection": "general_knowledge",
      "default_k": 5,
      "default_threshold": 0.5,
      "metadata_schema": null,
      "description": "General-purpose knowledge base"
    }
  ],
  "request_id": "..."
}
```

---

### 4. Create Test Data (Campus Profile)

Before querying, you need to ingest some documents into the `campus` profile's collection:

```bash
curl -X POST http://localhost:8000/rag_upsert \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-upsert-001" \
  -d '{
    "collection": "campus_classroom_data",
    "documents": [
      {
        "content": "Photosynthesis is the process by which plants convert light energy into chemical energy. It occurs in chloroplasts and requires sunlight, water, and carbon dioxide. The products are glucose and oxygen.",
        "source": "biology_lesson_photosynthesis.md",
        "metadata": {
          "classroom_id": "bio-101",
          "subject": "biology",
          "teacher_id": "prof-smith",
          "date": "2024-03-15",
          "document_type": "lesson_notes"
        }
      },
      {
        "content": "Cell division is the process by which a parent cell divides into two daughter cells. There are two types: mitosis (for growth) and meiosis (for reproduction).",
        "source": "biology_lesson_cell_division.md",
        "metadata": {
          "classroom_id": "bio-101",
          "subject": "biology",
          "teacher_id": "prof-smith",
          "date": "2024-03-16",
          "document_type": "lesson_notes"
        }
      },
      {
        "content": "The Pythagorean theorem states that in a right triangle, a² + b² = c², where c is the hypotenuse.",
        "source": "math_lesson_pythagoras.md",
        "metadata": {
          "classroom_id": "math-201",
          "subject": "mathematics",
          "teacher_id": "prof-jones",
          "date": "2024-03-15",
          "document_type": "lesson_notes"
        }
      }
    ]
  }' | jq
```

**Expected response:**
```json
{
  "chunks_added": 3,
  "documents_processed": 3,
  "collection": "campus_classroom_data",
  "index_path": "var/indexes/campus_classroom_data/vdb.npz",
  "latency_ms": 234.5,
  "request_id": "test-upsert-001"
}
```

---

### 5. Test Fusion Query (Campus Profile)

```bash
curl -X POST http://localhost:8000/v1/fusion/query \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-query-002" \
  -d '{
    "profile_id": "campus",
    "query": "How does photosynthesis work?",
    "classroom_id": "bio-101",
    "top_k": 3
  }' | jq
```

**Expected response:**
```json
{
  "results": [
    {
      "text": "Photosynthesis is the process by which plants convert light energy into chemical energy. It occurs in chloroplasts and requires sunlight, water, and carbon dioxide. The products are glucose and oxygen.",
      "source": "biology_lesson_photosynthesis.md",
      "score": 0.87,
      "metadata": {
        "classroom_id": "bio-101",
        "subject": "biology",
        "teacher_id": "prof-smith",
        "date": "2024-03-15",
        "document_type": "lesson_notes"
      }
    }
  ],
  "trace": {
    "profile_id": "campus",
    "collection_used": "campus_classroom_data",
    "latency_ms": 45.2,
    "filters_applied": {
      "classroom_id": "bio-101"
    }
  },
  "tokens": null,
  "request_id": "test-query-002"
}
```

---

### 6. Test Query with Multiple Filters

```bash
curl -X POST http://localhost:8000/v1/fusion/query \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-query-003" \
  -d '{
    "profile_id": "campus",
    "query": "biology lessons",
    "filters": {
      "classroom_id": "bio-101",
      "subject": "biology",
      "date": "2024-03-15"
    },
    "top_k": 5
  }' | jq
```

---

### 7. Test Profile Not Found Error

```bash
curl -X POST http://localhost:8000/v1/fusion/query \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "nonexistent",
    "query": "test"
  }' | jq
```

**Expected error:**
```json
{
  "error": {
    "code": "InvalidRequestError",
    "message": "Profile 'nonexistent' not found. Available profiles: ['campus', 'avatar', 'default']",
    "status_code": 400
  }
}
```

---

### 8. Test Collection Not Found Error

```bash
curl -X POST http://localhost:8000/v1/fusion/query \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "avatar",
    "query": "test"
  }' | jq
```

**Expected error (if avatar collection doesn't exist):**
```json
{
  "error": {
    "code": "IndexNotFoundError",
    "message": "Collection 'avatar_knowledge_base' for profile 'avatar' does not exist",
    "status_code": 404
  }
}
```

---

## API Documentation

Once the server is running, visit:

**OpenAPI/Swagger UI:**
```
http://localhost:8000/docs
```

This provides interactive API documentation where you can:
- View all endpoints
- See request/response schemas
- Try out API calls directly in the browser

**ReDoc:**
```
http://localhost:8000/redoc
```

Alternative documentation format with cleaner layout.

---

## Integration Testing with Python

Create a simple test script:

```python
# test_fusion_api.py

import requests
import uuid

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] == True
    assert "latency_ms" in data
    print("✓ Health check passed")

def test_list_profiles():
    """Test profiles listing."""
    response = requests.get(f"{BASE_URL}/v1/fusion/profiles")
    assert response.status_code == 200
    data = response.json()
    assert "profiles" in data
    assert len(data["profiles"]) >= 3  # campus, avatar, default
    print(f"✓ Found {len(data['profiles'])} profiles")

def test_fusion_query():
    """Test fusion query endpoint."""
    request_id = str(uuid.uuid4())

    # First, ingest test data
    ingest_response = requests.post(
        f"{BASE_URL}/rag_upsert",
        headers={"X-Request-ID": request_id},
        json={
            "collection": "campus_classroom_data",
            "documents": [
                {
                    "content": "Test content about machine learning.",
                    "source": "test_doc.md",
                    "metadata": {
                        "classroom_id": "test-101",
                        "subject": "computer_science"
                    }
                }
            ]
        }
    )
    assert ingest_response.status_code == 200
    print("✓ Test data ingested")

    # Now query
    query_response = requests.post(
        f"{BASE_URL}/v1/fusion/query",
        headers={"X-Request-ID": request_id},
        json={
            "profile_id": "campus",
            "query": "machine learning",
            "classroom_id": "test-101",
            "top_k": 3
        }
    )
    assert query_response.status_code == 200
    data = query_response.json()
    assert "results" in data
    assert "trace" in data
    assert data["trace"]["profile_id"] == "campus"
    assert data["trace"]["collection_used"] == "campus_classroom_data"
    print(f"✓ Query returned {len(data['results'])} results in {data['trace']['latency_ms']:.2f}ms")

def test_invalid_profile():
    """Test error handling for invalid profile."""
    response = requests.post(
        f"{BASE_URL}/v1/fusion/query",
        json={
            "profile_id": "nonexistent",
            "query": "test"
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    print("✓ Invalid profile error handled correctly")

if __name__ == "__main__":
    print("Running Fusion API tests...\n")
    test_health()
    test_list_profiles()
    test_fusion_query()
    test_invalid_profile()
    print("\n✅ All tests passed!")
```

Run the test:

```bash
python test_fusion_api.py
```

---

## Performance Testing

### Latency Benchmark

```bash
#!/bin/bash
# benchmark_fusion.sh

echo "Fusion API Latency Benchmark"
echo "=============================="
echo

for i in {1..10}; do
  curl -s -X POST http://localhost:8000/v1/fusion/query \
    -H "Content-Type: application/json" \
    -H "X-Request-ID: bench-$i" \
    -d '{
      "profile_id": "campus",
      "query": "test query",
      "classroom_id": "bio-101",
      "top_k": 5
    }' | jq -r '.trace.latency_ms' | awk '{print "Request '$i': " $1 "ms"}'
done
```

---

## Troubleshooting

### Server Won't Start

**Error:** `ModuleNotFoundError: No module named 'rag'`

**Solution:** Make sure you're using `uv run`:
```bash
uv run uvicorn rag.api.main:app --reload --port 8000
```

**Error:** `mlx-data` incompatible platform

**Solution:** You're on Linux/Windows. MLX requires Apple Silicon. Deploy on M1/M2/M3/M4 Mac.

### Query Returns No Results

**Check:**
1. Does the collection exist? `ls var/indexes/campus_classroom_data/`
2. Did you ingest documents? Use `/rag_upsert` first
3. Is threshold too high? Try lowering to 0.3

### Profile Not Found

**Error:** `Profile 'campus' not found`

**Solution:** Check `src/rag/api/profiles.py` - make sure profile is registered.

---

## Next Steps

1. ✅ Verify server starts successfully
2. ✅ Test `/v1/fusion/profiles` endpoint
3. ✅ Ingest test data for campus profile
4. ✅ Test `/v1/fusion/query` with various filters
5. ✅ Verify error handling
6. ⬜ Integrate with mlx-openai-server
7. ⬜ Integrate with Smart Campus
8. ⬜ Deploy to production

---

**Document Version:** 1.0
**Last Updated:** 2025-11-20

# RAG CLI - Phase 4 Architecture

## Overview

The RAG CLI has been updated to align with **Phase 4 architecture**, supporting collection-based document management and the same file structure as the FastAPI Tier-3B service.

## Phase 4 Changes

### Collection-Based Architecture

**Before (Phase 3):**
- Single monolithic VectorDB: `var/indexes/vdb.npz`
- Flat source directory: `var/source_docs/*.pdf`
- No multi-collection support

**After (Phase 4):**
- Collection-based indexes: `var/indexes/{collection}/vdb.npz`
- Collection subdirectories: `var/source_docs/{collection}/*.pdf`
- Full multi-collection support
- Same structure as FastAPI API routes

### File Structure

```
var/
├── indexes/                    # Phase 4 index root
│   ├── default/                # Collection: default
│   │   ├── vdb.npz             # Vector database
│   │   └── vdb.npz.meta.json   # Metadata
│   ├── technical_docs/         # Collection: technical_docs
│   │   ├── vdb.npz
│   │   └── vdb.npz.meta.json
│   └── research/               # Collection: research
│       ├── vdb.npz
│       └── vdb.npz.meta.json
└── source_docs/                # Source document root
    ├── default/                # Sources for default collection
    │   ├── doc1.pdf
    │   └── doc2.pdf
    ├── technical_docs/         # Sources for technical_docs
    │   ├── mlx_guide.pdf
    │   └── api_reference.pdf
    └── research/               # Sources for research
        └── paper.pdf
```

## Usage

### Starting the CLI

```bash
# Use default collection
uv run rag-cli

# Use specific collection
uv run rag-cli --collection technical_docs

# Custom paths
uv run rag-cli --collection research \
               --index-root /custom/indexes \
               --source-root /custom/sources
```

### Available Commands

| Command | Description |
|---------|-------------|
| `rebuild` | Scan and rebuild current collection from source directory |
| `list` | Show all indexed documents in current collection |
| `collections` | Show all available collections with status |
| `help` | Show available commands |
| `exit` / `quit` | Exit the application |
| `<question>` | Query the RAG system |

### Workflow

#### 1. Create a Collection

```bash
# Create source directory
mkdir -p var/source_docs/my_collection

# Add PDFs
cp my_docs/*.pdf var/source_docs/my_collection/
```

#### 2. Build the Collection

```bash
# Start CLI with the collection
uv run rag-cli --collection my_collection

# In the CLI, rebuild
rebuild
```

#### 3. Query the Collection

```bash
# Type your question
What is MLX?

# View indexed documents
list

# See all collections
collections
```

### Collection Management

#### View All Collections

```
collections
```

Output:
```
┌──────────────────────────────────────────────┐
│    Collections (Phase 4 Architecture)        │
├──────────────────┬──────────────────┬────────┤
│ Collection       │ Status           │ Active │
├──────────────────┼──────────────────┼────────┤
│ default          │ ✓ Indexed        │   ●    │
│ research         │ ○ Source only    │        │
│ technical_docs   │ ✓ Indexed        │        │
└──────────────────┴──────────────────┴────────┘
```

**Status indicators:**
- `✓ Indexed` - Collection has both sources and index
- `○ Source only` - Collection has sources but no index (run `rebuild`)
- `⚠ Indexed (no source)` - Collection has index but source directory is empty/missing

#### Rebuild a Collection

The `rebuild` command scans the current collection's source directory and recreates the vector index:

```
rebuild
```

Output:
```
Rebuilding collection 'technical_docs'...
Source: var/source_docs/technical_docs
Index: var/indexes/technical_docs/vdb.npz

Found 5 PDF(s)

Processing technical_docs... ████████████████████ 100% 0:00:15

✓ Collection 'technical_docs' rebuilt successfully!
  • Processed: 5 PDF(s)
  • Chunks: 1,234
  • Index: var/indexes/technical_docs/vdb.npz
```

## Phase 4 Compliance

The CLI now follows the same conventions as the FastAPI API:

### File Paths

✅ Collections stored at: `{index_root}/{collection}/vdb.npz`
✅ Sources organized by: `{source_root}/{collection}/`
✅ Metadata files at: `{index_root}/{collection}/vdb.npz.meta.json`

### Ingestion Pipeline

✅ Uses same `gather_pdf_paths()` and `extract_text()` from `create_vdb.py`
✅ Chunking: 256 characters, 50 overlap (same as API)
✅ Metadata tracking per collection
✅ Embedding model: `sentence-transformers/all-MiniLM-L6-v2`

### Development vs Production

**CLI (Direct VDB Access):**
- For local development and testing
- Direct VectorDB access (no API server needed)
- Fast iteration on collections
- Rich terminal UI

**API (Phase 4 Endpoints):**
- For production Tier-2 integration
- HTTP REST endpoints (`/rag_query`, `/rag_upsert`, etc.)
- Request ID tracing and observability
- Latency measurement
- Full CRUD operations

## Arguments Reference

```
--collection <name>         Collection name (default: "default")
--index-root <path>         Root for all indexes (default: "var/indexes")
--source-root <path>        Root for source docs (default: "var/source_docs")
--model-id <id>             MLX model for generation
--reranker-id <id>          Cross-encoder for reranking
--top-k <n>                 Number of results to keep after reranking
--max-tokens <n>            Max tokens for generation
--no-reranker               Skip reranking step
```

## Examples

### Multi-Collection Workflow

```bash
# Build technical documentation collection
uv run rag-cli --collection technical_docs
rebuild
exit

# Build research papers collection
uv run rag-cli --collection research
rebuild
exit

# Query technical docs
uv run rag-cli --collection technical_docs
How does MLX handle embeddings?

# Switch to research collection
exit
uv run rag-cli --collection research
What are the latest findings on transformers?
```

### Integration with API

The CLI and API share the same index storage:

```bash
# Build collection via CLI
uv run rag-cli --collection my_docs
rebuild
exit

# Query via API
curl -X POST http://localhost:8000/rag_query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is MLX?",
    "collection": "my_docs",
    "k": 5
  }'
```

Both access the same `var/indexes/my_docs/vdb.npz` file.

## Migration from Phase 3

If you have an existing single VDB at `var/indexes/vdb.npz`:

```bash
# 1. Create default collection structure
mkdir -p var/indexes/default
mkdir -p var/source_docs/default

# 2. Move old index
mv var/indexes/vdb.npz var/indexes/default/
mv var/indexes/vdb.npz.meta.json var/indexes/default/ 2>/dev/null || true

# 3. Move source documents (if you had them in flat structure)
mv var/source_docs/*.pdf var/source_docs/default/ 2>/dev/null || true

# 4. Use the CLI
uv run rag-cli --collection default
```

## See Also

- [Phase 4 Provider Contract](./PHASE4_PROVIDER_CONTRACT.md) - FastAPI endpoints
- [Ingestion Pipeline](../src/rag/ingestion/create_vdb.py) - Batch ingestion tool
- [VectorDB Implementation](../src/rag/retrieval/vdb.py) - Core VDB class

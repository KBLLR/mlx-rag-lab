# Chat Workflows & Classification

## Overview

The Chat CLI provides conversational AI with automatic history saving and classification. Chats can be analyzed for sentiment, topics, and technical content, then used for document classification, RAG enhancement, or training data.

## Basic Usage

### Quick Start
```bash
# Simple chat (no save/classify)
uv run chat-cli

# Full featured: save + classify
uv run chat-cli --save-chat --classify-on-exit

# Via MLX Lab (interactive)
uv run mlxlab
# → Select: 💬 Chat - Conversational AI
```

### Available Modes

1. **chat** (default): Standard conversational assistant
2. **web**: Research mode - explicit about uncertainty, suggests verification
3. **thinking**: Step-by-step reasoning mode

```bash
uv run chat-cli --mode thinking --save-chat --classify-on-exit
```

### In-Chat Commands

- `/help` - Show available commands
- `/history` - Display conversation history
- `/clear` - Clear conversation history
- `/mode` - Show current interaction mode
- `/exit`, `/quit`, `/q` - Exit chat (triggers save/classify if enabled)

## Chat Storage & Classification

### Where Chats Are Saved

**Default location**: `var/chats/chat-YYYYMMDD-HHMMSS.json`

**Structure**:
```json
{
  "meta": {
    "timestamp": "2025-11-13T12:34:56",
    "model_id": "mlx-models/gpt-oss-20b-mxfp4",
    "mode": "chat",
    "max_tokens": 2048,
    "system_prompt": "You are a helpful..."
  },
  "history": [
    {"role": "user", "content": "What is MLX?"},
    {"role": "assistant", "content": "MLX is Apple's machine learning framework..."}
  ]
}
```

### Classification Output

When `--classify-on-exit` is enabled, the chat is analyzed using the LLM itself:

**Analyzed properties**:
- `overall_sentiment`: very negative | negative | neutral | positive | very positive
- `topics`: List of 3-8 high-level tags
- `has_technical_content`: true/false

**Example output**:
```json
{
  "overall_sentiment": "positive",
  "topics": ["machine learning", "Apple Silicon", "RAG", "MLX framework"],
  "has_technical_content": true
}
```

## Advanced Workflows

### 1. Document Classification from Chats

Use chat transcripts to build training data for document classifiers:

```bash
# Step 1: Have conversations on different topics
uv run chat-cli --mode chat --save-chat --classify-on-exit

# Step 2: Extract classified conversations
python scripts/extract_chat_topics.py var/chats/ --output var/training/chat_topics.json

# Step 3: Train classifier on chat patterns
uv run train-cli --data var/training/chat_topics.json --task classification
```

### 2. Chat-to-Embeddings Pipeline

Convert chat transcripts into vector embeddings for similarity search:

```python
from rag.models.model import Model
from pathlib import Path
import json
import mlx.core as mx

# Load embedding model
encoder = Model()

# Process saved chats
chats_dir = Path("var/chats")
for chat_file in chats_dir.glob("chat-*.json"):
    data = json.loads(chat_file.read_text())

    # Extract full conversation
    full_text = " ".join([
        msg["content"]
        for msg in data["history"]
    ])

    # Generate embedding
    embedding = encoder.run([full_text])

    # Save for retrieval
    # ... (add to VectorDB or separate index)
```

### 3. Multi-Bank Chat History

Organize chats by topic/project:

```bash
# Save to project-specific directory
uv run chat-cli \
  --save-chat \
  --output-dir var/chats/ml-research \
  --classify-on-exit

uv run chat-cli \
  --save-chat \
  --output-dir var/chats/code-review \
  --classify-on-exit
```

### 4. Sentiment Analysis Dashboard

Analyze sentiment trends across multiple conversations:

```python
from pathlib import Path
import json
from collections import Counter

# Scan all saved chats
chats = Path("var/chats").glob("chat-*.json")
sentiments = []

for chat_file in chats:
    data = json.loads(chat_file.read_text())
    # Classification stored inline with chat when --classify-on-exit used
    # Or re-classify on demand:
    # sentiment = classify_chat(data["history"])
    sentiments.append(data.get("sentiment", "neutral"))

# Aggregate
sentiment_counts = Counter(sentiments)
print(f"Positive: {sentiment_counts['positive']}")
print(f"Negative: {sentiment_counts['negative']}")
print(f"Neutral: {sentiment_counts['neutral']}")
```

### 5. RAG Enhancement with Chat Context

Use chat history to improve RAG retrieval:

```python
from rag.retrieval.vdb import VectorDB
from rag.models.model import Model

# Load chat history
chat_data = json.loads(Path("var/chats/chat-20251113-123456.json").read_text())

# Extract key topics from conversation
topics = [msg["content"] for msg in chat_data["history"] if msg["role"] == "user"]

# Use as context for VectorDB query
vdb = VectorDB("var/indexes/my-bank/vdb.npz")
results = vdb.query(" ".join(topics[-3:]), k=10)  # Last 3 user messages

# Generate response with chat context
from libs.mlx_core.model_engine import MLXModelEngine
model = MLXModelEngine("mlx-models/gpt-oss-20b-mxfp4")

context = "\n".join([r["text"] for r in results])
prompt = f"Previous conversation: {topics}\n\nContext: {context}\n\nQuestion: {user_input}"
response = model.generate(prompt, max_tokens=512)
```

## Classification Models

### Current: LLM-based Classification

The chat CLI uses the loaded LLM (GPT-OSS 20B, Phi-3, etc.) to classify conversations. This provides:
- ✅ Zero-shot classification (no training needed)
- ✅ Contextual understanding
- ✅ Flexible taxonomy (can analyze any property)
- ⚠️ Requires model inference (slower, uses GPU)

### Alternative: Embedding-based Classification

For faster classification at scale, use the existing `classify-cli`:

```bash
# Extract all user messages from chat
python scripts/chat_to_text.py var/chats/chat-*.json --output var/temp/chat_texts.txt

# Classify using embeddings
uv run classify-cli \
  --mode sentiment \
  --texts-file var/temp/chat_texts.txt \
  --output var/classifications/chat_sentiment.json
```

**Embedding-based pros**:
- ⚡ Much faster (no LLM generation)
- 📊 Consistent scores across runs
- 🔢 Suitable for batch processing 1000s of chats

**Embedding-based cons**:
- ❌ Less contextual understanding
- ❌ Fixed label set (sentiment/emotion/custom)
- ❌ May miss nuanced conversation dynamics

## Tips & Best Practices

### For Training Data Collection
1. Use consistent `--mode` for similar conversation types
2. Enable `--classify-on-exit` to auto-label conversations
3. Review classifications before using as training data (LLMs can be wrong)

### For Production Use
1. Implement chat archival strategy (chats grow large)
2. Use `--output-dir` to organize by project/topic
3. Consider privacy: scrub sensitive info before saving

### For Performance
1. Disable `--classify-on-exit` for casual chats (saves tokens)
2. Use `--max-tokens 512` for faster responses (vs 2048)
3. Local models (mlx-models/) avoid repeated downloads

### For Analysis
1. Save raw chat + classification separately (easier to reprocess)
2. Store metadata (timestamp, model, mode) for reproducibility
3. Version your classification schema (overall_sentiment v1, v2, etc.)

## Integration Examples

### With Ingest Pipeline

```bash
# 1. Chat about documents
uv run chat-cli --save-chat --output-dir var/chats/doc-review

# 2. Extract key points from chat
python scripts/extract_key_points.py var/chats/doc-review/ > var/temp/key_points.txt

# 3. Ingest as supplementary context
echo "var/temp/key_points.txt" >> var/source_docs/my-bank/supplementary.txt
uv run ingest-cli --banks-root var/source_docs --output-dir var/indexes
```

### With Classification Pipeline

```bash
# Classify saved chats in batch
for chat in var/chats/*.json; do
  uv run classify-cli \
    --text "$(jq -r '.history[].content' $chat | tr '\n' ' ')" \
    --mode zero-shot \
    --labels technical casual question-answering creative \
    --output "var/classifications/$(basename $chat)"
done
```

## Future Enhancements

Potential additions tracked in project tasks:

- [ ] Chat session management (resume previous chat by ID)
- [ ] Multi-turn topic tracking (detect topic shifts)
- [ ] Chat merging (combine related conversations)
- [ ] Automatic summarization on exit
- [ ] Export to common formats (Markdown, CSV)
- [ ] Chat-based fine-tuning dataset generator

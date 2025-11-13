# GPT-OSS Chat Wrapper Usage Guide

## Overview

The `ChatSession` wrapper provides clean abstraction for GPT-OSS 20B (and other MLX LLMs) with:
- ✅ Proper `tokenizer.chat_template` usage
- ✅ Structured conversation history
- ✅ Real streaming support
- ✅ Tool/function calling hooks (for future MCP integration)

## Quick Start

### Single-Turn Chat

```python
from rag.chat import ChatSession

# Initialize session
session = ChatSession(
    model_id="mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx",
    system_prompt="You are a helpful AI assistant specialized in MLX and Apple Silicon.",
    max_tokens=512
)

# Single question
response = session.chat("What is MLX?")
print(response)
```

### Multi-Turn Conversation

```python
from rag.chat import ChatSession

session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")

# Turn 1
response1 = session.chat("What is Apple Silicon?")
print(f"Assistant: {response1}\n")

# Turn 2 (continues conversation)
response2 = session.chat("How does it compare to x86?")
print(f"Assistant: {response2}\n")

# Turn 3
response3 = session.chat("Give me 3 key advantages")
print(f"Assistant: {response3}\n")

# View full history
print("\nConversation History:")
for msg in session.get_history():
    print(f"{msg['role']}: {msg['content'][:50]}...")
```

### Streaming Chat (Real-time)

```python
from rag.chat import ChatSession

session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")

print("Assistant: ", end="", flush=True)
for token in session.chat_stream("Explain quantum computing in simple terms"):
    print(token, end="", flush=True)
print("\n")
```

### Interactive Chat Loop

```python
from rag.chat import ChatSession

def main():
    session = ChatSession(
        "mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx",
        system_prompt="You are a helpful assistant.",
        max_tokens=1024
    )

    print("Chat session started. Type 'exit' to quit, 'clear' to reset history.\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ['exit', 'quit']:
            break

        if user_input.lower() == 'clear':
            session.clear_history(keep_system=True)
            print("History cleared.\n")
            continue

        # Stream response
        print("Assistant: ", end="", flush=True)
        for token in session.chat_stream(user_input):
            print(token, end="", flush=True)
        print("\n")

if __name__ == "__main__":
    main()
```

## Advanced Features

### Custom System Prompts

```python
from rag.chat import ChatSession

# Researcher mode
researcher = ChatSession(
    "mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx",
    system_prompt=(
        "You are a research assistant. Provide detailed, well-cited responses. "
        "Be explicit about uncertainty and avoid fabricating sources."
    )
)

# Code helper mode
coder = ChatSession(
    "mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx",
    system_prompt=(
        "You are a coding assistant. Provide complete, runnable code examples. "
        "Explain your reasoning step-by-step. Prefer modern Python patterns."
    )
)
```

### Manual History Management

```python
from rag.chat import ChatSession, Message, Role

session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")

# Add messages manually
session.messages.append(Message(Role.USER, "What's 2+2?"))
session.messages.append(Message(Role.ASSISTANT, "2+2 equals 4."))

# Continue from this point
response = session.chat("What about 3+3?")
print(response)  # Model has context of previous math question
```

### Local vs HuggingFace Models

```python
from pathlib import Path
from rag.chat import ChatSession

# Check if local model exists
local_model = Path("mlx-models/gpt-oss-20b-mxfp4")

if local_model.exists():
    # Use local (faster, no download)
    session = ChatSession(str(local_model))
else:
    # Auto-download from HuggingFace (~12GB first run)
    session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")
```

### Non-Streaming for Batch Processing

```python
from rag.chat import ChatSession

session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")

questions = [
    "What is MLX?",
    "How does it use Metal?",
    "What models are available?"
]

answers = []
for q in questions:
    # Non-streaming, add to history
    answer = session.chat(q, add_to_history=True)
    answers.append(answer)
    print(f"Q: {q}")
    print(f"A: {answer}\n")
```

### One-Shot Questions (No History)

```python
from rag.chat import ChatSession

session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")

# Don't add to history - useful for independent queries
answer1 = session.chat("What is 2+2?", add_to_history=False)
answer2 = session.chat("What is the capital of France?", add_to_history=False)

# History remains empty
assert len(session.messages) == 1  # Only system message
```

## Integration Patterns

### With RAG (Retrieval-Augmented Generation)

```python
from rag.chat import ChatSession
from rag.retrieval.vdb import VectorDB

# Load VectorDB
vdb = VectorDB("var/indexes/my-docs/vdb.npz")

# Initialize chat
session = ChatSession(
    "mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx",
    system_prompt="You are an assistant with access to technical documentation. Use provided context to answer."
)

def rag_query(question: str, top_k: int = 5) -> str:
    """Query with RAG context."""

    # Retrieve relevant chunks
    results = vdb.query(question, k=top_k)
    context = "\n\n".join([r["text"] for r in results])

    # Build augmented prompt
    augmented_question = f"Context:\n{context}\n\nQuestion: {question}"

    # Generate answer with context
    return session.chat(augmented_question)

# Use it
answer = rag_query("How does MLX optimize for Apple Silicon?")
print(answer)
```

### With Classification

```python
from rag.chat import ChatSession
from rag.models.text_classifier import TextClassifier

session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")
classifier = TextClassifier()

# Have conversation
response = session.chat("I love using MLX on my M3 Mac!")

# Classify sentiment
sentiment = classifier.analyze_sentiment([response])[0]
print(f"Assistant sentiment: {sentiment}")

# Adjust based on sentiment (example)
if sentiment.get("negative", 0) > 0.7:
    session.add_system_message("Note: User seems frustrated. Be more helpful and patient.")
```

## Architecture Notes

### Why This Design?

**Separation of Concerns**:
- `ChatSession` manages conversation state
- `Message` represents individual turns
- `_format_prompt()` handles template logic
- `chat()` / `chat_stream()` handle generation
- `_post_process()` cleans output

**Extensibility**:
- `Role` enum supports future tool calling
- `register_tool()` / `execute_tool_loop()` are hooks for MCP integration
- `temperature` / `top_p` parameters ready for custom sampling (when MLX supports)

**Chat Template Priority**:
1. Try `tokenizer.chat_template` (model-specific formatting)
2. Fallback to simple concatenation
3. Warn user if template missing

### Future: Tool Calling & MCP Integration

The wrapper includes hooks for future function calling:

```python
# Placeholder API (not yet implemented)
session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")

# Register tools
session.register_tool(
    name="search_docs",
    description="Search technical documentation",
    callback=lambda query: vdb.query(query, k=5)
)

session.register_tool(
    name="run_code",
    description="Execute Python code safely",
    callback=safe_exec
)

# Model can now "call" these tools
response = session.execute_tool_loop("Find info about MLX arrays and show an example")
```

**Requirements for full implementation**:
1. Tool schema in system prompt (JSON format)
2. Parser for tool call syntax in model output
3. Execution layer with sandboxing
4. Tool result injection back into conversation

**MCP Server Integration** (future):
- Wrap `ChatSession` in MCP server
- Expose as `chat` resource
- Tools become MCP tools
- Supports stateful conversations across requests

## Performance Tips

### Memory Management

```python
# Clear history periodically for long conversations
if len(session.messages) > 50:
    # Keep last 10 messages + system prompt
    recent = session.messages[:1] + session.messages[-10:]
    session.messages = recent
```

### Faster Response (Trade Quality)

```python
# Use smaller max_tokens for quick responses
session = ChatSession(
    "mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx",
    max_tokens=128  # vs default 512
)
```

### Batch Processing

```python
# Create session once, reuse for multiple queries
session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")

for question in large_question_list:
    answer = session.chat(question, add_to_history=False)
    # Process answer...
```

## Troubleshooting

### Model Not Found

```bash
# Download GPT-OSS 20B locally
uv run python scripts/download_gpt_oss_20b.py

# Then use local path
session = ChatSession("mlx-models/gpt-oss-20b-mxfp4")
```

### Chat Template Warning

If you see:
```
Warning: mlx-community/XXX has no chat_template, using fallback formatting
```

This means the model doesn't define a chat template. Fallback formatting still works but may not match model's training format. Consider using a model with explicit chat template support.

### Streaming Issues

If streaming doesn't work:
- Ensure you're calling `chat_stream()` not `chat()`
- Check MLX version (`mlx_lm>=0.18`)
- Try non-streaming first to verify model loads

### Out of Memory

```python
# Use quantized model
session = ChatSession("mlx-community/Phi-3-mini-4k-instruct-4bit")  # Smaller

# Or reduce max_tokens
session.max_tokens = 256
```

## Comparison with Old chat_cli.py

**Old (apps/chat_cli.py)**:
- ❌ Manual string formatting
- ❌ No chat_template usage
- ❌ Tight coupling (prompt + model + history mixed)
- ❌ Fake streaming flag (not wired)

**New (src/rag/chat/gpt_oss_wrapper.py)**:
- ✅ Proper chat_template with fallback
- ✅ Clean separation: Message, Role, ChatSession
- ✅ Real streaming via `mlx_lm.stream_generate`
- ✅ Extensible for tools/MCP

**Migration Path**:
Update `apps/chat_cli.py` to use `ChatSession` internally instead of `MLXModelEngine` directly.

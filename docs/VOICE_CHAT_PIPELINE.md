# Voice Chat Pipeline: GPT-OSS + Marvis TTS

## Architecture Overview

```
User Input (text)
    ↓
ChatSession (GPT-OSS 20B)
    - Manages conversation history
    - Uses tokenizer.chat_template
    - Generates response
    ↓
Response Text
    ↓
MarvisTTSClient (Marvis TTS 100m)
    - Synthesizes speech
    - Returns audio array
    ↓
Audio Output (WAV file + optional playback)
```

## Components

### 1. Chat Wrapper (`src/rag/chat/gpt_oss_wrapper.py`)

**Purpose**: Clean abstraction for GPT-OSS conversation management

**Key Features**:
- ✅ Proper `tokenizer.chat_template` usage
- ✅ Structured `Message` / `Role` system
- ✅ Real streaming via `mlx_lm.stream_generate`
- ✅ Conversation history management
- ✅ Tool/function calling hooks (for future MCP)

**API**:
```python
from rag.chat import ChatSession

session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")

# Blocking
response = session.chat("What is MLX?")

# Streaming
for token in session.chat_stream("Explain quantum computing"):
    print(token, end="", flush=True)
```

### 2. TTS Wrapper (`src/rag/tts/marvis_tts.py`)

**Purpose**: Text-to-speech for Apple Silicon

**Key Features**:
- ✅ Marvis TTS 100m model
- ✅ Metal (MPS) acceleration
- ✅ WAV output
- ✅ Configurable voice/language
- ✅ Batch processing

**API**:
```python
from rag.tts import MarvisTTSClient, TTSConfig

client = MarvisTTSClient("Marvis-AI/marvis-tts-100m-v0.2")

# Synthesize
audio = client.synthesize("Hello world!")

# Save
client.save_wav(audio, "output.wav")

# One-shot
client.stream_to_file("Hello!", "hello.wav")
```

### 3. Voice Chat CLI (`apps/voice_chat_cli.py`)

**Purpose**: Full pipeline integration

**Features**:
- ✅ Interactive chat loop
- ✅ Automatic audio generation
- ✅ Audio file saving
- ✅ Text streaming option
- ✅ Conversation history

## Usage

### Quick Start

```bash
# Install dependencies (if not already)
pip install transformers torch torchaudio soundfile

# Interactive voice chat
uv run voice-chat-cli

# With custom models
uv run voice-chat-cli \
  --chat-model mlx-models/gpt-oss-20b-mxfp4 \
  --tts-model Marvis-AI/marvis-tts-100m-v0.2
```

### Single Query

```bash
# One-shot: question → audio
uv run voice-chat-cli --single "What is machine learning?"

# Output:
# - Console: text response
# - var/voice_chat/response_TIMESTAMP.wav
```

### Advanced Options

```bash
uv run voice-chat-cli \
  --chat-model mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx \
  --max-tokens 256 \
  --stream \
  --output-dir var/my_voice_sessions \
  --system-prompt "You are a concise assistant. Be brief."
```

**Flags**:
- `--chat-model`: GPT-OSS or other MLX model
- `--tts-model`: TTS model (default: Marvis)
- `--max-tokens`: Response length (shorter = faster TTS)
- `--stream`: Stream text as it generates (then TTS)
- `--output-dir`: Where to save audio
- `--no-save-audio`: Skip saving (just show text)
- `--single "text"`: One-shot mode

### Interactive Commands

While in interactive mode:
- `/exit`, `/quit`, `/q` - Exit
- `/clear` - Clear conversation history
- `/history` - Show conversation history

## Performance Notes

### Latency Breakdown

**Typical flow** (M3 Max, GPT-OSS 20B MXFP4):
1. **Text generation**: 2-5s for 128 tokens
2. **TTS synthesis**: 1-3s for ~50 words
3. **Total**: 3-8s per response

**Optimization tips**:
- Use `--max-tokens 256` (vs 512) for faster responses
- Shorter system prompt = less processing
- Local models (mlx-models/) avoid download delays

### Memory Usage

- **GPT-OSS 20B MXFP4**: ~12GB
- **Marvis TTS 100m**: ~400MB
- **Total**: ~12.5GB (fits M3 Max with headroom)

### Metal Acceleration

Both models use Metal (MPS):
```python
# Chat: MLX native (Metal backend)
# TTS: PyTorch MPS backend

# Verify Metal is used:
import torch
print(torch.backends.mps.is_available())  # Should be True
```

## Integration Examples

### 1. Voice-Augmented RAG

```python
from rag.chat import ChatSession
from rag.tts import MarvisTTSClient
from rag.retrieval.vdb import VectorDB

# Setup
vdb = VectorDB("var/indexes/docs/vdb.npz")
chat = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")
tts = MarvisTTSClient()

def voice_rag_query(question: str):
    # Retrieve context
    results = vdb.query(question, k=5)
    context = "\n".join([r["text"] for r in results])

    # Generate answer
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    answer = chat.chat(prompt)

    # Speak answer
    audio = tts.synthesize(answer)
    tts.save_wav(audio, "answer.wav")

    return answer

# Use it
voice_rag_query("How does MLX optimize for Apple Silicon?")
```

### 2. Batch Audio Generation

```python
from rag.tts import batch_synthesize

questions_and_answers = [
    "What is MLX? MLX is Apple's ML framework...",
    "How fast is it? Very fast on M-series chips...",
    "Who made it? Apple's ML research team..."
]

batch_synthesize(
    questions_and_answers,
    output_dir="var/audio_dataset",
    prefix="qa"
)
# Creates: qa_000.wav, qa_001.wav, qa_002.wav
```

### 3. Streaming Text + Final Audio

```python
from rag.chat import ChatSession
from rag.tts import MarvisTTSClient

chat = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")
tts = MarvisTTSClient()

# Stream text for user to see
full_response = ""
print("Assistant: ", end="", flush=True)
for token in chat.chat_stream("Explain neural networks"):
    print(token, end="", flush=True)
    full_response += token
print()

# Then synthesize complete response
audio = tts.synthesize(full_response)
tts.save_wav(audio, "response.wav")
```

## Troubleshooting

### TTS Dependencies Missing

```bash
pip install transformers torch torchaudio soundfile scipy
```

### Metal Not Available

If TTS falls back to CPU:
```python
import torch
print(torch.backends.mps.is_available())  # Check Metal
print(torch.backends.mps.is_built())      # Check build
```

**Fix**: Ensure PyTorch has MPS support:
```bash
pip install --upgrade torch torchvision torchaudio
```

### Chat Template Warnings

```
Warning: mlx-community/XXX has no chat_template, using fallback
```

This is OK - fallback formatting still works. For best results, use models with explicit chat templates (GPT-OSS 20B should have one).

### Audio Quality Issues

Try adjusting TTS config:
```python
from rag.tts import TTSConfig

config = TTSConfig(
    sample_rate=22050,  # Try 16000 or 44100
    speed=1.0,          # Adjust playback speed
    language="en"
)

audio = tts.synthesize(text, config)
```

## Comparison: Old vs New

### Old `apps/chat_cli.py` Issues

❌ **Broken chat formatting**:
```python
# Manual string concat - no chat_template
prompt = f"System: {system}\nUser: {user}\nAssistant:"
```

❌ **Hallucinating responses**:
```
Assistant: Sure! Here's a simple Python function...
User: I need to write a function...  # Fake user message!
Assistant: Sure! Here's a simple...   # Repeating!
```

❌ **No real streaming**: Flag existed but not wired

### New Architecture

✅ **Proper chat template**:
```python
# Uses tokenizer.chat_template or smart fallback
prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
```

✅ **Clean separation**:
- `ChatSession`: conversation management
- `Message` / `Role`: structured messages
- `_format_prompt()`: template logic
- `chat()` / `chat_stream()`: generation

✅ **Real streaming**:
```python
for token in session.chat_stream("..."):
    print(token, end="")  # Actual streaming from MLX
```

✅ **TTS integration**: Complete voice pipeline

## Future Enhancements

### Tool Calling (Planned)

```python
session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")

# Register tools
session.register_tool(
    name="search",
    description="Search documentation",
    callback=lambda q: vdb.query(q, k=5)
)

# Model can call tools
response = session.execute_tool_loop("Find info about MLX arrays")
```

### MCP Server Integration (Planned)

Wrap `ChatSession` as MCP server resource:
```python
# Expose chat as MCP resource
# - Stateful conversations
# - Tool calling via MCP tools
# - Multi-client support
```

### Real-time Audio Streaming (Future)

Instead of synthesizing full response:
```python
# Stream audio as text is generated
for token in session.chat_stream("..."):
    audio_chunk = tts.synthesize_chunk(token)
    play_audio_chunk(audio_chunk)
```

Requires:
- Streaming TTS model
- Audio player integration
- Buffer management

## File Layout

```
src/rag/
├── chat/
│   ├── __init__.py
│   └── gpt_oss_wrapper.py      # ChatSession, Message, Role
├── tts/
│   ├── __init__.py
│   └── marvis_tts.py            # MarvisTTSClient, TTSConfig
└── cli/
    └── entrypoints.py           # voice_chat_cli_main

apps/
└── voice_chat_cli.py            # VoiceChatPipeline, main()

docs/
├── CHAT_WRAPPER_USAGE.md        # ChatSession examples
└── VOICE_CHAT_PIPELINE.md       # This file
```

## Dependencies

**Core** (already in project):
- `mlx` - Apple's ML framework
- `mlx_lm` - MLX language models
- `transformers` - Model loading
- `rich` - Console output

**TTS-specific** (may need install):
```bash
pip install torch torchaudio soundfile scipy
```

## Quick Reference

```bash
# Interactive voice chat
uv run voice-chat-cli

# Single query
uv run voice-chat-cli --single "Hello!"

# Custom models + stream
uv run voice-chat-cli \
  --chat-model mlx-models/gpt-oss-20b-mxfp4 \
  --max-tokens 256 \
  --stream

# No audio saving (just show text)
uv run voice-chat-cli --no-save-audio

# Custom output location
uv run voice-chat-cli --output-dir my_audio_sessions
```

**Python API**:
```python
# Chat only
from rag.chat import ChatSession
session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")
response = session.chat("Hello!")

# TTS only
from rag.tts import MarvisTTSClient
tts = MarvisTTSClient()
audio = tts.synthesize("Hello world!")
tts.save_wav(audio, "hello.wav")

# Full pipeline
from apps.voice_chat_cli import VoiceChatPipeline
pipeline = VoiceChatPipeline("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")
text, audio_path = pipeline.process_message("What is MLX?")
```

# Musicgen Vision and Configuration Session - 2025-11-08

## 1. Current Vision for mlx-RAG + MusicGen (Ground Truth Version)

**Core Audio Stack:** Meta's MusicGen over a 32 kHz EnCodec tokenizer with 4 codebooks sampled at 50 Hz. Single-stage autoregressive Transformer.

**Model Zoo:** `musicgen-small` currently; Meta also exposes `medium`, `large`, and `melody` checkpoints.

**MLX Side:** Using the `encodec-32khz` variant converted to MLX (e.g., `mlx-community/encodec-32khz-float32`) plugged into the MLX MusicGen example.

**Sane High-Level Vision for mlx-RAG:**

> **Text RAG core**, with optional **multimodal renderers**:
> *   MusicGen for **music/soundscapes**
> *   FLUX for **images**
> *   Llasa (or similar) for **voice**

MusicGen's job is:
*   Provide **emotion / atmosphere** around RAG outputs.
*   Allow **configurable, reproducible audio behaviors** (styles, moods, durations).
*   Later, act as a **music prototyping tool** driven by the knowledge graph / RAG context.

## 2. MusicGen Configuration Surface (What Knobs Actually Matter)

### 2.1. Model-Level Configuration

*   `model_size`: "small" | "medium" | "large" | "melody"
*   `backend`: `mlx` (future-proofing)

Example:
```yaml
musicgen:
  model:
    size: small
    backend: mlx
```

### 2.2. Generation-Level Configuration

**Core knobs:**
*   `duration_s`: float (converts to `max_steps = ceil(duration_s * steps_per_second)`)
*   `use_sampling`: bool
*   `top_k`: int
*   `top_p`: float
*   `temperature`: float
*   `cfg_coef`: float (Classifier-free guidance strength)
*   `two_step_cfg`: bool (stub for now)

**Adapter-specific knobs:**
*   `normalize_duration`: "crop" | "pad" | "strict"
*   `loudness_normalization`: `bool`

Example Config Block (Base Preset):
```yaml
musicgen:
  defaults:
    duration_s: 8
    use_sampling: true
    top_k: 250
    top_p: 0.0
    temperature: 1.0
    cfg_coef: 3.0
    normalize_duration: crop
```

### 2.3. Prompt-Level Metadata

*   `prepend_tags`: list of style / mood tokens.
*   `append_structure`: e.g., "with a clear intro, build, and outro."
*   `language`: "english, spanish, ..."

## 3. Presets for MusicGen (Styles, Roles, and Quality Tiers)

### 3.1. Style / Mood Presets

Bundles of `prompt_tags`, generation params, and default `duration_s`.

Example:
```yaml
musicgen:
  presets:
    ambient_lofi:
      description: "Chill, minimal, loopable background bed"
      prompt_tags:
        - "warm lo-fi hip hop"
        - "soft drums, vinyl crackle"
        - "no sudden changes"
      duration_s: 20
      top_k: 250
      temperature: 0.8
      cfg_coef: 2.5
    # ... other style presets
```

### 3.2. Functional Presets (What the Music is *For*)

Control duration, repetition, and dynamics, independent of style.

Example:
```yaml
musicgen:
  roles:
    ui_sfx:
      duration_s: 1.0
      temperature: 0.9
      top_k: 150
    # ... other role presets
```

### 3.3. Quality Tiers (Model Size + Parameters)

Map to MusicGen's small/medium/large lineup for "preview vs final" behavior.

Example:
```yaml
musicgen:
  quality:
    preview:
      model_size: small
      max_duration_s: 10
      steps_per_second: 50
    # ... other quality tiers
```

## 4. Flows: MusicGen ↔ RAG

### 4.1. RAG → MusicGen (Context-Conditioned Music)

**Flow A: Answer with soundtrack**
1.  User query → RAG pipeline → answer + metadata.
2.  Music selection policy chooses style preset and role.
3.  Build prompt: `"{preset_tags}. {summary_of_topic}. {emotional_tone_description}."`
4.  Call `MusicgenAdapter.generate_music(...)` with merged config.
5.  Attach `.wav` path to answer payload.

**Flow B: Contextual "scene" soundscapes**
*   RAG retrieves page chunk, tags `environment` and `time`.
*   Use dedicated `environment_*` preset group.
*   Generate 30–60 second loops; mix under narration or show in UI.

### 4.2. MusicGen → RAG (Soft Integration)

**1. Prompt reflection → RAG**
*   Log full prompt text, chosen preset/style/role, and user query.
*   This becomes extra context for RAG to suggest music presets.

**2. Metadata RAG over music catalog**
*   Store generated tracks with structured metadata (prompt, mood tags, style, tempo).
*   Allow RAG to search over this metadata for candidate tracks.

### 4.3. Flow Design for CLI & Programmatic Usage

**Programmatic API:**
```python
music = music_service.generate(
    text_context=answer_text,
    role="background_bed",
    preset="ambient_lofi",
    quality="preview",
)
```

**CLI:**
```bash
rag musicgen \
  --context-file answer.txt \
  --preset ambient_lofi \
  --role background_bed \
  --quality preview \
  --out var/music/answer1.wav
```

**Internal Logic:**
1.  Extract semantic features.
2.  Compose MusicGen prompt.
3.  Resolve config from `preset + role + quality`.
4.  Call adapter.
5.  Return path + structured metadata.

## Next Steps

Define the config schema properly in code and wire one or two flows end-to-end (e.g., "answer with optional background music" first).

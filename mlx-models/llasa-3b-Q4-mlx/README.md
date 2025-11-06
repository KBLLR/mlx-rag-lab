---
base_model:
- srinivasbilla/llasa-3b
- HKUST-Audio/Llasa-3B
tags:
- mlx
---

# srinivasbilla/llasa-3b-Q4-mlx

The Model [srinivasbilla/llasa-3b-Q4-mlx](https://huggingface.co/srinivasbilla/llasa-3b-Q4-mlx) was converted to MLX format from [srinivasbilla/llasa-3b](https://huggingface.co/srinivasbilla/llasa-3b) using mlx-lm version **0.20.5**.

## Use with mlx

```bash
pip install mlx-lm
```

```python
from mlx_lm import load, generate

model, tokenizer = load("srinivasbilla/llasa-3b-Q4-mlx")

prompt="hello"

if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template is not None:
    messages = [{"role": "user", "content": prompt}]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

response = generate(model, tokenizer, prompt=prompt, verbose=True)
```
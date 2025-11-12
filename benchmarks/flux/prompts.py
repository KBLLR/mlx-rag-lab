# benchmarks/flux/prompts.py

"""
Prompt library for Flux benchmarking.

You can reference these by key (e.g. --prompt-key astronaut_horse)
or just pass a raw --prompt string.
"""

PROMPTS = {
    # Your classic benchmark meme
    "astronaut_horse": "a photo of an astronaut riding a horse on mars",
    # Faster 'schnell pic' style benchmark
    "schnell_pic": (
        "a cinematic photo of an astronaut riding a horse on mars, "
        "dramatic lighting, shallow depth of field"
    ),
    # Pro portrait baseline
    "pro_portrait": (
        "ultra-detailed professional studio portrait of a person, "
        "sharp focus, soft lighting, 85mm lens, high dynamic range, 8k"
    ),
    # LoRA-style subject prompt template (for dreambooth-ish adapters)
    "lora_subject": (
        "a photo of <sks> dog lying on the sand at a beach in Greece, "
        "golden hour, detailed fur, natural colors"
    ),
}


def list_prompt_keys():
    """Return available prompt keys."""
    return sorted(PROMPTS.keys())


def resolve_prompt(key_or_text: str) -> str:
    """
    If key_or_text matches a known prompt key, return that prompt.
    Otherwise, treat it as a raw prompt string.
    """
    return PROMPTS.get(key_or_text, key_or_text)

from __future__ import annotations

from typing import Any, Dict, Generator, Optional, Tuple

import mlx.core as mx
import mlx.nn as nn

from mlx_lm.generate import generate_step as _generate_step
from mlx_lm.sample_utils import make_sampler, make_logits_processors


Array = mx.array


def generate_step(
    prompt: Array,
    model: nn.Module,
    *,
    # old-style API:
    temp: float = 0.0,
    temperature: Optional[float] = None,
    top_p: float = 1.0,
    repetition_penalty: Optional[float] = None,
    repetition_context_size: int = 20,
    logit_bias: Optional[Dict[int, float]] = None,
    max_tokens: int = 256,
    # allow newer kwargs to pass through
    **kwargs: Any,
) -> Generator[Tuple[Array, Array], None, None]:
    """
    Backwards-compatible wrapper around mlx_lm.generate.generate_step.

    This lets you keep calling:

        generate_step(prompt, model, temperature=0.7, top_p=0.9, ...)

    even though the real generate_step now takes `sampler` and `logits_processors`.
    """
    # Prefer explicit `temperature`, fall back to `temp`
    if temperature is not None:
        temp = float(temperature)

    sampler = make_sampler(
        temp=temp,
        top_p=top_p,
    )

    logits_processors = make_logits_processors(
        logit_bias=logit_bias,
        repetition_penalty=repetition_penalty,
        repetition_context_size=repetition_context_size,
    )

    # Delegate to the real function
    yield from _generate_step(
        prompt=prompt,
        model=model,
        max_tokens=max_tokens,
        sampler=sampler,
        logits_processors=logits_processors,
        **kwargs,
    )

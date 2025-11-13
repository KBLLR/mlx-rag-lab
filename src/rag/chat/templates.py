"""
Chat templating helpers for GPT-OSS style models.

Provides utilities to sanitize assistant outputs that include
`<|channel|>analysis` / `<|channel|>final` control tags so they can be
round-tripped through tokenizer.chat_template safely.
"""

from __future__ import annotations

import re
from typing import Iterable

CHANNEL_BLOCK_RE = re.compile(
    r"<\|channel\|\>(?P<channel>[^<]+)<\|message\|\>(?P<content>.*?)<\|end\|>",
    re.DOTALL,
)


def extract_channel_blocks(text: str) -> list[tuple[str, str]]:
    """Return all (<channel>, content) blocks found in text."""
    blocks: list[tuple[str, str]] = []
    for match in CHANNEL_BLOCK_RE.finditer(text):
        channel = match.group("channel").strip().lower()
        content = match.group("content").strip()
        blocks.append((channel, content))
    return blocks


def strip_channel_controls(text: str) -> str:
    """
    Remove GPT-OSS control tags, preferring the 'final' channel content if present.
    """
    blocks = extract_channel_blocks(text)
    if blocks:
        # Prefer the most recent 'final' block, otherwise last block
        cleaned = None
        for channel, content in reversed(blocks):
            if "final" in channel:
                cleaned = content
                break
        if cleaned is None:
            cleaned = blocks[-1][1]
        text = cleaned
    # Remove residual control markers
    control_tokens: Iterable[str] = [
        "<|start|>assistant",
        "<|assistant|>",
        "<|endoftext|>",
        "<|end|>",
        "<|analysis|>",
        "<|final|>",
        "<|message|>",
        "<|channel|>",
    ]
    for token in control_tokens:
        text = text.replace(token, " ")

    # Drop echoed "User: ..." that models sometimes append
    if "\nUser:" in text:
        text = text.split("\nUser:")[0]

    # Normalize whitespace but keep sentence breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

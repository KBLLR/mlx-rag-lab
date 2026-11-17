"""Saved chunk text must be read back from a running offset.

The old decoder set the read position to the current chunk length instead of
advancing past that chunk, so every chunk after the second came back wrong.
"""

from __future__ import annotations

import os

from rag.retrieval.vdb import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    chunks_to_mx_array,
    mx_array_to_chunks,
)


def test_mx_array_to_chunks_keeps_text_after_the_second_chunk():
    chunks = ["aa", "bbb", "cccc", "d"]
    data = [ord(char) for text in chunks for char in text]
    lengths = [len(text) for text in chunks]

    assert mx_array_to_chunks(data, lengths) == chunks

    encoded, encoded_lengths = chunks_to_mx_array(chunks)
    assert mx_array_to_chunks(encoded, encoded_lengths) == chunks


def test_chunk_settings_keep_defaults_when_unset():
    if os.getenv("RAG_CHUNK_SIZE") is None:
        assert CHUNK_SIZE == 256
    if os.getenv("RAG_CHUNK_OVERLAP") is None:
        assert CHUNK_OVERLAP == 50

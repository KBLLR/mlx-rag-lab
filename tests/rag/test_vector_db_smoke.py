"""Smoke tests for the VectorDB ingestion and query pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from rag.retrieval.vdb import VectorDB


def test_vector_db_round_trip(tmp_path: Path):
    vdb = VectorDB()
    vdb.ingest("Apples are rich in fiber and vitamins.", "doc_apples.txt")
    vdb.ingest("Bananas provide potassium and quick energy.", "doc_bananas.txt")

    out_path = tmp_path / "demo" / "vdb.npz"
    vdb.savez(out_path)

    reloaded = VectorDB(str(out_path))
    results = reloaded.query("apples fiber", k=3)

    assert results, "expected at least one retrieved chunk"
    assert any("Apples" in chunk["text"] for chunk in results)
    assert all("source" in chunk for chunk in results)


def test_ingest_skips_empty_documents():
    vdb = VectorDB()
    vdb.ingest("", "empty_doc.txt")

    assert vdb.embeddings is None
    assert vdb.content == []

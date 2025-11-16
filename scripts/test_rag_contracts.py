"""Ad-hoc contract tests for the Phase-0 RAG API.

This script intentionally lives outside of src/ so it can evolve without
touching the deployed FastAPI service. It exercises the public endpoints and
validates that the responses still match the canonical Pydantic schemas.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from dataclasses import dataclass
from typing import Callable, Coroutine, Iterable, List

import httpx
from httpx import AsyncClient, HTTPStatusError, RequestError
from pydantic import ValidationError

from src.rag.api.schemas import (
    Document,
    HealthResponse,
    QueryOptions,
    RagQueryRequest,
    RagQueryResponse,
    RagStatsResponse,
    RagUpsertRequest,
    RagUpsertResponse,
    UpsertOptions,
)

PASS = "✓"
FAIL = "✗"


@dataclass
class TestResult:
    name: str
    success: bool
    detail: str


async def verify_health(client: AsyncClient) -> str:
    resp = await client.get("/health")
    resp.raise_for_status()
    payload = HealthResponse.model_validate(resp.json())
    return f"status={payload.status} tier={payload.tier} model={payload.embedding_model or 'n/a'}"


async def verify_upsert(client: AsyncClient, request: RagUpsertRequest) -> str:
    resp = await client.post("/rag_upsert", json=request.model_dump())
    resp.raise_for_status()
    payload = RagUpsertResponse.model_validate(resp.json())
    return f"bank={payload.bank_name} chunks_added={payload.chunks_added} docs={payload.documents_processed}"


async def verify_query(client: AsyncClient, request: RagQueryRequest) -> str:
    resp = await client.post("/rag_query", json=request.model_dump())
    resp.raise_for_status()
    payload = RagQueryResponse.model_validate(resp.json())
    return f"results={len(payload.results)} bank={payload.bank_name}"


async def verify_stats(client: AsyncClient, bank_name: str) -> str:
    resp = await client.get("/rag_stats", params={"bank_name": bank_name})
    resp.raise_for_status()
    payload = RagStatsResponse.model_validate(resp.json())
    return f"chunks={payload.num_chunks} docs={payload.num_documents} model={payload.embedding_model}"


async def run_test(
    name: str,
    coro_factory: Callable[[], Coroutine[None, None, str]],
) -> TestResult:
    try:
        detail = await coro_factory()
        return TestResult(name=name, success=True, detail=detail)
    except HTTPStatusError as exc:
        body = exc.response.text
        detail = f"{exc.response.status_code} {exc.request.method} {exc.request.url.path} :: {body[:200]}"
        return TestResult(name=name, success=False, detail=detail)
    except RequestError as exc:
        return TestResult(name=name, success=False, detail=f"request error: {exc}")
    except ValidationError as exc:
        return TestResult(name=name, success=False, detail=f"schema mismatch: {exc}")
    except Exception as exc:  # pragma: no cover - catch-all for unexpected issues
        return TestResult(name=name, success=False, detail=f"unexpected error: {exc}")


def render_results(results: Iterable[TestResult]) -> None:
    for result in results:
        icon = PASS if result.success else FAIL
        print(f"{icon} {result.name}: {result.detail}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate RAG API contracts.")
    parser.add_argument(
        "--base-url",
        default=os.getenv("RAG_API_BASE_URL", "http://localhost:8000"),
        help="RAG API base URL (default: %(default)s or $RAG_API_BASE_URL)",
    )
    parser.add_argument(
        "--bank",
        default=os.getenv("RAG_API_BANK", "default"),
        help="Bank name to use for contract validation (default: %(default)s or $RAG_API_BANK)",
    )
    parser.add_argument(
        "--query",
        default=os.getenv("RAG_API_CONTRACT_QUERY", "How does MLX handle embeddings?"),
        help="Query text for /rag_query tests.",
    )
    return parser


async def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    upsert_request = RagUpsertRequest(
        bank_name=args.bank,
        documents=[
            Document(
                content="MLX RAG contract test document. Safe to delete.",
                source="contract_test.md",
                metadata={"category": "contract-tests"},
            )
        ],
        options=UpsertOptions(chunk_size=128, chunk_overlap=32),
    )
    query_request = RagQueryRequest(
        bank_name=args.bank,
        query=args.query,
        options=QueryOptions(top_k=3, rerank=False),
    )

    client_timeout = float(os.getenv("RAG_API_TIMEOUT", "15"))

    async with AsyncClient(base_url=args.base_url, timeout=client_timeout) as client:
        tests: List[TestResult] = []
        tests.append(await run_test("GET /health", lambda: verify_health(client)))
        tests.append(
            await run_test(
                "POST /rag_upsert",
                lambda: verify_upsert(client, upsert_request),
            )
        )
        tests.append(
            await run_test(
                "POST /rag_query",
                lambda: verify_query(client, query_request),
            )
        )
        tests.append(
            await run_test(
                "GET /rag_stats",
                lambda: verify_stats(client, bank_name=args.bank),
            )
        )

    render_results(tests)
    return 0 if all(result.success for result in tests) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except RequestError as exc:
        print(f"{FAIL} Unable to reach server: {exc}")
        raise SystemExit(1)

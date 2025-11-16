"""Rich-powered CLI dashboard for monitoring the RAG API service health."""

from __future__ import annotations

import asyncio
import os
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, Dict, Mapping, MutableMapping

import httpx
from httpx import AsyncClient, HTTPStatusError, RequestError
from pydantic import ValidationError
from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.rag.api.schemas import HealthResponse, RagStatsResponse

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_BANK = "default"
DEFAULT_TIMEOUT = 15.0
DEFAULT_REFRESH = 5.0

LAT_HEALTH = "GET /health"
LAT_STATS = "GET /rag_stats"


@dataclass
class RuntimeConfig:
    base_url: str
    bank: str
    timeout: float
    refresh_interval: float
    env_values: Mapping[str, str]


@dataclass
class DashboardState:
    reachable: bool
    health: HealthResponse | None
    stats: RagStatsResponse | None
    errors: Dict[str, str]
    timestamp: float


def parse_float(value: str | None, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


def load_config() -> RuntimeConfig:
    refresh_env = os.getenv("RAG_DASHBOARD_REFRESH") or os.getenv(
        "RAG_HEALTH_REFRESH", str(DEFAULT_REFRESH)
    )
    env_values: Dict[str, str] = {
        "RAG_API_BASE_URL": os.getenv("RAG_API_BASE_URL", DEFAULT_BASE_URL),
        "RAG_API_BANK": os.getenv("RAG_API_BANK", DEFAULT_BANK),
        "RAG_API_TIMEOUT": os.getenv("RAG_API_TIMEOUT", str(DEFAULT_TIMEOUT)),
        "RAG_DASHBOARD_REFRESH": refresh_env,
    }
    return RuntimeConfig(
        base_url=env_values["RAG_API_BASE_URL"],
        bank=env_values["RAG_API_BANK"],
        timeout=parse_float(env_values["RAG_API_TIMEOUT"], DEFAULT_TIMEOUT),
        refresh_interval=parse_float(env_values["RAG_DASHBOARD_REFRESH"], DEFAULT_REFRESH),
        env_values=env_values,
    )


async def fetch_health(
    client: AsyncClient,
    latencies: MutableMapping[str, Deque[float]],
) -> tuple[HealthResponse | None, str | None]:
    start = time.perf_counter()
    try:
        response = await client.get("/health")
        response.raise_for_status()
        payload = HealthResponse.model_validate(response.json())
        latencies[LAT_HEALTH].append((time.perf_counter() - start) * 1000)
        return payload, None
    except HTTPStatusError as exc:
        return None, f"{exc.response.status_code} {exc.request.method} {exc.request.url.path}"
    except RequestError as exc:
        return None, f"request error: {exc}"
    except ValidationError as exc:
        return None, f"schema mismatch: {exc}"


async def fetch_stats(
    client: AsyncClient,
    bank: str,
    latencies: MutableMapping[str, Deque[float]],
) -> tuple[RagStatsResponse | None, str | None]:
    start = time.perf_counter()
    try:
        response = await client.get("/rag_stats", params={"bank_name": bank})
        response.raise_for_status()
        payload = RagStatsResponse.model_validate(response.json())
        latencies[LAT_STATS].append((time.perf_counter() - start) * 1000)
        return payload, None
    except HTTPStatusError as exc:
        return None, f"{exc.response.status_code} {exc.request.method} {exc.request.url.path}"
    except RequestError as exc:
        return None, f"request error: {exc}"
    except ValidationError as exc:
        return None, f"schema mismatch: {exc}"


async def collect_state(
    client: AsyncClient,
    config: RuntimeConfig,
    latencies: MutableMapping[str, Deque[float]],
) -> DashboardState:
    errors: Dict[str, str] = {}
    health, health_error = await fetch_health(client, latencies)
    reachable = health is not None
    if health_error:
        errors[LAT_HEALTH] = health_error

    stats = None
    if reachable:
        stats, stats_error = await fetch_stats(client, config.bank, latencies)
        if stats_error:
            errors[LAT_STATS] = stats_error
    else:
        errors.setdefault(LAT_STATS, "skipped (server offline)")

    return DashboardState(
        reachable=reachable,
        health=health,
        stats=stats,
        errors=errors,
        timestamp=time.time(),
    )


def build_server_panel(state: DashboardState) -> Panel:
    table = Table.grid(padding=(0, 1))
    status_text = Text("ONLINE", style="bold green") if state.reachable else Text("OFFLINE", style="bold red")
    table.add_row("Status", status_text)
    if state.health:
        table.add_row("Tier", state.health.tier)
        table.add_row("Models loaded", "yes" if state.health.models_loaded else "no")
    if state.health and state.health.embedding_model:
        table.add_row("Preferred model", state.health.embedding_model)
    ts = datetime.fromtimestamp(state.timestamp).strftime("%Y-%m-%d %H:%M:%S")
    table.add_row("Last refresh", ts)
    if not state.reachable and state.errors.get(LAT_HEALTH):
        table.add_row("Error", state.errors[LAT_HEALTH])
    return Panel(table, title="Server Reachability", box=box.ROUNDED)


def build_config_panel(config_values: Mapping[str, str]) -> Panel:
    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("Environment Variable")
    table.add_column("Value", overflow="fold")
    for key, value in config_values.items():
        table.add_row(key, value or "<unset>")
    return Panel(table, title="Active Config (env)", box=box.ROUNDED)


def build_embedding_panel(state: DashboardState) -> Panel:
    table = Table(box=box.SIMPLE)
    table.add_column("Field")
    table.add_column("Value", overflow="fold")
    if state.health:
        table.add_row("Model (health)", state.health.embedding_model or "n/a")
    if state.stats:
        table.add_row("Model (stats)", state.stats.embedding_model)
        if state.stats.embedding_dim is not None:
            table.add_row("Embedding dim", str(state.stats.embedding_dim))
    if not state.health and not state.stats:
        table.add_row("Info", "No data available (server offline)")
    return Panel(table, title="Embedding Models", box=box.ROUNDED)


def build_index_panel(state: DashboardState, bank: str) -> Panel:
    if not state.stats:
        message = "No stats available"
        if not state.reachable:
            message = "Waiting for server..."
        return Panel(message, title=f"Index Stats [{bank}]", box=box.ROUNDED)

    stats = state.stats
    table = Table(box=box.SIMPLE)
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Bank", stats.bank_name)
    table.add_row("Documents", f"{stats.num_documents}")
    table.add_row("Chunks", f"{stats.num_chunks}")
    table.add_row("Chunk size", f"{stats.chunk_size}")
    table.add_row("Overlap", f"{stats.chunk_overlap}")
    if stats.created_at:
        table.add_row("Created", stats.created_at)
    if stats.updated_at:
        table.add_row("Updated", stats.updated_at)
    return Panel(table, title=f"Index Stats [{bank}]", box=box.ROUNDED)


def build_latency_panel(latencies: Mapping[str, Deque[float]]) -> Panel:
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("Endpoint")
    table.add_column("Last (ms)", justify="right")
    table.add_column("Avg (ms)", justify="right")
    table.add_column("Samples", justify="right")
    for endpoint, samples in latencies.items():
        last = f"{samples[-1]:.1f}" if samples else "-"
        avg = f"{(sum(samples) / len(samples)):.1f}" if samples else "-"
        table.add_row(endpoint, last, avg, str(len(samples)))
    return Panel(table, title="Recent Latency", box=box.ROUNDED)


def build_error_panel(state: DashboardState) -> Panel:
    if not state.errors:
        return Panel("No active errors", title="Errors", box=box.ROUNDED, style="green")
    lines = [f"{endpoint}: {message}" for endpoint, message in state.errors.items()]
    text = "\n".join(lines)
    return Panel(text, title="Errors", box=box.ROUNDED, style="red")


def render_layout(
    state: DashboardState,
    config: RuntimeConfig,
    latencies: Mapping[str, Deque[float]],
) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="top", size=9),
        Layout(name="middle", ratio=2),
        Layout(name="bottom", size=10),
    )
    layout["top"].split_row(
        Layout(name="server"),
        Layout(name="config"),
    )
    layout["middle"].split_row(
        Layout(name="embedding"),
        Layout(name="index"),
    )
    layout["bottom"].split_row(
        Layout(name="latency", ratio=3),
        Layout(name="errors", ratio=2),
    )

    layout["top"]["server"].update(build_server_panel(state))
    layout["top"]["config"].update(build_config_panel(config.env_values))
    layout["middle"]["embedding"].update(build_embedding_panel(state))
    layout["middle"]["index"].update(build_index_panel(state, config.bank))
    layout["bottom"]["latency"].update(build_latency_panel(latencies))
    layout["bottom"]["errors"].update(build_error_panel(state))
    return layout


async def run_dashboard() -> None:
    console = Console()
    latencies: Dict[str, Deque[float]] = {
        LAT_HEALTH: deque(maxlen=20),
        LAT_STATS: deque(maxlen=20),
    }

    config = load_config()
    console.print(
        f"[bold cyan]Starting RAG health dashboard[/] → {config.base_url} (bank: {config.bank})",
    )

    async with AsyncClient(base_url=config.base_url, timeout=config.timeout) as client:
        with Live(console=console, refresh_per_second=4, transient=False) as live:
            while True:
                state = await collect_state(client, config, latencies)
                live.update(render_layout(state, config, latencies))
                await asyncio.sleep(config.refresh_interval)


def main() -> None:
    try:
        asyncio.run(run_dashboard())
    except KeyboardInterrupt:
        Console().print("\n[bold yellow]Dashboard stopped by user.[/]")


if __name__ == "__main__":
    main()

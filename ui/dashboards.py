"""
Pre-built dashboard layouts for specific use cases.
"""

from typing import Optional

from rich.columns import Columns
from rich.console import Group
from rich.table import Table
from rich.text import Text  # kept for future formatting / consistency

from .molecules import stat_card
from .theme import style


def build_chat_dashboard(
    model_name: Optional[str],
    total_messages: int,
    last_latency: Optional[float] = None,
) -> Group:
    """Build a small stat dashboard for chat-oriented pipelines."""
    cards = [
        stat_card("Model", model_name),
        stat_card("Messages", str(total_messages)),
    ]

    if last_latency is not None:
        cards.append(
            stat_card(
                "Last Response",
                f"{last_latency:.2f}",
                unit="s",
            )
        )

    return Group(
        Columns(
            cards,
            equal=True,
            expand=True,
        )
    )


def build_rag_dashboard(
    vdb_path: str,
    num_chunks: int,
    model_name: str,
    last_query: Optional[str] = None,
) -> Group:
    """Build a compact RAG status dashboard."""
    table = Table.grid(padding=(0, 2))

    # Left column = label, right column = value
    table.add_column(style("text.muted"), style=style("text.muted"))
    table.add_column(style("text.primary"), style=style("text.primary"))

    table.add_row("VDB:", vdb_path)
    table.add_row("Chunks:", f"{num_chunks:,}")
    table.add_row("Model:", model_name)

    if last_query:
        # Truncate long queries to keep the layout tight
        if len(last_query) > 50:
            display_query = last_query[:50] + "..."
        else:
            display_query = last_query

        table.add_row("Last Query:", display_query)

    return Group(table)


def build_musicgen_dashboard(
    model_size: str,
    duration: float,
    prompt: str,
) -> Group:
    """Build a dashboard for MusicGen runs."""
    cards = [
        stat_card("Model", model_size),
        stat_card("Duration", f"{duration:.1f}", unit="s"),
    ]

    meta_table = Table.grid(padding=(0, 2))
    meta_table.add_column(style("text.muted"), style=style("text.muted"))
    meta_table.add_column(style("text.primary"), style=style("text.primary"))

    if len(prompt) > 60:
        display_prompt = prompt[:60] + "..."
    else:
        display_prompt = prompt

    meta_table.add_row("Prompt:", display_prompt)

    return Group(
        Columns(
            cards,
            equal=True,
            expand=True,
        ),
        meta_table,
    )

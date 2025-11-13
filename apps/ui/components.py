"""Shared UI components for CLI applications."""

import statistics
from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

from apps.ui.console import get_console
from apps.ui.utils import get_confidence_color, format_percentage, format_duration


def render_header(title: str, meta: dict[str, Any] | None = None) -> None:
    """Render a fixed header panel with title and metadata.

    Args:
        title: The main title to display
        meta: Optional dictionary of metadata to display (key-value pairs)

    Example:
        render_header("Chat CLI", {"Model": "GPT-OSS", "Temp": 0.7, "Tokens": 512})
    """
    console = get_console()

    if meta:
        meta_str = " | ".join(f"{k}: {v}" for k, v in meta.items())
        content = f"[header]{title}[/header]\n[dim]{meta_str}[/dim]"
    else:
        content = f"[header]{title}[/header]"

    panel = Panel(
        content,
        border_style="blue",
        padding=(0, 1),
    )
    console.print(panel)


def render_footer(hints: list[str]) -> None:
    """Render a fixed footer with hints/shortcuts.

    Args:
        hints: List of hint strings to display

    Example:
        render_footer(["/help", "/history", "/clear", "/exit"])
    """
    console = get_console()

    hint_str = " | ".join(hints)
    panel = Panel(
        f"[footer]{hint_str}[/footer]",
        border_style="cyan",
        padding=(0, 1),
    )
    console.print(panel)


def render_confidence_bars(
    predictions: list[dict[str, Any]], max_width: int = 20, show_scores: bool = True
) -> None:
    """Render horizontal bar chart for confidence scores.

    Args:
        predictions: List of prediction dictionaries with 'label' and 'score' keys
        max_width: Maximum width of the bar in characters
        show_scores: Whether to show numeric scores alongside bars

    Example:
        predictions = [
            {"label": "positive", "score": 0.85},
            {"label": "neutral", "score": 0.10},
            {"label": "negative", "score": 0.05},
        ]
        render_confidence_bars(predictions)
    """
    console = get_console()

    for pred in predictions:
        label = pred["label"]
        score = pred["score"]
        filled = int(score * max_width)
        bar = "█" * filled + "░" * (max_width - filled)
        color = get_confidence_color(score)

        if show_scores:
            score_str = format_percentage(score)
            console.print(f"[{color}]{bar}[/{color}] {label} ({score_str})")
        else:
            console.print(f"[{color}]{bar}[/{color}] {label}")


def render_task_progress(
    current: int,
    total: int,
    current_item: str | None = None,
    speed: float | None = None,
    eta: float | None = None,
) -> Progress:
    """Create a Rich Progress instance for task tracking.

    Args:
        current: Current progress count
        total: Total items to process
        current_item: Optional name of current item being processed
        speed: Optional processing speed (items/sec)
        eta: Optional estimated time remaining in seconds

    Returns:
        Rich Progress object

    Example:
        progress = render_task_progress(45, 150, "file.pdf", 2.3, 45.0)
    """
    console = get_console()

    progress = Progress(
        TextColumn("[progress]{task.description}"),
        BarColumn(),
        TextColumn("[progress]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    )

    task_desc = f"Processing {current}/{total}"
    if current_item:
        task_desc += f" - {current_item}"

    progress.add_task(task_desc, completed=current, total=total)

    if speed is not None:
        console.print(f"[dim]Speed: {speed:.1f} items/sec[/dim]")

    if eta is not None:
        console.print(f"[dim]ETA: {format_duration(eta)}[/dim]")

    return progress


def show_confidence_warning(predictions: list[dict[str, float]]) -> None:
    """Show warning when predictions are too uniform (low confidence).

    Args:
        predictions: List of prediction dictionaries with 'score' key

    Example:
        predictions = [
            {"label": "positive", "score": 0.12},
            {"label": "neutral", "score": 0.12},
            {"label": "negative", "score": 0.11},
        ]
        show_confidence_warning(predictions)  # Will show warning
    """
    console = get_console()

    scores = [p["score"] for p in predictions]
    if len(scores) < 2:
        return

    std_dev = statistics.stdev(scores)
    if std_dev < 0.05:
        console.print("[warning]⚠ Low confidence: scores too uniform[/warning]")
        console.print("[dim]Model is uncertain about this classification[/dim]")


def show_system_warning(message: str, details: str | None = None) -> None:
    """Display a system warning message.

    Args:
        message: Main warning message
        details: Optional additional details

    Example:
        show_system_warning("High memory usage detected", "Consider clearing cache")
    """
    console = get_console()

    if details:
        content = f"[warning]⚠ {message}[/warning]\n[dim]{details}[/dim]"
    else:
        content = f"[warning]⚠ {message}[/warning]"

    panel = Panel(
        content,
        border_style="yellow",
        title="Warning",
        padding=(0, 1),
    )
    console.print(panel)


def render_results_table(
    data: list[dict[str, Any]],
    columns: list[str],
    title: str | None = None,
    show_header: bool = True,
) -> None:
    """Render a results table with Rich formatting.

    Args:
        data: List of dictionaries containing row data
        columns: List of column names to display
        title: Optional table title
        show_header: Whether to show column headers

    Example:
        data = [
            {"text": "Hello", "label": "positive", "score": 0.95},
            {"text": "Goodbye", "label": "negative", "score": 0.87},
        ]
        render_results_table(data, ["text", "label", "score"], "Classification Results")
    """
    console = get_console()

    table = Table(title=title, show_header=show_header, header_style="bold cyan")

    # Add columns
    for col in columns:
        table.add_column(col.title(), style="white")

    # Add rows
    for row in data:
        values = [str(row.get(col, "")) for col in columns]
        table.add_row(*values)

    console.print(table)


def render_chat_message(role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
    """Render a single chat message with formatting.

    Args:
        role: Message role (user, assistant, system)
        content: Message content
        metadata: Optional metadata (e.g., timestamp, token count)

    Example:
        render_chat_message("user", "How does RAG work?")
        render_chat_message("assistant", "RAG combines...", {"tokens": 150})
    """
    console = get_console()

    role_colors = {
        "user": "cyan",
        "assistant": "green",
        "system": "yellow",
    }

    color = role_colors.get(role.lower(), "white")
    prefix = f"[{color}]{role.title()}:[/{color}]"

    if metadata:
        meta_str = " | ".join(f"{k}: {v}" for k, v in metadata.items())
        console.print(f"{prefix} {content}")
        console.print(f"[dim]{meta_str}[/dim]")
    else:
        console.print(f"{prefix} {content}")

    console.print()  # Add blank line after message

"""
Loading spinners, progress indicators, and Live update helpers.
"""

from contextlib import contextmanager
from typing import Any

from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text  # kept for future formatting / consistency

from .theme import get_console, style


@contextmanager
def status_spinner(
    text: str = "state.loading",
    style_token: str = "text.info",
):
    """
    Show a Rich spinner with a styled status message while a block is running.

    Usage:
        with status_spinner("Loading models...", "state.loading"):
            do_expensive_stuff()
    """
    console = get_console()
    spinner = Spinner(
        "dots",
        text=text,
        style=style(style_token),
    )
    with console.status(spinner):
        yield


def transition_to_screen(
    old_layout: Any,
    new_layout: Any,
    console: Any | None = None,
    steps: int = 3,
    step_delay: float = 0.1,
) -> None:
    """
    Simple Live-based transition between two layouts.

    For now this is effectively:
      - render old_layout once
      - wait `step_delay`
      - swap to `new_layout`

    `steps` is reserved for future multi-step animations.
    """
    import time

    if console is None:
        console = get_console()

    # Render old_layout, then swap to new_layout after a brief delay
    with Live(old_layout, console=console, refresh_per_second=10) as live:
        time.sleep(step_delay)
        live.update(new_layout)

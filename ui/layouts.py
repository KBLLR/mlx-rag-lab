"""
Device frame layout builder for fixed-header CLI apps.
"""

import time
from contextlib import contextmanager
from typing import Any

from rich import box
from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

# Adjust import to your package structure if needed
from .theme import get_console, style


def _count_lines(renderable: RenderableType) -> int:
    """Best-effort line count for sizing header regions.

    - Text: use `plain` content split by newline
    - str: split by newline
    - anything else: assume a small fixed height
    """
    if isinstance(renderable, Text):
        return len(renderable.plain.split("\n"))
    if isinstance(renderable, str):
        return len(renderable.split("\n"))
    # Fallback default height for unknown renderables
    return 5


def _get_border_box() -> box.Box | None:
    """Return a Rich box style based on UI settings.

    border_style in settings:
      - "square"  -> box.SQUARE
      - "minimal" -> box.MINIMAL
      - "none"    -> no border (None)
      - anything else -> box.SQUARE
    """
    # Local import matches the disassembled code
    from .settings import load_ui_settings

    settings = load_ui_settings()
    border_style = settings.get("border_style", "square")

    if border_style == "square":
        return box.SQUARE
    if border_style == "minimal":
        return box.MINIMAL
    if border_style == "none":
        return None
    return box.SQUARE


def build_frame(
    header_renderable: RenderableType,
    caption_renderable: RenderableType | None = None,
    body_renderable: RenderableType | None = None,
    footer_renderable: RenderableType | None = None,
    border_color: str = "frame.border",
) -> Layout:
    """Build a Rich Layout with fixed header/footer and framed body.

    Layout structure:

        ┌─────────────────────────┐
        │ header (fixed size)     │
        ├─────────────────────────┤
        │ body   (flex / fill)    │
        ├─────────────────────────┤  ← only if footer_renderable
        │ footer (fixed size)     │
        └─────────────────────────┘

    Sizing logic:

    - Header height is based on header_renderable plus:
        +2 lines padding
        +caption height (+1 extra line) if present
    - Footer is either 2 or 0 lines depending on footer_renderable.
    """
    layout = Layout()

    # Estimate header height
    header_lines = _count_lines(header_renderable) + 2
    if caption_renderable:
        header_lines += _count_lines(caption_renderable) + 1

    # Footer height
    footer_lines = 2 if footer_renderable else 0

    # Split layout vertically
    if footer_renderable:
        layout.split_column(
            Layout(name="header", size=header_lines),
            Layout(name="body"),
            Layout(name="footer", size=footer_lines),
        )
    else:
        layout.split_column(
            Layout(name="header", size=header_lines),
            Layout(name="body"),
        )

    # Settings + border configuration
    from .settings import load_ui_settings

    settings = load_ui_settings()
    border_box = _get_border_box()
    transparent_frame = settings.get("transparent_frame", False)

    # Header content: header + optional caption stacked
    header_content: RenderableType = header_renderable
    if caption_renderable:
        header_content = Group(header_renderable, caption_renderable)

    # Header background style
    if transparent_frame:
        header_style = ""
    else:
        header_style = style("frame.bg")

    # Header: either plain padding or framed Panel
    if border_box is None:
        # No frame: just padded content
        from rich.padding import Padding

        layout["header"].update(Padding(header_content, (0, 2)))
    else:
        layout["header"].update(
            Panel(
                header_content,
                border_style=style(border_color),
                box=border_box,
                padding=(0, 2),
                style=header_style,
            )
        )

    # Body: always wrapped in a Panel, but box style may differ
    body_content: RenderableType = body_renderable or ""

    if border_box is None:
        # No global frame, but body still gets a square box
        layout["body"].update(
            Panel(
                body_content,
                box=box.SQUARE,
                border_style=style(border_color),
                padding=(1, 2),
                style=style("frame.bg"),
            )
        )
    else:
        layout["body"].update(
            Panel(
                body_content,
                border_style=style(border_color),
                box=border_box,
                padding=(1, 2),
                style=style("frame.bg"),
            )
        )

    # Footer, if present
    if footer_renderable:
        if transparent_frame:
            footer_style = ""
        else:
            # style(token, bold=True, dim=True) per disassembly
            footer_style = style("frame.bg", True, dim=True)

        if border_box is None:
            from rich.padding import Padding

            layout["footer"].update(Padding(footer_renderable, (0, 2)))
        else:
            layout["footer"].update(
                Panel(
                    footer_renderable,
                    border_style=style(border_color),
                    box=border_box,
                    padding=(0, 2),
                    style=footer_style,
                )
            )

    return layout


@contextmanager
def live_frame(
    layout: Layout,
    console: Console | None = None,
    refresh_per_second: int = 4,
    screen: bool = True,
) -> Any:
    """Context manager wrapping a layout in a Rich Live display.

    Yields the `Live` instance so callers can manually refresh / update.
    """
    if console is None:
        console = get_console()

    with Live(
        layout,
        console=console,
        refresh_per_second=refresh_per_second,
        screen=screen,
        auto_refresh=True,
    ) as live:
        yield live


def show_app_splash(
    app_id: str,
    console: Console | None = None,
    duration: float = 1.5,
) -> None:
    """Show a framed ASCII splash screen for a given app id.

    Uses APP_METADATA from app_frames and theming from theme.get_app_color.
    """
    if console is None:
        console = get_console()

    # Local imports to match the decompiled structure
    from .app_frames import APP_METADATA
    from .theme import get_app_color

    metadata = APP_METADATA.get(app_id, APP_METADATA.get("mlxlab", {}))
    color_token = get_app_color(app_id)

    ascii_art = Text(
        metadata.get("ascii", ""),
        style=style(color_token, True, bold=True),
    )
    title = Text(
        metadata.get("title", ""),
        style=style(color_token, True, bold=True),
    )
    caption = Text(
        metadata.get("caption", ""),
        style=style("text.secondary"),
    )

    splash = Group(
        Text(""),
        Align.center(ascii_art),
        Text(""),
        Align.center(title),
        Align.center(caption),
        Text(""),
    )

    console.clear()
    console.print(
        Panel(
            splash,
            border_style=style(color_token, True, bold=True),
            padding=(3, 5),
            style=style("frame.bg"),
        ),
        justify="center",
    )

    time.sleep(duration)

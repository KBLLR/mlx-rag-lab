"""
Full-screen framed app with fixed header/footer and scrollable body.
For apps that need true device frame layout with scroll support.
"""

from __future__ import annotations

import threading
from typing import Callable, List, Optional

from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .app_frames import APP_METADATA
from .theme import get_app_color, get_console, style


class ScrollableBody:
    """Manages scrollable content with viewport tracking."""

    def __init__(self, max_lines: int = 1000) -> None:
        self.lines: List[RenderableType] = []
        self.scroll_offset: int = 0
        self.max_lines: int = max_lines
        self.auto_scroll: bool = True
        self._lock = threading.Lock()

    def add_line(self, line: RenderableType) -> None:
        """Append a single line to the scrollback."""
        with self._lock:
            self.lines.append(line)

            # Trim scrollback if it exceeds max_lines
            if len(self.lines) > self.max_lines:
                self.lines = self.lines[-self.max_lines :]

            # If user has scrolled up, try to keep view stable
            if self.scroll_offset > 0:
                self.scroll_offset = max(0, self.scroll_offset - 1)

            # Auto-scroll to bottom if enabled
            if self.auto_scroll:
                self.scroll_offset = max(0, len(self.lines) - 1)

    def add_lines(self, lines: List[RenderableType]) -> None:
        """Append multiple lines to the scrollback."""
        with self._lock:
            self.lines.extend(lines)

            if len(self.lines) > self.max_lines:
                self.lines = self.lines[-self.max_lines :]

            if self.auto_scroll:
                self.scroll_offset = max(0, len(self.lines) - 1)

    def clear(self) -> None:
        """Clear all lines and reset scroll."""
        with self._lock:
            self.lines = []
            self.scroll_offset = 0

    def scroll_up(self, amount: int = 1) -> None:
        """Scroll up by a number of lines."""
        with self._lock:
            self.auto_scroll = False
            self.scroll_offset = max(0, self.scroll_offset - amount)

    def scroll_down(self, amount: int = 1, viewport_height: int = 10) -> None:
        """Scroll down by a number of lines, re-enabling auto-scroll at bottom."""
        with self._lock:
            max_offset = max(0, len(self.lines) - viewport_height)
            self.scroll_offset = min(
                max_offset, self.scroll_offset + amount
            )
            if self.scroll_offset >= max_offset:
                self.auto_scroll = True

    def scroll_to_bottom(self, viewport_height: int = 10) -> None:
        """Jump directly to bottom and re-enable auto-scroll."""
        with self._lock:
            self.auto_scroll = True
            self.scroll_offset = max(0, len(self.lines) - viewport_height)

    def get_visible_lines(self, viewport_height: int) -> List[RenderableType]:
        """
        Return the slice of lines currently visible given the viewport height.
        Pads with empty Text to fill the viewport if needed.
        """
        with self._lock:
            if not self.lines:
                # One empty muted line if there is nothing
                return [
                    Text("", style=style("text.muted")),
                ]

            start = self.scroll_offset
            end = min(len(self.lines), start + viewport_height)
            visible = self.lines[start:end]

            # Pad to viewport height
            while len(visible) < viewport_height:
                visible.append(Text(""))

            return visible

    def get_scroll_indicator(self, viewport_height: int) -> str:
        """
        Return a string like " [1-10/123]" when content overflows viewport,
        or empty string when everything fits.
        """
        total = len(self.lines)
        if total <= viewport_height:
            return ""

        current = self.scroll_offset + 1
        end = min(total, self.scroll_offset + viewport_height)
        return f" [{current}-{end}/{total}]"


class FramedApp:
    """
Full-screen app with fixed header/footer and scrollable body.

Usage:
    app = FramedApp("chat")
    app.set_footer("Type /help for commands")

    with app.run():
        app.add_content(Text("User: Hello"))
        app.add_content(Text("Assistant: Hi there!"))
    """

    def __init__(
        self,
        app_id: str,
        console: Optional[Console] = None,
        viewport_height: int = 20,
        refresh_rate: int = 10,
    ) -> None:
        self.app_id: str = app_id
        self.console: Console = console or get_console()
        self.viewport_height: int = viewport_height
        self.refresh_rate: int = refresh_rate

        # Pull metadata, defaulting to "mlxlab"
        self.metadata: dict = APP_METADATA.get(
            app_id, APP_METADATA.get("mlxlab", {})
        )

        self.color_token: str = get_app_color(app_id)

        self.body: ScrollableBody = ScrollableBody()
        self.footer_text: Optional[RenderableType] = None

        self._live: Optional[Live] = None
        self._layout: Optional[Layout] = None
        self._running: bool = False

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def set_footer(self, text: RenderableType) -> None:
        """Set footer content (text or any renderable)."""
        self.footer_text = text

    def add_content(self, line: RenderableType) -> None:
        """Append a single line to the scrollable body."""
        self.body.add_line(line)

    def add_lines(self, lines: List[RenderableType]) -> None:
        """Append multiple lines to the scrollable body."""
        self.body.add_lines(lines)

    def clear_body(self) -> None:
        """Clear all content in the scrollable body."""
        self.body.clear()

    # -------------------------------------------------------------------------
    # Layout + rendering
    # -------------------------------------------------------------------------

    def _build_layout(self) -> Layout:
        """Create top-level layout with header, body, footer regions."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=7),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )
        return layout

    def _update_layout(self) -> None:
        """Update header, body and footer panels based on current state."""
        if not self._layout:
            return

        # Header: title + caption
        title_text = Text(
            self.metadata.get("title", ""),
            style=style(self.color_token, bold=True),
        )
        caption_text = Text(
            self.metadata.get("caption", ""),
            style=style("text.secondary"),
        )

        header_content = Group(
            Align.center(title_text),
            Align.center(caption_text),
        )

        self._layout["header"].update(
            Panel(
                header_content,
                border_style=style(self.color_token),
                padding=(1, 2),
                style=style("frame.bg"),
            )
        )

        # Body: visible lines from scrollable body
        visible_lines = self.body.get_visible_lines(self.viewport_height)
        body_group = Group(*visible_lines)

        self._layout["body"].update(
            Panel(
                body_group,
                border_style=style("frame.chrome"),
                padding=(1, 2),
                style=style("frame.bg"),
            )
        )

        # Footer: footer text + optional scroll indicator
        scroll_indicator = self.body.get_scroll_indicator(self.viewport_height)

        if self.footer_text:
            if isinstance(self.footer_text, str):
                footer_content: RenderableType = Text.from_markup(
                    str(self.footer_text)
                )
            else:
                footer_content = self.footer_text
        else:
            footer_content = Text(
                "Press Ctrl+C to exit", style=style("text.muted")
            )

        if scroll_indicator and isinstance(footer_content, Text):
            footer_with_scroll = Text()
            footer_with_scroll.append_text(footer_content)
            footer_with_scroll.append(
                scroll_indicator, style=style("text.muted")
            )
            footer_content = footer_with_scroll

        self._layout["footer"].update(
            Panel(
                Align.center(footer_content),
                border_style=style("frame.chrome"),
                padding=(0, 2),
                style=style("frame.bg", dim=True),
            )
        )

    # -------------------------------------------------------------------------
    # Context manager + runtime
    # -------------------------------------------------------------------------

    def run(self) -> "FramedApp":
        """
        Simple helper to make:

            with FramedApp("chat").run() as app:
                ...

        feel natural. Returns self.
        """
        return self

    def __enter__(self) -> "FramedApp":
        self._layout = self._build_layout()
        self._update_layout()

        self._live = Live(
            self._layout,
            console=self.console,
            screen=True,
            auto_refresh=False,
            refresh_per_second=self.refresh_rate,
        )
        self._live.__enter__()

        self._running = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._running = False
        if self._live:
            self._live.__exit__(exc_type, exc_val, exc_tb)
            self._live = None

    def refresh(self) -> None:
        """Rebuild panels and trigger a Live refresh if running."""
        if not self._running or not self._live:
            return
        self._update_layout()
        self._live.refresh()

    # -------------------------------------------------------------------------
    # Scroll controls (delegate to body + refresh)
    # -------------------------------------------------------------------------

    def scroll_up(self, amount: int = 3) -> None:
        """Scroll body up by N lines and refresh."""
        self.body.scroll_up(amount=amount)
        self.refresh()

    def scroll_down(self, amount: int = 3) -> None:
        """Scroll body down by N lines and refresh."""
        self.body.scroll_down(amount=amount, viewport_height=self.viewport_height)
        self.refresh()

    def scroll_to_bottom(self) -> None:
        """Scroll directly to bottom and refresh."""
        self.body.scroll_to_bottom(viewport_height=self.viewport_height)
        self.refresh()

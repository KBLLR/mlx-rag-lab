"""
Base framed application class with scrollable body and fixed header/footer.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Optional

from rich.console import Console, Group, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.text import Text

from .app_frames import get_app_frame
from .theme import get_console


class ScrollableBody:
    """Manages scrollable content with a viewport."""

    def __init__(self, viewport_height: int = 20) -> None:
        self.viewport_height = viewport_height
        self.lines: list[RenderableType] = []
        self._scroll_offset = 0

    def add_line(self, renderable: RenderableType) -> None:
        """Add a line to the body."""
        self.lines.append(renderable)
        # Auto-scroll to bottom when new content is added
        self._scroll_offset = max(0, len(self.lines) - self.viewport_height)

    def get_visible_lines(self) -> Group:
        """Get the current viewport of lines."""
        start = self._scroll_offset
        end = start + self.viewport_height
        visible = self.lines[start:end]
        return Group(*visible) if visible else Group(Text(""))

    def get_scroll_indicator(self, viewport_height: int) -> str:
        """Return scroll position indicator string."""
        total = len(self.lines)
        if total <= viewport_height:
            return ""

        current = self._scroll_offset + viewport_height
        return f" [{current}/{total}]"

    def scroll_up(self, amount: int = 1) -> None:
        """Scroll up by amount."""
        self._scroll_offset = max(0, self._scroll_offset - amount)

    def scroll_down(self, amount: int = 1) -> None:
        """Scroll down by amount."""
        max_offset = max(0, len(self.lines) - self.viewport_height)
        self._scroll_offset = min(max_offset, self._scroll_offset + amount)

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom."""
        self._scroll_offset = max(0, len(self.lines) - self.viewport_height)

    def scroll_to_top(self) -> None:
        """Scroll to the top."""
        self._scroll_offset = 0

    def clear(self) -> None:
        """Clear all content."""
        self.lines.clear()
        self._scroll_offset = 0


class FramedApp:
    """
    Base class for framed applications with fixed header/footer.

    Provides:
    - Fixed header with app branding
    - Scrollable body with viewport management
    - Optional footer
    - Live rendering with Rich

    Usage:
        app = FramedApp("chat", viewport_height=20)
        with app.run():
            app.add_content(Text("Hello, world!"))
            app.refresh()
    """

    def __init__(
        self,
        app_id: str,
        console: Optional[Console] = None,
        viewport_height: int = 20,
        refresh_rate: int = 4,
    ) -> None:
        """
        Initialize a framed application.

        Args:
            app_id: Application identifier (must exist in APP_METADATA)
            console: Rich Console instance (defaults to shared console)
            viewport_height: Number of visible lines in body viewport
            refresh_rate: Live refresh rate in Hz
        """
        self.app_id = app_id
        self.console = console or get_console()
        self.viewport_height = viewport_height
        self.refresh_rate = refresh_rate

        # Body management
        self.body = ScrollableBody(viewport_height)

        # Layout and Live state
        self._layout: Optional[Layout] = None
        self._live: Optional[Live] = None
        self._running = False

        # Footer renderable (can be overridden by subclasses)
        self._footer_renderable: Optional[RenderableType] = None

    def add_content(self, renderable: RenderableType) -> None:
        """Add content to the scrollable body."""
        self.body.add_line(renderable)
        self.refresh()

    def set_footer(self, renderable: RenderableType) -> None:
        """Set custom footer content."""
        self._footer_renderable = renderable
        self.refresh()

    def clear_body(self) -> None:
        """Clear all body content."""
        self.body.clear()
        self.refresh()

    def _update_layout(self) -> None:
        """Build/update the layout with current content."""
        body_content = self.body.get_visible_lines()

        self._layout = get_app_frame(
            app_id=self.app_id,
            body_renderable=body_content,
            footer_renderable=self._footer_renderable,
        )

    def refresh(self) -> None:
        """Refresh the display with current content."""
        if self._running and self._live:
            self._update_layout()
            if self._layout:
                self._live.update(self._layout)

    @contextmanager
    def run(self):
        """
        Context manager to run the framed app with Live rendering.

        Yields:
            self: The FramedApp instance for method chaining

        Example:
            with app.run():
                app.add_content(Text("Running..."))
                # Do work...
        """
        self._running = True
        self._update_layout()

        with Live(
            self._layout,
            console=self.console,
            refresh_per_second=self.refresh_rate,
            screen=True,
        ) as live:
            self._live = live
            try:
                yield self
            finally:
                self._running = False
                self._live = None

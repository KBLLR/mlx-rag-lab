"""
framed_app.py

Rich-based framed layout helper for CLI apps.

Provides a fixed FRAME:
    ┌───────────────────────────────┐
    │ HEADER (fixed height)        │
    ├───────────────────────────────┤
    │ BODY (expands / scroll area) │
    ├───────────────────────────────┤
    │ FOOTER (fixed height)        │
    └───────────────────────────────┘

Usage example
-------------

from rich.text import Text
from rich.panel import Panel
from .framed_app import FramedApp, FrameConfig

def main():
    app = FramedApp(title="MLX Lab", config=FrameConfig())
    app.set_header(Text("MLX Lab · Local-first pipelines", style="bold cyan"))
    app.set_body(Panel("Body content goes here"))
    app.set_footer(Text("↑↓ navigate · q quit", style="dim"))

    # Simple loop example
    def tick(app: FramedApp) -> bool:
        # Return False to exit, True to continue
        return True

    app.run(tick=tick)

if __name__ == "__main__":
    main()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol

from rich.align import Align
from rich.console import Console, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


class TickFn(Protocol):
    def __call__(self, app: "FramedApp") -> bool:
        """
        Called every iteration when using FramedApp.run().

        Return:
            True  → continue loop
            False → stop loop
        """


@dataclass
class FrameConfig:
    """Configuration for the framed layout."""

    header_height: int = 3
    footer_height: int = 3
    refresh_per_second: int = 20
    screen: bool = False
    transient: bool = False
    redirect_stdout: bool = True
    redirect_stderr: bool = True
    # Optional default styles
    header_style: str = "bold cyan"
    footer_style: str = "dim"
    border_style: str = "blue"
    body_border_style: str = "dim"
    pad_body: bool = True


@dataclass
class FrameState:
    """Current renderables held by the frame."""

    header: RenderableType = field(
        default_factory=lambda: Text("", style="bold cyan")
    )
    body: RenderableType = field(
        default_factory=lambda: Text("Body not set", style="dim")
    )
    footer: RenderableType = field(
        default_factory=lambda: Text("", style="dim")
    )


class FramedApp:
    """
    Base framed application helper.

    Responsibilities:
    - Own a Rich Console
    - Build and manage a Layout with header / body / footer
    - Provide simple setters to update sections
    - Optionally manage a Live loop with `.run()`
    """

    def __init__(
        self,
        *,
        console: Optional[Console] = None,
        title: Optional[str] = None,
        config: Optional[FrameConfig] = None,
    ) -> None:
        self.console: Console = console or Console()
        self.title: Optional[str] = title
        self.config: FrameConfig = config or FrameConfig()
        self.state: FrameState = FrameState()

        # Build the initial layout
        self.layout: Layout = self._build_layout()
        self._apply_state_to_layout()

    # -------------------------------------------------------------------------
    # Layout construction
    # -------------------------------------------------------------------------

    def _build_layout(self) -> Layout:
        """Create the base header/body/footer layout."""
        root = Layout(name="root")

        # Top-level vertical split
        root.split_column(
            Layout(name="header", size=self.config.header_height),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=self.config.footer_height),
        )

        return root

    # -------------------------------------------------------------------------
    # State → Layout mapping
    # -------------------------------------------------------------------------

    def _render_header(self) -> RenderableType:
        header = self.state.header
        if isinstance(header, str):
            header = Text(header, style=self.config.header_style)

        panel = Panel(
            Align.left(header),
            style=self.config.border_style,
            border_style=self.config.border_style,
            padding=(0, 1),
            title=self.title,
            title_align="left",
        )
        return panel

    def _render_body(self) -> RenderableType:
        body = self.state.body

        if self.config.pad_body:
            body = Panel(
                body,
                border_style=self.config.body_border_style,
                padding=(0, 1),
            )

        return body

    def _render_footer(self) -> RenderableType:
        footer = self.state.footer
        if isinstance(footer, str):
            footer = Text(footer, style=self.config.footer_style)

        panel = Panel(
            Align.left(footer),
            style=self.config.border_style,
            border_style=self.config.border_style,
            padding=(0, 1),
        )
        return panel

    def _apply_state_to_layout(self) -> None:
        """Sync FrameState into Layout renderables."""
        self.layout["header"].update(self._render_header())
        self.layout["body"].update(self._render_body())
        self.layout["footer"].update(self._render_footer())

    # -------------------------------------------------------------------------
    # Public API: section setters
    # -------------------------------------------------------------------------

    def set_header(self, renderable: RenderableType) -> None:
        """Update header renderable and refresh layout."""
        self.state.header = renderable
        self.layout["header"].update(self._render_header())

    def set_body(self, renderable: RenderableType) -> None:
        """Update body renderable and refresh layout."""
        self.state.body = renderable
        self.layout["body"].update(self._render_body())

    def set_footer(self, renderable: RenderableType) -> None:
        """Update footer renderable and refresh layout."""
        self.state.footer = renderable
        self.layout["footer"].update(self._render_footer())

    # -------------------------------------------------------------------------
    # Live helpers
    # -------------------------------------------------------------------------

    def create_live(self, **kwargs) -> Live:
        """
        Create a Live context for manual control.

        Example:
            app = FramedApp()
            app.set_header("Header")
            app.set_body("Body")
            app.set_footer("Footer")

            with app.create_live() as live:
                ... # update app.set_body(...) etc, Live will redraw
        """
        live = Live(
            self.layout,
            console=self.console,
            refresh_per_second=self.config.refresh_per_second,
            screen=self.config.screen,
            transient=self.config.transient,
            redirect_stdout=self.config.redirect_stdout,
            redirect_stderr=self.config.redirect_stderr,
            **kwargs,
        )
        return live

    # -------------------------------------------------------------------------
    # Simple loop runner
    # -------------------------------------------------------------------------

    def run(
        self,
        tick: Optional[TickFn] = None,
        *,
        on_start: Optional[Callable[["FramedApp"], None]] = None,
        on_stop: Optional[Callable[["FramedApp"], None]] = None,
    ) -> None:
        """
        Run a simple Live loop.

        Args:
            tick:
                Callback called in a loop. Receives the app instance.
                Return False to stop, True (or None) to continue.
            on_start:
                Optional callback run once before the loop.
            on_stop:
                Optional callback run once after the loop exits.
        """
        if tick is None:
            # If no tick, just render one frame and exit.
            with self.create_live():
                self._apply_state_to_layout()
            return

        try:
            if on_start is not None:
                on_start(self)

            with self.create_live():
                while True:
                    self._apply_state_to_layout()
                    result = tick(self)
                    if result is False:
                        break

        except KeyboardInterrupt:
            # Graceful exit on Ctrl+C
            pass
        finally:
            if on_stop is not None:
                on_stop(self)

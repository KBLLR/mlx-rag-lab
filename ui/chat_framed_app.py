"""
Chat-specific framed app with input footer.
Body shows chat history, footer is the live input field.
"""

from __future__ import annotations

import queue
import threading
from typing import Callable, Optional

from rich.console import Console, RenderableType
from rich.text import Text

from .framed_app import FramedApp
from .theme import style


class ChatFramedApp(FramedApp):
    """
    Specialized FramedApp for chat interfaces.

    - Header: App title (fixed)
    - Body: Chat history (scrollable)
    - Footer: Input prompt (interactive)

    Usage:
        app = ChatFramedApp("chat")

        with app.run():
            while True:
                user_input = app.get_input("> ")
                if user_input:
                    app.add_message("User", user_input, "green")
                    response = get_ai_response(user_input)
                    app.add_message("Assistant", response, "blue")
    """

    __firstlineno__ = 17  # only here to mirror the original metadata; harmless

    def __init__(
        self,
        app_id: str,
        console: Optional[Console] = None,
        viewport_height: int = 20,
        refresh_rate: int = 10,
    ) -> None:
        super().__init__(
            app_id=app_id,
            console=console,
            viewport_height=viewport_height,
            refresh_rate=refresh_rate,
        )

        # Footer state
        self._input_prompt: str = ""
        self._input_placeholder: str = "Type your message..."
        self._waiting_for_input: bool = False

    # -------------------------------------------------------------------------
    # Public configuration API
    # -------------------------------------------------------------------------

    def set_input_prompt(self, prompt: str) -> None:
        """Set the current input prompt label (e.g. '> ', 'You', etc.)."""
        self._input_prompt = prompt

    def set_input_placeholder(self, text: str) -> None:
        """Set the placeholder text shown when waiting for input."""
        self._input_placeholder = text

    # -------------------------------------------------------------------------
    # Message helpers
    # -------------------------------------------------------------------------

    def add_message(
        self,
        sender: str,
        message: str,
        sender_color: str = "cyan",
    ) -> None:
        """Append a chat-style message to the body."""
        sender_text = Text(f"{sender}: ", style=f"bold {sender_color}")
        message_text = Text(message, style=style("text.primary"))

        line = Text()
        line.append_text(sender_text)
        line.append_text(message_text)

        self.add_content(line)

    def add_system_message(self, message: str) -> None:
        """Append a system/meta message to the body."""
        self.add_content(
            Text(
                message,
                style=style("text.muted"),
            )
        )

    # -------------------------------------------------------------------------
    # Layout hook
    # -------------------------------------------------------------------------

    def _update_layout(self) -> None:
        """
        Extend base layout update to inject a dynamic footer:

        - If waiting for input: show prompt + placeholder hint.
        - Otherwise: show scroll indicator + exit hint.
        """
        from rich.align import Align
        from rich.console import Group
        from rich.panel import Panel

        # Let the base class set up header/body/etc.
        super()._update_layout()

        # If layout hasn't been initialized yet, bail.
        if not self._layout:
            return

        # Build footer content
        if self._waiting_for_input:
            footer_content = Text()

            # Prompt label
            footer_content.append(
                self._input_prompt,
                style=style("text.accent"),
            )

            # Separator space
            footer_content.append(
                " ",
                style=style("text.muted"),
            )

            # Placeholder (muted, italic)
            footer_content.append(
                self._input_placeholder,
                style=style("text.muted", dim=False, italic=True),
            )
        else:
            # Scroll indicator from body, plus exit hint
            scroll_indicator = self.body.get_scroll_indicator(self.viewport_height)

            footer_content = Text(
                "Press Ctrl+C to exit",
                style=style("text.muted"),
            )

            if scroll_indicator:
                footer_content.append(
                    scroll_indicator,
                    style=style("text.muted"),
                )

        # Push footer into layout
        self._layout["footer"].update(
            Panel(
                Align.center(footer_content),
                border_style=style("frame.chrome"),
                padding=(0, 2),
                style=style("frame.bg", dim=True),
            )
        )

    # -------------------------------------------------------------------------
    # Input API
    # -------------------------------------------------------------------------

    def get_input(self, prompt: str = "> ") -> Optional[str]:
        """
        Blocking input:

        - Temporarily turns footer into "waiting for input" state.
        - Suspends Live context to use Console.input cleanly.
        - Restores Live afterwards and refreshes layout.

        Returns:
            str | None (None on EOF/KeyboardInterrupt)
        """
        # Update internal prompt state and mark as waiting
        self._input_prompt = prompt
        self._waiting_for_input = True

        # Trigger a UI refresh so footer shows the input state
        self.refresh()

        # Temporarily exit Live context (if active) to avoid corrupting layout
        if self._live:
            self._live.__exit__(None, None, None)

        try:
            # Build rich-styled input prompt
            rich_prompt = (
                "["
                + style("text.accent")
                + "]"
                + prompt
                + "[/]"
                + " "
            )
            user_input = self.console.input(rich_prompt)
        except (EOFError, KeyboardInterrupt):
            user_input = None

        # If app is still running, re-enter Live context
        if self._running and self._live:
            self._live.__enter__()

        # Clear waiting state and refresh layout
        self._waiting_for_input = False
        self.refresh()

        return user_input

    def get_input_async(self, prompt: str = "> ") -> str:
        """
        Async-friendly wrapper around get_input.

        Returns empty string instead of None to make simple loops easier.
        """
        value = self.get_input(prompt)
        return value or ""

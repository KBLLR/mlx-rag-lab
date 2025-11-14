"""
Vertical card menu with ASCII typography and arrow key navigation.
Each app gets its own ASCII art statement piece.
"""

from typing import Any, Callable, List, Optional, Tuple

from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .theme import get_console, style


class Card:
    """Single menu card with ASCII typography."""

    __static_attributes__ = (
        "ascii_title",
        "color_token",
        "description",
        "eyebrow",
        "id",
    )

    def __init__(
        self,
        id: str,
        eyebrow: str,
        ascii_title: str,
        description: str,
        color_token: str = "text.accent",
    ) -> None:
        self.id = id
        self.eyebrow = eyebrow
        self.ascii_title = ascii_title
        self.description = description
        self.color_token = color_token

    def render(self, selected: bool = False) -> Panel:
        """Render this card as a Rich Panel."""
        eyebrow_text = Text(
            self.eyebrow,
            style=style("text.muted"),
        )

        ascii_text = Text(
            self.ascii_title,
            style=style(self.color_token, bold=True),
        )

        desc_text = Text(
            self.description,
            style=style("text.secondary"),
        )

        content = Group(
            eyebrow_text,
            Text(""),
            ascii_text,
            Text(""),
            desc_text,
        )

        if selected:
            border_style = style(self.color_token, bold=True)
            bg_style = style("frame.bg")
        else:
            border_style = style("frame.chrome")
            bg_style = ""

        return Panel(
            content,
            border_style=border_style,
            style=bg_style,
            padding=(1, 3),
            expand=True,
        )


class CardMenu:
    """Vertical card menu with up/down arrow navigation."""

    __static_attributes__ = (
        "cards",
        "console",
        "scroll_offset",
        "selected_index",
        "visible_cards",
    )

    def __init__(
        self,
        cards: List[Card],
        console: Optional[Console] = None,
        visible_cards: int = 5,
    ) -> None:
        self.cards: List[Card] = cards
        self.console: Console = console or get_console()
        self.selected_index: int = 0
        self.visible_cards: int = visible_cards
        self.scroll_offset: int = 0

    def _navigate(self, direction: str) -> None:
        """Move selection up or down and adjust scroll window."""
        if direction == "up":
            if self.selected_index > 0:
                self.selected_index -= 1
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
            return

        if direction == "down":
            if self.selected_index < len(self.cards) - 1:
                self.selected_index += 1
                if (
                    self.selected_index
                    >= self.scroll_offset + self.visible_cards
                ):
                    self.scroll_offset = (
                        self.selected_index - self.visible_cards + 1
                    )
            return

    def _render_menu(self) -> RenderableType:
        """Render the current window of cards plus footer hints."""
        visible_cards: List[RenderableType] = []

        for i in range(
            self.scroll_offset,
            min(self.scroll_offset + self.visible_cards, len(self.cards)),
        ):
            card = self.cards[i]
            selected = i == self.selected_index
            visible_cards.append(card.render(selected=selected))

        help_text = Text(
            "Navigate: ↑↓  Select: Enter  Exit: Esc/q",
            style=style("text.muted"),
        )

        if len(self.cards) > self.visible_cards:
            scroll_info = Text(
                f"[{self.selected_index + 1}/{len(self.cards)}]",
                style=style("text.muted"),
            )
            footer = Group(
                Text(""),
                Align.center(help_text),
                Align.center(scroll_info),
            )
        else:
            footer = Group(
                Text(""),
                Align.center(help_text),
            )

        return Group(*visible_cards, footer)

    def show(self) -> Optional[str]:
        """
        Run the interactive menu.

        Returns:
            Selected card id, or None if the user exits / error / KeyboardInterrupt.
        """
        import sys  # kept for parity with the compiled version; not strictly needed

        try:
            import readchar
        except ImportError:
            self.console.print(
                "[red]readchar not installed. Install with: uv pip install readchar[/red]"
            )
            return None

        selected_id: Optional[str] = None

        try:
            with Live(
                self._render_menu(),
                console=self.console,
                refresh_per_second=20,
                screen=False,
            ) as live:
                while True:
                    live.update(self._render_menu())

                    key = readchar.readkey()

                    # Arrow navigation
                    if key == readchar.key.UP:
                        self._navigate("up")
                        continue
                    if key == readchar.key.DOWN:
                        self._navigate("down")
                        continue

                    # Enter / CR / LF -> select
                    if key in (readchar.key.ENTER, readchar.key.CR, readchar.key.LF):
                        selected_id = self.cards[self.selected_index].id
                        break

                    # ESC / q / Q -> exit
                    if key in (readchar.key.ESC, "q", "Q"):
                        break

        except Exception as e:
            self.console.print(
                f"\n[red]Keyboard input error: {e}[/red]"
            )
            self.console.print(
                "[yellow]Tip: Run in interactive mode or use --help[/yellow]"
            )
            return None
        except KeyboardInterrupt:
            return None

        return selected_id


def show_card_menu(
    cards: List[Card],
    console: Optional[Console] = None,
    visible_cards: int = 5,
) -> Optional[str]:
    """Convenience wrapper to show a grid menu and return the selected id."""
    menu = CardMenu(cards=cards, console=console, visible_cards=visible_cards)
    return menu.show()


# Public aliases used elsewhere
GridMenu = CardMenu
show_grid_menu = show_card_menu

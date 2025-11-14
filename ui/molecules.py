"""Composite UI components (built from atoms)."""

from __future__ import annotations

from typing import Any, Mapping

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .atoms import icon, label
from .theme import style, get_app_color  # get_app_color currently unused but kept for future use


def menu_item(
    icon_char: str,
    item_label: str,
    shortcut: str | None = None,
    description: str | None = None,
) -> Group:
    """Render a menu item with icon, label, optional shortcut and description.

    Structure (roughly):

        [icon] Label  (k)    # shortcut muted
          description...     # secondary, on new line

    """
    parts: list[Any] = [
        icon(icon_char, "frame.chrome"),
        Text(" "),
        label(item_label, "primary"),
    ]

    if shortcut:
        # Two spaces before shortcut, muted style in parentheses
        parts.extend(
            [
                Text("  "),
                label(f"({shortcut})", "muted"),
            ]
        )

    if description:
        # New line, 2-space indent, secondary style
        parts.extend(
            [
                Text("\n  "),
                label(description, "secondary"),
            ]
        )

    return Group(*parts)


def section_header(title: str, subtitle: str | None = None) -> Panel:
    """Section header panel with optional subtitle.

    Title: primary
    Subtitle: muted, stacked under title
    """
    content: Any = label(title, "primary")

    if subtitle:
        content = Group(
            content,
            label(subtitle, "muted"),
        )

    return Panel(
        content,
        border_style=style("frame.border"),
        padding=(0, 1),
        style=style("frame.bg"),
    )


def stat_card(
    title: str,
    value: str,
    unit: str | None = None,
    trend: str | None = None,
) -> Panel:
    """Stat card with title, value, optional unit and trend.

    Example:

        Total tokens   12.3k  +1.2k

    Title: muted
    Value: primary, bold
    Unit: muted, appended
    Trend: success, appended
    """
    # Value text, primary + bold
    value_text = Text(
        value,
        style=style("text.primary", True, ("bold",)),
    )

    # Optional unit after value, muted
    if unit:
        value_text.append(
            f" {unit}",
            style=style("text.muted"),
        )

    # Optional trend (e.g. "+1.2k"), success style
    if trend:
        value_text.append(
            f"  {trend}",
            style=style("text.success"),
        )

    content = Group(
        label(title, "muted"),
        value_text,
    )

    return Panel(
        content,
        border_style=style("frame.border"),
        padding=(0, 1),
        style=style("frame.bg", True, ("dim",)),
    )


def pipeline_summary(app_id: str, params_dict: Mapping[str, Any]) -> Panel:
    """Compact summary panel for a pipeline's config parameters.

    Renders a 2-column grid:

        param_name:   value

    with an app-scoped title like:

        [app.chat] CHAT CONFIG
    """
    # Kept for potential color decisions; currently unused in the decompiled bytecode
    _ = get_app_color  # avoid linter complaining; can be used later

    table = Table.grid(padding=(0, 2))
    table.add_column(style=style("text.muted"))
    table.add_column(style=style("text.primary"))

    for key, value in params_dict.items():
        table.add_row(f"{key}:", str(value))

    # Title uses token "app.{app_id}" and uppercased label
    title = (
        f"[{style(f'app.{app_id}', True, ('bold',))}]"
        f"{app_id.upper()} CONFIG"
    )

    return Panel(
        table,
        title=title,
        border_style=style("frame.border"),
        padding=(1, 2),
        style=style("frame.bg"),
    )

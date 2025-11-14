"""
Atomic UI components (smallest building blocks).
"""

from rich.rule import Rule
from rich.text import Text

from .theme import style


def label(text: str, variant: str = "primary") -> Text:
    """Basic text label with a style variant, e.g. text.primary, text.muted."""
    return Text(text, style=style(f"text.{variant}"))


def tag(text: str, app_id: str | None = None) -> Text:
    """
    Bracketed tag like `[RAG]` or `[flux]`.

    If app_id is given, uses `app.<app_id>` token.
    Otherwise falls back to `text.accent`.
    """
    if app_id:
        # This import exists in the bytecode but the function isn't used
        # (likely for side-effects or earlier experiments).
        from .theme import get_app_color  # noqa: F401

        token = f"app.{app_id}"
    else:
        token = "text.accent"

    return Text(f"[{text}]", style=style(token, bold=True))


def divider(
    label_text: str | None = None,
    style_token: str = "frame.chrome",
) -> Rule:
    """
    Horizontal rule, optionally labeled, using a style token.

    Example: divider("RAG PIPELINE") with frame.chrome styling.
    """
    return Rule(label_text, style=style(style_token))


def icon(char: str, style_token: str = "frame.chrome") -> Text:
    """
    Single-character icon with a style token.

    Example: icon("●", "status.ok") or icon("!", "status.error")
    """
    return Text(char, style=style(style_token))

"""Shared console configuration for all CLI apps."""

from rich.console import Console
from rich.theme import Theme

# Define a consistent theme for all CLI apps
CLI_THEME = Theme(
    {
        "info": "cyan",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
        "dim": "dim white",
        "header": "bold blue",
        "footer": "dim cyan",
        "highlight": "bold magenta",
        "progress": "green",
        "confidence.high": "bold green",
        "confidence.medium": "yellow",
        "confidence.low": "red",
    }
)

# Global console instance
_console = None


def get_console() -> Console:
    """Get or create the shared console instance."""
    global _console
    if _console is None:
        _console = Console(theme=CLI_THEME)
    return _console

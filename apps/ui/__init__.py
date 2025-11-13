"""Shared UI components for MLX-RAG Lab CLI applications."""

from apps.ui.console import get_console
from apps.ui.components import (
    render_header,
    render_footer,
    render_confidence_bars,
    render_task_progress,
    show_confidence_warning,
    show_system_warning,
)
from apps.ui.utils import truncate_source_path, get_confidence_color

__all__ = [
    "get_console",
    "render_header",
    "render_footer",
    "render_confidence_bars",
    "render_task_progress",
    "show_confidence_warning",
    "show_system_warning",
    "truncate_source_path",
    "get_confidence_color",
]

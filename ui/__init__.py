"""
Rich-based CLI UI design system for mlx-RAG.
Provides theme, layout, components, and settings.
"""

from .app_frames import APP_METADATA, get_app_frame
from .atoms import divider, icon, label, tag
from .dashboards import (
    build_chat_dashboard,
    build_musicgen_dashboard,
    build_rag_dashboard,
)
from .chat_framed_app import ChatFramedApp
from .framed_app import FramedApp, ScrollableBody
from .layouts import build_frame, live_frame, show_app_splash
from .molecules import menu_item, pipeline_summary, section_header, stat_card
from .playground import run_ui_playground
from .settings import configure_ui_settings, load_ui_settings, save_ui_settings
from .spinners import status_spinner, transition_to_screen
from .grid_menu import (
    Card,
    CardMenu,
    GridMenu,
    show_card_menu,
    show_grid_menu,
)
from .theme import get_app_color, get_console, reload_theme, style

__all__ = [
    # theme
    "get_console",
    "get_app_color",
    "reload_theme",
    "style",
    # grid/menu
    "Card",
    "CardMenu",
    "GridMenu",
    "show_card_menu",
    "show_grid_menu",
    # layouts
    "build_frame",
    "live_frame",
    "show_app_splash",
    # app frames
    "get_app_frame",
    "APP_METADATA",
    # frame core
    "FramedApp",
    "ScrollableBody",
    "ChatFramedApp",
    # atoms
    "label",
    "tag",
    "divider",
    "icon",
    # molecules
    "menu_item",
    "section_header",
    "stat_card",
    "pipeline_summary",
    # dashboards
    "build_chat_dashboard",
    "build_rag_dashboard",
    "build_musicgen_dashboard",
    # spinners / transitions
    "status_spinner",
    "transition_to_screen",
    # settings
    "configure_ui_settings",
    "load_ui_settings",
    "save_ui_settings",
    # playground
    "run_ui_playground",
]

# Source Generated with Decompyle++
# File: __init__.cpython-313.pyc (Python 3.13)

'''
Rich-based CLI UI design system for mlx-RAG.
Provides theme, layout, components, and settings.
'''
from app_frames import APP_METADATA, get_app_frame
from atoms import divider, icon, label, tag
from dashboards import build_chat_dashboard, build_musicgen_dashboard, build_rag_dashboard
from chat_framed_app import ChatFramedApp
from framed_app import FramedApp, ScrollableBody
from layouts import build_frame, live_frame, show_app_splash
from molecules import menu_item, pipeline_summary, section_header, stat_card
from playground import run_ui_playground
from settings import configure_ui_settings, load_ui_settings, save_ui_settings
from spinners import status_spinner, transition_to_screen
from grid_menu import Card, CardMenu, GridMenu, show_card_menu, show_grid_menu
from theme import get_app_color, get_console, reload_theme, style
__all__ = [
    'get_console',
    'get_app_color',
    'reload_theme',
    'style',
    'Card',
    'CardMenu',
    'GridMenu',
    'show_card_menu',
    'show_grid_menu',
    'build_frame',
    'live_frame',
    'show_app_splash',
    'get_app_frame',
    'APP_METADATA',
    'FramedApp',
    'ScrollableBody',
    'ChatFramedApp',
    'label',
    'tag',
    'divider',
    'icon',
    'menu_item',
    'section_header',
    'stat_card',
    'pipeline_summary',
    'build_chat_dashboard',
    'build_rag_dashboard',
    'build_musicgen_dashboard',
    'status_spinner',
    'transition_to_screen',
    'configure_ui_settings',
    'load_ui_settings',
    'save_ui_settings',
    'run_ui_playground']

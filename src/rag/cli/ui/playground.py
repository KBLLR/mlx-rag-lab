Unsupported opcode: MAKE_FUNCTION (122)
# Source Generated with Decompyle++
# File: playground.cpython-313.pyc (Python 3.13)

__doc__ = '\nUI Playground - Interactive UI tweaking and preset selection.\n'
import time
from typing import Any, Dict
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from app_frames import get_app_frame
from atoms import divider, label
from layouts import live_frame
from settings import DEFAULT_SETTINGS, UISettings, load_ui_settings, save_ui_settings
from theme import get_console, style
PRESETS: Dict[(str, Dict[(str, Any)])] = {
    'glass_default': {
        'name': 'Glass Default',
        'description': 'Default dark theme with glass effect and per-app colors',
        'settings': {
            'theme_variant': 'default',
            'border_style': 'square',
            'app_color_mode': 'per_app_color',
            'show_icons': True,
            'transparent_frame': False } },
    'transparent': {
        'name': 'Transparent Frame',
        'description': 'Terminal transparency with filled body - perfect for blur effects',
        'settings': {
            'theme_variant': 'default',
            'border_style': 'square',
            'app_color_mode': 'per_app_color',
            'show_icons': True,
            'transparent_frame': True } },
    'high_contrast': {
        'name': 'High Contrast',
        'description': 'High contrast mode with unified accent color',
        'settings': {
            'theme_variant': 'high_contrast',
            'border_style': 'square',
            'app_color_mode': 'mono_accent',
            'show_icons': True,
            'transparent_frame': False } },
    'retro_grid': {
        'name': 'Retro Grid',
        'description': 'Neon-style with minimal borders and per-app colors',
        'settings': {
            'theme_variant': 'neon',
            'border_style': 'minimal',
            'app_color_mode': 'per_app_color',
            'show_icons': False,
            'transparent_frame': False } },
    'minimal_frame': {
        'name': 'Minimal Frame',
        'description': 'Clean minimal look with no borders and mono accent',
        'settings': {
            'theme_variant': 'default',
            'border_style': 'none',
            'app_color_mode': 'mono_accent',
            'show_icons': False,
            'transparent_frame': False } } }
# WARNING: Decompyle incomplete

Unsupported opcode: MAKE_FUNCTION (122)
# Source Generated with Decompyle++
# File: settings.cpython-313.pyc (Python 3.13)

__doc__ = '\nUI settings persistence and configuration menu.\n'
import json
from pathlib import Path
from typing import Literal
from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
UISettings = dict[(str, str | bool)]
DEFAULT_SETTINGS: UISettings = {
    'theme_variant': 'default',
    'border_style': 'square',
    'app_color_mode': 'per_app_color',
    'show_icons': True,
    'transparent_frame': False }
REPO_ROOT = None(__file__).resolve().parents[4]
SETTINGS_FILE = REPO_ROOT / 'var' / 'ui_settings.json'
# WARNING: Decompyle incomplete

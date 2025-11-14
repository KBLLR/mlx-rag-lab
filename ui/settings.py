"""
UI settings persistence and configuration menu.

Backed by a simple JSON file in `var/ui_settings.json`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel

# Simple alias: a dict with str keys and str/bool values
UISettings = dict[str, str | bool]

# Defaults used when no settings file exists or when load fails
DEFAULT_SETTINGS: UISettings = {
    "theme_variant": "default",         # "default" | "high_contrast" | "neon"
    "border_style": "square",           # "square" | "minimal" | "none"
    "app_color_mode": "per_app_color",  # "per_app_color" | "mono_accent"
    "show_icons": True,
    "transparent_frame": False,
}

# Repo root = 4 levels above this file
REPO_ROOT = Path(__file__).resolve().parents[4]
SETTINGS_FILE = REPO_ROOT / "var" / "ui_settings.json"


def load_ui_settings() -> UISettings:
    """
    Load UI settings from var/ui_settings.json.

    Returns a dict merged as:
    {**DEFAULT_SETTINGS, **loaded_json}
    falling back to DEFAULT_SETTINGS.copy() on any error.
    """
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                # Start from defaults, then override with stored values
                data: UISettings = {**DEFAULT_SETTINGS, **json.load(f)}
                return data
        except Exception:
            # If anything goes wrong, return a fresh copy of defaults
            return DEFAULT_SETTINGS.copy()
    # No file yet: start with defaults
    return DEFAULT_SETTINGS.copy()


def save_ui_settings(settings: UISettings) -> None:
    """
    Persist UI settings to var/ui_settings.json (creating parent dirs).
    """
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def configure_ui_settings(console: Console) -> None:
    """
    Interactive UI settings editor.

    - Lets the user pick theme variant, border style, color mode,
      whether to show icons, and whether to use a transparent frame.
    - Saves settings and then calls theme.reload_theme().
    """
    current = load_ui_settings()

    console.clear()
    console.print(Panel("UI Settings Configuration", style="bold"))

    # Theme variant
    theme_variant = inquirer.select(
        message="Theme variant:",
        choices=["default", "high_contrast", "neon"],
        default=current.get("theme_variant", "default"),
    ).execute()

    # Border style
    border_style = inquirer.select(
        message="Border style:",
        choices=["square", "minimal", "none"],
        default=current.get("border_style", "square"),
    ).execute()

    # App color mode
    app_color_mode = inquirer.select(
        message="App color mode:",
        choices=["per_app_color", "mono_accent"],
        default=current.get("app_color_mode", "per_app_color"),
    ).execute()

    # Show icons
    show_icons = inquirer.confirm(
        message="Show app icons in menus?",
        default=current.get("show_icons", True),
    ).execute()

    # Transparent frame
    transparent_frame = inquirer.confirm(
        message="Transparent frame (uses terminal background)?",
        default=current.get("transparent_frame", False),
    ).execute()

    # Build new settings dict
    new_settings: UISettings = {
        "theme_variant": theme_variant,
        "border_style": border_style,
        "app_color_mode": app_color_mode,
        "show_icons": show_icons,
        "transparent_frame": transparent_frame,
    }

    save_ui_settings(new_settings)

    # Apply theme changes immediately
    from .theme import reload_theme  # local import to avoid cycles

    reload_theme()

    console.print("\n[green]Settings saved to var/ui_settings.json[/green]")
    console.print("\nTheme will be applied when you return to the menu.\n")
    input("Press Enter to return to menu...")

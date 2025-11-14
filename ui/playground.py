"""
UI Playground - Interactive UI tweaking and preset selection.

Lets you preview and tweak global CLI UI settings (frame, borders, colors)
and save them to var/ui_settings.json.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .app_frames import get_app_frame
from .atoms import divider, label
from .layouts import live_frame
from .settings import DEFAULT_SETTINGS, UISettings, load_ui_settings, save_ui_settings
from .theme import get_console, style


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

PRESETS: Dict[str, Dict[str, Any]] = {
    "glass_default": {
        "name": "Glass Default",
        "description": "Default dark theme with glass effect and per-app colors",
        "settings": {
            "theme_variant": "default",
            "border_style": "square",
            "app_color_mode": "per_app_color",
            "show_icons": True,
            "transparent_frame": False,
        },
    },
    "transparent": {
        "name": "Transparent Frame",
        "description": "Terminal transparency with filled body - perfect for blur effects",
        "settings": {
            "theme_variant": "default",
            "border_style": "square",
            "app_color_mode": "per_app_color",
            "show_icons": True,
            "transparent_frame": True,
        },
    },
    "high_contrast": {
        "name": "High Contrast",
        "description": "High contrast mode with unified accent color",
        "settings": {
            "theme_variant": "high_contrast",
            "border_style": "square",
            "app_color_mode": "mono_accent",
            "show_icons": True,
            "transparent_frame": False,
        },
    },
    "retro_grid": {
        "name": "Retro Grid",
        "description": "Neon-style with minimal borders and per-app colors",
        "settings": {
            "theme_variant": "neon",
            "border_style": "minimal",
            "app_color_mode": "per_app_color",
            "show_icons": False,
            "transparent_frame": False,
        },
    },
    "minimal_frame": {
        "name": "Minimal Frame",
        "description": "Clean minimal look with no borders and mono accent",
        "settings": {
            "theme_variant": "default",
            "border_style": "none",
            "app_color_mode": "mono_accent",
            "show_icons": False,
            "transparent_frame": False,
        },
    },
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_settings_preview(
    settings: Dict[str, Any],
    preset_name: Optional[str] = None,
) -> Group:
    """Build a Rich Group showing current settings and a short explainer."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style=style("text.muted"))
    table.add_column(style=style("text.primary"))

    if preset_name:
        table.add_row("Active Preset:", preset_name)
        table.add_row("", "")

    table.add_row(
        "Theme Variant:",
        str(settings.get("theme_variant", "default")),
    )
    table.add_row(
        "Border Style:",
        str(settings.get("border_style", "square")),
    )
    table.add_row(
        "App Color Mode:",
        str(settings.get("app_color_mode", "per_app_color")),
    )
    table.add_row(
        "Show Icons:",
        str(settings.get("show_icons", True)),
    )
    table.add_row(
        "Transparent Frame:",
        str(settings.get("transparent_frame", False)),
    )

    panel = Panel(
        table,
        title="Current Settings",
        border_style=style("frame.border"),
        padding=(1, 2),
    )

    return Group(
        panel,
        Text(""),
        label(
            "These settings control the look and feel of all CLI apps.",
            "secondary",
        ),
        label(
            "Changes are saved to var/ui_settings.json",
            "muted",
        ),
    )


def _show_preview(
    console: Console,
    settings: Dict[str, Any],
    preset_name: Optional[str] = None,
) -> None:
    """Render a live preview frame with given settings."""
    body = _build_settings_preview(settings, preset_name)

    footer = Text(
        "Press Enter to continue...",
        style=style("text.muted"),
    )

    layout = get_app_frame("mlxlab", body, footer)

    console.clear()
    with live_frame(
        layout,
        console=console,
        refresh_per_second=2,
        screen=False,
    ):
        time.sleep(0.5)
        input()  # no prompt, just "press enter"


def _choose_preset(
    console: Console,
    current_settings: UISettings,
) -> Optional[Dict[str, Any]]:
    """Let the user pick a preset and preview it."""
    console.clear()
    console.print(Panel("Choose a UI Preset", style="bold"))

    choices: list[Choice] = []

    for preset_id, preset_data in PRESETS.items():
        choices.append(
            Choice(
                preset_id,
                name=f"{preset_data['name']} - {preset_data['description']}",
            )
        )

    choices.append(Choice(None, name="Cancel"))

    selected = (
        inquirer.select(
            message="Select a preset to preview:",
            choices=choices,
        )
        .execute()
    )

    if selected is None:
        return None

    preset_settings: Dict[str, Any] = PRESETS[selected]["settings"].copy()

    console.clear()
    console.print(
        f"\n[bold]Preview: {PRESETS[selected]['name']}[/bold]\n",
    )
    _show_preview(console, preset_settings, PRESETS[selected]["name"])

    return preset_settings


def _tweak_settings(
    console: Console,
    current_settings: Dict[str, Any],
) -> Dict[str, Any]:
    """Interactively tweak individual settings."""
    console.clear()
    console.print(Panel("Tweak Individual Settings", style="bold"))

    theme_variant = (
        inquirer.select(
            message="Theme variant:",
            choices=["default", "high_contrast", "neon"],
            default=current_settings.get("theme_variant", "default"),
        )
        .execute()
    )

    border_style = (
        inquirer.select(
            message="Border style:",
            choices=["square", "minimal", "none"],
            default=current_settings.get("border_style", "square"),
        )
        .execute()
    )

    app_color_mode = (
        inquirer.select(
            message="App color mode:",
            choices=["per_app_color", "mono_accent"],
            default=current_settings.get("app_color_mode", "per_app_color"),
        )
        .execute()
    )

    show_icons = (
        inquirer.confirm(
            message="Show app icons in menus?",
            default=current_settings.get("show_icons", True),
        )
        .execute()
    )

    new_settings: Dict[str, Any] = {
        "theme_variant": theme_variant,
        "border_style": border_style,
        "app_color_mode": app_color_mode,
        "show_icons": show_icons,
    }

    console.clear()
    console.print("\n[bold]Preview: Custom Settings[/bold]\n")
    _show_preview(console, new_settings, "Custom")

    return new_settings


def _reset_to_defaults(console: Console) -> Dict[str, Any]:
    """Reset settings to factory defaults (with confirmation & preview)."""
    console.clear()
    console.print(Panel("Reset to Factory Defaults", style="bold"))

    confirm = (
        inquirer.confirm(
            message="Reset all settings to factory defaults?",
            default=False,
        )
        .execute()
    )

    if not confirm:
        # Just reload current settings, user bailed
        return load_ui_settings()

    console.clear()
    console.print("\n[bold]Preview: Factory Defaults[/bold]\n")
    _show_preview(console, DEFAULT_SETTINGS.copy(), "Factory Defaults")

    return DEFAULT_SETTINGS.copy()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_ui_playground(console: Optional[Console] = None) -> None:
    """
    Run the interactive UI playground.

    Lets the user:
      - choose a preset
      - tweak individual settings
      - reset to defaults
      - preview current config
      - save or cancel
    """
    if console is None:
        console = get_console()

    settings: Dict[str, Any] = load_ui_settings()

    while True:
        console.clear()
        console.print(
            Panel(
                (
                    "UI Playground - Tweak the frame, borders, and colors\n"
                    "Changes are saved to var/ui_settings.json"
                ),
                title="UI Playground",
                style="bold",
            )
        )

        action = (
            inquirer.select(
                message="What would you like to do?",
                choices=[
                    Choice("preset", "Choose a preset"),
                    Choice("tweak", "Tweak individual settings"),
                    Choice("reset", "Reset to defaults"),
                    Choice("preview", "Preview current settings"),
                    Choice("save", "Save and return to main menu"),
                    Choice("cancel", "Cancel (discard changes)"),
                ],
            )
            .execute()
        )

        if action == "preset":
            new_settings = _choose_preset(console, settings)
            if new_settings is not None:
                settings = new_settings

        elif action == "tweak":
            settings = _tweak_settings(console, settings)

        elif action == "reset":
            settings = _reset_to_defaults(console)

        elif action == "preview":
            console.clear()
            console.print("\n[bold]Current Settings Preview[/bold]\n")
            _show_preview(console, settings, None)

        elif action == "save":
            save_ui_settings(settings)

            # lazy import to avoid circulars on module import
            from .theme import reload_theme

            reload_theme()

            console.clear()
            console.print("\n[green]Settings saved successfully![/green]")
            console.print(
                "Theme will be applied when you return to the menu.\n",
            )
            time.sleep(1.5)
            return

        elif action == "cancel":
            console.clear()
            console.print("\n[yellow]Changes discarded.[/yellow]\n")
            time.sleep(1.0)
            return

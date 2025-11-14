"""
Rich theme and semantic color tokens for mlx-RAG CLI.
All CLIs should import get_console() instead of creating their own Console.
"""
from pathlib import Path
from rich.console import Console
from rich.theme import Theme

THEME_VARIANTS = {
    'default': {
        'frame.bg': 'on grey11',
        'frame.border': 'bright_black',
        'frame.chrome': 'grey50',
        'text.primary': 'white',
        'text.secondary': 'grey70',
        'text.muted': 'grey50',
        'text.error': 'red',
        'text.success': 'green',
        'text.warning': 'yellow',
        'text.accent': 'cyan',
        'state.loading': 'yellow',
        'state.ready': 'green',
        'state.error': 'red',
        'state.idle': 'grey50'
    },
    'high_contrast': {
        'frame.bg': 'on black',
        'frame.border': 'white',
        'frame.chrome': 'bright_white',
        'text.primary': 'bright_white',
        'text.secondary': 'white',
        'text.muted': 'bright_black',
        'text.error': 'bright_red',
        'text.success': 'bright_green',
        'text.warning': 'bright_yellow',
        'text.accent': 'bright_cyan',
        'state.loading': 'bright_yellow',
        'state.ready': 'bright_green',
        'state.error': 'bright_red',
        'state.idle': 'bright_black'
    },
    'neon': {
        'frame.bg': 'on grey7',
        'frame.border': 'bright_magenta',
        'frame.chrome': 'bright_cyan',
        'text.primary': 'bright_white',
        'text.secondary': 'bright_cyan',
        'text.muted': 'magenta',
        'text.error': 'bright_red',
        'text.success': 'bright_green',
        'text.warning': 'bright_yellow',
        'text.accent': 'bright_magenta',
        'state.loading': 'bright_yellow',
        'state.ready': 'bright_green',
        'state.error': 'bright_red',
        'state.idle': 'magenta'
    }
}

APP_COLORS = {
    'app.chat': 'green',
    'app.voice_chat': 'bright_green',
    'app.sts_avatar': 'bright_cyan',
    'app.rag': 'magenta',
    'app.ingest': 'blue',
    'app.classify': 'bright_magenta',
    'app.flux': 'cyan',
    'app.musicgen': 'green',
    'app.whisper': 'yellow',
    'app.bench': 'red',
    'app.generators': 'bright_yellow',
    'app.mlxlab': 'bright_white'
}

_console: Console | None = None
_current_theme_tokens: dict | None = None


def _load_settings():
    """Load UI settings from file."""
    from settings import SETTINGS_FILE

    if SETTINGS_FILE.exists():
        try:
            import json
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass

    return {
        'theme_variant': 'default',
        'border_style': 'square',
        'app_color_mode': 'per_app_color',
        'show_icons': True
    }


def _build_theme_tokens(settings):
    """Build theme tokens based on settings."""
    variant = settings.get('theme_variant', 'default')
    app_color_mode = settings.get('app_color_mode', 'per_app_color')

    # Get theme variant tokens
    tokens = THEME_VARIANTS.get(variant, THEME_VARIANTS['default']).copy()

    # Apply app color mode
    if app_color_mode == 'per_app_color':
        tokens.update(APP_COLORS)
    else:
        # Mono accent mode - use text.accent for all apps
        accent = tokens.get('text.accent', 'cyan')
        for app_key in APP_COLORS.keys():
            tokens[app_key] = accent

    return tokens


def get_theme_tokens():
    """Get current theme tokens (cached)."""
    global _current_theme_tokens
    if _current_theme_tokens is None:
        settings = _load_settings()
        _current_theme_tokens = _build_theme_tokens(settings)
    return _current_theme_tokens


def reload_theme():
    """Force reload theme from settings file."""
    global _console, _current_theme_tokens
    _console = None
    _current_theme_tokens = None


def get_console(force_terminal=False, soft_wrap=False):
    """
    Get the shared Console instance.
    All CLIs should use this instead of Console() to ensure consistent theming.
    """
    global _console
    if _console is None:
        tokens = get_theme_tokens()
        theme = Theme(tokens)
        _console = Console(theme=theme, force_terminal=force_terminal, soft_wrap=soft_wrap, highlight=False)
    return _console


def get_app_color(app_id: str):
    """
    Get the accent color for a specific app.
    Returns a real style string, not a token.
    """
    tokens = get_theme_tokens()
    return tokens.get(f'app.{app_id}', tokens.get('app.mlxlab', 'bright_white'))


def style(token: str, bold=False, dim=False):
    """Build a style string from semantic token + modifiers."""
    tokens = get_theme_tokens()
    base = tokens.get(token, token)
    modifiers = []
    if bold:
        modifiers.append('bold')
    if dim:
        modifiers.append('dim')
    return ' '.join([base] + modifiers) if modifiers else base

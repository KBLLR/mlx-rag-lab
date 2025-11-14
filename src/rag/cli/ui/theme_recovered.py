Unsupported opcode: MAKE_FUNCTION (122)
# Source Generated with Decompyle++
# File: theme.cpython-313.pyc (Python 3.13)

__doc__ = '\nRich theme and semantic color tokens for mlx-RAG CLI.\nAll CLIs should import get_console() instead of creating their own Console.\n'
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
        'state.idle': 'grey50' },
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
        'state.idle': 'bright_black' },
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
        'state.idle': 'magenta' } }
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
    'app.mlxlab': 'bright_white' }
_console: Console | None = None
_current_theme_tokens: dict | None = None
# WARNING: Decompyle incomplete

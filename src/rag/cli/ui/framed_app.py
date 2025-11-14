Unsupported opcode: MAKE_FUNCTION (122)
# Source Generated with Decompyle++
# File: framed_app.cpython-313.pyc (Python 3.13)

__doc__ = '\nFull-screen framed app with fixed header/footer and scrollable body.\nFor apps that need true device frame layout with scroll support.\n'
import threading
from typing import Callable, List, Optional
from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from app_frames import APP_METADATA
from theme import get_app_color, get_console, style
# WARNING: Decompyle incomplete

Unsupported opcode: MAKE_FUNCTION (122)
# Source Generated with Decompyle++
# File: chat_framed_app.cpython-313.pyc (Python 3.13)

__doc__ = '\nChat-specific framed app with input footer.\nBody shows chat history, footer is the live input field.\n'
import queue
import threading
from typing import Callable, Optional
from rich.console import Console, RenderableType
from rich.text import Text
from framed_app import FramedApp
from theme import style
# WARNING: Decompyle incomplete

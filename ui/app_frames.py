"""
Per-app frame builders with metadata (titles, colors, captions).
"""

from rich.align import Align
from rich.console import Group
from rich.layout import Layout
from rich.text import Text

from .layouts import build_frame
from .theme import get_app_color, style


APP_METADATA: dict[str, dict[str, str]] = {
    "chat": {
        "title": "CHAT",
        "caption": "Conversational AI - Multi-turn dialogue",
        "ascii": """
     ██████╗██╗  ██╗ █████╗ ████████╗
    ██╔════╝██║  ██║██╔══██╗╚══██╔══╝
    ██║     ███████║███████║   ██║
    ██║     ██╔══██║██╔══██║   ██║
    ╚██████╗██║  ██║██║  ██║   ██║
     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝
        """,
    },
    "voice_chat": {
        "title": "VOICE",
        "caption": "Text-to-Speech - Push-to-talk",
        "ascii": """
    ██╗   ██╗ ██████╗ ██╗ ██████╗███████╗
    ██║   ██║██╔═══██╗██║██╔════╝██╔════╝
    ██║   ██║██║   ██║██║██║     █████╗
    ╚██╗ ██╔╝██║   ██║██║██║     ██╔══╝
     ╚████╔╝ ╚██████╔╝██║╚██████╗███████╗
      ╚═══╝   ╚═════╝ ╚═╝ ╚═════╝╚══════╝
        """,
    },
    "sts_avatar": {
        "title": "STS AVATAR",
        "caption": "Speech-to-Speech - Avatar lip-sync",
        "ascii": """
    ███████╗████████╗███████╗
    ██╔════╝╚══██╔══╝██╔════╝
    ███████╗   ██║   ███████╗
    ╚════██║   ██║   ╚════██║
    ███████║   ██║   ███████║
    ╚══════╝   ╚═╝   ╚══════╝
        """,
    },
    "rag": {
        "title": "RAG",
        "caption": "Retrieval-Augmented Generation - Question answering",
        "ascii": """
    ██████╗  █████╗  ██████╗
    ██╔══██╗██╔══██╗██╔════╝
    ██████╔╝███████║██║  ███╗
    ██╔══██╗██╔══██║██║   ██║
    ██║  ██║██║  ██║╚██████╔╝
    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝
        """,
    },
    "ingest": {
        "title": "INGEST",
        "caption": "Vector index builder - Multi-bank support",
        "ascii": """
    ██╗███╗   ██╗ ██████╗ ███████╗███████╗████████╗
    ██║████╗  ██║██╔════╝ ██╔════╝██╔════╝╚══██╔══╝
    ██║██╔██╗ ██║██║  ███╗█████╗  ███████╗   ██║
    ██║██║╚██╗██║██║   ██║██╔══╝  ╚════██║   ██║
    ██║██║ ╚████║╚██████╔╝███████╗███████║   ██║
    ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚══════╝   ╚═╝
        """,
    },
    "classify": {
        "title": "CLASSIFY",
        "caption": "Text classification - Sentiment, emotion, zero-shot",
        "ascii": """
     ██████╗██╗      █████╗ ███████╗███████╗██╗███████╗██╗   ██╗
    ██╔════╝██║     ██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝
    ██║     ██║     ███████║███████╗███████╗██║█████╗   ╚████╔╝
    ██║     ██║     ██╔══██║╚════██║╚════██║██║██╔══╝    ╚██╔╝
    ╚██████╗███████╗██║  ██║███████║███████║██║██║        ██║
     ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝        ╚═╝
        """,
    },
    "flux": {
        "title": "FLUX",
        "caption": "Text-to-image - MLX-native generation",
        "ascii": """
    ███████╗██╗     ██╗   ██╗██╗  ██╗
    ██╔════╝██║     ██║   ██║╚██╗██╔╝
    █████╗  ██║     ██║   ██║ ╚███╔╝
    ██╔══╝  ██║     ██║   ██║ ██╔██╗
    ██║     ███████╗╚██████╔╝██╔╝ ██╗
    ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝
        """,
    },
    "musicgen": {
        "title": "MUSICGEN",
        "caption": "Audio generation - Prompt library included",
        "ascii": """
    ███╗   ███╗██╗   ██╗███████╗██╗ ██████╗
    ████╗ ████║██║   ██║██╔════╝██║██╔════╝
    ██╔████╔██║██║   ██║███████╗██║██║
    ██║╚██╔╝██║██║   ██║╚════██║██║██║
    ██║ ╚═╝ ██║╚██████╔╝███████║██║╚██████╗
    ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝ ╚═════╝
        """,
    },
    "whisper": {
        "title": "WHISPER",
        "caption": "Speech-to-text - MLX acceleration",
        "ascii": """
    ██╗    ██╗██╗  ██╗██╗███████╗██████╗ ███████╗██████╗
    ██║    ██║██║  ██║██║██╔════╝██╔══██╗██╔════╝██╔══██╗
    ██║ █╗ ██║███████║██║███████╗██████╔╝█████╗  ██████╔╝
    ██║███╗██║██╔══██║██║╚════██║██╔═══╝ ██╔══╝  ██╔══██╗
    ╚███╔███╔╝██║  ██║██║███████║██║     ███████╗██║  ██║
     ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝
        """,
    },
    "bench": {
        "title": "BENCHMARK",
        "caption": "Performance testing - Latency & throughput",
        "ascii": """
    ██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗
    ██╔══██╗██╔════╝████╗  ██║██╔════╝██║  ██║
    ██████╔╝█████╗  ██╔██╗ ██║██║     ███████║
    ██╔══██╗██╔══╝  ██║╚██╗██║██║     ██╔══██║
    ██████╔╝███████╗██║ ╚████║╚██████╗██║  ██║
    ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝
        """,
    },
    "generators": {
        "title": "GENERATORS",
        "caption": "Synthetic dataset creation - Q&A, classification",
        "ascii": """
     ██████╗ ███████╗███╗   ██╗
    ██╔════╝ ██╔════╝████╗  ██║
    ██║  ███╗█████╗  ██╔██╗ ██║
    ██║   ██║██╔══╝  ██║╚██╗██║
    ╚██████╔╝███████╗██║ ╚████║
     ╚═════╝ ╚══════╝╚═╝  ╚═══╝
        """,
    },
    "mlxlab": {
        "title": "MLX LAB",
        "caption": "Local-first MLX pipelines - Metal-accelerated",
        "ascii": """
    ███╗   ███╗██╗     ██╗  ██╗    ██╗      █████╗ ██████╗
    ████╗ ████║██║     ╚██╗██╔╝    ██║     ██╔══██╗██╔══██╗
    ██╔████╔██║██║      ╚███╔╝     ██║     ███████║██████╔╝
    ██║╚██╔╝██║██║      ██╔██╗     ██║     ██╔══██║██╔══██╗
    ██║ ╚═╝ ██║███████╗██╔╝ ██╗    ███████╗██║  ██║██████╔╝
    ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝╚═════╝
        """,
    },
}


def get_app_frame(
    app_id: str,
    body_renderable,
    footer_renderable: Group | Layout | None = None,
) -> Layout:
    """
    Build a framed layout for a given app id.

    Uses:
    - header: ASCII art + app style
    - caption: app caption, secondary text
    - body_renderable: main content area (required)
    - footer_renderable: optional footer panel
    """
    # Fallback to "mlxlab" metadata if unknown app_id
    metadata = APP_METADATA.get(app_id, APP_METADATA["mlxlab"])

    # Not used in the disassembly, but kept for consistency / future styling
    color = get_app_color(app_id)  # noqa: F841

    header_text = Text(
        metadata["ascii"],
        style=style(f"app.{app_id}", bold=True),
    )
    header = Align.center(header_text)

    caption_text = Text(
        metadata["caption"],
        style=style("text.secondary"),
    )
    caption = Align.center(caption_text)

    frame = build_frame(
        header_renderable=header,
        caption_renderable=caption,
        body_renderable=body_renderable,
        footer_renderable=footer_renderable,
        border_color="frame.border",
    )
    return frame

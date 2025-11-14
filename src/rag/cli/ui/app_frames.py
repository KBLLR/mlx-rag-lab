Unsupported opcode: MAKE_FUNCTION (122)
# Source Generated with Decompyle++
# File: app_frames.cpython-313.pyc (Python 3.13)

__doc__ = '\nPer-app frame builders with metadata (titles, colors, captions).\n'
from rich.align import Align
from rich.console import Group
from rich.layout import Layout
from rich.text import Text
from layouts import build_frame
from theme import get_app_color, style
APP_METADATA = {
    'chat': {
        'title': 'CHAT',
        'caption': 'Conversational AI - Multi-turn dialogue',
        'ascii': '\n     ██████╗██╗  ██╗ █████╗ ████████╗\n    ██╔════╝██║  ██║██╔══██╗╚══██╔══╝\n    ██║     ███████║███████║   ██║\n    ██║     ██╔══██║██╔══██║   ██║\n    ╚██████╗██║  ██║██║  ██║   ██║\n     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝\n        ' },
    'voice_chat': {
        'title': 'VOICE',
        'caption': 'Text-to-Speech - Push-to-talk',
        'ascii': '\n    ██╗   ██╗ ██████╗ ██╗ ██████╗███████╗\n    ██║   ██║██╔═══██╗██║██╔════╝██╔════╝\n    ██║   ██║██║   ██║██║██║     █████╗\n    ╚██╗ ██╔╝██║   ██║██║██║     ██╔══╝\n     ╚████╔╝ ╚██████╔╝██║╚██████╗███████╗\n      ╚═══╝   ╚═════╝ ╚═╝ ╚═════╝╚══════╝\n        ' },
    'sts_avatar': {
        'title': 'STS AVATAR',
        'caption': 'Speech-to-Speech - Avatar lip-sync',
        'ascii': '\n    ███████╗████████╗███████╗\n    ██╔════╝╚══██╔══╝██╔════╝\n    ███████╗   ██║   ███████╗\n    ╚════██║   ██║   ╚════██║\n    ███████║   ██║   ███████║\n    ╚══════╝   ╚═╝   ╚══════╝\n        ' },
    'rag': {
        'title': 'RAG',
        'caption': 'Retrieval-Augmented Generation - Question answering',
        'ascii': '\n    ██████╗  █████╗  ██████╗\n    ██╔══██╗██╔══██╗██╔════╝\n    ██████╔╝███████║██║  ███╗\n    ██╔══██╗██╔══██║██║   ██║\n    ██║  ██║██║  ██║╚██████╔╝\n    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝\n        ' },
    'ingest': {
        'title': 'INGEST',
        'caption': 'Vector index builder - Multi-bank support',
        'ascii': '\n    ██╗███╗   ██╗ ██████╗ ███████╗███████╗████████╗\n    ██║████╗  ██║██╔════╝ ██╔════╝██╔════╝╚══██╔══╝\n    ██║██╔██╗ ██║██║  ███╗█████╗  ███████╗   ██║\n    ██║██║╚██╗██║██║   ██║██╔══╝  ╚════██║   ██║\n    ██║██║ ╚████║╚██████╔╝███████╗███████║   ██║\n    ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚══════╝   ╚═╝\n        ' },
    'classify': {
        'title': 'CLASSIFY',
        'caption': 'Text classification - Sentiment, emotion, zero-shot',
        'ascii': '\n     ██████╗██╗      █████╗ ███████╗███████╗██╗███████╗██╗   ██╗\n    ██╔════╝██║     ██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝\n    ██║     ██║     ███████║███████╗███████╗██║█████╗   ╚████╔╝\n    ██║     ██║     ██╔══██║╚════██║╚════██║██║██╔══╝    ╚██╔╝\n    ╚██████╗███████╗██║  ██║███████║███████║██║██║        ██║\n     ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝        ╚═╝\n        ' },
    'flux': {
        'title': 'FLUX',
        'caption': 'Text-to-image - MLX-native generation',
        'ascii': '\n    ███████╗██╗     ██╗   ██╗██╗  ██╗\n    ██╔════╝██║     ██║   ██║╚██╗██╔╝\n    █████╗  ██║     ██║   ██║ ╚███╔╝\n    ██╔══╝  ██║     ██║   ██║ ██╔██╗\n    ██║     ███████╗╚██████╔╝██╔╝ ██╗\n    ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝\n        ' },
    'musicgen': {
        'title': 'MUSICGEN',
        'caption': 'Audio generation - Prompt library included',
        'ascii': '\n    ███╗   ███╗██╗   ██╗███████╗██╗ ██████╗\n    ████╗ ████║██║   ██║██╔════╝██║██╔════╝\n    ██╔████╔██║██║   ██║███████╗██║██║\n    ██║╚██╔╝██║██║   ██║╚════██║██║██║\n    ██║ ╚═╝ ██║╚██████╔╝███████║██║╚██████╗\n    ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝ ╚═════╝\n        ' },
    'whisper': {
        'title': 'WHISPER',
        'caption': 'Speech-to-text - MLX acceleration',
        'ascii': '\n    ██╗    ██╗██╗  ██╗██╗███████╗██████╗ ███████╗██████╗\n    ██║    ██║██║  ██║██║██╔════╝██╔══██╗██╔════╝██╔══██╗\n    ██║ █╗ ██║███████║██║███████╗██████╔╝█████╗  ██████╔╝\n    ██║███╗██║██╔══██║██║╚════██║██╔═══╝ ██╔══╝  ██╔══██╗\n    ╚███╔███╔╝██║  ██║██║███████║██║     ███████╗██║  ██║\n     ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝\n        ' },
    'bench': {
        'title': 'BENCHMARK',
        'caption': 'Performance testing - Latency & throughput',
        'ascii': '\n    ██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗\n    ██╔══██╗██╔════╝████╗  ██║██╔════╝██║  ██║\n    ██████╔╝█████╗  ██╔██╗ ██║██║     ███████║\n    ██╔══██╗██╔══╝  ██║╚██╗██║██║     ██╔══██║\n    ██████╔╝███████╗██║ ╚████║╚██████╗██║  ██║\n    ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝\n        ' },
    'generators': {
        'title': 'GENERATORS',
        'caption': 'Synthetic dataset creation - Q&A, classification',
        'ascii': '\n     ██████╗ ███████╗███╗   ██╗\n    ██╔════╝ ██╔════╝████╗  ██║\n    ██║  ███╗█████╗  ██╔██╗ ██║\n    ██║   ██║██╔══╝  ██║╚██╗██║\n    ╚██████╔╝███████╗██║ ╚████║\n     ╚═════╝ ╚══════╝╚═╝  ╚═══╝\n        ' },
    'mlxlab': {
        'title': 'MLX LAB',
        'caption': 'Local-first MLX pipelines - Metal-accelerated',
        'ascii': '\n    ███╗   ███╗██╗     ██╗  ██╗    ██╗      █████╗ ██████╗\n    ████╗ ████║██║     ╚██╗██╔╝    ██║     ██╔══██╗██╔══██╗\n    ██╔████╔██║██║      ╚███╔╝     ██║     ███████║██████╔╝\n    ██║╚██╔╝██║██║      ██╔██╗     ██║     ██╔══██║██╔══██╗\n    ██║ ╚═╝ ██║███████╗██╔╝ ██╗    ███████╗██║  ██║██████╔╝\n    ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝╚═════╝\n        ' } }
# WARNING: Decompyle incomplete

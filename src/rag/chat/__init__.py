"""
Chat abstractions for MLX models with proper conversation management.
"""

from .gpt_oss_wrapper import ChatSession, Message, Role

__all__ = ["ChatSession", "Message", "Role"]

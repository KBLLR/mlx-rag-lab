#!/usr/bin/env python3
"""
Clean chat wrapper for GPT-OSS 20B (and other MLX LLMs) with:
- Proper tokenizer.chat_template usage
- Structured conversation history
- Streaming support
- Tool/function calling hooks for future MCP integration
"""

from dataclasses import dataclass
from enum import Enum
from typing import Iterator, List, Optional, Dict, Any, Callable
import mlx.core as mx
from mlx_lm import load, generate, stream_generate
from .templates import strip_channel_controls


class Role(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"  # For future function calling


@dataclass
class Message:
    """Single message in conversation."""
    role: Role
    content: str
    name: Optional[str] = None  # For tool calls
    tool_calls: Optional[List[Dict]] = None  # For function calling (future)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for chat_template."""
        result = {"role": self.role.value, "content": self.content}
        if self.name:
            result["name"] = self.name
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        return result


class ChatSession:
    """
    Manages conversation with GPT-OSS or other MLX LLM.

    Usage:
        session = ChatSession("mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx")

        # Single turn
        response = session.chat("Hello!")

        # Multi-turn with streaming
        for token in session.chat_stream("What is MLX?"):
            print(token, end="", flush=True)
    """

    def __init__(
        self,
        model_id: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
    ):
        """
        Initialize chat session.

        Args:
            model_id: Model path or HuggingFace ID
            system_prompt: Optional system message
            max_tokens: Max tokens per response
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
        """
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p

        # Load model and tokenizer
        print(f"Loading {model_id}...")
        self.model, self.tokenizer = load(model_id)

        # Initialize conversation history
        self.messages: List[Message] = []
        if system_prompt:
            self.messages.append(Message(Role.SYSTEM, system_prompt))

        # Check if model supports chat template
        self.has_chat_template = hasattr(self.tokenizer, "chat_template") and self.tokenizer.chat_template is not None

        if not self.has_chat_template:
            print(f"Warning: {model_id} has no chat_template, using fallback formatting")

    def _format_prompt(self, messages: List[Message]) -> str:
        """
        Format messages into prompt string.
        Uses tokenizer.chat_template if available, fallback otherwise.
        """
        # Convert to dicts for chat_template
        messages_dict = [msg.to_dict() for msg in messages]

        if self.has_chat_template:
            # Use model's native chat template
            try:
                prompt = self.tokenizer.apply_chat_template(
                    messages_dict,
                    add_generation_prompt=True,
                    tokenize=False
                )
                return prompt
            except Exception as e:
                print(f"Warning: chat_template failed ({e}), using fallback")

        # Fallback: simple concatenation
        lines = []
        for msg in messages:
            if msg.role == Role.SYSTEM:
                lines.append(f"System: {msg.content}")
            elif msg.role == Role.USER:
                lines.append(f"User: {msg.content}")
            elif msg.role == Role.ASSISTANT:
                lines.append(f"Assistant: {msg.content}")

        lines.append("Assistant:")
        return "\n".join(lines)

    def chat(self, user_message: str, add_to_history: bool = True) -> str:
        """
        Single-turn chat (blocking).

        Args:
            user_message: User's input
            add_to_history: Whether to add to conversation history

        Returns:
            Assistant's response
        """
        # Add user message
        temp_messages = self.messages.copy()
        temp_messages.append(Message(Role.USER, user_message))

        # Format prompt
        prompt = self._format_prompt(temp_messages)

        # Generate response (NOTE: mlx_lm.generate doesn't support temp/top_p kwargs directly)
        # It uses model's default sampling. For custom sampling, need to use lower-level APIs.
        response = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=self.max_tokens,
            verbose=False
        )

        # Clean response
        response = self._post_process(response)

        # Update history if requested
        if add_to_history:
            self.messages.append(Message(Role.USER, user_message))
            self.messages.append(Message(Role.ASSISTANT, response))

        return response

    def chat_stream(self, user_message: str, add_to_history: bool = True) -> Iterator[str]:
        """
        Streaming chat (yields tokens as generated).

        Args:
            user_message: User's input
            add_to_history: Whether to add to conversation history

        Yields:
            Individual tokens as they're generated
        """
        # Add user message
        temp_messages = self.messages.copy()
        temp_messages.append(Message(Role.USER, user_message))

        # Format prompt
        prompt = self._format_prompt(temp_messages)

        # Stream tokens
        full_response = ""
        for token_data in stream_generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=self.max_tokens
        ):
            token = token_data.text
            full_response += token
            yield token

        # Update history if requested
        if add_to_history:
            self.messages.append(Message(Role.USER, user_message))
            self.messages.append(Message(Role.ASSISTANT, full_response))

    def _post_process(self, response: str) -> str:
        """
        Clean up model response.
        Remove common artifacts, trim whitespace, etc.
        """
        # Remove potential special tokens
        response = response.strip()

        # Remove GPT-OSS control tags (analysis/final channels)
        response = strip_channel_controls(response)

        # Remove common artifacts (adjust based on model behavior)
        for artifact in ["<|endoftext|>", "</s>", "<|im_end|>"]:
            response = response.replace(artifact, "")

        return response.strip()

    def add_system_message(self, content: str):
        """Add a system message to the conversation."""
        self.messages.append(Message(Role.SYSTEM, content))

    def clear_history(self, keep_system: bool = True):
        """
        Clear conversation history.

        Args:
            keep_system: If True, keep system messages
        """
        if keep_system:
            self.messages = [msg for msg in self.messages if msg.role == Role.SYSTEM]
        else:
            self.messages = []

    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history as list of dicts."""
        return [msg.to_dict() for msg in self.messages]

    def set_temperature(self, temperature: float):
        """Update sampling temperature (for next generations)."""
        self.temperature = max(0.0, min(1.0, temperature))

    # ===== Future: Tool/Function Calling =====
    # These are hooks for future MCP/agent integration

    def register_tool(self, name: str, description: str, callback: Callable):
        """
        Register a tool/function that the model can call.

        Args:
            name: Tool name
            description: What the tool does (for model prompt)
            callback: Function to execute when tool is called

        Note: This is a placeholder for future function calling support.
        Actual implementation would need:
        - Tool schema in prompt
        - Parsing tool call requests from model output
        - Executing callback with parsed args
        - Injecting tool response back into conversation
        """
        # TODO: Implement when MLX supports function calling
        # or when we have a prompt template for tool use
        raise NotImplementedError("Tool calling not yet implemented")

    def execute_tool_loop(self, user_message: str, max_iterations: int = 5) -> str:
        """
        Execute conversation with tool calling loop.
        Model can call tools, receive results, and continue.

        Note: Placeholder for future agent/MCP integration.
        """
        # TODO: Implement tool calling loop
        # 1. Generate response
        # 2. Parse for tool calls
        # 3. Execute tools
        # 4. Add tool results to history
        # 5. Continue generation
        # 6. Repeat until no more tool calls or max iterations
        raise NotImplementedError("Tool loop not yet implemented")


# ===== Utility Functions =====

def create_chat_session(
    model_id: str = "mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx",
    system_prompt: str = "You are a helpful, direct, and technically precise AI assistant.",
    **kwargs
) -> ChatSession:
    """
    Convenience function to create a chat session.

    Args:
        model_id: Model to use
        system_prompt: Initial system prompt
        **kwargs: Additional ChatSession arguments

    Returns:
        Initialized ChatSession
    """
    return ChatSession(model_id, system_prompt=system_prompt, **kwargs)

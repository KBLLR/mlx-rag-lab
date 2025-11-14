#!/usr/bin/env python3
"""
Chat CLI - Conversational interface using MLXModelEngine (GPT-OSS 20B, Phi-3, etc).

- Pure chat (no RAG).
- No streaming for now (to avoid generate_step/temperature API mismatch).
- Keeps --temperature and --stream flags to stay compatible with mlxlab config,
  but does NOT pass them into MLX internals yet.
"""

import argparse
import gc
import json
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from libs.mlx_core.model_engine import MLXModelEngine
from rag.chat.templates import strip_channel_controls
from ui import FramedApp, get_console, label

console = get_console()

DEFAULT_MODEL_ID = "mlx-models/gpt-oss-20b-mxfp4"
FALLBACK_MODEL_ID = "mlx-community/Jinx-gpt-oss-20b-mxfp4-mlx"

DEFAULT_SYSTEM_PROMPT = "You are a helpful, direct, and technically precise AI assistant."

MODE_SUFFIXES = {
    "chat": "",
    "web": (
        " You are in research mode. You do not have live web access, but you should lean on broad "
        "background knowledge, be explicit about uncertainty, and avoid fabricating citations. "
        "When relevant, mention what you would verify or look up."
    ),
    "thinking": (
        " You are in deep thinking mode. Work through problems step by step, explicitly explaining "
        "your reasoning before giving a concise final answer. Prefer clarity and correctness over brevity."
    ),
}

_model_engine: MLXModelEngine | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MLX Chat CLI – conversational interface with LLMs."
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default=None,
        help=f"MLX model ID or path (default: {DEFAULT_MODEL_ID} if exists, else {FALLBACK_MODEL_ID})",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Max tokens per response.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="(Currently ignored) Intended sampling temperature.",
    )
    parser.add_argument(
        "--system-prompt",
        type=str,
        default=DEFAULT_SYSTEM_PROMPT,
        help="Base system prompt to set assistant behavior (mode-specific hints are appended).",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["chat", "web", "thinking"],
        default="chat",
        help="Interaction mode: 'chat', 'web' (researcher-style), or 'thinking' (step-by-step).",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="(Currently ignored) Streaming is not implemented in this CLI.",
    )
    parser.add_argument(
        "--save-chat",
        action="store_true",
        help="Save conversation history on exit.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("var/chats"),
        help="Directory to save chat logs (default: var/chats)",
    )
    parser.add_argument(
        "--classify-on-exit",
        action="store_true",
        help="Classify conversation sentiment/topics on exit.",
    )
    return parser


def build_system_prompt(base_prompt: str, mode: str) -> str:
    suffix = MODE_SUFFIXES.get(mode, "")
    if suffix:
        return f"{base_prompt.rstrip()} {suffix}".strip()
    return base_prompt


def cleanup_handler(signum, frame):
    global _model_engine

    console.print("\n\n🧹 Cleaning up...", style="yellow")

    if _model_engine is not None:
        del _model_engine
        _model_engine = None

    gc.collect()
    console.print("✅ Cleanup complete. Bye.\n", style="green")
    sys.exit(0)


def format_chat_prompt(
    system_prompt: str,
    history: List[Dict],
    user_input: str,
    tokenizer,
) -> str:
    """
    Build a prompt using the tokenizer's native chat template when available.
    Falls back to the legacy System/User/Assistant formatting if template application fails.
    """
    messages: list[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    chat_template = getattr(tokenizer, "chat_template", None)
    if chat_template:
        try:
            return tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=False,
            )
        except Exception as exc:
            console.print(
                f"[yellow]chat_template failed ({exc}); falling back to plain formatting[/yellow]"
            )

    lines: list[str] = []
    if system_prompt:
        lines.append(f"System: {system_prompt}")

    for msg in history:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            lines.append(f"User: {content}")
        elif role == "assistant":
            lines.append(f"Assistant: {content}")

    lines.append(f"User: {user_input}")
    lines.append("Assistant:")
    return "\n".join(lines)


def classify_conversation(model_engine: MLXModelEngine, history: List[Dict]) -> dict:
    if not history:
        return {}

    instructions = (
        "You are a conversation analyst. Given the transcript below, identify:\n"
        "1) overall_sentiment: one of ['very negative','negative','neutral','positive','very positive']\n"
        "2) topics: a short list of 3–8 high-level tags\n"
        "3) has_technical_content: true if the conversation involves code, ML, tools, or debugging, else false\n"
        "Respond ONLY as compact JSON with keys: overall_sentiment, topics, has_technical_content.\n"
    )

    transcript_lines: list[str] = []
    for msg in history:
        transcript_lines.append(f"{msg['role']}: {msg['content']}")

    prompt = instructions + "\nTranscript:\n" + "\n".join(transcript_lines) + "\n\nJSON:"

    # IMPORTANT: same pattern as rag_cli: no temperature kwarg.
    raw = model_engine.generate(
        prompt,
        max_tokens=256,
    )

    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(raw[start : end + 1])
        else:
            parsed = {"raw": raw}
    except Exception:
        parsed = {"raw": raw}

    return parsed


def save_chat_log(
    output_dir: Path,
    history: List[Dict],
    meta: Dict,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = output_dir / f"chat-{timestamp}.json"

    payload = {"meta": meta, "history": history}

    log_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return log_path


def print_help_panel() -> None:
    help_md = Markdown(
        "\n".join(
            [
                "### Commands",
                "",
                "- `/help` — show this help",
                "- `/history` — dump the conversation so far",
                "- `/clear` — clear in-memory history",
                "- `/mode` — show the active interaction mode",
                "- `/exit`, `/quit`, `/q` — exit the chat",
                "",
                "`--mode`, `--save-chat`, `--classify-on-exit` are set at startup.",
            ]
        )
    )
    console.print(Panel(help_md, title="Chat Commands", border_style="magenta"))


def main() -> None:
    global _model_engine

    # Don't register signal handler - let FramedApp context manager handle it
    # signal.signal(signal.SIGINT, cleanup_handler)

    args = build_parser().parse_args()

    if args.stream:
        console.print("[yellow]Note: --stream is currently ignored in chat-cli.[/yellow]")

    model_id = args.model_id
    if model_id is None:
        local_path = Path(DEFAULT_MODEL_ID)
        if local_path.exists():
            model_id = str(local_path)
            console.print(f"[green]Using local model: {model_id}[/green]")
        else:
            model_id = FALLBACK_MODEL_ID
            console.print(f"[yellow]Local model not found, using HuggingFace: {model_id}[/yellow]")
            console.print(
                "[dim]To download locally: uv run python scripts/download_gpt_oss_20b.py[/dim]\n"
            )

    base_system_prompt = args.system_prompt or DEFAULT_SYSTEM_PROMPT
    system_prompt = build_system_prompt(base_system_prompt, args.mode)

    console.print(f"\n[bold cyan]Loading model...[/bold cyan]")
    _model_engine = MLXModelEngine(model_id, model_type="text")
    model_engine = _model_engine
    console.print("[green]Model loaded successfully![/green]\n")

    # Create framed app
    app = FramedApp("chat", viewport_height=20)

    # Set footer with commands
    footer_text = Text()
    footer_text.append("Commands: ", style="dim")
    footer_text.append("/help /history /clear /mode /exit", style="cyan")
    app.set_footer(footer_text)

    # Add system prompt to body
    model_name = Path(model_id).name if "/" in model_id else model_id
    app.add_content(label(f"System: {system_prompt}", "muted"))
    app.add_content(label(f"Model: {model_name} | Mode: {args.mode} | Max Tokens: {args.max_tokens}", "muted"))
    app.add_content(Text(""))

    history: List[Dict] = []

    try:
        with app.run():
            while True:
                try:
                    # Exit the Live context temporarily for input
                    if app._live:
                        app._live.__exit__(None, None, None)

                    user_input = console.input("[bold green]You:[/bold green] ").strip()

                    # Re-enter Live context
                    if app._running and app._live:
                        app._live.__enter__()

                except (EOFError, KeyboardInterrupt):
                    console.print("\n[cyan]Bye.[/cyan]")
                    break

                if not user_input:
                    continue

                lowered = user_input.lower()
                if lowered in ("/exit", "/quit", "/q"):
                    console.print("\n[cyan]Bye.[/cyan]")
                    break
                elif lowered == "/clear":
                    history = []
                    app.clear_body()
                    app.add_content(label(f"System: {system_prompt}", "muted"))
                    app.add_content(label(f"Model: {model_name} | Mode: {args.mode}", "muted"))
                    app.add_content(Text(""))
                    app.refresh()
                    continue
                elif lowered == "/history":
                    if not history:
                        app.add_content(label("History is empty.", "muted"))
                        app.refresh()
                        continue
                    app.add_content(Text(""))
                    app.add_content(label(f"=== History ({len(history)} messages) ===", "accent"))
                    for msg in history:
                        role_text = Text()
                        if msg["role"] == "user":
                            role_text.append("You: ", style="bold green")
                        else:
                            role_text.append("Assistant: ", style="bold cyan")
                        role_text.append(msg["content"])
                        app.add_content(role_text)
                    app.add_content(label("=== End History ===", "accent"))
                    app.refresh()
                    continue
                elif lowered in ("/help", "/?"):
                    app.add_content(Text(""))
                    app.add_content(label("=== Commands ===", "accent"))
                    app.add_content(label("  /help - show this help", "secondary"))
                    app.add_content(label("  /history - show conversation history", "secondary"))
                    app.add_content(label("  /clear - clear history", "secondary"))
                    app.add_content(label("  /mode - show current mode", "secondary"))
                    app.add_content(label("  /exit, /quit, /q - exit chat", "secondary"))
                    app.refresh()
                    continue
                elif lowered == "/mode":
                    app.add_content(label(f"Current mode: {args.mode}", "accent"))
                    app.refresh()
                    continue

                # Add user message to display
                user_msg = Text()
                user_msg.append("You: ", style="bold green")
                user_msg.append(user_input)
                app.add_content(user_msg)
                app.refresh()

                prompt = format_chat_prompt(
                    system_prompt,
                    history,
                    user_input,
                    tokenizer=model_engine.tokenizer,
                )

                try:
                    response_text = model_engine.generate(
                        prompt,
                        max_tokens=args.max_tokens,
                    )
                    if isinstance(response_text, (dict, list)):
                        response_text = json.dumps(response_text, indent=2, ensure_ascii=False)
                    response_text = strip_channel_controls(response_text or "")

                    # Add assistant message to display
                    assistant_msg = Text()
                    assistant_msg.append("Assistant: ", style="bold cyan")
                    assistant_msg.append(response_text)
                    app.add_content(assistant_msg)
                    app.add_content(Text(""))  # Blank line for spacing
                    app.refresh()

                    history.append({"role": "user", "content": user_input})
                    history.append({"role": "assistant", "content": response_text})

                except Exception as e:
                    error_msg = Text()
                    error_msg.append("Error: ", style="bold red")
                    error_msg.append(str(e), style="red")
                    app.add_content(error_msg)
                    app.refresh()
                    continue
    finally:
        # Cleanup
        if _model_engine is not None:
            console.print("\n🧹 Cleaning up...", style="yellow")
            del _model_engine
            _model_engine = None
            gc.collect()
            console.print("✅ Cleanup complete. Bye.\n", style="green")

    if history:
        if args.classify_on_exit:
            console.print("\n[dim]Analyzing conversation...[/dim]")
            try:
                analysis = classify_conversation(model_engine, history)
                console.print(
                    Panel.fit(
                        json.dumps(analysis, indent=2, ensure_ascii=False),
                        title="Conversation Analysis",
                        border_style="green",
                    )
                )
            except Exception as e:
                console.print(f"[red]Classification failed: {e}[/red]")

        if args.save_chat:
            try:
                meta = {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "model_id": model_id,
                    "mode": args.mode,
                    "max_tokens": args.max_tokens,
                    "system_prompt": system_prompt,
                }
                log_path = save_chat_log(args.output_dir, history, meta)
                console.print(f"\n[green]Chat saved to[/green] [bold]{log_path}[/bold]\n")
            except Exception as e:
                console.print(f"[red]Failed to save chat: {e}[/red]")


if __name__ == "__main__":
    main()

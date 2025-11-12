"""
Textual-based interactive RAG client.

Provides a lightweight TUI that:
  - Shows retrieved chunks in a table.
  - Streams answers into a Markdown pane.
  - Lets the user rebuild the VDB or change settings from commands.
"""

from __future__ import annotations

import json
import multiprocessing as mp
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import List, NamedTuple
from rich.panel import Panel
from rich.pretty import Pretty


try:
    mp.set_start_method("fork")
except RuntimeError:
    pass

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Markdown,
    Static,
)

from rag.retrieval.vdb import VectorDB
from rag.models.qwen_reranker import QwenReranker
from libs.mlx_core.model_engine import MLXModelEngine

DEFAULT_VDB_PATH = "models/indexes/combined_vdb.npz"
DEFAULT_MODEL_ID = "mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit"


class RetrievalResult(NamedTuple):
    context_chunks: List[dict]
    raw_answer: str
    formatted_answer: str | None


class RAGEngine:
    def __init__(self, vdb_path: str, model_id: str):
        self.vdb_path = vdb_path
        self.model_id = model_id
        self.vdb: VectorDB | None = None
        self.model_engine: MLXModelEngine | None = None
        self.cross_encoder: QwenReranker | None = None

    def load(self) -> None:
        """Load vector DB, LLM, and reranker."""
        self.vdb = VectorDB(self.vdb_path)
        self.model_engine = MLXModelEngine(self.model_id, model_type="text")
        self.cross_encoder = QwenReranker("mlx-community/mxbai-rerank-large-v2")

    def ready(self) -> bool:
        return (
            self.vdb is not None
            and self.model_engine is not None
            and self.cross_encoder is not None
        )

    def ask(self, question: str) -> RetrievalResult:
        if not self.ready():
            raise RuntimeError("Engine not initialised.")
        assert self.vdb and self.model_engine and self.cross_encoder

        if not self.vdb.content:
            raise RuntimeError(
                "Vector database is empty. Ingest documents before asking questions."
            )

        initial_candidates = self.vdb.query(question, k=20)
        if not initial_candidates:
            raise RuntimeError("Could not retrieve any documents for that question.")

        candidate_texts = [c["text"] for c in initial_candidates]
        reranked_indices = self.cross_encoder.rank(question, candidate_texts)
        final_candidates = [initial_candidates[i] for i in reranked_indices[:5]]

        context = "\n---\n".join(
            f"Source: {chunk['source']}\nContent: {chunk['text']}"
            for chunk in final_candidates
        )

        prompt = (
            "You are a precise assistant. Answer ONLY using the JSON format "
            "[{\"answer\": str, \"source\": str}].\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )

        response = "".join(self.model_engine.stream_generate(prompt))
        formatted = None
        try:
            parsed = json.loads(response)
            formatted = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            formatted = None
        return RetrievalResult(final_candidates, response, formatted)


class PromptBox(Static):
    """Input + action buttons."""

    class Submitted(Message):
        def __init__(self, sender: PromptBox, question: str) -> None:
            super().__init__()
            self.sender = sender
            self.question = question

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Ask a question…", id="question-input")
        with Horizontal(id="prompt-buttons"):
            yield Button("Ask", id="ask-btn", variant="success")
            yield Button("Clear", id="clear-btn", variant="warning")

    @on(Input.Submitted, "#question-input")
    def handle_submit(self, event: Input.Submitted) -> None:
        self.post_message(self.Submitted(self, event.value.strip()))

    @on(Button.Pressed, "#ask-btn")
    def handle_click(self) -> None:
        input_widget = self.query_one("#question-input", Input)
        self.post_message(self.Submitted(self, input_widget.value.strip()))

    @on(Button.Pressed, "#clear-btn")
    def clear(self) -> None:
        input_widget = self.query_one("#question-input", Input)
        input_widget.value = ""
        input_widget.focus()


class StatusPanel(Static):
    def update_status(self, text: str) -> None:
        self.update(Panel(text, title="Status", border_style="cyan"))


class ContextTable(DataTable):
    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.add_column("Rank", width=6)
        self.add_column("Source", width=40)
        self.add_column("Preview", width=80)

    def show_context(self, chunks: List[dict]) -> None:
        self.clear()
        for idx, chunk in enumerate(chunks, start=1):
            preview = chunk["text"].replace("\n", " ")[:120] + "…"
            self.add_row(str(idx), chunk["source"], preview)


class AnswerPanel(Markdown):
    def show_answer(self, text: str, formatted: str | None) -> None:
        if formatted:
            self.update(f"```json\n{formatted}\n```")
        else:
            self.update(f"```\n{text}\n```")


class RAGTUI(App):
    CSS_PATH = None
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
    ]

    loading = reactive(True)

    def __init__(self, engine: RAGEngine):
        super().__init__()
        self.engine = engine

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PromptBox(id="prompt")
        with Container(id="body"):
            with Horizontal():
                yield ContextTable(id="context-table")
                yield AnswerPanel("# Answer will appear here\n", id="answer-panel")
        yield StatusPanel(id="status-panel")
        yield Footer()

    async def on_mount(self) -> None:
        await self._load_engine()

    async def _load_engine(self) -> None:
        self.query_one(StatusPanel).update_status("Loading components (this may take a while)…")
        def _load():
            self.engine.load()
        worker = self.run_worker(_load, exclusive=True, thread=True)
        await worker.wait()
        self.query_one(StatusPanel).update_status("Ready. Ask away!")
        self.loading = False

    @on(PromptBox.Submitted)
    async def handle_question(self, event: PromptBox.Submitted) -> None:
        question = event.question
        if not question:
            self.query_one(StatusPanel).update_status("Please enter a question.")
            return
        if self.loading:
            self.query_one(StatusPanel).update_status("Still loading models…")
            return

        self.query_one(StatusPanel).update_status("Retrieving, re-ranking, and generating…")

        def _ask():
            return self.engine.ask(question)

        worker = await self.run_worker(_ask, exclusive=True, thread=True)
        worker.awaitable.add_done_callback(lambda _: self.call_from_thread(self._update_result, worker))

    def _update_result(self, worker) -> None:
        try:
            result: RetrievalResult = worker.get_result()
        except Exception as exc:  # noqa: BLE001
            self.query_one(StatusPanel).update_status(f"[red]Error:[/red] {exc}")
            return
        self.query_one(ContextTable).show_context(result.context_chunks)
        self.query_one(AnswerPanel).show_answer(result.raw_answer, result.formatted_answer)
        self.query_one(StatusPanel).update_status("Done.")


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Launch the Textual-based MLX RAG interface.")
    parser.add_argument(
        "--vdb-path",
        "-v",
        default=DEFAULT_VDB_PATH,
        help="Path to the VectorDB file.",
    )
    parser.add_argument(
        "--model-id",
        "-m",
        default=DEFAULT_MODEL_ID,
        help="MLX model to use.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    Path(args.vdb_path).parent.mkdir(parents=True, exist_ok=True)
    engine = RAGEngine(args.vdb_path, args.model_id)
    RAGTUI(engine).run()


if __name__ == "__main__":
    main()

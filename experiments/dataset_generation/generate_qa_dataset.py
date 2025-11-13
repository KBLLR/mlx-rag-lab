import json
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import mlx.data as mxdata
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from unstructured.partition.pdf import partition_pdf

from libs.mlx_core.model_engine import MLXModelEngine
from rag.chat.templates import strip_channel_controls

console = Console()

SOURCE_DOCS_DIR = Path("var/source_docs")  # directory with PDFs
OUTPUT_DATASET_PATH = Path("var/benchmarking/generated_qa_dataset.json")

# Two-model setup: one for questions, one for answers (both MLX/Metal)
QUESTION_MODEL = os.getenv(
    "MLX_QUESTION_MODEL", "mlx-community/mistral-7b-instruct-v0.2-4bit"
)
ANSWER_MODEL = os.getenv(
    "MLX_ANSWER_MODEL", "mlx-community/mistral-7b-instruct-v0.2-4bit"
)
QUESTION_MAX_TOKENS = int(os.getenv("QUESTION_MAX_TOKENS", "160"))
ANSWER_MAX_TOKENS = int(os.getenv("ANSWER_MAX_TOKENS", "256"))

# How many Q&A per PDF
MAX_QA_PER_DOC = int(os.getenv("MAX_QA_PER_DOC", "20"))

# Drop obvious garbage chunks
MIN_CHARS_PER_CHUNK = int(os.getenv("MIN_CHARS_PER_CHUNK", "80"))

DEBUG = os.getenv("QA_DEBUG", "1") == "1"


@dataclass
class QAGenerationConfig:
    source_docs_dir: Path = SOURCE_DOCS_DIR
    output_dataset_path: Path = OUTPUT_DATASET_PATH
    question_model: str = QUESTION_MODEL
    answer_model: str = ANSWER_MODEL
    question_max_tokens: int = QUESTION_MAX_TOKENS
    answer_max_tokens: int = ANSWER_MAX_TOKENS
    max_qa_per_doc: int = MAX_QA_PER_DOC
    min_chars_per_chunk: int = MIN_CHARS_PER_CHUNK


def dprint(msg: str) -> None:
    if DEBUG:
        console.print(f"[dim]{msg}[/dim]")


# -----------------------------
# MLX helpers
# -----------------------------


class LocalTextGenerator:
    """Tiny wrapper around MLXModelEngine for prompt->text generation."""

    def __init__(self, model_id: str):
        self.model_id = model_id
        console.print(f"[cyan]Loading MLX model:[/cyan] [bold]{model_id}[/bold]")
        self.engine = MLXModelEngine(model_id, model_type="text")

    def generate(self, prompt: str, max_tokens: int) -> Optional[str]:
        try:
            output = self.engine.generate(prompt, max_tokens=max_tokens)
        except Exception as exc:
            console.print(f"[red]Generation failed on {self.model_id}: {exc}[/red]")
            return None

        if isinstance(output, (dict, list)):
            text = json.dumps(output, ensure_ascii=False)
        else:
            text = str(output)

        text = strip_channel_controls(text).strip()
        if not text:
            console.print(
                f"[yellow]Model {self.model_id} returned empty text. Skipping chunk.[/yellow]"
            )
            return None
        return text


# -----------------------------
# PDF handling
# -----------------------------


def list_pdf_files(source_dir: Path) -> List[Path]:
    pdf_files = list(source_dir.glob("*.pdf"))
    if not pdf_files:
        console.print(
            f"[red]No PDF files found in {source_dir}. "
            f"Place your documents in this folder as .pdf files.[/red]"
        )
    else:
        console.print("[bold cyan]Found the following PDF files:[/bold cyan]")
        for p in pdf_files:
            console.print(f"  • {p}")
    return pdf_files


def extract_chunks_for_pdf(pdf_path: Path, config: QAGenerationConfig) -> List[str]:
    pdf_path = pdf_path.expanduser().resolve()
    console.print(f"[INFO] Processing {pdf_path} for chunking...")

    try:
        elements = partition_pdf(filename=str(pdf_path))
    except Exception as e:
        console.print(f"[red]Error partitioning {pdf_path}: {e}. Skipping file.[/red]")
        return []

    chunks: List[str] = []
    for element in elements:
        text = getattr(element, "text", None)
        if not text:
            continue
        text = text.strip()
        if not text:
            continue
        if len(text) < config.min_chars_per_chunk:
            dprint(
                f"DEBUG: Skipping very short chunk from {pdf_path.name} "
                f"({len(text)} chars): {repr(text[:80])}"
            )
            continue
        chunks.append(text)

    console.print(
        f"[cyan]Extracted {len(chunks)} usable text chunks from {pdf_path.name}[/cyan]"
    )
    return chunks


def chunk_iterator(
    pdf_files: List[Path],
    config: QAGenerationConfig,
) -> Iterable[Dict[str, object]]:
    """Yield dict records compatible with mlx.data streams."""
    for pdf in pdf_files:
        chunks = extract_chunks_for_pdf(pdf, config)
        for idx, chunk_text in enumerate(chunks, start=1):
            yield {
                "pdf_path": str(pdf).encode("utf-8"),
                "chunk_index": idx,
                "chunk_text": chunk_text.encode("utf-8"),
            }


# -----------------------------
# Q & A generation
# -----------------------------


def generate_question(
    chunk_text: str,
    generator: LocalTextGenerator,
    max_tokens: int,
) -> Optional[str]:
    question_prompt = (
        "You are an expert question generator. "
        "Create a single, clear, and concise question that can be directly answered "
        "by the following text. The question should be specific and require "
        "understanding of the provided context. Do not include the answer "
        "in the question.\n\n"
        f"Context:\n{chunk_text}\n\n"
        "Question:"
    )

    return generator.generate(question_prompt, max_tokens=max_tokens)


def generate_answer(
    chunk_text: str,
    question: str,
    generator: LocalTextGenerator,
    max_tokens: int,
) -> Optional[str]:
    answer_prompt = (
        "You are an expert answer generator. "
        "Provide a concise and direct answer to the following question, "
        "using ONLY the provided context. "
        "If the context does not contain enough information to answer the question, "
        "state exactly: 'Not enough information'.\n\n"
        f"Context:\n{chunk_text}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    return generator.generate(answer_prompt, max_tokens=max_tokens)


def _decode_bytes_field(field) -> str:
    if hasattr(field, "tobytes"):
        return field.tobytes().decode("utf-8")
    return str(field)


# -----------------------------
# Main dataset generation
# -----------------------------


def generate_qa_dataset(
    config: Optional[QAGenerationConfig] = None,
    pdf_paths: Optional[List[Path]] = None,
) -> None:
    cfg = config or QAGenerationConfig()
    console.print("[bold cyan]Starting MLX Q&A Dataset Generation...[/bold cyan]")
    console.print(
        f"[cyan]Question model:[/cyan] [bold]{cfg.question_model}[/bold] "
        f"(max tokens {cfg.question_max_tokens})"
    )
    console.print(
        f"[cyan]Answer model:[/cyan] [bold]{cfg.answer_model}[/bold] "
        f"(max tokens {cfg.answer_max_tokens})"
    )
    console.print(
        f"[cyan]Max Q&A pairs per document:[/cyan] [bold]{cfg.max_qa_per_doc}[/bold]"
    )
    console.print(
        f"[cyan]Min chars per chunk:[/cyan] [bold]{cfg.min_chars_per_chunk}[/bold]"
    )

    pdf_files = pdf_paths or list_pdf_files(cfg.source_docs_dir)
    if not pdf_files:
        return

    question_generator = LocalTextGenerator(cfg.question_model)
    if cfg.question_model == cfg.answer_model:
        answer_generator = question_generator
    else:
        answer_generator = LocalTextGenerator(cfg.answer_model)

    qa_dataset: List[Dict[str, Any]] = []
    pairs_per_doc: Dict[str, int] = defaultdict(int)
    completed_docs: set[str] = set()

    progress_columns = [
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
    ]

    chunk_stream = mxdata.stream_python_iterable(
        lambda: chunk_iterator(pdf_files, cfg)
    )

    with Progress(*progress_columns, console=console) as progress:
        task = progress.add_task("Generating Q&A pairs...", total=None)

        for record in chunk_stream:
            pdf_path = Path(_decode_bytes_field(record["pdf_path"]))
            doc_key = str(pdf_path)
            chunk_idx = int(record["chunk_index"])
            chunk_text = _decode_bytes_field(record["chunk_text"])

            if doc_key in completed_docs:
                if len(completed_docs) == len(pdf_files):
                    break
                continue

            if pairs_per_doc[doc_key] >= MAX_QA_PER_DOC:
                completed_docs.add(doc_key)
                if len(completed_docs) == len(pdf_files):
                    break
                continue

            dprint(
                f"DEBUG: Processing chunk {chunk_idx} from {pdf_path.name}\n"
                f"DEBUG: Chunk text (first 200 chars): "
                f"{chunk_text[:200].replace(os.linesep, ' ')}"
            )

            question = generate_question(
                chunk_text,
                question_generator,
                cfg.question_max_tokens,
            )
            if not question:
                console.print(
                    f"[yellow]Skipping chunk {chunk_idx} in {pdf_path.name}: "
                    f"No question generated.[/yellow]"
                )
                progress.update(task, advance=1)
                continue

            answer = generate_answer(
                chunk_text,
                question,
                answer_generator,
                cfg.answer_max_tokens,
            )
            if not answer:
                console.print(
                    f"[yellow]Skipping chunk {chunk_idx} in {pdf_path.name}: "
                    f"No answer generated.[/yellow]"
                )
                progress.update(task, advance=1)
                continue

            normalized_answer = answer.strip().lower()
            if normalized_answer == "not enough information":
                console.print(
                    f"[yellow]Skipping chunk {chunk_idx} in {pdf_path.name}: "
                    f"Question not answerable by context.[/yellow]"
                )
                progress.update(task, advance=1)
                continue

            qa_dataset.append(
                {
                    "query": question,
                    "ground_truth_answer": answer,
                    "relevant_document_text": chunk_text,
                    "relevant_document_source": str(pdf_path),
                }
            )

            pairs_per_doc[doc_key] += 1
            if pairs_per_doc[doc_key] >= cfg.max_qa_per_doc:
                completed_docs.add(doc_key)

            console.print(
                f"[green]Generated Q&A {pairs_per_doc[doc_key]}/{cfg.max_qa_per_doc} "
                f"for {pdf_path.name} (chunk {chunk_idx}).[/green]"
            )
            progress.update(task, advance=1)

    # Save final dataset
    cfg.output_dataset_path.parent.mkdir(parents=True, exist_ok=True)
    with cfg.output_dataset_path.open("w", encoding="utf-8") as f:
        json.dump(qa_dataset, f, indent=2, ensure_ascii=False)

    console.print(
        f"[bold green]Dataset generation complete! "
        f"Saved {len(qa_dataset)} Q&A pairs to {cfg.output_dataset_path}[/bold green]"
    )


if __name__ == "__main__":
    generate_qa_dataset()

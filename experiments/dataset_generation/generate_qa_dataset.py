import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import ollama
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from unstructured.partition.pdf import partition_pdf

console = Console()

# -----------------------------
# Config
# -----------------------------

SOURCE_DOCS_DIR = Path("var/source_docs")  # directory with PDFs
OUTPUT_DATASET_PATH = Path("var/benchmarking/generated_qa_dataset.json")

# Two-model setup: one for questions, one for answers
QUESTION_MODEL = os.getenv("OLLAMA_QUESTION_MODEL", "qwen3:8b")
ANSWER_MODEL = os.getenv("OLLAMA_ANSWER_MODEL", "deepseek-r1:8b")

# How many Q&A per PDF
MAX_QA_PER_DOC = int(os.getenv("MAX_QA_PER_DOC", "20"))

# Drop obvious garbage chunks
MIN_CHARS_PER_CHUNK = int(os.getenv("MIN_CHARS_PER_CHUNK", "80"))

DEBUG = os.getenv("QA_DEBUG", "1") == "1"


def dprint(msg: str) -> None:
    if DEBUG:
        console.print(f"[dim]{msg}[/dim]")


# -----------------------------
# Ollama helpers
# -----------------------------


def _extract_response_text(resp: Any) -> Optional[str]:
    """
    Normalize different Ollama Python client return types:
    - dict with 'response'
    - GenerateResponse (mapping + attributes)
    - Chat-like objects with message.content / message.thinking
    - Thinking models exposing .thinking on the root object
    """

    # 1) dict-style direct
    if isinstance(resp, dict):
        raw = resp.get("response", None)
        if raw:
            text = str(raw).strip()
            if text:
                return text

    # 2) mapping-style: resp['response'] (GenerateResponse supports __getitem__)
    try:
        if not isinstance(resp, dict):
            raw = resp["response"]  # type: ignore[index]
            if raw:
                text = str(raw).strip()
                if text:
                    return text
    except Exception:
        pass

    # 3) attribute-style: resp.response
    raw_attr = getattr(resp, "response", None)
    if raw_attr:
        text = str(raw_attr).strip()
        if text:
            return text

    # 4) generate() thinking-capable models: resp.thinking
    thinking_attr = getattr(resp, "thinking", None)
    if thinking_attr:
        text = str(thinking_attr).strip()
        if text:
            return text

    # 5) chat-like objects: resp.message.content / resp.message.thinking
    msg = getattr(resp, "message", None)
    if msg is not None:
        # content
        content = getattr(msg, "content", None)
        if not content and isinstance(msg, dict):
            content = msg.get("content", None)
        if content:
            text = str(content).strip()
            if text:
                return text

        # thinking (last resort)
        msg_thinking = getattr(msg, "thinking", None)
        if not msg_thinking and isinstance(msg, dict):
            msg_thinking = msg.get("thinking", None)
        if msg_thinking:
            text = str(msg_thinking).strip()
            if text:
                return text

    # 6) nothing worked
    dprint(
        f"DEBUG: Could not extract 'response' from object of type {type(resp)} "
        f"repr(resp)[:300]={repr(resp)[:300]}"
    )
    return None


def call_ollama_safely(
    *,
    model: str,
    prompt: str,
    temperature: float,
    num_predict: int,
    max_attempts: int = 3,
    backoff_sec: float = 1.0,
) -> Optional[str]:
    """
    Wraps ollama.generate with retries and error handling.
    Important: we explicitly set think=False to avoid dumping everything into `thinking`.
    """
    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            dprint(
                f"DEBUG: Calling ollama model={model}, "
                f"attempt {attempt}/{max_attempts}, num_predict={num_predict}"
            )
            resp = ollama.generate(
                model=model,
                prompt=prompt,
                stream=False,
                # options = model-level knobs
                options={
                    "temperature": temperature,
                    "num_predict": num_predict,
                },
                # top-level think flag (reasoning models: Qwen3, DeepSeek, GPT-OSS, etc.)
                think=False,
            )

            text = _extract_response_text(resp)
            dprint(f"DEBUG: Raw LLM response (first 200): {repr(text)[:200]}")

            if text:
                return text

            last_error = RuntimeError("Empty or missing 'response' from ollama")

        except Exception as e:
            last_error = e
            dprint(
                f"DEBUG: ollama.generate failed on attempt "
                f"{attempt}/{max_attempts}: {e}"
            )

        if attempt < max_attempts:
            time.sleep(backoff_sec * attempt)

    console.print(
        f"[yellow]Giving up on this chunk after {max_attempts} attempts. "
        f"Last error: {last_error}[/yellow]"
    )
    return None


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


def extract_chunks_for_pdf(pdf_path: Path) -> List[str]:
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
        if len(text) < MIN_CHARS_PER_CHUNK:
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


# -----------------------------
# Q & A generation
# -----------------------------


def generate_question(chunk_text: str) -> Optional[str]:
    question_prompt = (
        "You are an expert question generator. "
        "Create a single, clear, and concise question that can be directly answered "
        "by the following text. The question should be specific and require "
        "understanding of the provided context. Do not include the answer "
        "in the question.\n\n"
        f"Context:\n{chunk_text}\n\n"
        "Question:"
    )

    return call_ollama_safely(
        model=QUESTION_MODEL,
        prompt=question_prompt,
        temperature=0.0,
        num_predict=128,
    )


def generate_answer(chunk_text: str, question: str) -> Optional[str]:
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

    return call_ollama_safely(
        model=ANSWER_MODEL,
        prompt=answer_prompt,
        temperature=0.0,
        num_predict=256,
    )


# -----------------------------
# Main dataset generation
# -----------------------------


def generate_qa_dataset() -> None:
    console.print(
        "[bold cyan]Starting Q&A Dataset Generation with two models...[/bold cyan]"
    )
    console.print(
        f"[cyan]Question model:[/cyan] [bold]{QUESTION_MODEL}[/bold] | "
        f"[cyan]Answer model:[/cyan] [bold]{ANSWER_MODEL}[/bold]"
    )
    console.print(
        f"[cyan]Max Q&A pairs per document:[/cyan] [bold]{MAX_QA_PER_DOC}[/bold]"
    )
    console.print(
        f"[cyan]Min chars per chunk:[/cyan] [bold]{MIN_CHARS_PER_CHUNK}[/bold]"
    )

    pdf_files = list_pdf_files(SOURCE_DOCS_DIR)
    if not pdf_files:
        return

    qa_dataset: List[Dict[str, Any]] = []

    progress_columns = [
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
    ]

    with Progress(*progress_columns, console=console) as progress:
        task = progress.add_task("Generating Q&A pairs...", total=None)

        for pdf_path in pdf_files:
            chunks = extract_chunks_for_pdf(pdf_path)
            if not chunks:
                continue

            pairs_for_doc = 0

            for idx, chunk_text in enumerate(chunks, start=1):
                if pairs_for_doc >= MAX_QA_PER_DOC:
                    console.print(
                        f"[magenta]Reached MAX_QA_PER_DOC={MAX_QA_PER_DOC} "
                        f"for {pdf_path.name}. Moving to next document.[/magenta]"
                    )
                    break

                dprint(
                    f"DEBUG: Processing chunk {idx} from {pdf_path.name}\n"
                    f"DEBUG: Chunk text (first 200 chars): "
                    f"{chunk_text[:200].replace(os.linesep, ' ')}"
                )

                # --- Question ---
                question = generate_question(chunk_text)
                if not question:
                    console.print(
                        f"[yellow]Skipping chunk {idx} in {pdf_path.name}: "
                        f"No question generated.[/yellow]"
                    )
                    progress.update(task, advance=1)
                    continue

                # --- Answer ---
                answer = generate_answer(chunk_text, question)
                if not answer:
                    console.print(
                        f"[yellow]Skipping chunk {idx} in {pdf_path.name}: "
                        f"No answer generated.[/yellow]"
                    )
                    progress.update(task, advance=1)
                    continue

                if answer.strip().lower() == "not enough information":
                    console.print(
                        f"[yellow]Skipping chunk {idx} in {pdf_path.name}: "
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

                pairs_for_doc += 1
                console.print(
                    f"[green]Generated Q&A {pairs_for_doc}/{MAX_QA_PER_DOC} "
                    f"for {pdf_path.name} (chunk {idx}).[/green]"
                )
                progress.update(task, advance=1)

    # Save final dataset
    OUTPUT_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_DATASET_PATH.open("w", encoding="utf-8") as f:
        json.dump(qa_dataset, f, indent=2, ensure_ascii=False)

    console.print(
        f"[bold green]Dataset generation complete! "
        f"Saved {len(qa_dataset)} Q&A pairs to {OUTPUT_DATASET_PATH}[/bold green]"
    )


if __name__ == "__main__":
    generate_qa_dataset()

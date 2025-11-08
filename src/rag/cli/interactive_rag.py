
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.live import Live
import os
from pathlib import Path
from rag.retrieval.vdb import VectorDB
from libs.mlx_core.model_engine import MLXModelEngine
from rag.ingestion.create_vdb import process_pdfs
from rag.models.qwen_reranker import QwenReranker
import json

# --- Configuration ---
TEMPLATE = """You are an expert assistant. Your goal is to provide short, direct, and factually grounded answers based ONLY on the provided context. Your total response, including context, must not exceed 4096 tokens.

For each piece of context, the source document is provided. When you form your answer, you MUST cite the source document in the 'source' field of your JSON output. Do not make up sources.

Provide your answer in JSON format, as a list of dictionaries, where each dictionary has an 'answer' key for the concise response and a 'source' key for the citation.

Context:
{context}

Question: {question}

Concise Answer (JSON):"""

DEFAULT_VDB_PATH = "models/indexes/combined_vdb.npz"
DEFAULT_MODEL_ID = "mlx-community/Phi-3-mini-4k-instruct-unsloth-4bit"
SOURCE_DOCS_DIR = "var/source_docs"

# --- Typer App and Rich Console ---
app = typer.Typer(help="An interactive RAG CLI for querying documents with MLX.")
console = Console()

# --- RAG Core Class ---
class InteractiveRAG:
    def __init__(self, vdb_path: str, model_id: str):
        self.vdb_path = vdb_path
        self.model_id = model_id
        self.vdb = None
        self.model_engine = None
        self.cross_encoder = None
        self._load_components()

    def _load_components(self):
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task1 = progress.add_task("Loading VectorDB...", total=1)
            try:
                self.vdb = VectorDB(self.vdb_path)
                progress.update(task1, advance=1, description=f"[green]VectorDB loaded with {len(self.vdb.content)} chunks.")
            except Exception as e:
                progress.update(task1, description=f"[yellow]VectorDB not found or failed to load: {e}")
                self.vdb = VectorDB() # Initialize an empty VDB

            task2 = progress.add_task(f"Loading LLM ({self.model_id})...", total=1)
            self.model_engine = MLXModelEngine(self.model_id, model_type="text")
            progress.update(task2, advance=1, description="[green]LLM loaded.")

            task3 = progress.add_task("Loading Reranker (Qwen2)...", total=1)
            self.cross_encoder = QwenReranker("mlx-community/mxbai-rerank-large-v2")
            progress.update(task3, advance=1, description="[green]Reranker loaded.")

    def rebuild_vdb(self):
        console.print(f"[bold cyan]Rebuilding VectorDB from PDFs in {SOURCE_DOCS_DIR}...[/bold cyan]")
        pdf_files = list(Path(SOURCE_DOCS_DIR).glob("*.pdf"))
        if not pdf_files:
            console.print("[yellow]No PDF files found. VDB will be empty.[/yellow]")
            self.vdb = VectorDB()
            # Clear out the old VDB file if it exists
            if Path(self.vdb_path).exists():
                Path(self.vdb_path).unlink()
            return

        new_vdb = VectorDB() # Create a new, empty VDB instance

        progress_columns = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ]
        with Progress(*progress_columns, console=console) as progress:
            task = progress.add_task("Processing PDFs...", total=len(pdf_files))
            for pdf_path in pdf_files:
                pdf_path_str = str(pdf_path)
                console.print(f"\n[INFO] Processing {pdf_path_str}...")
                
                elements, _ = process_pdfs([pdf_path_str])
                content = "\n\n".join([e.text for e in elements])
                
                if content.strip():
                    new_vdb.ingest(content=content, document_name=pdf_path_str)
                else:
                    console.print(f"[yellow]No content extracted from {pdf_path_str}. Skipping.[/yellow]")
                
                progress.update(task, advance=1)

        if not new_vdb.content:
            console.print("[yellow]No content extracted from any PDFs. VDB remains unchanged.[/yellow]")
        else:
            new_vdb.savez(self.vdb_path)
            self.vdb = new_vdb
            console.print(f"[bold green]Vector database rebuilt successfully from {len(pdf_files)} PDF(s).[/bold green]")

    def ask_question(self, question: str):
        if not self.vdb or not self.vdb.content:
            console.print("[bold yellow]Warning:[/bold yellow] Vector database is empty. Please use 'rebuild-vdb' first.")
            return

        with console.status("[bold green]Retrieving and re-ranking documents..."):
            # 1. Retrieve a larger number of initial candidates
            initial_candidates = self.vdb.query(question, k=20) # Retrieve 20 candidates
            if not initial_candidates:
                console.print("[yellow]Could not retrieve any documents for the query.[/yellow]")
                return

            # 2. Re-rank the candidates with the cross-encoder
            candidate_texts = [c["text"] for c in initial_candidates]
            reranked_indices = self.cross_encoder.rank(question, candidate_texts)
            
            # Select the top 5 re-ranked candidates
            final_candidates = [initial_candidates[i] for i in reranked_indices[:5]]

            # 3. Format context for the LLM
            context = "\n---\n".join([
                f"Source: {chunk['source']}\nContent: {chunk['text']}"
                for chunk in final_candidates
            ])
            prompt = TEMPLATE.format(context=context, question=question)

        console.print(Panel.fit(context, title="Final Retrieved Context (Re-ranked)", border_style="blue"))

        console.print("\n[bold]Answer (streaming):[/bold]")
        
        full_response = ""
        # Stream tokens directly to the console for a typewriter effect
        for token in self.model_engine.stream_generate(prompt):
            console.print(token, end="")
            full_response += token
        
        console.print("\n") # Add a newline after streaming is complete

        # Now, parse and pretty-print the final JSON
        try:
            parsed_json = json.loads(full_response)
            pretty_json = json.dumps(parsed_json, indent=2)
            syntax = Syntax(pretty_json, "json", theme="default", line_numbers=True)
            console.print(Panel(syntax, title="Final Answer (Formatted JSON)", border_style="green"))
        except json.JSONDecodeError:
            console.print(Panel(full_response, title="Final Answer (Raw)", border_style="yellow"))

    def list_documents(self):
        if not self.vdb or not self.vdb.content:
            console.print("[yellow]No documents found in the vector database.[/yellow]")
            return

        # Get unique document names from the content list
        doc_names = sorted(list(set(item['source'] for item in self.vdb.content)))

        table = Table(title="Indexed Documents")
        table.add_column("Index", style="dim", width=6)
        table.add_column("Document Path", style="cyan")

        for i, doc_name in enumerate(doc_names):
            table.add_row(str(i + 1), doc_name)
        
        console.print(table)

    def run_interactive_loop(self):
        """Runs the interactive command loop for the CLI."""
        console.print("\n[bold]Entering interactive mode.[/bold]")
        console.print("Available commands: [cyan]ask[/cyan], [cyan]list-docs[/cyan], [cyan]rebuild-vdb[/cyan], [cyan]exit[/cyan]")
        while True:
            try:
                user_input = console.input("[bold magenta]RAG>[/bold magenta] ").strip()
                if not user_input:
                    continue
                
                command, *args = user_input.split(maxsplit=1)
                arg_line = args[0] if args else ""

                if command.lower() in ["exit", "quit"]:
                    console.print("[bold cyan]Goodbye![/bold cyan]")
                    break
                elif command.lower() == "ask":
                    if not arg_line:
                        console.print("[yellow]Please provide a question after 'ask'.[/yellow]")
                        continue
                    self.ask_question(arg_line)
                elif command.lower() == "list-docs":
                    self.list_documents()
                elif command.lower() == "rebuild-vdb":
                    self.rebuild_vdb()
                else:
                    console.print(f"[bold red]Error:[/bold red] Unknown command '{command}'")

            except (KeyboardInterrupt, EOFError):
                console.print("\n[bold cyan]Goodbye![/bold cyan]")
                break

# --- Typer Commands ---

# Global instance of the RAG engine
rag_cli: InteractiveRAG

@app.command()
def ask(question: str = typer.Argument(..., help="The question to ask the RAG system.")):
    """Ask a question and get an answer from the RAG system."""
    rag_cli.ask_question(question)

@app.command(name="list-docs")
def list_docs():
    """List all the documents currently indexed in the VectorDB."""
    rag_cli.list_documents()

@app.command(name="rebuild-vdb")
def rebuild_vdb():
    """Rebuild the VectorDB from the PDFs in the source directory."""
    rag_cli.rebuild_vdb()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    An interactive RAG CLI for querying documents with MLX.
    """
    global rag_cli
    # Initialize the RAG components only once before any command
    if not hasattr(ctx, "obj") or ctx.obj is None:
        initialize_app()
        ctx.obj = rag_cli

    if ctx.invoked_subcommand is None:
        rag_cli.run_interactive_loop()

# --- Main Execution ---

def initialize_app():
    """Initialize directories and load components."""
    console.print(Panel.fit("[bold green]Welcome to the Interactive RAG CLI![/bold green]", border_style="green"))
    os.makedirs(SOURCE_DOCS_DIR, exist_ok=True)
    
    vdb_path = Path(DEFAULT_VDB_PATH)
    # Initial VDB creation if it doesn't exist or is empty
    if not vdb_path.exists() or vdb_path.stat().st_size == 0:
        console.print(f"[yellow]No existing VDB found at {vdb_path}. Attempting initial build...[/yellow]")
        # Temporarily create an instance to call rebuild
        temp_rag = InteractiveRAG(DEFAULT_VDB_PATH, DEFAULT_MODEL_ID)
        temp_rag.rebuild_vdb()

    # Load the main RAG instance for the CLI commands
    global rag_cli
    rag_cli = InteractiveRAG(DEFAULT_VDB_PATH, DEFAULT_MODEL_ID)

if __name__ == "__main__":
    app()

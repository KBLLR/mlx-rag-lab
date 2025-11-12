from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def print_section(title: str):
    console.print(Panel(Text(title, justify="center", style="bold blue"), expand=False))

def print_variable(name: str, value: str):
    console.print(f"[bold green]{name}:[/bold green] [yellow]{value}[/yellow]")

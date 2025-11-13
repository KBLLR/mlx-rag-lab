"""
Classification CLI - sentiment analysis and text classification for chunks.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict

from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
import statistics

from apps.ui import (
    get_console,
    render_header,
    render_footer,
    render_confidence_bars,
    show_confidence_warning,
    truncate_source_path,
    get_confidence_color,
)

console = get_console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MLX Classification CLI - Sentiment analysis and text classification"
    )

    # Mode selection
    parser.add_argument(
        "--mode",
        type=str,
        choices=["sentiment", "emotion", "zero-shot", "interactive"],
        default="sentiment",
        help="Classification mode",
    )

    # Input source
    parser.add_argument(
        "--vdb-path",
        type=Path,
        help="Path to vector database to classify chunks from",
    )
    parser.add_argument(
        "--text",
        type=str,
        help="Single text to classify",
    )
    parser.add_argument(
        "--texts-file",
        type=Path,
        help="JSON file with list of texts to classify",
    )

    # Zero-shot options
    parser.add_argument(
        "--labels",
        type=str,
        nargs="+",
        help="Labels for zero-shot classification (space-separated)",
    )
    parser.add_argument(
        "--labels-file",
        type=Path,
        help="JSON file with labels or label descriptions",
    )

    # Output options
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON file for results",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of top predictions to show/save",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.1,
        help="Minimum confidence score threshold (default 0.1, use 0.0 to show all)",
    )

    return parser


def classify_vdb_chunks(
    vdb_path: Path,
    classifier,
    mode: str,
    labels: List[str],
    top_k: int,
    min_score: float
) -> List[Dict]:
    """Classify all chunks from a vector database."""
    from rag.retrieval.vdb import VectorDB

    console.print(f"\n[bold cyan]Loading VDB from {vdb_path}[/bold cyan]")
    vdb = VectorDB(str(vdb_path))

    console.print(f"[green]Found {len(vdb.content)} chunks to classify[/green]\n")

    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Classifying chunks...", total=len(vdb.content))

        # Process in batches for efficiency
        batch_size = 32
        for i in range(0, len(vdb.content), batch_size):
            batch_chunks = vdb.content[i : i + batch_size]
            batch_texts = [chunk["text"] for chunk in batch_chunks]

            # Classify batch
            predictions = classifier.classify_batch(
                batch_texts, labels or [], top_k=top_k, mode=mode
            )

            # Store results
            for chunk, preds in zip(batch_chunks, predictions):
                # Filter by min_score
                filtered_preds = [(label, score) for label, score in preds if score >= min_score]

                if filtered_preds:
                    results.append({
                        "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                        "source": chunk.get("source", "unknown"),
                        "predictions": [
                            {"label": label, "score": float(score)}
                            for label, score in filtered_preds
                        ]
                    })

            progress.update(task, advance=len(batch_chunks))

    return results


def render_confidence_bars_string(predictions: List[Dict], max_width: int = 15) -> str:
    """Render horizontal bar chart for confidence scores as a string for table cells."""
    bars = []
    for pred in predictions:
        label = pred['label']
        score = pred['score']
        filled = int(score * max_width)
        bar = "█" * filled + "░" * (max_width - filled)

        # Use shared color function
        color = get_confidence_color(score)
        bars.append(f"[{color}]{bar}[/{color}] {label} ({score:.1%})")

    return "\n".join(bars)


def detect_low_confidence(results: List[Dict]) -> Dict:
    """Detect patterns indicating low model confidence."""
    if not results:
        return {"is_low_confidence": False}

    all_scores = []
    for result in results:
        if result.get("predictions"):
            all_scores.extend([p["score"] for p in result["predictions"]])

    if not all_scores or len(all_scores) < 2:
        return {"is_low_confidence": False}

    avg_score = statistics.mean(all_scores)
    std_dev = statistics.stdev(all_scores)

    # Check for uniform distributions (all scores very similar)
    is_uniform = std_dev < 0.02

    # Check for low maximum scores
    max_score = max(all_scores)
    is_low_max = max_score < 0.2

    return {
        "is_low_confidence": is_uniform or is_low_max,
        "reason": "uniform distribution" if is_uniform else "low maximum score" if is_low_max else None,
        "avg_score": avg_score,
        "std_dev": std_dev,
        "max_score": max_score,
    }


def display_results(results: List[Dict], top_k: int = 3, mode: str = "sentiment", vdb_path: str = None):
    """Display classification results in a table with confidence visualization."""
    if not results:
        console.print("[yellow]No results matched the criteria (possibly min-score threshold too high)[/yellow]")
        console.print("[dim]Try lowering --min-score to 0.0 to see all results[/dim]")
        return

    # Render header with metadata
    meta = {"Mode": mode.title()}
    if vdb_path:
        meta["VDB"] = Path(vdb_path).name
    meta["Results"] = len(results)
    render_header("Classification Results", meta)

    # Check for low confidence patterns
    confidence_analysis = detect_low_confidence(results)
    if confidence_analysis["is_low_confidence"]:
        warning_msg = f"""⚠️  [bold yellow]Low Confidence Detected[/bold yellow]

The model appears uncertain about these classifications.
Reason: {confidence_analysis["reason"]}

Statistics:
• Average score: {confidence_analysis["avg_score"]:.1%}
• Score variation: {confidence_analysis["std_dev"]:.3f}
• Maximum score: {confidence_analysis["max_score"]:.1%}

[dim]This often indicates:[/dim]
[dim]• Content doesn't clearly match any category[/dim]
[dim]• Model may need fine-tuning for this domain[/dim]
[dim]• Consider different labels or classification mode[/dim]"""

        console.print(Panel(warning_msg, border_style="yellow", title="Confidence Warning"))
        console.print()

    table = Table(show_header=True, header_style="bold magenta", title_style="bold cyan")
    table.add_column("Text", style="cyan", no_wrap=False, max_width=40)
    table.add_column("Source", style="dim", max_width=35)
    table.add_column("Confidence", style="white", no_wrap=False)

    for result in results[:20]:  # Show first 20
        text = result["text"]
        source = truncate_source_path(result.get("source", "N/A"), max_len=35)

        # Format predictions with bars
        bars = render_confidence_bars_string(result["predictions"][:top_k])

        table.add_row(text, source, bars)

    console.print(table)

    if len(results) > 20:
        console.print(f"\n[dim]... and {len(results) - 20} more results[/dim]")

    # Show footer with helpful hints
    render_footer(["Use --output to save results", "Use --min-score to filter", "Use --top-k to limit predictions"])


def interactive_mode(classifier, mode: str, labels: List[str]):
    """Interactive classification mode."""
    meta = {"Mode": mode.title()}
    if labels and mode == "zero-shot":
        meta["Labels"] = ", ".join(labels[:3]) + ("..." if len(labels) > 3 else "")
    render_header("Interactive Classification", meta)

    render_footer(["Type text to classify", "Ctrl+C to exit"])
    console.print()

    while True:
        try:
            text = input("📝 > ").strip()
            if not text:
                continue

            # Classify
            predictions = classifier.classify_single(text, labels, top_k=5, mode=mode)

            # Display
            console.print("\n[bold]Predictions:[/bold]")
            for label, score in predictions:
                # Color code by score
                if score > 0.5:
                    color = "green"
                elif score > 0.3:
                    color = "yellow"
                else:
                    color = "red"

                console.print(f"  [{color}]{label}: {score:.2%}[/{color}]")

            console.print()

        except (EOFError, KeyboardInterrupt):
            console.print("\n[cyan]Bye![/cyan]")
            break


def main() -> None:
    args = build_parser().parse_args()

    # Initialize classifier
    from rag.models.text_classifier import TextClassifier

    console.print("[bold]Initializing MLX Text Classifier...[/bold]")
    classifier = TextClassifier()

    # Load labels if provided
    labels = None
    if args.labels:
        labels = args.labels
    elif args.labels_file and args.labels_file.exists():
        with open(args.labels_file) as f:
            labels_data = json.load(f)
            if isinstance(labels_data, list):
                labels = labels_data
            elif isinstance(labels_data, dict):
                # Use descriptions if provided
                labels = list(labels_data.keys())

    # Validate mode requirements
    if args.mode == "zero-shot" and not labels:
        console.print("[red]Error: zero-shot mode requires --labels or --labels-file[/red]")
        return

    # Interactive mode
    if args.mode == "interactive":
        interactive_mode(classifier, args.mode, labels or [])
        return

    # Determine input source
    results = []

    if args.vdb_path:
        results = classify_vdb_chunks(
            args.vdb_path, classifier, args.mode, labels, args.top_k, args.min_score
        )
    elif args.text:
        predictions = classifier.classify_single(
            args.text, labels, top_k=args.top_k, mode=args.mode
        )
        results = [{
            "text": args.text,
            "predictions": [
                {"label": label, "score": float(score)}
                for label, score in predictions
            ]
        }]
    elif args.texts_file and args.texts_file.exists():
        with open(args.texts_file) as f:
            texts = json.load(f)

        predictions = classifier.classify_batch(texts, labels or [], top_k=args.top_k, mode=args.mode)

        results = [{
            "text": text,
            "predictions": [
                {"label": label, "score": float(score)}
                for label, score in preds
            ]
        } for text, preds in zip(texts, predictions)]
    else:
        console.print("[red]Error: Please provide input via --vdb-path, --text, or --texts-file[/red]")
        return

    # Display results
    console.print()
    display_results(results, args.top_k, mode=args.mode, vdb_path=str(args.vdb_path) if args.vdb_path else None)

    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Add timestamp to filename to prevent overwrites if file exists
        if output_path.exists():
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stem = output_path.stem
            suffix = output_path.suffix
            output_path = output_path.parent / f"{stem}_{timestamp}{suffix}"
            console.print(f"[yellow]File exists, saving to {output_path.name} instead[/yellow]")

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]✓ Results saved to {output_path}[/green]")

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total classified: {len(results)}")

    if args.mode == "sentiment":
        # Count sentiments
        sentiment_counts = {}
        for result in results:
            if result["predictions"]:
                top_label = result["predictions"][0]["label"]
                sentiment_counts[top_label] = sentiment_counts.get(top_label, 0) + 1

        console.print(f"\n[bold]Sentiment Distribution:[/bold]")
        for sentiment, count in sorted(sentiment_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(results)) * 100
            console.print(f"  {sentiment}: {count} ({percentage:.1f}%)")


if __name__ == "__main__":
    main()

"""Smart Campus Room Ingestion CLI

This script ingests room personality data from JSON files into the RAG vector database.
It's designed for Phase-4 Smart Campus integration.

Usage:
    uv run ingest-rooms-cli --rooms-dir /path/to/rooms/data
    uv run ingest-rooms-cli --rooms-dir /path/to/rooms/data --collection rooms --output var/indexes/rooms/vdb.npz

Expected JSON format for room files:
{
  "room_id": "peace",
  "name": "Peace Room",
  "personality": "The Peace room is designed for quiet, focused individual work...",
  "rules": ["Maintain silence at all times", "Use headphones for any audio"],
  "atmosphere": "Calm, minimal distractions, soft lighting",
  "entities": [
    {
      "entity_id": "sensor.peace_temperature",
      "description": "Monitors room temperature for optimal study conditions"
    }
  ]
}
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure src is in path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from rag.retrieval.vdb import VectorDB

console = Console()

DEFAULT_COLLECTION = "rooms"
DEFAULT_OUTPUT_PATH = "var/indexes/rooms/vdb.npz"


def load_room_json(file_path: Path) -> Dict[str, Any]:
    """Load and parse a room JSON file.

    Args:
        file_path: Path to the room JSON file

    Returns:
        Parsed room data dictionary

    Raises:
        json.JSONDecodeError: If file is not valid JSON
        FileNotFoundError: If file does not exist
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_room_chunks(room_data: Dict[str, Any], source_file: str) -> List[Dict[str, Any]]:
    """Extract text chunks from room data with appropriate metadata.

    Args:
        room_data: Parsed room JSON data
        source_file: Source filename for attribution

    Returns:
        List of chunk dictionaries with text, metadata
    """
    chunks = []
    room_id = room_data.get("room_id", "unknown")
    room_name = room_data.get("name", room_id)

    # Extract personality section
    personality = room_data.get("personality", "")
    if personality.strip():
        chunks.append({
            "text": f"Room: {room_name}\n\nPersonality: {personality}",
            "metadata": {
                "room_id": room_id,
                "source_file": source_file,
                "section": "personality",
                "tags": ["personality", "description"],
            }
        })

    # Extract rules section (join list into text)
    rules = room_data.get("rules", [])
    if rules:
        rules_text = f"Room: {room_name}\n\nRules:\n" + "\n".join(f"- {rule}" for rule in rules)
        chunks.append({
            "text": rules_text,
            "metadata": {
                "room_id": room_id,
                "source_file": source_file,
                "section": "rules",
                "tags": ["rules", "guidelines"],
            }
        })

    # Extract atmosphere section
    atmosphere = room_data.get("atmosphere", "")
    if atmosphere.strip():
        chunks.append({
            "text": f"Room: {room_name}\n\nAtmosphere: {atmosphere}",
            "metadata": {
                "room_id": room_id,
                "source_file": source_file,
                "section": "atmosphere",
                "tags": ["atmosphere", "environment"],
            }
        })

    # Extract entity descriptions
    entities = room_data.get("entities", [])
    for entity in entities:
        entity_id = entity.get("entity_id", "")
        description = entity.get("description", "")
        if entity_id and description:
            chunks.append({
                "text": f"Room: {room_name}\n\nEntity: {entity_id}\n{description}",
                "metadata": {
                    "room_id": room_id,
                    "source_file": source_file,
                    "section": "entity",
                    "entity_id": entity_id,
                    "tags": ["entity", "sensor", "device"],
                }
            })

    return chunks


def ingest_rooms(rooms_dir: Path, collection: str, output_path: Path) -> int:
    """Ingest all room JSON files from a directory into the vector database.

    Args:
        rooms_dir: Directory containing room JSON files
        collection: Collection name for metadata
        output_path: Output path for the vector database file

    Returns:
        Number of chunks ingested

    Raises:
        FileNotFoundError: If rooms_dir does not exist
    """
    if not rooms_dir.exists():
        raise FileNotFoundError(f"Rooms directory not found: {rooms_dir}")

    # Find all JSON files
    json_files = list(rooms_dir.glob("*.json"))

    if not json_files:
        console.print(f"[yellow]No JSON files found in {rooms_dir}[/yellow]")
        return 0

    console.print(f"\n[bold cyan]Ingesting Smart Campus Rooms[/bold cyan]")
    console.print(f"Source: {rooms_dir}")
    console.print(f"Collection: {collection}")
    console.print(f"Output: {output_path}")
    console.print(f"Found: {len(json_files)} room file(s)\n")

    # Initialize VectorDB
    vdb = VectorDB()
    total_chunks = 0
    processed_files = []

    # Progress bar
    progress_columns = [
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ]

    with Progress(*progress_columns, console=console) as progress:
        task = progress.add_task("Processing rooms...", total=len(json_files))

        for json_file in json_files:
            try:
                # Load room data
                room_data = load_room_json(json_file)
                room_id = room_data.get("room_id", json_file.stem)

                # Extract chunks
                chunks = extract_room_chunks(room_data, json_file.name)

                if not chunks:
                    console.print(f"[yellow]No content extracted from {json_file.name}[/yellow]")
                    progress.update(task, advance=1)
                    continue

                # Ingest each chunk
                for chunk_data in chunks:
                    vdb.ingest(
                        content=chunk_data["text"],
                        document_name=json_file.name,
                        metadata=chunk_data["metadata"],
                    )
                    total_chunks += 1

                processed_files.append(json_file.name)

            except json.JSONDecodeError as e:
                console.print(f"[red]Invalid JSON in {json_file.name}: {e}[/red]")
            except Exception as e:
                console.print(f"[red]Error processing {json_file.name}: {e}[/red]")

            progress.update(task, advance=1)

    # Save VectorDB
    if total_chunks > 0:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        vdb.savez(str(output_path))

        # Write metadata file
        metadata_path = output_path.parent / "metadata.json"
        metadata = {
            "collection": collection,
            "num_chunks": total_chunks,
            "num_files": len(processed_files),
            "files": processed_files,
            "source_dir": str(rooms_dir),
        }
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        console.print(f"\n[bold green]✓ Ingestion complete![/bold green]")
        console.print(f"  • Files processed: {len(processed_files)}")
        console.print(f"  • Chunks created: {total_chunks}")
        console.print(f"  • Index saved: {output_path}")
        console.print(f"  • Metadata saved: {metadata_path}\n")
    else:
        console.print("\n[yellow]No chunks were created. VectorDB not saved.[/yellow]\n")

    return total_chunks


def main() -> None:
    """Entry point for the room ingestion CLI."""
    parser = argparse.ArgumentParser(
        description="Ingest Smart Campus room data into RAG vector database (Phase-4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--rooms-dir",
        type=Path,
        required=True,
        help="Directory containing room JSON files",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=DEFAULT_COLLECTION,
        help=f"Collection name (default: {DEFAULT_COLLECTION})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(DEFAULT_OUTPUT_PATH),
        help=f"Output path for vector database (default: {DEFAULT_OUTPUT_PATH})",
    )

    args = parser.parse_args()

    try:
        num_chunks = ingest_rooms(
            rooms_dir=args.rooms_dir,
            collection=args.collection,
            output_path=args.output,
        )

        if num_chunks == 0:
            sys.exit(1)

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

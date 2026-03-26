from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from chroma_support import ChromaSettings, ingest_document, parse_metadata

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    file: Path = typer.Argument(..., help="Archivo a ingestar"),
    metadata: Optional[List[str]] = typer.Option(
        None,
        "--metadata",
        "-m",
        help="Metadata adicional (clave=valor). Puedes repetir la opción.",
    ),
    encoding: str = typer.Option("utf-8", help="Encoding del archivo"),
):
    """Ingesta un documento en la colección de Chroma."""

    settings = ChromaSettings.from_env()
    user_metadata = parse_metadata(metadata)

    try:
        summary = ingest_document(
            file,
            metadata=user_metadata,
            encoding=encoding,
            settings=settings,
        )
    except FileNotFoundError as exc:
        raise typer.BadParameter(str(exc)) from exc
    except Exception as exc:
        console.print(f"[red]Error durante la ingesta:[/] {exc}")
        raise typer.Exit(code=1)

    table = Table(title="Resumen de ingesta")
    table.add_column("Documento")
    table.add_column("Chunks")
    table.add_column("Metadata extra")
    table.add_row(str(summary["document"]), str(summary["chunks"]), str(user_metadata or {}))
    console.print(table)


if __name__ == "__main__":
    app()
